package main

import (
	"context"
	"fmt"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/RicardoMBregalda/tcc-log-management/go-api/internal/cache"
	"github.com/RicardoMBregalda/tcc-log-management/go-api/internal/database"
	"github.com/RicardoMBregalda/tcc-log-management/go-api/internal/fabric"
	"github.com/RicardoMBregalda/tcc-log-management/go-api/internal/handlers"
	"github.com/RicardoMBregalda/tcc-log-management/go-api/internal/merkle"
	"github.com/RicardoMBregalda/tcc-log-management/go-api/internal/middleware"
	"github.com/RicardoMBregalda/tcc-log-management/go-api/internal/models"
	"github.com/RicardoMBregalda/tcc-log-management/go-api/internal/wal"
	"github.com/RicardoMBregalda/tcc-log-management/go-api/pkg/config"
	
	"github.com/gin-gonic/gin"
	swaggerFiles "github.com/swaggo/files"
	ginSwagger "github.com/swaggo/gin-swagger"
	
	_ "github.com/RicardoMBregalda/tcc-log-management/go-api/docs" // swagger docs
)

// Version and build information (set via ldflags)
var (
	Version   = "dev"
	BuildTime = "unknown"
)

// @title Log Management API
// @version 1.0
// @description High-performance log management API with WAL, Merkle Tree, and Fabric integration
// @termsOfService http://swagger.io/terms/

// @contact.name Ricardo M. Bregalda
// @contact.email ricardo@example.com

// @license.name MIT
// @license.url https://opensource.org/licenses/MIT

// @host localhost:5001
// @BasePath /

// @schemes http https

// @securityDefinitions.apikey ApiKeyAuth
// @in header
// @name Authorization

func main() {
	// Print banner
	printBanner()

	// TODO: Initialize logger (zap or logrus)
	log.Println("🔧 Initializing logger...")

	// Load configuration
	log.Println("📝 Loading configuration...")
	cfg, err := config.LoadConfig("config.yaml")
	if err != nil {
		log.Fatalf("❌ Failed to load configuration: %v", err)
	}

	// Connect to MongoDB with retry
	log.Println("🗄️  Connecting to MongoDB...")
	mongoClient, err := database.ConnectWithRetry(&cfg.MongoDB, 5)
	if err != nil {
		log.Fatalf("❌ Failed to connect to MongoDB: %v", err)
	}
	defer mongoClient.Close(context.Background())
	log.Println("✅ MongoDB connected")

	// Initialize collections
	collections := database.NewCollections(mongoClient)

	// Connect to Redis
	log.Println("💾 Connecting to Redis...")
	redisCache, err := cache.NewRedisClient(&cfg.Redis)
	if err != nil {
		log.Printf("⚠️  Warning: Failed to create Redis client: %v", err)
	} else if redisCache.Enabled {
		defer redisCache.Close()
		log.Println("✅ Redis cache connected")
	} else {
		log.Println("⚠️  Redis cache disabled (graceful degradation)")
	}

	// Initialize WAL
	log.Println("🔒 Initializing Write-Ahead Log...")
	insertCallback := func(log *models.Log) error {
		ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		defer cancel()
		return collections.InsertLog(ctx, log)
	}
	
	walInstance, err := wal.NewWriteAheadLog(cfg.WAL.Directory, cfg.WAL.CheckInterval)
	if err != nil {
		log.Printf("⚠️  Warning: Failed to create WAL: %v", err)
		// Create dummy WAL
		walInstance = &wal.WriteAheadLog{}
	} else if cfg.WAL.Enabled {
		walInstance.StartProcessor(insertCallback)
		log.Println("✅ WAL processor started")
	} else {
		log.Println("⚠️  WAL disabled")
	}
	defer func() {
		if cfg.WAL.Enabled && walInstance != nil {
			walInstance.StopProcessor()
		}
	}()

	// Initialize Fabric client
	log.Println("🔗 Initializing Fabric client...")
	fabricClient := fabric.NewFabricClient(&cfg.Fabric)
	if cfg.Fabric.SyncEnabled {
		log.Println("✅ Fabric client initialized")
	} else {
		log.Println("⚠️  Fabric sync disabled")
	}

	// Initialize Merkle Batch Processor
	log.Println("🌳 Initializing Merkle Tree Batch Processor...")
	batchProcessor := merkle.NewBatchProcessor(collections, fabricClient, &cfg.Batching)
	
	ctx := context.Background()
	if err := batchProcessor.Start(ctx); err != nil {
		log.Fatalf("❌ Failed to start batch processor: %v", err)
	}
	defer func() {
		stopCtx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
		defer cancel()
		batchProcessor.Stop(stopCtx)
	}()
	log.Printf("✅ Batch processor started with %d workers\n", cfg.Batching.BatchExecutorWorkers)

	// Setup Gin router
	if !cfg.Server.Debug {
		gin.SetMode(gin.ReleaseMode)
	}

	router := gin.New()

	// Middlewares
	router.Use(gin.Logger())
	router.Use(gin.Recovery())
	router.Use(middleware.CORS())
	router.Use(middleware.RequestID())
	router.Use(middleware.SecurityHeaders())

	// Create app dependencies
	deps := NewAppDependencies(cfg, mongoClient, collections, redisCache, fabricClient, batchProcessor)

	// Create handlers
	healthHandler := handlers.NewHealthHandler(mongoClient, collections, redisCache, fabricClient, batchProcessor, Version, BuildTime)
	logHandler := handlers.NewLogHandler(collections, redisCache, walInstance)
	merkleHandler := handlers.NewMerkleHandler(batchProcessor, redisCache)
	walHandler := handlers.NewWALHandler(walInstance)
	statsHandler := handlers.NewStatsHandler(collections, mongoClient, redisCache, fabricClient, batchProcessor, walInstance)

	// Register routes
	registerRoutes(router, deps, healthHandler, logHandler, merkleHandler, walHandler, statsHandler)

	// TODO: Register Swagger docs

	// Setup server
	port := os.Getenv("SERVER_PORT")
	if port == "" {
		port = "5001"
	}

	srv := &http.Server{
		Addr:         fmt.Sprintf(":%s", port),
		Handler:      router,
		ReadTimeout:  30 * time.Second,
		WriteTimeout: 30 * time.Second,
		IdleTimeout:  120 * time.Second,
	}

	// Start server in goroutine
	go func() {
		log.Printf("🚀 Starting server on port %s...\n", port)
		log.Printf("📖 API Documentation: http://localhost:%s/swagger/index.html\n", port)
		log.Printf("🏥 Health Check: http://localhost:%s/health\n", port)

		if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatalf("❌ Failed to start server: %v\n", err)
		}
	}()

	// Wait for interrupt signal for graceful shutdown
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit

	log.Println("🛑 Shutting down server...")

	// Graceful shutdown with timeout
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	// TODO: Stop WAL processor
	// TODO: Close MongoDB connection
	// TODO: Close Redis connection

	if err := srv.Shutdown(ctx); err != nil {
		log.Fatal("❌ Server forced to shutdown:", err)
	}

	log.Println("✅ Server exited gracefully")
}

// registerRoutes registers all API routes
func registerRoutes(
	router *gin.Engine, 
	deps *AppDependencies,
	healthHandler *handlers.HealthHandler,
	logHandler *handlers.LogHandler,
	merkleHandler *handlers.MerkleHandler,
	walHandler *handlers.WALHandler,
	statsHandler *handlers.StatsHandler,
) {
	// Root redirect
	router.GET("/", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{
			"name":    "Go Log Management API",
			"version": Version,
			"docs":    "/swagger/index.html",
		})
	})

	// Health endpoint
	router.GET("/health", healthHandler.HealthCheck)

	// API v1 group
	v1 := router.Group("/api/v1")
	{
		// TODO: Register handlers
		v1.GET("/ping", func(c *gin.Context) {
			c.JSON(http.StatusOK, gin.H{
				"message": "pong",
				"version": Version,
			})
		})
	}

	// Logs endpoints
	logs := router.Group("/logs")
	{
		logs.POST("", logHandler.CreateLog)
		logs.GET("", logHandler.GetLogs)
		logs.GET("/:id", logHandler.GetLogByID)
		logs.DELETE("/:id", logHandler.DeleteLog)
	}

	// Merkle endpoints
	merkle := router.Group("/merkle")
	{
		merkle.POST("/batch", merkleHandler.CreateBatch)
		merkle.GET("/batch/:id", merkleHandler.GetBatch)
		merkle.POST("/verify/:id", merkleHandler.VerifyBatch)
		merkle.GET("/batches", merkleHandler.ListBatches)
		merkle.GET("/stats", merkleHandler.GetBatchStats)
		merkle.POST("/force-batch", merkleHandler.ForceBatch)
	}

	// WAL endpoints
	walGroup := router.Group("/wal")
	{
		walGroup.GET("/stats", walHandler.GetStats)
		walGroup.POST("/force-process", walHandler.ForceProcess)
		walGroup.GET("/health", walHandler.GetHealth)
	}

	// Stats endpoints
	stats := router.Group("/stats")
	{
		stats.GET("", statsHandler.GetStats)
		stats.GET("/logs", statsHandler.GetLogStats)
		stats.GET("/sync", statsHandler.GetSyncStats)
	}

	// Swagger documentation
	router.GET("/swagger/*any", ginSwagger.WrapHandler(swaggerFiles.Handler))
}

// Legacy handlers - keeping for backward compatibility
// makeHealthHandler creates a health check handler with dependencies (deprecated)
// @Summary Health check
// @Description Check if the API is running and healthy
// @Tags Health
// @Produce json
// @Success 200 {object} map[string]interface{}
// @Router /health [get]
func makeHealthHandler(deps *AppDependencies) gin.HandlerFunc {
	return func(c *gin.Context) {
		ctx, cancel := context.WithTimeout(c.Request.Context(), 3*time.Second)
		defer cancel()

		status := "healthy"
		services := gin.H{}

		// Check MongoDB
		mongoStatus := "healthy"
		if err := deps.MongoClient.HealthCheck(ctx); err != nil {
			mongoStatus = "unhealthy"
			status = "degraded"
		}
		services["mongodb"] = mongoStatus

		// Check Redis
		redisStatus := "disabled"
		if deps.RedisCache.Enabled {
			if err := deps.RedisCache.HealthCheck(ctx); err != nil {
				redisStatus = "unhealthy"
				status = "degraded"
			} else {
				redisStatus = "healthy"
			}
		}
		services["redis"] = redisStatus

		// Check Fabric
		fabricStatus := "disabled"
		if deps.Config.Fabric.SyncEnabled {
			if err := deps.FabricClient.HealthCheck(ctx); err != nil {
				fabricStatus = "unhealthy"
				status = "degraded"
			} else {
				fabricStatus = "healthy"
			}
		}
		services["fabric"] = fabricStatus

		// Check Batch Processor
		batchStatus := "stopped"
		if deps.BatchProcessor.IsRunning() {
			batchStatus = "running"
		}
		services["batch_processor"] = batchStatus

		c.JSON(http.StatusOK, gin.H{
			"status":     status,
			"version":    Version,
			"build_time": BuildTime,
			"timestamp":  time.Now().UTC().Format(time.RFC3339),
			"services":   services,
		})
	}
}

// makeStatsHandler creates a stats handler with dependencies
func makeStatsHandler(deps *AppDependencies) gin.HandlerFunc {
	return func(c *gin.Context) {
		ctx, cancel := context.WithTimeout(c.Request.Context(), 5*time.Second)
		defer cancel()

		stats := gin.H{
			"timestamp": time.Now().UTC().Format(time.RFC3339),
		}

		// MongoDB stats
		if mongoStats, err := deps.MongoClient.GetStats(ctx); err == nil {
			stats["mongodb"] = mongoStats
		}

		// Redis stats
		if deps.RedisCache.Enabled {
			if redisStats, err := deps.RedisCache.GetStats(ctx); err == nil {
				stats["redis"] = redisStats
			}
		}

		// Fabric stats
		if deps.Config.Fabric.SyncEnabled {
			stats["fabric"] = deps.FabricClient.GetStats()
		}

		// Batch processor stats
		stats["batch_processor"] = deps.BatchProcessor.GetStats()

		// Sync stats
		if syncStats, err := deps.Collections.AggregateSyncStats(ctx); err == nil {
			stats["sync"] = syncStats
		}

		// Total logs count
		if totalLogs, err := deps.Collections.CountLogs(ctx, map[string]interface{}{}); err == nil {
			stats["total_logs"] = totalLogs
		}

		c.JSON(http.StatusOK, stats)
	}
}



// printBanner prints the application banner
func printBanner() {
	banner := `
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║    🚀 Go Log Management API                                   ║
║    Version: %-10s                                       ║
║    Build: %-15s                                       ║
║                                                               ║
║    ⚡ High-Performance • 🔒 Zero Data Loss • 🌳 Merkle Tree  ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
`
	fmt.Printf(banner, Version, BuildTime)
}
