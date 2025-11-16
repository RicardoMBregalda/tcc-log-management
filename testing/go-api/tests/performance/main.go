package main

import (
	"encoding/csv"
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"time"
)

const (
	DefaultAPIURL         = "http://localhost:5001"
	DefaultScenariosFile  = "../../../src/test_scenarios.json"
	DefaultResultsDir     = "results_go"
	DefaultPostgresConn   = "host=localhost port=5432 user=loguser password=logpass dbname=logdb sslmode=disable connect_timeout=5"
	DefaultMaxConnections = 50
)

func main() {
	// Parse command line flags
	apiURL := flag.String("api-url", DefaultAPIURL, "Base URL da API Go")
	scenariosFile := flag.String("scenarios", DefaultScenariosFile, "Arquivo de cenários de teste")
	resultsDir := flag.String("results", DefaultResultsDir, "Diretório para salvar resultados")
	quickMode := flag.Bool("quick", false, "Modo rápido (apenas S1, S5, S9)")
	specificScenarios := flag.String("scenarios-list", "", "Lista de cenários específicos (ex: S1,S3,S5)")
	architecture := flag.String("architecture", "both", "Arquitetura a testar: hybrid, traditional ou both")
	postgresConn := flag.String("postgres-conn", DefaultPostgresConn, "String de conexão PostgreSQL")
	flag.Parse()

	fmt.Println("╔═══════════════════════════════════════════════════════════╗")
	fmt.Println("║        Performance Tests - Go Implementation              ║")
	fmt.Println("╚═══════════════════════════════════════════════════════════╝")
	fmt.Printf("\n📋 Configuração:\n")
	
	if *architecture == "hybrid" || *architecture == "both" {
		fmt.Printf("   🔷 API Híbrida: %s\n", *apiURL)
	}
	if *architecture == "traditional" || *architecture == "both" {
		fmt.Printf("   🔶 PostgreSQL: %s\n", *postgresConn)
	}
	
	fmt.Printf("   Cenários: %s\n", *scenariosFile)
	fmt.Printf("   Resultados: %s\n", *resultsDir)
	if *quickMode {
		fmt.Println("   Modo: RÁPIDO (S1, S5, S9)")
	} else if *specificScenarios != "" {
		fmt.Printf("   Modo: ESPECÍFICO (%s)\n", *specificScenarios)
	} else {
		fmt.Println("   Modo: COMPLETO (todos os cenários)")
	}

	// Criar diretório de resultados
	if err := os.MkdirAll(*resultsDir, 0755); err != nil {
		fmt.Printf("❌ Erro ao criar diretório de resultados: %v\n", err)
		os.Exit(1)
	}

	// Carregar cenários de teste
	testConfig, err := LoadTestScenarios(*scenariosFile)
	if err != nil {
		fmt.Printf("❌ Erro ao carregar cenários: %v\n", err)
		os.Exit(1)
	}

	// Selecionar cenários
	var scenarios []TestScenario
	if *quickMode {
		scenarios = testConfig.GetQuickScenarios()
		fmt.Printf("\n📊 Executando %d cenários (modo rápido)\n", len(scenarios))
	} else if *specificScenarios != "" {
		scenarioIDs := strings.Split(*specificScenarios, ",")
		for _, id := range scenarioIDs {
			id = strings.TrimSpace(id)
			if scenario := testConfig.GetScenarioByID(id); scenario != nil {
				scenarios = append(scenarios, *scenario)
			}
		}
		fmt.Printf("\n📊 Executando %d cenários específicos\n", len(scenarios))
	} else {
		scenarios = testConfig.Scenarios
		fmt.Printf("\n📊 Executando todos os %d cenários\n", len(scenarios))
	}

	if len(scenarios) == 0 {
		fmt.Println("❌ Nenhum cenário para executar")
		os.Exit(1)
	}

	// Variáveis para testadores
	var hybridTester *APITester
	var postgresTester *PostgresTester

	// Inicializar testadores baseado na arquitetura
	if *architecture == "hybrid" || *architecture == "both" {
		fmt.Println("\n🏥 Verificando saúde da API Híbrida...")
		hybridTester = NewAPITester(*apiURL)
		if err := hybridTester.HealthCheck(); err != nil {
			fmt.Printf("❌ API Híbrida não está respondendo: %v\n", err)
			fmt.Println("\n💡 Certifique-se de que a API está rodando:")
			fmt.Println("   cd testing/go-api")
			fmt.Println("   ./api")
			
			if *architecture == "hybrid" {
				os.Exit(1)
			}
			fmt.Println("⚠️  Continuando apenas com PostgreSQL...")
			hybridTester = nil
		}
	}

	if *architecture == "traditional" || *architecture == "both" {
		fmt.Println("\n🏥 Verificando saúde do PostgreSQL...")
		var err error
		postgresTester, err = NewPostgresTester(*postgresConn, DefaultMaxConnections)
		if err != nil {
			fmt.Printf("❌ Erro ao conectar ao PostgreSQL: %v\n", err)
			fmt.Println("\n💡 Certifique-se de que o PostgreSQL está rodando:")
			fmt.Println("   cd traditional-architecture")
			fmt.Println("   ./start-traditional.sh")
			
			if *architecture == "traditional" {
				os.Exit(1)
			}
			fmt.Println("⚠️  Continuando apenas com API Híbrida...")
			postgresTester = nil
		} else {
			if err := postgresTester.HealthCheck(); err != nil {
				fmt.Printf("❌ PostgreSQL não está respondendo: %v\n", err)
				postgresTester.Close()
				postgresTester = nil
				
				if *architecture == "traditional" {
					os.Exit(1)
				}
			}
		}
	}

	// Verificar se pelo menos um testador está disponível
	if hybridTester == nil && postgresTester == nil {
		fmt.Println("\n❌ Nenhuma arquitetura disponível para teste")
		os.Exit(1)
	}

	// Executar testes
	allResults := make([]*TestResults, 0, len(scenarios)*4) // *4 porque pode ter hybrid+postgres × insert+query
	startTime := time.Now()

	for i, scenario := range scenarios {
		fmt.Printf("\n" + strings.Repeat("═", 70))
		fmt.Printf("\n📝 Cenário %d/%d: %s\n", i+1, len(scenarios), scenario.Name)
		fmt.Printf("   %s\n", scenario.Description)
		fmt.Println(strings.Repeat("─", 70))

		// ==================== TESTES HÍBRIDA ====================
		if hybridTester != nil {
			fmt.Println("\n🔷 ARQUITETURA HÍBRIDA (MongoDB + Fabric)")
			fmt.Println(strings.Repeat("─", 70))

			// Teste de inserção híbrida
			monitor := NewPerformanceMonitor()
			insertResults, err := hybridTester.RunInsertTest(scenario, monitor)
			if err != nil {
				fmt.Printf("❌ Erro no teste de inserção híbrida: %v\n", err)
			} else {
				allResults = append(allResults, insertResults)
				insertFile := filepath.Join(*resultsDir, fmt.Sprintf("%s_hybrid_insert.json", scenario.ID))
				if err := SaveResults(insertResults, insertFile); err != nil {
					fmt.Printf("⚠️  Erro ao salvar resultado: %v\n", err)
				}
			}

			time.Sleep(2 * time.Second)

			// Teste de consulta híbrida
			monitor = NewPerformanceMonitor()
			queryResults, err := hybridTester.RunQueryTest(scenario, monitor)
			if err != nil {
				fmt.Printf("❌ Erro no teste de consulta híbrida: %v\n", err)
			} else {
				allResults = append(allResults, queryResults)
				queryFile := filepath.Join(*resultsDir, fmt.Sprintf("%s_hybrid_query.json", scenario.ID))
				if err := SaveResults(queryResults, queryFile); err != nil {
					fmt.Printf("⚠️  Erro ao salvar resultado: %v\n", err)
				}
			}
		}

		// ==================== TESTES POSTGRESQL ====================
		if postgresTester != nil {
			fmt.Println("\n🔶 ARQUITETURA TRADICIONAL (PostgreSQL)")
			fmt.Println(strings.Repeat("─", 70))

			// Teste de inserção PostgreSQL
			monitor := NewPerformanceMonitor()
			insertResults, err := postgresTester.RunInsertTest(scenario, monitor)
			if err != nil {
				fmt.Printf("❌ Erro no teste de inserção PostgreSQL: %v\n", err)
			} else {
				allResults = append(allResults, insertResults)
				insertFile := filepath.Join(*resultsDir, fmt.Sprintf("%s_postgres_insert.json", scenario.ID))
				if err := SaveResults(insertResults, insertFile); err != nil {
					fmt.Printf("⚠️  Erro ao salvar resultado: %v\n", err)
				}
			}

			time.Sleep(2 * time.Second)

			// Teste de consulta PostgreSQL
			monitor = NewPerformanceMonitor()
			queryResults, err := postgresTester.RunQueryTest(scenario, monitor)
			if err != nil {
				fmt.Printf("❌ Erro no teste de consulta PostgreSQL: %v\n", err)
			} else {
				allResults = append(allResults, queryResults)
				queryFile := filepath.Join(*resultsDir, fmt.Sprintf("%s_postgres_query.json", scenario.ID))
				if err := SaveResults(queryResults, queryFile); err != nil {
					fmt.Printf("⚠️  Erro ao salvar resultado: %v\n", err)
				}
			}
		}

		// Pausa entre cenários
		if i < len(scenarios)-1 {
			fmt.Println("\n⏸  Aguardando 5 segundos antes do próximo cenário...")
			time.Sleep(5 * time.Second)
		}
	}

	// Fechar conexões
	if postgresTester != nil {
		postgresTester.Close()
	}

	totalDuration := time.Since(startTime)

	// Gerar relatórios consolidados
	fmt.Println("\n" + strings.Repeat("═", 60))
	fmt.Println("📊 Gerando relatórios consolidados...")
	fmt.Println(strings.Repeat("─", 60))

	// Salvar todos os resultados em JSON
	allResultsFile := filepath.Join(*resultsDir, "all_results.json")
	if err := saveAllResults(allResults, allResultsFile); err != nil {
		fmt.Printf("⚠️  Erro ao salvar resultados consolidados: %v\n", err)
	} else {
		fmt.Printf("✅ Resultados JSON: %s\n", allResultsFile)
	}

	// Gerar CSV
	csvFile := filepath.Join(*resultsDir, "results.csv")
	if err := generateCSV(allResults, csvFile); err != nil {
		fmt.Printf("⚠️  Erro ao gerar CSV: %v\n", err)
	} else {
		fmt.Printf("✅ Resultados CSV: %s\n", csvFile)
	}

	// Gerar relatório Markdown
	mdFile := filepath.Join(*resultsDir, "report.md")
	if err := generateMarkdownReport(allResults, totalDuration, mdFile); err != nil {
		fmt.Printf("⚠️  Erro ao gerar relatório Markdown: %v\n", err)
	} else {
		fmt.Printf("✅ Relatório Markdown: %s\n", mdFile)
	}

	// Sumário final
	fmt.Println("\n" + strings.Repeat("═", 60))
	fmt.Println("🎉 Testes Concluídos!")
	fmt.Println(strings.Repeat("─", 60))
	fmt.Printf("⏱️  Duração Total: %.2f minutos\n", totalDuration.Minutes())
	fmt.Printf("📊 Total de Testes: %d\n", len(allResults))
	fmt.Printf("📁 Resultados em: %s\n", *resultsDir)
	fmt.Println(strings.Repeat("═", 60))
}

func saveAllResults(results []*TestResults, filename string) error {
	data, err := json.MarshalIndent(results, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(filename, data, 0644)
}

func generateCSV(results []*TestResults, filename string) error {
	file, err := os.Create(filename)
	if err != nil {
		return err
	}
	defer file.Close()

	writer := csv.NewWriter(file)
	defer writer.Flush()

	// Header
	header := []string{
		"Scenario", "Type", "Total Logs", "Rate", "Duration (s)",
		"Throughput (logs/s)", "Success", "Errors",
		"Avg Latency (ms)", "P50 (ms)", "P95 (ms)", "P99 (ms)",
		"CPU Avg (%)", "Memory Avg (MB)", "Disk Read (MB)", "Disk Write (MB)",
	}
	if err := writer.Write(header); err != nil {
		return err
	}

	// Data
	for _, r := range results {
		testType := "Insert"
		if strings.Contains(r.ScenarioID, "query") {
			testType = "Query"
		}

		row := []string{
			r.ScenarioID,
			testType,
			fmt.Sprintf("%d", r.TotalLogs),
			fmt.Sprintf("%d", r.Rate),
			fmt.Sprintf("%.2f", r.Duration),
			fmt.Sprintf("%.2f", r.Throughput),
			fmt.Sprintf("%d", r.SuccessCount),
			fmt.Sprintf("%d", r.ErrorCount),
			fmt.Sprintf("%.2f", r.AvgLatency),
			fmt.Sprintf("%.2f", r.P50Latency),
			fmt.Sprintf("%.2f", r.P95Latency),
			fmt.Sprintf("%.2f", r.P99Latency),
			fmt.Sprintf("%.2f", r.Resources.CPU.Avg),
			fmt.Sprintf("%d", r.Resources.Memory.AvgMB),
			fmt.Sprintf("%.2f", r.Resources.Disk.ReadMB),
			fmt.Sprintf("%.2f", r.Resources.Disk.WriteMB),
		}
		if err := writer.Write(row); err != nil {
			return err
		}
	}

	return nil
}

func generateMarkdownReport(results []*TestResults, totalDuration time.Duration, filename string) error {
	file, err := os.Create(filename)
	if err != nil {
		return err
	}
	defer file.Close()

	fmt.Fprintf(file, "# Performance Test Report - Go API\n\n")
	fmt.Fprintf(file, "**Data:** %s\n\n", time.Now().Format("2006-01-02 15:04:05"))
	fmt.Fprintf(file, "**Duração Total:** %.2f minutos\n\n", totalDuration.Minutes())
	fmt.Fprintf(file, "**Total de Testes:** %d\n\n", len(results))

	// Tabela de resultados
	fmt.Fprintf(file, "## Resultados Consolidados\n\n")
	fmt.Fprintf(file, "| Cenário | Tipo | Logs | Taxa | Duração (s) | Throughput | Latência Média | P95 | P99 |\n")
	fmt.Fprintf(file, "|---------|------|------|------|-------------|------------|----------------|-----|-----|\n")

	for _, r := range results {
		testType := "Insert"
		if strings.Contains(r.ScenarioID, "query") {
			testType = "Query"
		}

		fmt.Fprintf(file, "| %s | %s | %d | %d/s | %.2f | %.2f logs/s | %.2f ms | %.2f ms | %.2f ms |\n",
			r.ScenarioID, testType, r.TotalLogs, r.Rate, r.Duration,
			r.Throughput, r.AvgLatency, r.P95Latency, r.P99Latency)
	}

	// Recursos
	fmt.Fprintf(file, "\n## Uso de Recursos\n\n")
	fmt.Fprintf(file, "| Cenário | Tipo | CPU Avg | Memory Avg | Disk Read | Disk Write |\n")
	fmt.Fprintf(file, "|---------|------|---------|------------|-----------|------------|\n")

	for _, r := range results {
		testType := "Insert"
		if strings.Contains(r.ScenarioID, "query") {
			testType = "Query"
		}

		fmt.Fprintf(file, "| %s | %s | %.2f%% | %d MB | %.2f MB | %.2f MB |\n",
			r.ScenarioID, testType,
			r.Resources.CPU.Avg, r.Resources.Memory.AvgMB,
			r.Resources.Disk.ReadMB, r.Resources.Disk.WriteMB)
	}

	fmt.Fprintf(file, "\n---\n")
	fmt.Fprintf(file, "*Relatório gerado automaticamente em %s*\n", time.Now().Format("2006-01-02 15:04:05"))

	return nil
}
