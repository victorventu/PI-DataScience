# Simulador de Vendas - FCA (Projeto Integrador)

Gera dados **sintéticos** de vendas com a mesma estrutura (**43 colunas**) do relatório real da F.C.A. Serviços Pecuários, mas com clientes, fornecedores, vendedores e valores fictícios. Assim a base pode ser usada livremente nas disciplinas (DevOps, Big Data, etc.) sem expor dados reais.

Clientes, fornecedores, vendedores e cidades são criados por algoritmo com a biblioteca **Faker** (dados fictícios em português). Não existe nenhum vínculo com pessoas ou empresas reais.

## Dois modos de uso

| Modo | Para que serve | Como funciona |
|---|---|---|
| **Lote** | Criar o **histórico** de vendas (jan/2016 a out/2026) | Gera tudo de uma vez e grava no CSV |
| **Contínuo (streaming)** | Simular o sistema de vendas **ao vivo** | Gera novos pedidos com a data e hora de **agora**, em intervalos aleatórios, e **continua a numeração de onde o histórico parou** |

## Estrutura dos arquivos

```
simulator/
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
sudo apt install -y python3 python3-pip python3-venv

# (recomendado) criar um ambiente virtual
python3 -m venv venv
source venv/bin/activate

# instalar a dependência (Faker)
pip install -r requirements.txt
```

## 2. Copiar os arquivos para a VM

```bash
scp -r simulator usuario@ip-da-vm:/opt/fca/
```

Ou clonar o repositório do projeto na VM.

## 3. Gerar o histórico (modo lote)

```bash
python3 gerador_vendas.py --pedidos 100000 --seed 42 --sobrescrever --saida dados/vendas.csv
```

Isso gera cerca de **136 mil linhas** (100 mil pedidos) de **01/01/2016 a 31/10/2026**. Com a mesma `--seed` o arquivo sai sempre igual.

> Use `--sobrescrever` quando quiser **recomeçar do zero** (apaga o CSV e o arquivo de estado). Sem essa opção, uma nova execução **acrescenta** linhas ao CSV existente.

### Parâmetros

| Parâmetro | Descrição | Padrão |
|---|---|---|
| `--saida` | Caminho do CSV de saída | `dados/vendas.csv` |
| `--seed` | Semente aleatória (mesmos dados a cada execução) | aleatória |
| `--pedidos` | Quantidade de pedidos no modo lote (cada pedido tem de 1 a 3 linhas) | 100000 |
| `--data-inicio` / `--data-fim` | Período do histórico (AAAA-MM-DD) | 2016-01-01 / 2026-10-31 |
| `--sobrescrever` | Lote: apaga o CSV e o estado e recomeça do zero | desligado |
| `--continuo` | Liga o modo contínuo (streaming) | desligado |
| `--intervalo-min` / `--intervalo-max` | Contínuo: tempo (segundos) entre um pedido e outro | 2 / 20 |
| `--limite` | Contínuo: para depois de N pedidos (0 = roda até `Ctrl+C`) | 0 |
| `--estado` | Caminho do arquivo JSON de estado | `estado_gerador.json` na pasta do CSV |
| `--vendedores` | Quantidade de vendedores | 4 |
| `--clientes` | Quantidade de clientes | 400 |
| `--fornecedores` / `--cidades` | Quantidade de fornecedores / cidades | 5 / 25 |
| `--pct-sujeira` | Proporção (0 a 1) de datas e textos fora do padrão | 0.15 |

O CSV usa `;` como separador e UTF-8.

## 4. Gerar em tempo real (modo contínuo)

```bash
python3 gerador_vendas.py --continuo --intervalo-min 2 --intervalo-max 20 --saida dados/vendas_live.csv
```

Os pedidos saem em intervalos **aleatórios**, como vendas de verdade. Para parar, use `Ctrl+C`.

Para gerar só alguns pedidos e parar (bom para testes e para o cron):

```bash
python3 gerador_vendas.py --continuo --limite 20 --intervalo-min 1 --intervalo-max 3 --saida dados/vendas_live.csv
```

### O arquivo de estado (`estado_gerador.json`)

Guarda os clientes, vendedores e contadores (pedido, nota fiscal, cupom). É ele que faz o modo contínuo **continuar a numeração do histórico**, sem repetir números.

- Rode o **lote antes** do contínuo e use o **mesmo arquivo de estado** nos dois.
- **Não rode dois geradores ao mesmo tempo** com o mesmo estado, porque os números iriam se repetir.
- Se o ETL lê tudo que está na pasta `raw`, guarde o estado em outra pasta com `--estado` (exemplo abaixo).

## 5. Automação na VM (DevOps)

Estrutura de diretórios usada no projeto:

| Caminho | Finalidade |
|---|---|
| `/opt/fca/simulator` | Código do simulador |
| `/opt/fca/data/raw` | Dados brutos gerados (CSV) |
| `/opt/fca/data/processed` | Dados tratados pelo ETL em R |
| `/opt/fca/logs` | Logs |

**Passo 1 - histórico (uma vez):**

```bash
cd /opt/fca/simulator
python3 gerador_vendas.py --pedidos 100000 --seed 42 --sobrescrever \
    --saida /opt/fca/data/raw/vendas.csv \
    --estado /opt/fca/simulator/estado_gerador.json
```

**Passo 2 - novos pedidos a cada hora (cron):**

```bash
crontab -e
```

```cron
0 * * * * cd /opt/fca/simulator && python3 gerador_vendas.py --continuo --limite 20 --intervalo-min 1 --intervalo-max 3 --saida /opt/fca/data/raw/vendas_live.csv --estado /opt/fca/simulator/estado_gerador.json >> /opt/fca/logs/simulador.log 2>&1
```

**Alternativa - rodar sempre em segundo plano (systemd):**

```ini
# /etc/systemd/system/gerador-vendas.service
[Unit]
Description=Gerador de vendas sinteticas (Projeto Integrador)

[Service]
WorkingDirectory=/opt/fca/simulator
ExecStart=/usr/bin/python3 gerador_vendas.py --continuo --intervalo-min 5 --intervalo-max 30 --saida /opt/fca/data/raw/vendas_live.csv --estado /opt/fca/simulator/estado_gerador.json
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now gerador-vendas
sudo systemctl status gerador-vendas
```

Use o cron **ou** o systemd, não os dois ao mesmo tempo.

## 6. Conferir o resultado

```bash
head -n 3 /opt/fca/data/raw/vendas.csv
wc -l /opt/fca/data/raw/vendas.csv
ls -lh /opt/fca/data/raw/
tail -n 3 /opt/fca/data/raw/vendas_live.csv
```

Ou com Python:

```python
import pandas as pd
df = pd.read_csv("/opt/fca/data/raw/vendas.csv", sep=";")
print(df.shape)   # (cerca de 136 mil linhas, 43 colunas)
print(df.head())
```

## O que foi simulado

**Padrões de negócio**

- **Sazonalidade:** `NUTRIÇÃO` e `KM` vendem mais de maio a setembro (seca); `GERAL` e `QUALIDADE DE LEITE` vendem mais de outubro a janeiro.
- **Crescimento:** o volume de pedidos cresce cerca de 6% ao ano e os preços são reajustados cerca de 6% ao ano.
- **Dias da semana:** sábado vende bem menos e domingo quase nada.
- **Clientes:** novos clientes entram ao longo dos anos e poucos clientes compram muito mais que os outros.
- **Documentos:** cerca de 47% dos pedidos têm Nota Fiscal, 23% têm Cupom Fiscal e 30% ainda não têm documento.
- **Numeração:** número de pedido, orçamento, NF e cupom sempre crescem junto com a data. O `IdProduto` é fixo.
- **Comissão:** `Vr.Comiss.` é a comissão **acumulada do vendedor no mês** (zera na virada do mês).

**Inconsistências propositais (para o tratamento no ETL em R)**

- **Datas em formatos diferentes** (cerca de 15%): por exemplo `2026-05-21 10:00:00`, `21/05/2026 10:00:00`, `21-05-2026 10:00:00` e `2026/05/21 10:00:00`. Nas datas curtas: `21/05/26`, `21-05-26`, `21/05/2026` e `2026-05-21`.
- **Textos com maiúsculas e minúsculas misturadas** em Cliente, Vendedor, Fornecedor e Cidade (o mesmo nome aparece em MAIÚSCULO, minúsculo e Title Case).
- **`Cód.Cliente` repetido** para clientes diferentes. Use o **nome padronizado** como chave do cliente.
- **Valores nulos esperados:** campos de NF e cupom só existem nos itens com esses documentos; `Preço Compra.` é nulo nos serviços.
- **Cupom com data de vencimento** em uma pequena parte dos casos (cupom é à vista).

**Nenhum dado real:** só o "formato" (colunas, tipos e faixas de valores) segue o relatório real. O catálogo de produtos é fixo, com nomes genéricos.

## Dicionário de dados (43 colunas)

| # | Coluna | Descrição | Pode ser nula? |
|---|---|---|---|
| 1 | `Nº Ped.` | Número do pedido (se repete em cada item do pedido) | Não |
| 2 | `Nº Orc.` | Número do orçamento que originou o pedido | Não |
| 3 | `Dt.Ped.` | Data e hora do pedido | Não |
| 4 | `Cliente` | Nome do cliente (produtor rural ou pessoa) | Não |
| 5 | `Produto` | Nome do produto ou serviço vendido | Não |
| 6 | `IdProduto` | Código do produto | Não |
| 7 | `Qnt.` | Quantidade vendida, na unidade da coluna `Un.` | Não |
| 8 | `Total Líquido` | Valor do item em R$ (`Qnt.` × `Vr.Unit.`) | Não |
| 9 | `Vendedor` | Vendedor responsável pelo pedido | Não |
| 10 | `Vr.Unit.` | Preço unitário de venda em R$ | Não |
| 11 | `Grupo` | Grupo do produto (7 grupos) | Não |
| 12 | `Marca` | REPRESENTAÇÃO ou INDEFINIDA | Não |
| 13 | `Fornecedor` | Fornecedor do produto | Sim (serviços e parte dos itens) |
| 14 | `Tot.Kg Bruto` | Peso bruto total do item em kg (`Qnt.` × `Peso Br. Un.`) | Não |
| 15 | `Total Bruto` | Valor antes do desconto (`Total Líquido` + `Tot.Desc.`) | Não |
| 16 | `Peso Br. Un.` | Peso bruto por unidade vendida (kg) | Não |
| 17 | `Dt.Cup.Sat.` | Data/hora do cupom fiscal SAT | Sim (só vendas por cupom) |
| 18 | `Dt.NF Lcto.` | Data/hora do lançamento da nota fiscal | Sim (só vendas com NF) |
| 19 | `N° NF.` | Número da nota fiscal | Sim (só vendas com NF) |
| 20 | `Dt.Cupom` | Data/hora do cupom fiscal | Sim (só vendas por cupom) |
| 21 | `Cód. NF.` | Código da nota fiscal (igual a `N° NF.`) | Sim (só vendas com NF) |
| 22 | `Dt.NF.Emis.` | Data/hora de emissão da nota fiscal | Sim (só vendas com NF) |
| 23 | `Nº Cup.` | Número do cupom fiscal | Sim (só vendas por cupom) |
| 24 | `Nº Cup.Sat.` | Número do cupom SAT | Sim (só vendas por cupom) |
| 25 | `Peso Líq. Un.` | Peso líquido por unidade vendida (kg) | Não |
| 26 | `Tot.Desc.` | Desconto total do item em R$ (0 quando não há desconto) | Não |
| 27 | `Cód.Cliente` | Código do cliente | Não |
| 28 | `Vr.Comiss.` | Comissão acumulada do vendedor no mês, em R$ | Não |
| 29 | `Un.` | Unidade de venda (KG, SC, UN, PC, LT, MIL) | Não |
| 30 | `Condição` | Condição de pagamento | Não |
| 31 | `Tot.Kg Líq.` | Peso líquido total do item em kg | Não |
| 32 | `SubGrupo` | Subcategoria dentro do grupo | Sim (≈15% em branco) |
| 33 | `Venc. Pedido` | Data de vencimento do pedido | Não |
| 34 | `Emissão Fin.` | Data de emissão financeira | Não |
| 35 | `Vr.Total NF.` | Valor do item na nota fiscal (0 quando não faturado) | Não |
| 36 | `Venc. Cupom` | Data de vencimento do cupom | Sim (quase sempre) |
| 37 | `Venc. Nota` | Data de vencimento da nota fiscal | Sim (só vendas com NF) |
| 38 | `Título` | Identificador do título financeiro do item | Não |
| 39 | `Cidade` | Cidade registrada na nota fiscal | Sim (só vendas com NF) |
| 40 | `Estado` | UF registrada na nota fiscal | Sim (só vendas com NF) |
| 41 | `Tipo Venda` | PRODUTOS, REPRESENTAÇÃO ou SERVIÇOS | Não |
| 42 | `Preço Compra.` | Custo de compra unitário em R$ | Sim (serviços não têm custo) |
| 43 | `Modelo NF` | Modelo da nota fiscal (55 = NF-e) | Sim (só vendas com NF) |

## Próximos passos

- Rodar o gerador dentro de um container Docker.
- Conectar o ETL em R à pasta `/opt/fca/data/raw` para limpar os dados e gravar em `/opt/fca/data/processed`.
- Mostrar o pipeline no Grafana (pedidos por hora, hora da última atualização e linhas processadas).
