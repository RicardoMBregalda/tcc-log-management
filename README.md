# Análise de Viabilidade de Blockchain para Gestão de Logs Corporativos

Este repositório contém o código-fonte e a infraestrutura para o Trabalho de Conclusão de Curso (TCC) intitulado "Análise da Viabilidade Técnica e Econômica da Blockchain Permissionada (Hyperledger Fabric) para a Gestão de Logs Corporativos: Um Estudo Comparativo de Desempenho e Integridade."

O objetivo deste projeto é implementar e comparar duas arquiteturas para o armazenamento e gerenciamento de logs em um ambiente simulado, avaliando métricas de desempenho, custo de recursos e garantias de integridade.

## Arquiteturas Implementadas

1.  **Arquitetura Tradicional:** Um cluster de banco de dados PostgreSQL em modo primário-standby, representando uma solução centralizada e de alta disponibilidade.

2.  **Arquitetura Híbrida:** Uma rede blockchain Hyperledger Fabric para ancoragem de hashes de logs (garantia de integridade *on-chain*) e um banco de dados MongoDB para o armazenamento dos logs completos (*off-chain*).

## Estrutura do Repositório

```
├── traditional-architecture/   # Arquivos da arquitetura PostgreSQL
│   ├── docker-compose.yml
│   ├── init-primary-db.sh
│   └── init-standby.sh
├── hybrid-architecture/        # Arquivos da arquitetura Blockchain
│   ├── fabric-network/
│   │   ├── crypto-config.yaml
│   │   ├── configtx.yaml
│   │   ├── docker-compose.yml
│   │   └── generate-artifacts.sh
│   └── chaincode/
│       ├── go.mod
│       ├── go.sum
│       └── logchaincode.go
└── testing/                    # Scripts para geração de carga e medição
    ├── api_server.py
    ├── log_generator.py
    └── performance_tester.py
```

## Pré-requisitos

Antes de começar, garanta que você tenha as seguintes ferramentas instaladas e configuradas em sua máquina:

* **Windows 10/11 com WSL 2:** O ambiente foi desenvolvido e testado usando o Subsistema do Windows para Linux.
* **Docker Desktop:** Instalado e configurado para usar o backend do WSL 2. [Guia de Instalação](https://www.docker.com/products/docker-desktop/).
* **Go (Golang):** Versão 1.18 ou superior. [Guia de Instalação](https://go.dev/doc/install).
* **Python:** Versão 3.8 ou superior. [Guia de Instalação](https://www.python.org/downloads/).
* **Git:** Para clonar o repositório.

## Guia de Instalação e Execução

Siga os passos abaixo para configurar e executar os ambientes de teste.

### 1. Clone o Repositório

```bash
git clone <URL_DO_SEU_REPOSITORIO>
cd tcc-log-management
```

### 2. Configurando a Arquitetura Tradicional (PostgreSQL)

Este ambiente simula um cluster PostgreSQL com replicação.

1.  Navegue para o diretório da arquitetura:

    ```bash
    cd traditional-architecture
    ```

2.  Torne os scripts executáveis:

    ```bash
    chmod +x init-primary-db.sh init-standby.sh
    ```

3.  Inicie os contêineres:

    ```bash
    docker compose up -d
    ```

4.  Para verificar se a replicação está funcionando, execute o teste de "somente leitura" no standby. O comando abaixo deve retornar um erro, confirmando o sucesso da configuração:

    ```bash
    docker exec -it postgres-standby psql -U logadmin logdb -c "CREATE TABLE test (id INT);"
    ```

### 3. Configurando a Arquitetura Híbrida (Fabric + MongoDB)

Esta é a configuração da rede blockchain.

1.  Navegue para o diretório da rede Fabric:

    ```bash
    cd ../hybrid-architecture/fabric-network 
    # (Se estiver na raiz, use 'cd hybrid-architecture/fabric-network')
    ```

2.  **Baixe as Ferramentas do Hyperledger Fabric.** Este comando baixa os binários `cryptogen` e `configtxgen` necessários.

    ```bash
    curl -sSL [https://raw.githubusercontent.com/hyperledger/fabric/main/scripts/bootstrap.sh](https://raw.githubusercontent.com/hyperledger/fabric/main/scripts/bootstrap.sh) | bash -s -- 2.4.9 1.5.6 -d -s
    ```

3.  **Gere os Artefatos Criptográficos.** Este script cria os certificados, chaves e o bloco gênesis.

    ```bash
    chmod +x generate-artifacts.sh
    ./generate-artifacts.sh
    ```

4.  **Inicialize o módulo do Chaincode.**

    ```bash
    cd ../chaincode
    go mod init logchaincode
    go mod tidy
    cd ../fabric-network
    ```

5.  **Inicie a Rede Blockchain.** Este comando pode levar vários minutos na primeira vez, pois baixará todas as imagens Docker.

    ```bash
    docker compose up -d
    ```

6.  Aguarde cerca de 40 segundos para os contêineres estabilizarem e, em seguida, **execute o script de setup do canal e do chaincode**. 

    ```bash
    chmod +x setup_network.sh
    docker exec cli ./setup_network.sh
    ```
    A execução bem-sucedida terminará com a mensagem `########### FIM DO SETUP - SUCESSO! ###########`.


### 4. Executando os Testes de Performance

Com os dois ambientes rodando, você pode executar os testes de performance.

1.  Navegue para o diretório de testes:

    ```bash
    cd ../../testing 
    # (Se estiver em fabric-network, use 'cd ../../testing')
    ```

2.  Instale as dependências Python:

    ```bash
    pip install psycopg2-binary requests Flask pymongo
    ```

3.  **Para testar a arquitetura PostgreSQL:**
    * Primeiro, crie a tabela de logs no banco de dados primário (execute apenas uma vez):

        ```bash
        docker exec -it postgres-primary psql -U logadmin logdb -c "CREATE TABLE logs (id UUID PRIMARY KEY, timestamp TIMESTAMPTZ, content JSONB);"
        ```

    * Execute o teste:

        ```bash
        python3 performance_tester.py postgresql --count 10000 --threads 50
        ```

4.  **Para testar a arquitetura Híbrida:**
    * **Em um terminal**, inicie o servidor de API. Ele ficará em execução.

        ```bash
        python3 api_server.py
        ```

    * **Abra um segundo terminal** e, no mesmo diretório `testing/`, execute o teste:

        ```bash
        python3 performance_tester.py hybrid --count 1000 --threads 20
        ```

## Limpando o Ambiente

Após concluir os testes, você pode parar e remover todos os contêineres e volumes para liberar recursos.

* Para limpar o ambiente **PostgreSQL**:

    ```bash
    cd ../traditional-architecture
    docker compose down --volumes
    ```

* Para limpar o ambiente **Híbrido**:

    ```bash
    cd ../hybrid-architecture/fabric-network
    docker compose down --volumes
    ```

## Autor

* **[Ricardo Bregalda]** - [ricardomeneguzzib@gmail.com](mailto:ricardomeneguzzib@gmail.com)