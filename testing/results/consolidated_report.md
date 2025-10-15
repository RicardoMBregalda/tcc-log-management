# Relatório Consolidado - Matriz de Cenários TCC

**Data:** 2025-10-14 10:30:25

## Cenários Testados

| ID | Nome | Volume | Taxa (logs/s) |
|---|---|---|---|
| S1 | Baixo Volume + Baixa Taxa | 10,000 | 100 |
| S2 | Baixo Volume + Média Taxa | 10,000 | 1000 |
| S3 | Baixo Volume + Alta Taxa | 10,000 | 10000 |
| S4 | Médio Volume + Baixa Taxa | 100,000 | 100 |
| S5 | Médio Volume + Média Taxa | 100,000 | 1000 |
| S6 | Médio Volume + Alta Taxa | 100,000 | 10000 |
| S7 | Alto Volume + Baixa Taxa | 1,000,000 | 100 |
| S8 | Alto Volume + Média Taxa | 1,000,000 | 1000 |
| S9 | Alto Volume + Alta Taxa | 1,000,000 | 10000 |

## Resultados por Cenário

### S1: Baixo Volume + Baixa Taxa

| Arquitetura | Throughput (logs/s) | P50 (ms) | P95 (ms) | P99 (ms) | CPU % | RAM % |
|---|---|---|---|---|---|---|
| HYBRID | 89.52 | 26.69 | 38.38 | 46.91 | 13.0 | 30.1 |
| POSTGRES | 97.52 | 17.64 | 61.20 | 101.84 | 53.4 | 99.0 |

### S2: Baixo Volume + Média Taxa

| Arquitetura | Throughput (logs/s) | P50 (ms) | P95 (ms) | P99 (ms) | CPU % | RAM % |
|---|---|---|---|---|---|---|
| HYBRID | 279.43 | 113.65 | 198.42 | 262.60 | 36.7 | 30.8 |
| POSTGRES | 503.52 | 87.62 | 163.53 | 221.35 | 28.8 | 99.1 |

### S3: Baixo Volume + Alta Taxa

| Arquitetura | Throughput (logs/s) | P50 (ms) | P95 (ms) | P99 (ms) | CPU % | RAM % |
|---|---|---|---|---|---|---|
| HYBRID | 258.61 | 221.90 | 303.51 | 1274.77 | 25.8 | 31.3 |
| POSTGRES | 499.32 | 92.83 | 168.76 | 226.47 | 26.4 | 99.2 |

### S4: Médio Volume + Baixa Taxa

| Arquitetura | Throughput (logs/s) | P50 (ms) | P95 (ms) | P99 (ms) | CPU % | RAM % |
|---|---|---|---|---|---|---|
| HYBRID | 90.86 | 27.39 | 39.40 | 48.08 | 15.0 | 31.7 |
| POSTGRES | 69.82 | 17.27 | 130.76 | 738.27 | 35.2 | 99.3 |

### S5: Médio Volume + Média Taxa

| Arquitetura | Throughput (logs/s) | P50 (ms) | P95 (ms) | P99 (ms) | CPU % | RAM % |
|---|---|---|---|---|---|---|
| HYBRID | 249.31 | 218.62 | 409.78 | 1229.81 | 23.7 | 34.5 |
| POSTGRES | 57.86 | 101.15 | 7998.36 | 17111.88 | 41.3 | 94.2 |

### S6: Médio Volume + Alta Taxa

| Arquitetura | Throughput (logs/s) | P50 (ms) | P95 (ms) | P99 (ms) | CPU % | RAM % |
|---|---|---|---|---|---|---|
| HYBRID | 240.33 | 218.31 | 329.71 | 2352.81 | 24.5 | 39.2 |
| POSTGRES | 639.31 | 69.90 | 138.86 | 164.51 | 9.5 | 33.7 |

### S7: Alto Volume + Baixa Taxa

| Arquitetura | Throughput (logs/s) | P50 (ms) | P95 (ms) | P99 (ms) | CPU % | RAM % |
|---|---|---|---|---|---|---|
| HYBRID | 94.79 | 29.15 | 54.99 | 101.90 | 21.3 | 44.3 |
| POSTGRES | 95.63 | 14.79 | 21.53 | 29.00 | 2.7 | 33.2 |

### S8: Alto Volume + Média Taxa

| Arquitetura | Throughput (logs/s) | P50 (ms) | P95 (ms) | P99 (ms) | CPU % | RAM % |
|---|---|---|---|---|---|---|
| HYBRID | 214.24 | 221.64 | 383.63 | 739.61 | 65.5 | 62.2 |
| POSTGRES | 339.64 | 111.50 | 348.86 | 399.79 | 5.9 | 33.4 |

### S9: Alto Volume + Alta Taxa

| Arquitetura | Throughput (logs/s) | P50 (ms) | P95 (ms) | P99 (ms) | CPU % | RAM % |
|---|---|---|---|---|---|---|
| HYBRID | 206.44 | 159.25 | 340.56 | 504.90 | 89.4 | 89.5 |
| POSTGRES | 402.80 | 93.07 | 332.14 | 383.41 | 6.5 | 33.4 |

## Análise Comparativa

*Ver análise detalhada em analyze_results.py*
