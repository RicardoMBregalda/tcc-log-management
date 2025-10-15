# Relatório de Performance - TCC Log Management
**Data/Hora:** 2025-10-13T22:33:13.313112
---
## 1. Throughput (Operações/Segundo)
| Tipo de Operação | PostgreSQL | Híbrido (Fabric+Mongo) | Diferença |
|-----------------|------------|------------------------|------------|
| **Inserção** | 76.56 | 66.06 | -13.7% |
| **Consulta** | 9.90 | 7.57 | -23.6% |

## 2. Latência (ms)
### 2.1. Inserção
| Métrica | PostgreSQL | Híbrido (Fabric+Mongo) | Diferença |
|---------|------------|------------------------|------------|
| Média | 8.63 | 24.36 | +182.3% |
| Mediana | 8.80 | 23.88 | +171.5% |
| P95 | 15.53 | 34.74 | +123.8% |
| P99 | 19.07 | 52.76 | +176.6% |
| Mínimo | 1.46 | 6.58 | +350.8% |
| Máximo | 33.10 | 92.01 | +177.9% |

### 2.2. Consulta
| Métrica | PostgreSQL | Híbrido (Fabric+Mongo) | Diferença |
|---------|------------|------------------------|------------|
| Média | 0.95 | 5.36 | +465.5% |
| Mediana | 0.85 | 4.91 | +480.8% |
| P95 | 1.67 | 7.14 | +328.1% |
| P99 | 0.00 | 0.00 | +0.0% |
| Mínimo | 0.70 | 4.53 | +543.2% |
| Máximo | 3.18 | 13.59 | +326.7% |

## 3. Uso de Recursos
### 3.1. CPU (%)
| Operação | Métrica | PostgreSQL | Híbrido (Fabric+Mongo) |
|----------|---------|------------|------------------------|
| Inserção | Média | 1.9% | 13.8% |
| Inserção | Máxima | 27.6% | 61.4% |
| Consulta | Média | 2.0% | 2.2% |
| Consulta | Máxima | 32.9% | 25.9% |

### 3.2. Memória (%)
| Operação | Métrica | PostgreSQL | Híbrido (Fabric+Mongo) |
|----------|---------|------------|------------------------|
| Inserção | Média | 26.3% | 26.8% |
| Inserção | Máxima | 26.5% | 27.4% |
| Consulta | Média | 26.3% | 27.1% |
| Consulta | Máxima | 26.4% | 27.3% |

### 3.3. Disco (MB)
| Operação | Tipo | PostgreSQL | Híbrido (Fabric+Mongo) |
|----------|------|------------|------------------------|
| Inserção | Leitura | 0.00 | 0.12 |
| Inserção | Escrita | 44.42 | 62.86 |
| Consulta | Leitura | 0.00 | 0.00 |
| Consulta | Escrita | 0.82 | 4.30 |

## 4. Análise e Conclusões
### 4.1. Inserção de Logs
- O sistema híbrido apresenta **throughput 13.7% menor** devido ao overhead da sincronização com Fabric
- Latência média **182.3% maior** no híbrido devido à gravação na blockchain
- **Trade-off:** A arquitetura híbrida sacrifica 13.7% de throughput em troca de imutabilidade e auditoria

### 4.2. Consulta de Logs
- Diferença de -23.6% no throughput de consulta
- Consultas não são impactadas pela blockchain (somente escritas)

### 4.3. Recomendações
- **PostgreSQL Tradicional:** Melhor para cenários que priorizam throughput máximo
- **Híbrido (Fabric+Mongo):** Ideal para cenários que necessitam auditoria, imutabilidade e rastreabilidade
- O overhead da blockchain é aceitável considerando os benefícios de governança e compliance

---
*Relatório gerado automaticamente por analyze_results.py*
