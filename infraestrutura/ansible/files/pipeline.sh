#!/bin/bash
echo "A iniciar o pipeline de dados - $(date)"

# 1. Gerar os dados no Simulador (Python)
python3 /opt/fca/simulator/gerador_vendas.py --saida /opt/fca/data/raw/vendas.csv

# 2. Enviar o CSV sujo para a máquina ETL
scp -o StrictHostKeyChecking=no /opt/fca/data/raw/vendas.csv aluno@192.168.122.117:/opt/fca/data/raw/

# 3. Mandar a máquina ETL rodar o script R
ssh -o StrictHostKeyChecking=no aluno@192.168.122.117 "Rscript /opt/fca/etl/tratamento.R"

# 4. Mandar a máquina ETL enviar o CSV limpo para o Data Lake (Big Data)
ssh -o StrictHostKeyChecking=no aluno@192.168.122.117 "scp -o StrictHostKeyChecking=no /opt/fca/data/processed/vendas_tratadas.csv aluno@192.168.122.17:/opt/fca/data/processed/"

echo "Pipeline concluído com sucesso."