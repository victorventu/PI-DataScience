# Big Data — Projeto Integrador FCA

Esta pasta contém a etapa de Big Data do projeto. Ela recebe o arquivo CSV já tratado pelo pipeline em R e realiza as etapas de Data Warehouse, OLAP, Machine Learning e processamento com Hadoop/Spark.

## Arquivos desta pasta

- [`PI_BigData_v3.ipynb`](PI_BigData_v3.ipynb): notebook original desenvolvido no Google Colab. Ele foi enviado diretamente do Colab para o repositório GitHub `victorventu/PI-DataScience`, na branch `main`, dentro desta pasta `big-data`.
- `bigdata.py`: versão do código exportada do notebook para Python.

O notebook é a versão recomendada para consultar e executar o fluxo no Google Colab, pois preserva a organização em células e os recursos interativos utilizados durante o desenvolvimento.

## Arquivo de entrada

O arquivo esperado é:

`vendas_limpa.csv`

Ele deve ser gerado pela etapa de tratamento em R. O CSV utiliza separador ponto e vírgula (`;`) e precisa manter as colunas esperadas pelo código, como `Dt.Ped.`, `Produto`, `IdProduto`, `Qnt.`, `Total Líquido`, `Cliente`, `Grupo`, `Vendedor`, `Fornecedor`, `Cidade` e `Estado`.

## Como executar

O código foi desenvolvido originalmente no Google Colab. Para executar a análise:

1. Execute o pipeline de DevOps/R e obtenha o arquivo `vendas_limpa.csv`.
2. Coloque o CSV no Google Drive, no caminho esperado pelo código: `MyDrive/PI_DataScience/Gerador/vendas_limpa.csv`.
3. Abra o notebook [`PI_BigData_v3.ipynb`](PI_BigData_v3.ipynb) no Google Colab. O notebook também está disponível neste repositório, dentro da pasta `big-data`.
4. Monte o Google Drive quando solicitado.
5. Para executar a etapa que recebe os dados tratados pelo R, comece pela seção **Data Warehouse (DW)**, logo após o encerramento da Análise Exploratória de Dados (EDA).
6. Execute as células seguintes em ordem até o final: Data Warehouse/ETL, operações OLAP, Machine Learning, Hadoop e Spark.

O código também cria um banco SQLite (`datawarehouse_fca.db`) e arquivos Parquet durante a execução. No código atual, esses arquivos são gravados em caminhos dentro do ambiente do Colab/Google Drive.

## Observação importante sobre o tratamento dos dados

No notebook de Big Data do Colab, o tratamento dos dados também foi executado novamente de forma redundante. Essa repetição foi feita como uma conferência adicional, para verificar se os dados estavam sendo tratados corretamente e se os resultados permaneciam consistentes.

**Essa repetição não é obrigatória no fluxo integrado do projeto.** Como o pipeline de R já entrega o arquivo `vendas_limpa.csv` tratado, é possível começar diretamente pela seção **Data Warehouse (DW)**, logo após a parte de Análise Exploratória de Dados (EDA), e seguir com as etapas posteriores.

## Dependências utilizadas

O código utiliza bibliotecas Python para manipulação, visualização, modelagem e processamento dos dados, incluindo:

- pandas
- numpy
- matplotlib
- seaborn
- scikit-learn
- SQLite (biblioteca `sqlite3`, incluída no Python)
- networkx
- plotly
- ipywidgets
- pyspark

No Google Colab, pode ser necessário instalar alguma biblioteca que não esteja disponível no ambiente. Para executar fora do Colab, também será necessário adaptar os caminhos de entrada/saída e a inicialização do Spark.

## Atenção sobre o arquivo `bigdata.py`

O arquivo `bigdata.py` é uma exportação do código desenvolvido no Colab. Ele ainda contém comandos específicos desse ambiente, como a montagem do Google Drive e caminhos iniciados por `/content/drive/`.

Por isso, **não deve ser considerado um script Python independente pronto para execução local**. Para execução local ou automatizada no pipeline, será necessário ajustar os caminhos dos arquivos e adaptar os recursos específicos de notebook/Colab, como `display()` e a interface interativa `ipywidgets`.
