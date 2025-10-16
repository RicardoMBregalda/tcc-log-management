#!/bin/bash
# Otimiza kernel Linux para melhor performance de rede

echo "🔧 Otimizando Kernel Linux..."

# Aumentar limites de rede
sudo sysctl -w net.core.somaxconn=4096
sudo sysctl -w net.ipv4.tcp_max_syn_backlog=8192
sudo sysctl -w net.ipv4.ip_local_port_range="1024 65535"
sudo sysctl -w net.ipv4.tcp_tw_reuse=1
sudo sysctl -w net.ipv4.tcp_fin_timeout=15

# Aumentar limites de arquivos
sudo sysctl -w fs.file-max=2097152
ulimit -n 65536

echo "✅ Kernel otimizado!"
echo "   - somaxconn: 4096"
echo "   - tcp_max_syn_backlog: 8192"
echo "   - file-max: 2097152"
echo "   - Ganho esperado: -5ms em alta carga"
