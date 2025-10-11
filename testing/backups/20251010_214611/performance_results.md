# Relatório de Performance - TCC Log Management
**Data/Hora:** 2025-10-10T21:41:54.069939
---
## 1. Throughput (Operações/Segundo)
| Tipo de Operação | PostgreSQL | Híbrido (Fabric+Mongo) | Diferença |
|-----------------|------------|------------------------|------------|
| **Inserção** | 81.03 | 59.33 | -26.8% |
| **Consulta** | 9.88 | 9.82 | -0.6% |

## 2. Latência (ms)
### 2.1. Inserção
| Métrica | PostgreSQL | Híbrido (Fabric+Mongo) | Diferença |
|---------|------------|------------------------|------------|
| Média | 9.00 | 48.44 | +438.0% |
| Mediana | 9.31 | 47.09 | +405.7% |
| P95 | 15.98 | 60.08 | +275.9% |
| P99 | 21.67 | 79.25 | +265.8% |
| Mínimo | 1.58 | 24.94 | +1479.8% |
| Máximo | 40.91 | 113.77 | +178.1% |

### 2.2. Consulta
| Métrica | PostgreSQL | Híbrido (Fabric+Mongo) | Diferença |
|---------|------------|------------------------|------------|
| Média | 1.15 | 4.32 | +275.9% |
| Mediana | 1.08 | 3.94 | +266.2% |
| P95 | 1.98 | 6.59 | +233.2% |
| P99 | 0.00 | 0.00 | +0.0% |
| Mínimo | 0.80 | 3.24 | +307.3% |
| Máximo | 2.65 | 8.77 | +230.4% |

## 3. Uso de Recursos
### 3.1. CPU (%)
| Operação | Métrica | PostgreSQL | Híbrido (Fabric+Mongo) |
|----------|---------|------------|------------------------|
| Inserção | Média | 1.4% | 1.9% |
| Inserção | Máxima | 23.1% | 34.7% |
| Consulta | Média | 1.6% | 2.0% |
| Consulta | Máxima | 20.6% | 25.5% |

### 3.2. Memória (%)
| Operação | Métrica | PostgreSQL | Híbrido (Fabric+Mongo) |
|----------|---------|------------|------------------------|
| Inserção | Média | 23.9% | 24.3% |
| Inserção | Máxima | 24.0% | 24.6% |
| Consulta | Média | 24.1% | 24.4% |
| Consulta | Máxima | 24.1% | 24.5% |

### 3.3. Disco (MB)
| Operação | Tipo | PostgreSQL | Híbrido (Fabric+Mongo) |
|----------|------|------------|------------------------|
| Inserção | Leitura | 0.00 | 0.00 |
| Inserção | Escrita | 41.17 | 33.84 |
| Consulta | Leitura | 0.00 | 0.00 |
| Consulta | Escrita | 0.60 | 4.10 |

## 4. Análise e Conclusões
### 4.1. Inserção de Logs
- O sistema híbrido apresenta **throughput 26.8% menor** devido ao overhead da sincronização com Fabric
- Latência média **438.0% maior** no híbrido devido à gravação na blockchain
- **Trade-off:** A arquitetura híbrida sacrifica 26.8% de throughput em troca de imutabilidade e auditoria

### 4.2. Consulta de Logs
- Performance de consulta similar (-0.6%) - ambas arquiteturas usam PostgreSQL para leitura
- Consultas não são impactadas pela blockchain (somente escritas)

### 4.3. Recomendações
- **PostgreSQL Tradicional:** Melhor para cenários que priorizam throughput máximo
- **Híbrido (Fabric+Mongo):** Ideal para cenários que necessitam auditoria, imutabilidade e rastreabilidade
- O overhead da blockchain é aceitável considerando os benefícios de governança e compliance

---
*Relatório gerado automaticamente por analyze_results.py*
