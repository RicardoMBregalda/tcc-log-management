package main

import (
	"database/sql"
	"fmt"
	"math/rand"
	"sort"
	"strings"
	"sync"
	"sync/atomic"
	"time"

	_ "github.com/lib/pq"
)

// PostgresTester testa a arquitetura tradicional com PostgreSQL
type PostgresTester struct {
	ConnectionString string
	DB               *sql.DB
	MaxConnections   int
}

// NewPostgresTester cria um novo testador PostgreSQL
func NewPostgresTester(connString string, maxConns int) (*PostgresTester, error) {
	// Garantir parâmetros essenciais se não estiverem presentes
	if !strings.Contains(connString, "sslmode") {
		connString += " sslmode=disable"
	}
	if !strings.Contains(connString, "user=") {
		connString += " user=loguser"
	}
	if !strings.Contains(connString, "password=") {
		connString += " password=logpass"
	}
	if !strings.Contains(connString, "dbname=") {
		connString += " dbname=logdb"
	}
	if !strings.Contains(connString, "port=") {
		connString += " port=5432"
	}
	
	db, err := sql.Open("postgres", connString)
	if err != nil {
		return nil, fmt.Errorf("failed to open database: %w", err)
	}

	// Configurar pool de conexões
	db.SetMaxOpenConns(maxConns)
	db.SetMaxIdleConns(maxConns / 2)
	db.SetConnMaxLifetime(time.Minute * 3)

	// Testar conexão
	if err := db.Ping(); err != nil {
		db.Close()
		// Não mostrar senha no erro
		safeConnString := strings.ReplaceAll(connString, "password=logpass", "password=***")
		return nil, fmt.Errorf("failed to ping database: %w (connection: %s)", err, safeConnString)
	}

	return &PostgresTester{
		ConnectionString: connString,
		DB:               db,
		MaxConnections:   maxConns,
	}, nil
}

// Close fecha a conexão com o banco
func (pt *PostgresTester) Close() error {
	if pt.DB != nil {
		return pt.DB.Close()
	}
	return nil
}

// GeneratePostgresLog gera um log de teste para PostgreSQL
func GeneratePostgresLog() PostgresLog {
	sources := []string{"test-service-1", "test-service-2", "test-service-3", "test-service-4"}
	levels := []string{"DEBUG", "INFO", "WARNING", "ERROR"}
	actions := []string{"login", "logout", "update", "delete", "create", "read", "write"}
	users := []string{"user1", "user2", "user3", "admin", "guest"}

	return PostgresLog{
		Source:  sources[rand.Intn(len(sources))],
		Level:   levels[rand.Intn(len(levels))],
		Message: fmt.Sprintf("Performance test: %s by %s", actions[rand.Intn(len(actions))], users[rand.Intn(len(users))]),
		Metadata: fmt.Sprintf(`{"test_id":%d,"user":"%s","action":"%s"}`,
			rand.Int63(),
			users[rand.Intn(len(users))],
			actions[rand.Intn(len(actions))],
		),
	}
}

// PostgresLog representa um log no formato PostgreSQL
type PostgresLog struct {
	Source   string
	Level    string
	Message  string
	Metadata string
}

// RunInsertTest executa teste de inserção diretamente no PostgreSQL
func (pt *PostgresTester) RunInsertTest(scenario TestScenario, monitor *PerformanceMonitor) (*TestResults, error) {
	fmt.Printf("\n🚀 Executando teste de inserção PostgreSQL: %s\n", scenario.Name)
	fmt.Printf("   Total de logs: %d | Taxa: %d logs/s\n", scenario.TotalLogs, scenario.Rate)

	results := &TestResults{
		ScenarioID:   scenario.ID + "_postgres",
		ScenarioName: scenario.Name + " (PostgreSQL)",
		TotalLogs:    scenario.TotalLogs,
		Rate:         scenario.Rate,
	}

	// Iniciar monitoramento
	monitor.Start()
	startTime := time.Now()

	// Contadores atômicos
	var successCount, errorCount int64
	var wg sync.WaitGroup

	// Canal para latências
	latencyChan := make(chan float64, scenario.TotalLogs)

	// Query preparada
	insertQuery := `
		INSERT INTO logs (id, timestamp, source, level, message, metadata)
		VALUES (gen_random_uuid()::text, NOW(), $1, $2, $3, $4::jsonb)
	`

	// Semáforo adaptativo
	maxConcurrency := 50
	if scenario.Rate > 1000 {
		maxConcurrency = 100
	}
	sem := make(chan struct{}, maxConcurrency)

	// Rate limiting inteligente
	if scenario.Rate <= 1000 {
		// Ticker para taxas baixas/médias
		interval := time.Second / time.Duration(scenario.Rate)
		ticker := time.NewTicker(interval)
		defer ticker.Stop()

		for i := 0; i < scenario.TotalLogs; i++ {
			<-ticker.C

			wg.Add(1)
			sem <- struct{}{}

			go pt.insertPostgresLog(&wg, sem, insertQuery, latencyChan, &successCount, &errorCount)

			if (i+1)%(scenario.TotalLogs/10) == 0 && scenario.TotalLogs >= 10 {
				fmt.Printf("   Progresso: %d%%\n", (i+1)*100/scenario.TotalLogs)
			}
		}
	} else {
		// Para taxas altas, usar ticker mais rápido e monitorar taxa
		interval := time.Millisecond
		ticker := time.NewTicker(interval)
		defer ticker.Stop()

		targetInterval := time.Second / time.Duration(scenario.Rate)
		var lastSend time.Time = time.Now()

		for i := 0; i < scenario.TotalLogs; i++ {
			for time.Since(lastSend) < targetInterval {
				<-ticker.C
			}
			lastSend = time.Now()

			wg.Add(1)
			sem <- struct{}{}
			go pt.insertPostgresLog(&wg, sem, insertQuery, latencyChan, &successCount, &errorCount)

			if (i+1)%(scenario.TotalLogs/10) == 0 && scenario.TotalLogs >= 10 {
				fmt.Printf("   Progresso: %d%%\n", (i+1)*100/scenario.TotalLogs)
			}
		}
	}

	// Aguardar todas as inserções
	wg.Wait()
	close(latencyChan)

	// Parar monitoramento
	resourceStats := monitor.Stop()
	duration := time.Since(startTime).Seconds()

	// Coletar latências
	latencies := make([]float64, 0, scenario.TotalLogs)
	for lat := range latencyChan {
		latencies = append(latencies, lat)
	}

	// Calcular estatísticas
	results.Duration = duration
	results.SuccessCount = int(successCount)
	results.ErrorCount = int(errorCount)
	results.Throughput = float64(successCount) / duration
	results.Resources = resourceStats

	if len(latencies) > 0 {
		sort.Float64s(latencies)
		results.AvgLatency = calculateAvg(latencies)
		results.P50Latency = percentile(latencies, 0.50)
		results.P95Latency = percentile(latencies, 0.95)
		results.P99Latency = percentile(latencies, 0.99)
	}

	// Imprimir resultados
	pt.PrintResults(results)

	return results, nil
}

// insertPostgresLog insere um log individual no PostgreSQL (helper para RunInsertTest)
func (pt *PostgresTester) insertPostgresLog(wg *sync.WaitGroup, sem chan struct{}, insertQuery string, latencyChan chan float64, successCount, errorCount *int64) {
	defer wg.Done()
	defer func() { <-sem }()

	log := GeneratePostgresLog()
	reqStart := time.Now()

	// Executar INSERT
	_, err := pt.DB.Exec(insertQuery, log.Source, log.Level, log.Message, log.Metadata)

	latency := time.Since(reqStart).Seconds() * 1000 // ms

	if err != nil {
		atomic.AddInt64(errorCount, 1)
		if atomic.LoadInt64(errorCount) == 1 {
			fmt.Printf("\n⚠️  Erro PostgreSQL: %v\n", err)
		}
		return
	}

	atomic.AddInt64(successCount, 1)
	latencyChan <- latency
}

// RunQueryTest executa teste de consulta no PostgreSQL
func (pt *PostgresTester) RunQueryTest(scenario TestScenario, monitor *PerformanceMonitor) (*TestResults, error) {
	fmt.Printf("\n🔍 Executando teste de consulta PostgreSQL: %s\n", scenario.Name)

	results := &TestResults{
		ScenarioID:   scenario.ID + "_postgres_query",
		ScenarioName: scenario.Name + " (PostgreSQL Query)",
		TotalLogs:    scenario.TotalLogs / 10, // 10% do total de inserções
		Rate:         scenario.Rate,
	}

	// Iniciar monitoramento
	monitor.Start()
	startTime := time.Now()

	// Contadores
	var successCount, errorCount int64
	var wg sync.WaitGroup
	latencyChan := make(chan float64, results.TotalLogs)

	// Queries concorrentes
	concurrency := 20
	sem := make(chan struct{}, concurrency)

	// Queries variadas
	queries := []string{
		"SELECT * FROM logs ORDER BY timestamp DESC LIMIT 100",
		"SELECT * FROM logs WHERE level = 'ERROR' ORDER BY timestamp DESC LIMIT 50",
		"SELECT * FROM logs WHERE source LIKE 'test-service%' ORDER BY timestamp DESC LIMIT 75",
		"SELECT COUNT(*) FROM logs WHERE timestamp > NOW() - INTERVAL '1 hour'",
	}

	for i := 0; i < results.TotalLogs; i++ {
		wg.Add(1)
		sem <- struct{}{}

		go func() {
			defer wg.Done()
			defer func() { <-sem }()

			reqStart := time.Now()

			// Query aleatória
			query := queries[rand.Intn(len(queries))]
			rows, err := pt.DB.Query(query)

			latency := time.Since(reqStart).Seconds() * 1000

			if err != nil {
				atomic.AddInt64(&errorCount, 1)
				return
			}
			defer rows.Close()

			// Consumir resultados (simula processamento real)
			for rows.Next() {
				// Escanear mas não fazer nada com os dados
			}

			if err := rows.Err(); err != nil {
				atomic.AddInt64(&errorCount, 1)
				return
			}

			atomic.AddInt64(&successCount, 1)
			latencyChan <- latency
		}()

		// Progress
		if (i+1)%(results.TotalLogs/5) == 0 && results.TotalLogs >= 5 {
			fmt.Printf("   Progresso: %d%%\n", (i+1)*100/results.TotalLogs)
		}
	}

	wg.Wait()
	close(latencyChan)

	// Parar monitoramento
	resourceStats := monitor.Stop()
	duration := time.Since(startTime).Seconds()

	// Coletar latências
	latencies := make([]float64, 0, results.TotalLogs)
	for lat := range latencyChan {
		latencies = append(latencies, lat)
	}

	// Calcular estatísticas
	results.Duration = duration
	results.SuccessCount = int(successCount)
	results.ErrorCount = int(errorCount)
	results.Throughput = float64(successCount) / duration
	results.Resources = resourceStats

	if len(latencies) > 0 {
		sort.Float64s(latencies)
		results.AvgLatency = calculateAvg(latencies)
		results.P50Latency = percentile(latencies, 0.50)
		results.P95Latency = percentile(latencies, 0.95)
		results.P99Latency = percentile(latencies, 0.99)
	}

	pt.PrintResults(results)

	return results, nil
}

// PrintResults imprime os resultados formatados
func (pt *PostgresTester) PrintResults(results *TestResults) {
	fmt.Printf("\n✅ Resultados do Teste PostgreSQL:\n")
	fmt.Printf("   Duração:     %.2fs\n", results.Duration)
	fmt.Printf("   Sucesso:     %d/%d (%.1f%%)\n",
		results.SuccessCount, results.TotalLogs,
		float64(results.SuccessCount)*100/float64(results.TotalLogs))
	fmt.Printf("   Erros:       %d\n", results.ErrorCount)
	fmt.Printf("   Throughput:  %.2f logs/s\n", results.Throughput)
	fmt.Printf("   Latência:\n")
	fmt.Printf("     - Média:   %.2f ms\n", results.AvgLatency)
	fmt.Printf("     - P50:     %.2f ms\n", results.P50Latency)
	fmt.Printf("     - P95:     %.2f ms\n", results.P95Latency)
	fmt.Printf("     - P99:     %.2f ms\n", results.P99Latency)

	results.Resources.PrintStats()
}

// HealthCheck verifica se o PostgreSQL está respondendo
func (pt *PostgresTester) HealthCheck() error {
	var result int
	err := pt.DB.QueryRow("SELECT 1").Scan(&result)
	if err != nil {
		return fmt.Errorf("postgres health check failed: %w", err)
	}

	fmt.Println("✅ PostgreSQL está respondendo corretamente")
	return nil
}
