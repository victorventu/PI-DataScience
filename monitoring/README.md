# 📊 Módulo de Monitoramento e Observabilidade (`vm-monitoring`)

Este diretório contém a definição e orquestração da stack de observabilidade da **`vm-monitoring`** (`192.168.122.139`), responsável pelo acompanhamento técnico e operacional do ecossistema de dados da **F.C.A.**

## 🚀 Componentes da Stack Docker

A solução é orquestrada via **Docker Compose** e composta por 3 contêineres principais:

| Serviço | Contêiner | Porta | Função |
| :--- | :--- | :--- | :--- |
| **Grafana** | `grafana` | `3000` | Interface gráfica e painéis de navegação para métricas visuais. |
| **Prometheus** | `prometheus` | `9090` | Banco de dados de séries temporais para coleta (*scraping*) de métricas. |
| **Node Exporter** | `node-exporter` | `9100` | Agente coletor de métricas de SO/hardware da VM (CPU, RAM, disco e rede). |

## 🛠️ Como Subir o Ambiente na VM

Conecte-se via SSH na VM de monitoramento e execute os comandos abaixo:

```bash
# 1. Entrar no diretório de monitoramento
cd ~/monitoring

# 2. Subir os contêineres em segundo plano
docker compose up -d

# 3. Confirmar se os 3 contêineres estão ativos
docker ps
```

## 📈 Painéis e Dashboards do Projeto F.C.A.

### 🔧 1. Dashboard Técnico (DevOps e Infraestrutura)

- **Saúde das Máquinas Virtuais (VMs):** Monitoramento contínuo de uso de CPU, memória RAM, espaço em disco e tráfego de rede das VMs do ecossistema (`vm-simulator`, `vm-etl`, `vm-bigdata` e `vm-monitoring`).
- **Status dos Containers (Docker / Kubernetes):** Acompanhamento do desempenho, tempo de atividade (*uptime*) e consumo de recursos dos serviços empacotados.

### 📦 2. Dashboard de Negócio (Foco Operacional e Logístico F.C.A.)

- **Níveis de Alerta de Estoque:** Indicadores visuais e gráficos destacando:
  - 🟢 **Estoque Saudável:** Volume em conformidade com a demanda projetada.
  - 🟡 **Risco de Ruptura:** Produtos próximos do nível crítico de reposição.
  - 🔴 **Risco de Vencimento:** Lotes de vacinas e medicamentos com validade próxima.
- **Tendência de Vendas e Sazonalidade:** Séries temporais exibindo o volume histórico e projetado de vendas de vacinas, medicamentos e suplementos ao longo dos meses para antecipar picos do calendário sanitário animal.
- **Sugestão de Reposição:** Painéis informativos listando automaticamente os pedidos de compra recomendados com base no *lead time* dos fornecedores.

---

## 🔍 Comandos Úteis de Manutenção

- **Ver logs em tempo real:**

```bash
docker compose logs -f
```

- **Parar a stack de monitoramento:**

```bash
docker compose down
```

- **Reiniciar os serviços:**

```bash
docker compose restart
```

