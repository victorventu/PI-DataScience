## 🚀 Automação e Pipeline de Dados (F.C.A. Serviços Pecuários)

O ambiente do laboratório de dados é totalmente provisionado e gerido via **Ansible**, garantindo reprodutibilidade e automação nas 4 VMs do projeto (`simulator`, `etl`, `bigdata`, `monitoring`).

### ⚙️ Arquitetura do Simulador e Agendamento (Cron)
A `vm-simulator` executa de forma autónoma um script em Python (`gerador.py`) que simula dados transacionais do agronegócio (registos de animais, vacinas e stocks) e os guarda na camada *raw* do data lake local.

* **Diretório do Código:** `/opt/fca/simulator/`
* **Diretório de Saída (Dados Brutos):** `/opt/fca/data/raw/dados_foco.csv`
* **Periodicidade (Automática):** Execução a cada hora via **Cron** do sistema (`0 * * * *`).

### 🕹️ Execução Manual
Caso precise de gerar novos dados imediatamente (sem esperar pelo ciclo automático do agendamento), aceda à `vm-simulator` via SSH e execute o script manualmente:

\`\`\`bash
sudo python3 /opt/fca/simulator/gerador.py --output /opt/fca/data/raw
\`\`\`

Para confirmar que o ficheiro `.csv` foi atualizado com sucesso, verifique a hora da última modificação:

\`\`\`bash
ls -lh /opt/fca/data/raw/dados_foco.csv
\`\`\`

### 📦 Como Executar o Provisionamento (Ansible)
Para subir ou atualizar toda a infraestrutura e configurar os agendamentos nas VMs do laboratório, execute o seguinte playbook a partir da máquina de controlo:

\`\`\`bash
cd ansible/
ansible-playbook -i inventory.ini playbooks/setup.yml --ask-become-pass
\`\`\`


# Simulador de Vendas — FCA (Projeto Integrador)

Gera dados **sintéticos** de vendas, com a mesma estrutura (43 colunas) do
relatório real da empresa parceira, mas com clientes, fornecedores e valores
fictícios — para poder ser usado livremente na disciplina de DevOps.

Clientes, fornecedores, vendedores e cidades são gerados por algoritmo com a
biblioteca **Faker** (dados fictícios em português) — não são nomes
digitados por mim nem copiados de lugar nenhum, então não têm nenhum vínculo
com dado real ou sensível.

## Estrutura dos arquivos

```
simulador_vendas_fca/
├── gerador_vendas.py   # script principal
├── requirements.txt    # única dependência: Faker
└── README.md
```

## 1. Preparar a VM Linux

```bash
# verificar se o Python 3 já está instalado
python3 --version

# se não estiver:
sudo apt update
sudo apt install -y python3

# (opcional, mas recomendado) criar um ambiente virtual isolado
python3 -m venv venv
source venv/bin/activate

# instalar a única dependência (Faker, usada para gerar nomes fictícios)
pip install -r requirements.txt
```

## 2. Copiar os arquivos para a VM

Do seu computador para a VM (exemplo via `scp`):
```bash
scp -r simulador_vendas_fca usuario@ip-da-vm:~/
```
Ou clonando de um repositório Git, se o grupo já versionou o projeto.

## 3. Rodar em modo lote (gera um CSV de uma vez)

```bash
python3 gerador_vendas.py --pedidos 1000 --saida dados/vendas.csv --seed 42
```

Parâmetros principais:
| Parâmetro | Descrição | Padrão |
|---|---|---|
| `--pedidos` | quantos pedidos gerar (cada pedido pode virar 1–3 linhas) | 200 |
| `--saida` | caminho do CSV de saída | `dados/vendas.csv` |
| `--seed` | semente aleatória, para conseguir reproduzir os mesmos dados depois | aleatória |
| `--data-inicio` / `--data-fim` | período das datas de pedido (AAAA-MM-DD) | 2026-01-01 / 2026-09-01 |

O CSV usa `;` como separador (igual ao padrão de exportação do sistema real) e
é escrito em UTF-8.

## 4. Rodar em modo contínuo (simula um sistema "ao vivo", de forma esporádica)

Útil para testar pipelines de DevOps que devem ler dados incrementais (ex.:
um job que varre a pasta a cada X segundos, ou um `tail -f`):

```bash
python3 gerador_vendas.py --continuo --intervalo-min 2 --intervalo-max 20 --saida dados/vendas_live.csv
```

Isso deixa o processo rodando, gerando pedidos em intervalos **aleatórios**
entre `--intervalo-min` e `--intervalo-max` segundos — às vezes dois pedidos
seguidos bem rápido, às vezes uma pausa maior — em vez de um ritmo fixo e
mecânico, para parecer mais com vendas acontecendo de verdade. Encerra com
`Ctrl+C`.

### Rodando o modo contínuo em segundo plano na VM

Para não depender de manter o terminal aberto:

```bash
nohup python3 gerador_vendas.py --continuo --intervalo-min 5 --intervalo-max 30 --saida dados/vendas_live.csv \
    > gerador.log 2>&1 &
```

Ou, se a aula pedir algo mais "DevOps de verdade", criar um serviço `systemd`:

```ini
# /etc/systemd/system/gerador-vendas.service
[Unit]
Description=Gerador de vendas sintéticas (Projeto Integrador)

[Service]
WorkingDirectory=/home/usuario/simulador_vendas_fca
ExecStart=/usr/bin/python3 gerador_vendas.py --continuo --intervalo-min 5 --intervalo-max 30 --saida /home/usuario/simulador_vendas_fca/dados/vendas_live.csv
Restart=always

[Install]
WantedBy=multi-user.target
```
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now gerador-vendas
sudo systemctl status gerador-vendas
```

## 5. Conferir o resultado

```bash
head dados/vendas.csv
wc -l dados/vendas.csv
```

Ou, com Python/Pandas (se disponível):
```python
import pandas as pd
df = pd.read_csv("dados/vendas.csv", sep=";")
print(df.shape)
print(df.head())
```

## O que foi simulado (e por quê)

- **Estrutura idêntica**: as 43 colunas têm exatamente o mesmo nome/ordem do
  relatório real, para o restante do pipeline (Big Data/Analytics) não
  precisar mudar nada ao trocar o dataset real pelo sintético.
- **Proporções realistas**: coisas como "~47% dos pedidos já faturados",
  "~30% sem fornecedor preenchido" e colunas sempre vazias (`SubGrupo`,
  `Nº Cup.`, etc.) foram reproduzidas a partir do padrão observado no
  relatório real, sem copiar nenhum valor real.
- **Nenhum dado real ou sensível**: clientes, fornecedores, vendedores e
  cidades são gerados por algoritmo (Faker), não copiados nem inspirados em
  nomes reais — só a "forma" dos dados (tipos, faixas, distribuição) é
  parecida com a real. Só o catálogo de produtos é fixo (nomes de produtos
  veterinários genéricos, sem ligação com fornecedores reais).

## Possíveis próximos passos para a aula de DevOps

- Rodar o script dentro de um container Docker.
- Agendar execuções com `cron` em vez de modo contínuo.
- Fazer um pipeline (ex.: shell script ou Airflow) que lê o CSV gerado e
  carrega em um banco de dados.
