package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"math/rand"
	"net/http"
	"os"
	"sort"
	"sync"
	"sync/atomic"
	"time"
)

// APITester testa a API Go
type APITester struct {
	BaseURL    string
	Client     *http.Client
	RateLimiter *time.Ticker
}

// TestLog representa um log de teste (schema da API Go)
type TestLog struct {
	ID       string                 `json:"id,omitempty"`       // Omitir - API gera automaticamente
	Source   string                 `json:"source"`
	Level    string                 `json:"level"`
	Message  string                 `json:"message"`
	Metadata map[string]interface{} `json:"metadata,omitempty"`
	// Omitir Timestamp - API gera automaticamente
}

// TestResults representa os resultados de um teste
type TestResults struct {
	ScenarioID        string        `json:"scenario_id"`
	ScenarioName      string        `json:"scenario_name"`
	TotalLogs         int           `json:"total_logs"`
	Rate              int           `json:"rate"`
	Duration          float64       `json:"duration_seconds"`
	Throughput        float64       `json:"throughput_logs_per_sec"`
	SuccessCount      int           `json:"success_count"`
	ErrorCount        int           `json:"error_count"`
	AvgLatency        float64       `json:"avg_latency_ms"`
	P50Latency        float64       `json:"p50_latency_ms"`
	P95Latency        float64       `json:"p95_latency_ms"`
	P99Latency        float64       `json:"p99_latency_ms"`
	Resources         ResourceStats `json:"resources"`
}

// NewAPITester cria um novo testador de API
func NewAPITester(baseURL string) *APITester {
	return &APITester{
		BaseURL: baseURL,
		Client: &http.Client{
			Timeout: 30 * time.Second,
			Transport: &http.Transport{
				MaxIdleConns:        100,
				MaxIdleConnsPerHost: 100,
				IdleConnTimeout:     90 * time.Second,
			},
		},
	}
}

// GenerateTestLog gera um log de teste aleatório
func GenerateTestLog() TestLog {
	sources := []string{"test-service-1", "test-service-2", "test-service-3", "test-service-4"}
	levels := []string{"DEBUG", "INFO", "WARNING", "ERROR"}
	actions := []string{"login", "logout", "update", "delete", "create", "read", "write"}
	users := []string{"user1", "user2", "user3", "admin", "guest"}
	
	return TestLog{
		Source:  sources[rand.Intn(len(sources))],
		Level:   levels[rand.Intn(len(levels))],
		Message: fmt.Sprintf("Performance test: %s by %s", actions[rand.Intn(len(actions))], users[rand.Intn(len(users))]),
		// Omitir timestamp - API gera automaticamente em RFC3339
		Metadata: map[string]interface{}{
			"test_id": rand.Int63(),
			"user":    users[rand.Intn(len(users))],
			"action":  actions[rand.Intn(len(actions))],
		},
	}
}

// RunInsertTest executa teste de inserção de logs
func (at *APITester) RunInsertTest(scenario TestScenario, monitor *PerformanceMonitor) (*TestResults, error) {
	fmt.Printf("\n🚀 Executando teste de inserção: %s\n", scenario.Name)
	fmt.Printf("   Total de logs: %d | Taxa: %d logs/s\n", scenario.TotalLogs, scenario.Rate)

	results := &TestResults{
		ScenarioID:   scenario.ID,
		ScenarioName: scenario.Name,
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

	// Semáforo para limitar concorrência (adaptativo baseado na taxa)
	maxConcurrency := 50
	if scenario.Rate > 1000 {
		maxConcurrency = 100 // Mais concorrência para taxas altas
	}
	sem := make(chan struct{}, maxConcurrency)

	// Rate limiting mais inteligente
	// Para taxas baixas (<= 1000), usar ticker
	// Para taxas altas (> 1000), usar batches
	if scenario.Rate <= 1000 {
		// Rate limiting com ticker (taxas baixas/médias)
		interval := time.Second / time.Duration(scenario.Rate)
		ticker := time.NewTicker(interval)
		defer ticker.Stop()

		for i := 0; i < scenario.TotalLogs; i++ {
			<-ticker.C // Respeitar taxa

			wg.Add(1)
			sem <- struct{}{} // Adquirir semáforo

			go at.sendLog(&wg, sem, latencyChan, &successCount, &errorCount)

			// Progress indicator
			if (i+1)%(scenario.TotalLogs/10) == 0 && scenario.TotalLogs >= 10 {
				fmt.Printf("   Progresso: %d%%\n", (i+1)*100/scenario.TotalLogs)
			}
		}
	} else {
		// Para taxas altas, usar controle preciso de timing
		targetInterval := time.Second / time.Duration(scenario.Rate)
		ticker := time.NewTicker(time.Millisecond) // Check a cada 1ms
		defer ticker.Stop()

		var lastSend time.Time = time.Now()

		for i := 0; i < scenario.TotalLogs; i++ {
			// Aguardar até próximo slot
			for time.Since(lastSend) < targetInterval {
				<-ticker.C
			}
			lastSend = time.Now()

			wg.Add(1)
			sem <- struct{}{}
			go at.sendLog(&wg, sem, latencyChan, &successCount, &errorCount)

			// Progress indicator
			if (i+1)%(scenario.TotalLogs/10) == 0 && scenario.TotalLogs >= 10 {
				fmt.Printf("   Progresso: %d%%\n", (i+1)*100/scenario.TotalLogs)
			}
		}
	}

	// Aguardar todas as requisições
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
	at.PrintResults(results)

	return results, nil
}

// sendLog envia um log individual (helper para RunInsertTest)
func (at *APITester) sendLog(wg *sync.WaitGroup, sem chan struct{}, latencyChan chan float64, successCount, errorCount *int64) {
	defer wg.Done()
	defer func() { <-sem }() // Liberar semáforo

	log := GenerateTestLog()
	reqStart := time.Now()

	// Fazer requisição POST
	body, _ := json.Marshal(log)
	resp, err := at.Client.Post(
		at.BaseURL+"/logs",
		"application/json",
		bytes.NewBuffer(body),
	)

	latency := time.Since(reqStart).Seconds() * 1000 // ms

	if err != nil {
		atomic.AddInt64(errorCount, 1)
		// Log primeiro erro para debug
		if atomic.LoadInt64(errorCount) == 1 {
			fmt.Printf("\n⚠️  Erro HTTP: %v\n", err)
		}
		return
	}
	defer resp.Body.Close()

	if resp.StatusCode >= 200 && resp.StatusCode < 300 {
		atomic.AddInt64(successCount, 1)
		latencyChan <- latency
	} else {
		atomic.AddInt64(errorCount, 1)
		// Log primeiro erro de status para debug
		if atomic.LoadInt64(errorCount) == 1 {
			responseBody, _ := io.ReadAll(resp.Body)
			fmt.Printf("\n⚠️  HTTP %d: %s\n", resp.StatusCode, string(responseBody))
		}
	}
}

// RunQueryTest executa teste de consulta de logs
func (at *APITester) RunQueryTest(scenario TestScenario, monitor *PerformanceMonitor) (*TestResults, error) {
	fmt.Printf("\n🔍 Executando teste de consulta: %s\n", scenario.Name)
	
	results := &TestResults{
		ScenarioID:   scenario.ID + "_query",
		ScenarioName: scenario.Name + " (Query)",
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

	for i := 0; i < results.TotalLogs; i++ {
		wg.Add(1)
		sem <- struct{}{}

		go func() {
			defer wg.Done()
			defer func() { <-sem }()

			reqStart := time.Now()

			// Query aleatória (últimos N logs)
			resp, err := at.Client.Get(at.BaseURL + "/logs?limit=100")
			latency := time.Since(reqStart).Seconds() * 1000

			if err != nil {
				atomic.AddInt64(&errorCount, 1)
				return
			}
			defer resp.Body.Close()

			if resp.StatusCode >= 200 && resp.StatusCode < 300 {
				atomic.AddInt64(&successCount, 1)
				latencyChan <- latency
			} else {
				atomic.AddInt64(&errorCount, 1)
			}
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

	at.PrintResults(results)

	return results, nil
}

// PrintResults imprime os resultados formatados
func (at *APITester) PrintResults(results *TestResults) {
	fmt.Printf("\n✅ Resultados do Teste:\n")
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

// SaveResults salva os resultados em arquivo JSON
func SaveResults(results *TestResults, filename string) error {
	data, err := json.MarshalIndent(results, "", "  ")
	if err != nil {
		return fmt.Errorf("failed to marshal results: %w", err)
	}

	if err := os.WriteFile(filename, data, 0644); err != nil {
		return fmt.Errorf("failed to write results: %w", err)
	}

	return nil
}

// HealthCheck verifica se a API está respondendo
func (at *APITester) HealthCheck() error {
	resp, err := at.Client.Get(at.BaseURL + "/health")
	if err != nil {
		return fmt.Errorf("health check failed: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("health check returned status %d: %s", resp.StatusCode, string(body))
	}

	fmt.Println("✅ API está respondendo corretamente")
	return nil
}

// percentile calcula o percentil de uma lista ordenada
func percentile(sorted []float64, p float64) float64 {
	if len(sorted) == 0 {
		return 0
	}
	index := int(float64(len(sorted)) * p)
	if index >= len(sorted) {
		index = len(sorted) - 1
	}
	return sorted[index]
}
