# Análise de Cenários de Teste - TCC Log Management

**Data de Análise:** 2025-10-14 17:25:34

---

## Resumo Executivo

| Cenário | Arquitetura | Throughput (logs/s) | P50 (ms) | P95 (ms) | P99 (ms) | CPU % | RAM % |
|---------|-------------|---------------------|----------|----------|----------|-------|-------|
| S1 | HYBRID | 89.5 | 26.69 | 38.38 | 46.91 | 13.0 | 30.1 |
| S1 | POSTGRES | 97.5 | 17.64 | 61.20 | 101.84 | 53.4 | 99.0 |
| S2 | HYBRID | 279.4 | 113.65 | 198.42 | 262.60 | 36.7 | 30.8 |
| S2 | POSTGRES | 503.5 | 87.62 | 163.53 | 221.35 | 28.8 | 99.1 |
| S3 | HYBRID | 258.6 | 221.90 | 303.51 | 1274.77 | 25.8 | 31.3 |
| S3 | POSTGRES | 499.3 | 92.83 | 168.76 | 226.47 | 26.4 | 99.2 |
| S4 | HYBRID | 90.9 | 27.39 | 39.40 | 48.08 | 15.0 | 31.7 |
| S4 | POSTGRES | 69.8 | 17.27 | 130.76 | 738.27 | 35.2 | 99.3 |
| S5 | HYBRID | 249.3 | 218.62 | 409.78 | 1229.81 | 23.7 | 34.5 |
| S5 | POSTGRES | 57.9 | 101.15 | 7998.36 | 17111.88 | 41.3 | 94.2 |
| S6 | HYBRID | 240.3 | 218.31 | 329.71 | 2352.81 | 24.5 | 39.2 |
| S6 | POSTGRES | 639.3 | 69.90 | 138.86 | 164.51 | 9.5 | 33.7 |
| S7 | HYBRID | 94.8 | 29.15 | 54.99 | 101.90 | 21.3 | 44.3 |
| S7 | POSTGRES | 95.6 | 14.79 | 21.53 | 29.00 | 2.7 | 33.2 |
| S8 | HYBRID | 214.2 | 221.64 | 383.63 | 739.61 | 65.5 | 62.2 |
| S8 | POSTGRES | 339.6 | 111.50 | 348.86 | 399.79 | 5.9 | 33.4 |
| S9 | HYBRID | 206.4 | 159.25 | 340.56 | 504.90 | 89.4 | 89.5 |
| S9 | POSTGRES | 402.8 | 93.07 | 332.14 | 383.41 | 6.5 | 33.4 |

## Análise Detalhada por Cenário

### S1: Baixo Volume + Baixa Taxa

**Configuração:**
- Volume: 10,000 logs
- Taxa alvo: 100 logs/segundo

**Comparação:**

1. **Throughput:** PostgreSQL é 8.2% mais lento
   - Hybrid: 89.5 logs/s
   - PostgreSQL: 97.5 logs/s

2. **Latência P95:** Hybrid é 37.3% melhor
   - Hybrid: 38.38 ms
   - PostgreSQL: 61.20 ms

3. **Uso de CPU:**
   - Hybrid: 13.0%
   - PostgreSQL: 53.4%

---

### S2: Baixo Volume + Média Taxa

**Configuração:**
- Volume: 10,000 logs
- Taxa alvo: 1000 logs/segundo

**Comparação:**

1. **Throughput:** PostgreSQL é 44.5% mais lento
   - Hybrid: 279.4 logs/s
   - PostgreSQL: 503.5 logs/s

2. **Latência P95:** PostgreSQL é 21.3% melhor
   - Hybrid: 198.42 ms
   - PostgreSQL: 163.53 ms

3. **Uso de CPU:**
   - Hybrid: 36.7%
   - PostgreSQL: 28.8%

---

### S3: Baixo Volume + Alta Taxa

**Configuração:**
- Volume: 10,000 logs
- Taxa alvo: 10000 logs/segundo

**Comparação:**

1. **Throughput:** PostgreSQL é 48.2% mais lento
   - Hybrid: 258.6 logs/s
   - PostgreSQL: 499.3 logs/s

2. **Latência P95:** PostgreSQL é 79.8% melhor
   - Hybrid: 303.51 ms
   - PostgreSQL: 168.76 ms

3. **Uso de CPU:**
   - Hybrid: 25.8%
   - PostgreSQL: 26.4%

---

### S4: Médio Volume + Baixa Taxa

**Configuração:**
- Volume: 100,000 logs
- Taxa alvo: 100 logs/segundo

**Comparação:**

1. **Throughput:** Hybrid é 30.1% mais rápido
   - Hybrid: 90.9 logs/s
   - PostgreSQL: 69.8 logs/s

2. **Latência P95:** Hybrid é 69.9% melhor
   - Hybrid: 39.40 ms
   - PostgreSQL: 130.76 ms

3. **Uso de CPU:**
   - Hybrid: 15.0%
   - PostgreSQL: 35.2%

---

### S5: Médio Volume + Média Taxa

**Configuração:**
- Volume: 100,000 logs
- Taxa alvo: 1000 logs/segundo

**Comparação:**

1. **Throughput:** Hybrid é 330.9% mais rápido
   - Hybrid: 249.3 logs/s
   - PostgreSQL: 57.9 logs/s

2. **Latência P95:** Hybrid é 94.9% melhor
   - Hybrid: 409.78 ms
   - PostgreSQL: 7998.36 ms

3. **Uso de CPU:**
   - Hybrid: 23.7%
   - PostgreSQL: 41.3%

---

### S6: Médio Volume + Alta Taxa

**Configuração:**
- Volume: 100,000 logs
- Taxa alvo: 10000 logs/segundo

**Comparação:**

1. **Throughput:** PostgreSQL é 62.4% mais lento
   - Hybrid: 240.3 logs/s
   - PostgreSQL: 639.3 logs/s

2. **Latência P95:** PostgreSQL é 137.4% melhor
   - Hybrid: 329.71 ms
   - PostgreSQL: 138.86 ms

3. **Uso de CPU:**
   - Hybrid: 24.5%
   - PostgreSQL: 9.5%

---

### S7: Alto Volume + Baixa Taxa

**Configuração:**
- Volume: 1,000,000 logs
- Taxa alvo: 100 logs/segundo

**Comparação:**

1. **Throughput:** PostgreSQL é 0.9% mais lento
   - Hybrid: 94.8 logs/s
   - PostgreSQL: 95.6 logs/s

2. **Latência P95:** PostgreSQL é 155.4% melhor
   - Hybrid: 54.99 ms
   - PostgreSQL: 21.53 ms

3. **Uso de CPU:**
   - Hybrid: 21.3%
   - PostgreSQL: 2.7%

---

### S8: Alto Volume + Média Taxa

**Configuração:**
- Volume: 1,000,000 logs
- Taxa alvo: 1000 logs/segundo

**Comparação:**

1. **Throughput:** PostgreSQL é 36.9% mais lento
   - Hybrid: 214.2 logs/s
   - PostgreSQL: 339.6 logs/s

2. **Latência P95:** PostgreSQL é 10.0% melhor
   - Hybrid: 383.63 ms
   - PostgreSQL: 348.86 ms

3. **Uso de CPU:**
   - Hybrid: 65.5%
   - PostgreSQL: 5.9%

---

### S9: Alto Volume + Alta Taxa

**Configuração:**
- Volume: 1,000,000 logs
- Taxa alvo: 10000 logs/segundo

**Comparação:**

1. **Throughput:** PostgreSQL é 48.7% mais lento
   - Hybrid: 206.4 logs/s
   - PostgreSQL: 402.8 logs/s

2. **Latência P95:** PostgreSQL é 2.5% melhor
   - Hybrid: 340.56 ms
   - PostgreSQL: 332.14 ms

3. **Uso de CPU:**
   - Hybrid: 89.4%
   - PostgreSQL: 6.5%

---

## Conclusões

### Arquitetura Híbrida (MongoDB + Fabric)

**Vantagens:**
- ✅ Imutabilidade e auditoria via blockchain
- ✅ Merkle Tree para verificação de integridade
- ✅ Auto-batching reduz transações na blockchain

**Desvantagens:**
- ⚠️ Overhead de sincronização com Fabric
- ⚠️ Latência adicional para escrita

### PostgreSQL Tradicional

**Vantagens:**
- ✅ Throughput máximo
- ✅ Latência mínima
- ✅ Simplicidade operacional

**Desvantagens:**
- ⚠️ Sem imutabilidade garantida
- ⚠️ Sem trilha de auditoria distribuída

### Recomendações

- **Use Hybrid:** Quando auditoria, compliance e imutabilidade são críticos
- **Use PostgreSQL:** Quando throughput máximo é prioritário
- **Trade-off aceitável:** O overhead da blockchain é justificável pelos benefícios de governança

---
*Relatório gerado automaticamente por analyze_results.py*
