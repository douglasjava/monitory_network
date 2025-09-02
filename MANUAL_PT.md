# Manual de Configuração e Visualização de Métricas

Este manual explica como configurar e visualizar métricas do sistema de monitoramento de rede nas ferramentas 
Prometheus, InfluxDB e Grafana após a conexão da classe `metrics_exporter`.

## Índice

1. [Iniciando o Sistema de Monitoramento](#1-iniciando-o-sistema-de-monitoramento)
2. [Acessando e Visualizando Métricas no Prometheus](#2-acessando-e-visualizando-métricas-no-prometheus)
3. [Acessando e Visualizando Métricas no InfluxDB](#3-acessando-e-visualizando-métricas-no-influxdb)
4. [Acessando e Visualizando Métricas no Grafana](#4-acessando-e-visualizando-métricas-no-grafana)
5. [Testando o Sistema com Tráfego de Rede Simulado](#5-testando-o-sistema-com-tráfego-de-rede-simulado)
6. [Solução de Problemas Comuns](#6-solução-de-problemas-comuns)

## 1. Iniciando o Sistema de Monitoramento

### Pré-requisitos

Antes de começar, certifique-se de que você tem o seguinte instalado em seu sistema:

- Docker
- Docker Compose

### Passos para Iniciar o Sistema

1. Abra um terminal e navegue até o diretório do projeto:

   ```
   cd caminho/para/monitory_network
   ```

2. Construa e inicie todos os serviços usando Docker Compose:

   ```
   docker-compose up -d
   ```

   Este comando iniciará os seguintes serviços:
   - network-monitor: O aplicativo principal que monitora a largura de banda da rede
   - prometheus: Coleta e armazena métricas
   - influxdb: Banco de dados de séries temporais para armazenamento de métricas
   - grafana: Ferramenta de visualização para exibir métricas

3. Verifique se todos os contêineres estão em execução:

   ```
   docker-compose ps
   ```

   Você deve ver todos os serviços listados com o status "Up".

## 2. Acessando e Visualizando Métricas no Prometheus

O Prometheus é uma ferramenta de monitoramento que coleta e armazena métricas como séries temporais.

### Passos para Acessar o Prometheus

1. Abra seu navegador e acesse:

   ```
   http://localhost:9090
   ```

2. Você verá a interface web do Prometheus.

### Visualizando Métricas no Prometheus

1. Para visualizar as métricas de upload de rede:
   - Clique na caixa de pesquisa na parte superior da página
   - Digite `network_upload_mbps` e pressione Enter
   - Clique no botão "Execute" para executar a consulta
   - Você verá um gráfico mostrando a velocidade de upload da rede em Mbps

2. Para visualizar as métricas de download de rede:
   - Clique na caixa de pesquisa na parte superior da página
   - Digite `network_download_mbps` e pressione Enter
   - Clique no botão "Execute" para executar a consulta
   - Você verá um gráfico mostrando a velocidade de download da rede em Mbps

3. Para visualizar ambas as métricas em um único gráfico:
   - Digite a seguinte expressão na caixa de pesquisa:
     ```
     network_upload_mbps or network_download_mbps
     ```
   - Clique em "Execute"
   - Você verá um gráfico com ambas as métricas

4. Para explorar todas as métricas disponíveis:
   - Clique em "Status" no menu superior
   - Selecione "Targets"
   - Você verá todos os alvos que o Prometheus está monitorando
   - Clique em "Graph" no menu superior
   - Clique no botão "Insert metric at cursor" para ver todas as métricas disponíveis

## 3. Acessando e Visualizando Métricas no InfluxDB

O InfluxDB é um banco de dados de séries temporais otimizado para armazenar e consultar dados de monitoramento.

### Passos para Acessar o InfluxDB

1. Abra seu navegador e acesse:

   ```
   http://localhost:8086
   ```

2. Faça login com as seguintes credenciais:
   - Usuário: `admin`
   - Senha: `adminpassword`

### Visualizando Métricas no InfluxDB

1. Após fazer login, você verá o painel do InfluxDB.

2. Para visualizar os dados:
   - Clique em "Data Explorer" no menu lateral esquerdo
   - No painel "From", selecione o bucket `network_metrics`
   - No painel "Filter", selecione a medição `network_bandwidth`
   - No painel "Filter", selecione o campo `upload_mbps` ou `download_mbps`
   - Clique em "Submit" para executar a consulta
   - Você verá um gráfico com os dados selecionados

3. Para criar uma consulta personalizada:
   - Clique em "Scripts" no menu lateral esquerdo
   - Crie um novo script com a seguinte consulta Flux:
     ```
     from(bucket: "network_metrics")
       |> range(start: -1h)
       |> filter(fn: (r) => r._measurement == "network_bandwidth")
       |> filter(fn: (r) => r._field == "upload_mbps" or r._field == "download_mbps")
     ```
   - Clique em "Run" para executar a consulta
   - Você verá um gráfico com os dados de upload e download dos últimos 60 minutos

## 4. Acessando e Visualizando Métricas no Grafana

O Grafana é uma plataforma de visualização que permite criar dashboards interativos para suas métricas.

### Passos para Acessar o Grafana

1. Abra seu navegador e acesse:

   ```
   http://localhost:3000
   ```

2. Faça login com as seguintes credenciais:
   - Usuário: `admin`
   - Senha: `admin`
   
3. Na primeira vez que você fizer login, o Grafana solicitará que você altere a senha. Você pode alterar ou pular esta etapa.

### Visualizando Métricas no Grafana

1. Após fazer login, você verá o painel inicial do Grafana.

2. Para acessar o dashboard pré-configurado:
   - Clique em "Home" no menu superior
   - Clique em "Network Monitoring Dashboard"
   - Você verá um dashboard com dois painéis:
     - Network Bandwidth (Prometheus): Mostra dados de upload e download do Prometheus
     - Network Bandwidth (InfluxDB): Mostra dados de upload e download do InfluxDB

3. Para ajustar o intervalo de tempo:
   - Clique no seletor de tempo no canto superior direito
   - Selecione um intervalo predefinido ou defina um intervalo personalizado
   - Clique em "Apply"

4. Para criar um novo dashboard:
   - Clique no ícone "+" no menu lateral esquerdo
   - Selecione "Dashboard"
   - Clique em "Add new panel"
   - Selecione a fonte de dados (Prometheus ou InfluxDB)
   - Configure a consulta para as métricas desejadas
   - Clique em "Save" para salvar o painel

## 5. Testando o Sistema com Tráfego de Rede Simulado

Para testar o sistema de monitoramento, você pode gerar tráfego de rede artificial usando o script de teste incluído.

### Passos para Executar o Teste

1. Abra um novo terminal e navegue até o diretório do projeto:

   ```
   cd caminho/para/monitory_network
   ```

2. Execute o script de teste com os parâmetros desejados:

   ```
   python test_network_traffic.py --duration 120 --download-intensity 7 --upload-intensity 5
   ```

   Opções disponíveis:
   - `--duration`: Duração em segundos para gerar tráfego (padrão: 60)
   - `--download-intensity`: Nível de intensidade de download de 1 a 10 (padrão: 5)
   - `--upload-intensity`: Nível de intensidade de upload de 1 a 10 (padrão: 5)
   - `--download-only`: Gerar apenas tráfego de download
   - `--upload-only`: Gerar apenas tráfego de upload

3. Enquanto o script estiver em execução, você poderá ver as métricas de rede no Grafana, Prometheus e InfluxDB mostrando o tráfego simulado.

## 6. Solução de Problemas Comuns

### Problema: Os contêineres não iniciam

**Solução:**
1. Verifique se o Docker está em execução:
   ```
   docker info
   ```

2. Verifique os logs dos contêineres:
   ```
   docker-compose logs
   ```

3. Reinicie os serviços:
   ```
   docker-compose down
   docker-compose up -d
   ```

### Problema: Não consigo ver métricas no Prometheus

**Solução:**
1. Verifique se o serviço network-monitor está em execução:
   ```
   docker-compose ps network-monitor
   ```

2. Verifique os logs do serviço network-monitor:
   ```
   docker-compose logs network-monitor
   ```

3. Verifique se o Prometheus está configurado corretamente:
   ```
   docker-compose exec prometheus promtool check config /etc/prometheus/prometheus.yml
   ```

4. Verifique se o Prometheus pode acessar o alvo:
   - Acesse http://localhost:9090/targets
   - Verifique se o alvo "network-monitor" está "UP"

### Problema: Não consigo ver métricas no InfluxDB

**Solução:**
1. Verifique se o serviço InfluxDB está em execução:
   ```
   docker-compose ps influxdb
   ```

2. Verifique os logs do serviço InfluxDB:
   ```
   docker-compose logs influxdb
   ```

3. Verifique se o bucket foi criado corretamente:
   - Acesse http://localhost:8086
   - Faça login e vá para "Data > Buckets"
   - Verifique se o bucket "network_metrics" existe

### Problema: Não consigo ver o dashboard no Grafana

**Solução:**
1. Verifique se o serviço Grafana está em execução:
   ```
   docker-compose ps grafana
   ```

2. Verifique os logs do serviço Grafana:
   ```
   docker-compose logs grafana
   ```

3. Verifique se as fontes de dados estão configuradas corretamente:
   - Acesse http://localhost:3000/datasources
   - Verifique se as fontes de dados "Prometheus" e "InfluxDB" estão listadas e têm status "Working"

4. Importe manualmente o dashboard:
   - Acesse http://localhost:3000/dashboard/import
   - Clique em "Upload .json file"
   - Selecione o arquivo "grafana/provisioning/dashboards/network_dashboard.json"
   - Clique em "Import"

### Parando o Sistema

Para parar todos os serviços:

```
docker-compose down
```

Para parar e remover todos os volumes (isso excluirá todos os dados armazenados):

```
docker-compose down -v
```