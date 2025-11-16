# Performance Test Report - Go API

**Data:** 2025-11-15 10:53:58

**Duração Total:** 541.74 minutos

**Total de Testes:** 36

## Resultados Consolidados

| Cenário | Tipo | Logs | Taxa | Duração (s) | Throughput | Latência Média | P95 | P99 |
|---------|------|------|------|-------------|------------|----------------|-----|-----|
| S1 | Insert | 10000 | 100/s | 100.00 | 100.00 logs/s | 3.90 ms | 4.74 ms | 10.43 ms |
| S1_query | Query | 1000 | 100/s | 1.30 | 771.72 logs/s | 25.80 ms | 8.29 ms | 1058.44 ms |
| S1_postgres | Insert | 10000 | 100/s | 100.01 | 99.99 logs/s | 1.41 ms | 1.61 ms | 2.78 ms |
| S1_postgres_query | Query | 1000 | 100/s | 0.31 | 3261.75 logs/s | 5.62 ms | 22.62 ms | 35.42 ms |
| S2 | Insert | 10000 | 1000/s | 17.20 | 581.23 logs/s | 85.45 ms | 101.89 ms | 156.41 ms |
| S2_query | Query | 1000 | 1000/s | 1.32 | 755.80 logs/s | 26.36 ms | 8.67 ms | 1096.47 ms |
| S2_postgres | Insert | 10000 | 1000/s | 10.55 | 948.27 logs/s | 1.71 ms | 2.03 ms | 7.61 ms |
| S2_postgres_query | Query | 1000 | 1000/s | 0.37 | 2731.43 logs/s | 6.80 ms | 28.58 ms | 40.28 ms |
| S3 | Insert | 10000 | 10000/s | 17.63 | 567.14 logs/s | 174.21 ms | 199.37 ms | 335.18 ms |
| S3_query | Query | 1000 | 10000/s | 1.78 | 563.22 logs/s | 33.94 ms | 13.55 ms | 1307.00 ms |
| S3_postgres | Insert | 10000 | 10000/s | 10.83 | 923.27 logs/s | 1.73 ms | 1.99 ms | 9.02 ms |
| S3_postgres_query | Query | 1000 | 10000/s | 0.40 | 2520.11 logs/s | 7.32 ms | 30.56 ms | 41.50 ms |
| S4 | Insert | 100000 | 100/s | 1000.01 | 100.00 logs/s | 3.91 ms | 4.77 ms | 9.84 ms |
| S4_query | Query | 10000 | 100/s | 3.66 | 2733.39 logs/s | 7.25 ms | 8.32 ms | 19.74 ms |
| S4_postgres | Insert | 100000 | 100/s | 1000.03 | 100.00 logs/s | 1.40 ms | 1.65 ms | 2.54 ms |
| S4_postgres_query | Query | 10000 | 100/s | 8.65 | 1155.43 logs/s | 16.84 ms | 74.08 ms | 100.44 ms |
| S5 | Insert | 100000 | 1000/s | 171.95 | 581.56 logs/s | 85.86 ms | 103.77 ms | 145.87 ms |
| S5_query | Query | 10000 | 1000/s | 3.78 | 2647.84 logs/s | 7.48 ms | 7.77 ms | 9.62 ms |
| S5_postgres | Insert | 100000 | 1000/s | 104.82 | 954.03 logs/s | 1.81 ms | 2.43 ms | 7.88 ms |
| S5_postgres_query | Query | 10000 | 1000/s | 13.08 | 764.49 logs/s | 25.67 ms | 123.00 ms | 163.13 ms |
| S6 | Insert | 100000 | 10000/s | 170.81 | 585.44 logs/s | 170.53 ms | 200.06 ms | 276.78 ms |
| S6_query | Query | 10000 | 10000/s | 3.82 | 2620.82 logs/s | 7.55 ms | 8.14 ms | 10.43 ms |
| S6_postgres | Insert | 100000 | 10000/s | 108.77 | 919.38 logs/s | 1.62 ms | 2.05 ms | 5.71 ms |
| S6_postgres_query | Query | 10000 | 10000/s | 20.80 | 480.67 logs/s | 40.98 ms | 201.71 ms | 288.96 ms |
| S7 | Insert | 1000000 | 100/s | 10000.21 | 100.00 logs/s | 4.96 ms | 7.78 ms | 19.78 ms |
| S7_query | Query | 100000 | 100/s | 27.27 | 3666.98 logs/s | 5.38 ms | 7.91 ms | 11.12 ms |
| S7_postgres | Insert | 1000000 | 100/s | 10000.21 | 100.00 logs/s | 2.17 ms | 2.94 ms | 4.16 ms |
| S7_postgres_query | Query | 100000 | 100/s | 146.78 | 681.29 logs/s | 28.92 ms | 138.67 ms | 186.95 ms |
| S8 | Insert | 1000000 | 1000/s | 3243.48 | 308.31 logs/s | 162.12 ms | 249.08 ms | 309.44 ms |
| S8_query | Query | 100000 | 1000/s | 28.94 | 3455.88 logs/s | 5.71 ms | 7.90 ms | 11.50 ms |
| S8_postgres | Insert | 1000000 | 1000/s | 1022.75 | 977.75 logs/s | 3.07 ms | 7.76 ms | 11.86 ms |
| S8_postgres_query | Query | 100000 | 1000/s | 506.62 | 197.39 logs/s | 100.92 ms | 460.79 ms | 571.08 ms |
| S9 | Insert | 1000000 | 10000/s | 3100.75 | 322.50 logs/s | 309.98 ms | 502.11 ms | 575.95 ms |
| S9_query | Query | 100000 | 10000/s | 37.09 | 2696.09 logs/s | 7.34 ms | 7.83 ms | 11.23 ms |
| S9_postgres | Insert | 1000000 | 10000/s | 1069.53 | 934.99 logs/s | 4.47 ms | 8.17 ms | 16.82 ms |
| S9_postgres_query | Query | 100000 | 10000/s | 371.44 | 269.22 logs/s | 73.80 ms | 363.51 ms | 496.64 ms |

## Uso de Recursos

| Cenário | Tipo | CPU Avg | Memory Avg | Disk Read | Disk Write |
|---------|------|---------|------------|-----------|------------|
| S1 | Insert | 0.40% | 2 MB | 0.00 MB | 0.00 MB |
| S1_query | Query | 6.40% | 1 MB | 0.00 MB | 0.00 MB |
| S1_postgres | Insert | 0.40% | 2 MB | 0.00 MB | 0.00 MB |
| S1_postgres_query | Query | 0.00% | 0 MB | 0.00 MB | 0.00 MB |
| S2 | Insert | 15.39% | 2 MB | 0.00 MB | 0.00 MB |
| S2_query | Query | 6.40% | 2 MB | 0.00 MB | 0.00 MB |
| S2_postgres | Insert | 0.46% | 2 MB | 0.00 MB | 0.00 MB |
| S2_postgres_query | Query | 0.00% | 0 MB | 0.00 MB | 0.00 MB |
| S3 | Insert | 30.37% | 4 MB | 0.00 MB | 0.00 MB |
| S3_query | Query | 6.40% | 1 MB | 0.00 MB | 0.00 MB |
| S3_postgres | Insert | 0.49% | 2 MB | 0.00 MB | 0.00 MB |
| S3_postgres_query | Query | 0.00% | 0 MB | 0.00 MB | 0.00 MB |
| S4 | Insert | 0.38% | 2 MB | 0.00 MB | 0.00 MB |
| S4_query | Query | 5.97% | 1 MB | 0.00 MB | 0.00 MB |
| S4_postgres | Insert | 0.41% | 2 MB | 0.00 MB | 0.00 MB |
| S4_postgres_query | Query | 2.40% | 2 MB | 0.00 MB | 0.00 MB |
| S5 | Insert | 15.37% | 3 MB | 0.00 MB | 0.00 MB |
| S5_query | Query | 6.30% | 1 MB | 0.00 MB | 0.00 MB |
| S5_postgres | Insert | 0.52% | 2 MB | 0.00 MB | 0.00 MB |
| S5_postgres_query | Query | 2.39% | 2 MB | 0.00 MB | 0.00 MB |
| S6 | Insert | 30.36% | 5 MB | 0.00 MB | 0.00 MB |
| S6_query | Query | 6.40% | 2 MB | 0.00 MB | 0.00 MB |
| S6_postgres | Insert | 0.56% | 2 MB | 0.00 MB | 0.00 MB |
| S6_postgres_query | Query | 2.40% | 2 MB | 0.00 MB | 0.00 MB |
| S7 | Insert | 0.54% | 13 MB | 0.00 MB | 0.00 MB |
| S7_query | Query | 6.02% | 3 MB | 0.00 MB | 0.00 MB |
| S7_postgres | Insert | 0.40% | 12 MB | 0.00 MB | 0.00 MB |
| S7_postgres_query | Query | 2.39% | 2 MB | 0.00 MB | 0.00 MB |
| S8 | Insert | 15.29% | 14 MB | 0.00 MB | 0.00 MB |
| S8_query | Query | 6.14% | 4 MB | 0.00 MB | 0.00 MB |
| S8_postgres | Insert | 0.70% | 12 MB | 0.00 MB | 0.00 MB |
| S8_postgres_query | Query | 2.40% | 3 MB | 0.00 MB | 0.00 MB |
| S9 | Insert | 30.29% | 15 MB | 0.00 MB | 0.00 MB |
| S9_query | Query | 6.15% | 7 MB | 0.00 MB | 0.00 MB |
| S9_postgres | Insert | 0.83% | 12 MB | 0.00 MB | 0.00 MB |
| S9_postgres_query | Query | 2.40% | 2 MB | 0.00 MB | 0.00 MB |

---
*Relatório gerado automaticamente em 2025-11-15 10:53:58*
