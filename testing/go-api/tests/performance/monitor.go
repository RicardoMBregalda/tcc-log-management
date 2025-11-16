package main

import (
	"encoding/json"
	"fmt"
	"os"
	"runtime"
	"sync"
	"time"
)

// PerformanceMonitor monitora recursos do sistema
type PerformanceMonitor struct {
	cpuSamples    []float64
	memorySamples []uint64
	diskSamples   []DiskSample
	monitoring    bool
	mutex         sync.RWMutex
	stopChan      chan struct{}
	wg            sync.WaitGroup
}

// DiskSample representa uma amostra de I/O de disco
type DiskSample struct {
	ReadBytes  uint64
	WriteBytes uint64
	Timestamp  time.Time
}

// ResourceStats representa estatísticas de recursos coletadas
type ResourceStats struct {
	CPU    CPUStats    `json:"cpu"`
	Memory MemoryStats `json:"memory"`
	Disk   DiskStats   `json:"disk"`
}

// CPUStats representa estatísticas de CPU
type CPUStats struct {
	Avg float64 `json:"avg"`
	Max float64 `json:"max"`
	Min float64 `json:"min"`
}

// MemoryStats representa estatísticas de memória
type MemoryStats struct {
	AvgMB uint64 `json:"avg_mb"`
	MaxMB uint64 `json:"max_mb"`
	MinMB uint64 `json:"min_mb"`
}

// DiskStats representa estatísticas de disco
type DiskStats struct {
	ReadMB  float64 `json:"read_mb"`
	WriteMB float64 `json:"write_mb"`
}

// NewPerformanceMonitor cria um novo monitor de performance
func NewPerformanceMonitor() *PerformanceMonitor {
	return &PerformanceMonitor{
		cpuSamples:    make([]float64, 0, 1000),
		memorySamples: make([]uint64, 0, 1000),
		diskSamples:   make([]DiskSample, 0, 1000),
		stopChan:      make(chan struct{}),
	}
}

// Start inicia o monitoramento de recursos
func (pm *PerformanceMonitor) Start() {
	pm.mutex.Lock()
	pm.monitoring = true
	pm.cpuSamples = pm.cpuSamples[:0]
	pm.memorySamples = pm.memorySamples[:0]
	pm.diskSamples = pm.diskSamples[:0]
	pm.mutex.Unlock()

	pm.wg.Add(1)
	go pm.monitorLoop()
}

// Stop para o monitoramento e retorna as estatísticas
func (pm *PerformanceMonitor) Stop() ResourceStats {
	pm.mutex.Lock()
	pm.monitoring = false
	pm.mutex.Unlock()

	close(pm.stopChan)
	pm.wg.Wait()

	return pm.GetStats()
}

// monitorLoop coleta amostras de recursos periodicamente
func (pm *PerformanceMonitor) monitorLoop() {
	defer pm.wg.Done()

	ticker := time.NewTicker(1 * time.Second)
	defer ticker.Stop()

	for {
		select {
		case <-ticker.C:
			pm.collectSample()
		case <-pm.stopChan:
			return
		}
	}
}

// collectSample coleta uma amostra de recursos do sistema
func (pm *PerformanceMonitor) collectSample() {
	pm.mutex.Lock()
	defer pm.mutex.Unlock()

	if !pm.monitoring {
		return
	}

	// CPU usage (aproximação via número de goroutines)
	cpuPercent := float64(runtime.NumGoroutine()) * 0.1
	pm.cpuSamples = append(pm.cpuSamples, cpuPercent)

	// Memory usage
	var m runtime.MemStats
	runtime.ReadMemStats(&m)
	pm.memorySamples = append(pm.memorySamples, m.Alloc)

	// Disk I/O (simulado - em produção usar syscalls apropriados)
	// Para Linux, ler /proc/diskstats
	// Para Windows, usar performance counters
	sample := DiskSample{
		ReadBytes:  0,  // TODO: Implementar leitura real
		WriteBytes: 0,  // TODO: Implementar escrita real
		Timestamp:  time.Now(),
	}
	pm.diskSamples = append(pm.diskSamples, sample)
}

// GetStats retorna as estatísticas coletadas
func (pm *PerformanceMonitor) GetStats() ResourceStats {
	pm.mutex.RLock()
	defer pm.mutex.RUnlock()

	stats := ResourceStats{}

	// CPU stats
	if len(pm.cpuSamples) > 0 {
		stats.CPU = CPUStats{
			Avg: calculateAvg(pm.cpuSamples),
			Max: calculateMax(pm.cpuSamples),
			Min: calculateMin(pm.cpuSamples),
		}
	}

	// Memory stats
	if len(pm.memorySamples) > 0 {
		stats.Memory = MemoryStats{
			AvgMB: calculateAvgUint64(pm.memorySamples) / (1024 * 1024),
			MaxMB: calculateMaxUint64(pm.memorySamples) / (1024 * 1024),
			MinMB: calculateMinUint64(pm.memorySamples) / (1024 * 1024),
		}
	}

	// Disk stats
	if len(pm.diskSamples) >= 2 {
		first := pm.diskSamples[0]
		last := pm.diskSamples[len(pm.diskSamples)-1]
		
		stats.Disk = DiskStats{
			ReadMB:  float64(last.ReadBytes-first.ReadBytes) / (1024 * 1024),
			WriteMB: float64(last.WriteBytes-first.WriteBytes) / (1024 * 1024),
		}
	}

	return stats
}

// PrintStats imprime as estatísticas formatadas
func (rs *ResourceStats) PrintStats() {
	fmt.Printf("\n📊 Recursos do Sistema:\n")
	fmt.Printf("   CPU:    %.2f%% avg | %.2f%% max | %.2f%% min\n",
		rs.CPU.Avg, rs.CPU.Max, rs.CPU.Min)
	fmt.Printf("   Memory: %d MB avg | %d MB max | %d MB min\n",
		rs.Memory.AvgMB, rs.Memory.MaxMB, rs.Memory.MinMB)
	fmt.Printf("   Disk:   %.2f MB read | %.2f MB write\n",
		rs.Disk.ReadMB, rs.Disk.WriteMB)
}

// Funções auxiliares para cálculos estatísticos
func calculateAvg(values []float64) float64 {
	if len(values) == 0 {
		return 0
	}
	sum := 0.0
	for _, v := range values {
		sum += v
	}
	return sum / float64(len(values))
}

func calculateMax(values []float64) float64 {
	if len(values) == 0 {
		return 0
	}
	max := values[0]
	for _, v := range values {
		if v > max {
			max = v
		}
	}
	return max
}

func calculateMin(values []float64) float64 {
	if len(values) == 0 {
		return 0
	}
	min := values[0]
	for _, v := range values {
		if v < min {
			min = v
		}
	}
	return min
}

func calculateAvgUint64(values []uint64) uint64 {
	if len(values) == 0 {
		return 0
	}
	sum := uint64(0)
	for _, v := range values {
		sum += v
	}
	return sum / uint64(len(values))
}

func calculateMaxUint64(values []uint64) uint64 {
	if len(values) == 0 {
		return 0
	}
	max := values[0]
	for _, v := range values {
		if v > max {
			max = v
		}
	}
	return max
}

func calculateMinUint64(values []uint64) uint64 {
	if len(values) == 0 {
		return 0
	}
	min := values[0]
	for _, v := range values {
		if v < min {
			min = v
		}
	}
	return min
}

// SaveResourceStatsToFile salva as estatísticas em um arquivo
func SaveResourceStatsToFile(stats ResourceStats, filename string) error {
	file, err := os.Create(filename)
	if err != nil {
		return fmt.Errorf("failed to create file: %w", err)
	}
	defer file.Close()

	encoder := json.NewEncoder(file)
	encoder.SetIndent("", "  ")
	if err := encoder.Encode(stats); err != nil {
		return fmt.Errorf("failed to encode stats: %w", err)
	}

	return nil
}
