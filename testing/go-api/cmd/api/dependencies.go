package main

import (
	"github.com/RicardoMBregalda/tcc-log-management/go-api/internal/cache"
	"github.com/RicardoMBregalda/tcc-log-management/go-api/internal/database"
	"github.com/RicardoMBregalda/tcc-log-management/go-api/internal/fabric"
	"github.com/RicardoMBregalda/tcc-log-management/go-api/internal/merkle"
	"github.com/RicardoMBregalda/tcc-log-management/go-api/pkg/config"
)

// AppDependencies holds all application dependencies
type AppDependencies struct {
	Config         *config.Config
	MongoClient    *database.MongoClient
	Collections    *database.Collections
	RedisCache     *cache.RedisCache
	FabricClient   *fabric.FabricClient
	BatchProcessor *merkle.BatchProcessor
	// WAL will be added later
}

// NewAppDependencies creates a new AppDependencies instance
func NewAppDependencies(
	cfg *config.Config,
	mongoClient *database.MongoClient,
	collections *database.Collections,
	redisCache *cache.RedisCache,
	fabricClient *fabric.FabricClient,
	batchProcessor *merkle.BatchProcessor,
) *AppDependencies {
	return &AppDependencies{
		Config:         cfg,
		MongoClient:    mongoClient,
		Collections:    collections,
		RedisCache:     redisCache,
		FabricClient:   fabricClient,
		BatchProcessor: batchProcessor,
	}
}
