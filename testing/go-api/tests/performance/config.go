package main

import (
	"encoding/json"
	"fmt"
	"io"
	"os"
)

// TestScenario representa um cenário de teste
type TestScenario struct {
	ID                     string `json:"id"`
	Name                   string `json:"name"`
	TotalLogs              int    `json:"total_logs"`
	Rate                   int    `json:"rate"`
	Description            string `json:"description"`
	ExpectedDurationSeconds int    `json:"expected_duration_seconds"`
}

// TestConfig representa a configuração completa dos testes
type TestConfig struct {
	Description string `json:"description"`
	TestMatrix  struct {
		Volumes []int `json:"volumes"`
		Rates   []int `json:"rates"`
	} `json:"test_matrix"`
	Scenarios        []TestScenario `json:"scenarios"`
	MetricsToCollect []string       `json:"metrics_to_collect"`
	Output           struct {
		ResultsDir          string `json:"results_dir"`
		IndividualReports   string `json:"individual_reports"`
		ConsolidatedReport  string `json:"consolidated_report"`
		CSVFile             string `json:"csv_file"`
		JSONFile            string `json:"json_file"`
	} `json:"output"`
}

// LoadTestScenarios carrega os cenários do arquivo JSON
func LoadTestScenarios(filename string) (*TestConfig, error) {
	file, err := os.Open(filename)
	if err != nil {
		return nil, fmt.Errorf("failed to open test scenarios file: %w", err)
	}
	defer file.Close()

	data, err := io.ReadAll(file)
	if err != nil {
		return nil, fmt.Errorf("failed to read test scenarios: %w", err)
	}

	var config TestConfig
	if err := json.Unmarshal(data, &config); err != nil {
		return nil, fmt.Errorf("failed to parse test scenarios: %w", err)
	}

	return &config, nil
}

// GetScenarioByID encontra um cenário específico pelo ID
func (tc *TestConfig) GetScenarioByID(id string) *TestScenario {
	for _, scenario := range tc.Scenarios {
		if scenario.ID == id {
			return &scenario
		}
	}
	return nil
}

// GetQuickScenarios retorna os cenários para modo rápido (S1, S5, S9)
func (tc *TestConfig) GetQuickScenarios() []TestScenario {
	quick := []TestScenario{}
	quickIDs := []string{"S1", "S5", "S9"}
	
	for _, id := range quickIDs {
		if scenario := tc.GetScenarioByID(id); scenario != nil {
			quick = append(quick, *scenario)
		}
	}
	
	return quick
}
