# /opt/fca/etl/tratamento.R
cat("Iniciando o tratamento de dados em R...\n")

arquivo_entrada <- "/opt/fca/data/raw/vendas.csv"
arquivo_saida <- "/opt/fca/data/processed/vendas_tratadas.csv"

# Verifica se o arquivo gerado pelo simulador chegou na ETL
if (!file.exists(arquivo_entrada)) {
  stop("ERRO: Arquivo vendas.csv nao encontrado na pasta raw!")
}

# Lê os dados
dados <- read.csv(arquivo_entrada, stringsAsFactors = FALSE)
cat("Arquivo lido com sucesso. Linhas originais:", nrow(dados), "\n")

# Limpeza simples: Remove linhas com valores nulos e passa colunas para maiúsculo
dados_limpos <- na.omit(dados)
names(dados_limpos) <- toupper(names(dados_limpos))

# Cria a pasta de destino caso não exista e salva o arquivo limpo
dir.create(dirname(arquivo_saida), recursive = TRUE, showWarnings = FALSE)
write.csv(dados_limpos, arquivo_saida, row.names = FALSE)

cat("Tratamento concluído! Arquivo salvo em:", arquivo_saida, "\n")