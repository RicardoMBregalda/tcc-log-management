# Relatório de Testes de Tolerância a Falhas

**Data do Teste**: 2025-10-16T23:20:39.259109

**Total de Cenários**: 3

## 📊 Resumo Geral

### Vitórias por Métrica

| Métrica | Híbrida | Tradicional | Empate |
|---------|---------|-------------|--------|
| **Detecção de Falha** | 0 | 2 | 1 |
| **Recuperação** | 0 | 3 | 0 |
| **Perda de Dados** | 1 | 0 | 2 |
| **Disponibilidade** | 0 | 0 | 3 |

### 🏆 Pontuação Total

- **Híbrida**: 1 pontos
- **Tradicional**: 5 pontos

**Vencedor Geral**: 🎯 Arquitetura Tradicional

## 🔍 Detalhes por Cenário

### primary_database_failure

#### Tempos de Resposta

| Métrica | Híbrida | Tradicional | Diferença | Vencedor |
|---------|---------|-------------|-----------|----------|
| Detecção | 0.43s | 0.39s | 0.04s | traditional |
| Recuperação | 6.94s | 1.29s | 5.65s | traditional |

#### Integridade de Dados

| Métrica | Híbrida | Tradicional |
|---------|---------|-------------|
| Logs Enviados | 167 | 262 |
| Logs Recebidos | 167 | 162 |
| Logs Perdidos | 0 | 100 |
| % Perda | 0.0% | 38.17% |

**Vencedor em Integridade**: hybrid

#### Disponibilidade

- **Híbrida**: ❌ Parou de operar
- **Tradicional**: ❌ Parou de operar

---

### replica_node_failure

#### Tempos de Resposta

| Métrica | Híbrida | Tradicional | Diferença | Vencedor |
|---------|---------|-------------|-----------|----------|
| Detecção | 0.79s | 0.39s | 0.4s | traditional |
| Recuperação | 18.02s | 18.0s | 0.02s | traditional |

#### Integridade de Dados

| Métrica | Híbrida | Tradicional |
|---------|---------|-------------|
| Logs Enviados | 143 | 140 |
| Logs Recebidos | 143 | 140 |
| Logs Perdidos | 0 | 0 |
| % Perda | 0.0% | 0.0% |

**Vencedor em Integridade**: tie

#### Disponibilidade

- **Híbrida**: ✅ Continuou operando
- **Tradicional**: ✅ Continuou operando

---

### network_partition

#### Tempos de Resposta

| Métrica | Híbrida | Tradicional | Diferença | Vencedor |
|---------|---------|-------------|-----------|----------|
| Detecção | Nones | Nones | Nones | unknown |
| Recuperação | 7.77s | 5.04s | 2.73s | traditional |

#### Integridade de Dados

| Métrica | Híbrida | Tradicional |
|---------|---------|-------------|
| Logs Enviados | 98 | 97 |
| Logs Recebidos | 96 | 94 |
| Logs Perdidos | 0 | 0 |
| % Perda | 0.0% | 0.0% |

**Vencedor em Integridade**: tie

#### Disponibilidade

- **Híbrida**: ✅ Continuou operando
- **Tradicional**: ✅ Continuou operando

---

