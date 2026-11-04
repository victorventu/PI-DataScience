# 1. Pacotes
library(tidyverse)
library(janitor)
library(skimr)
library(ggplot2)
library(corrplot)

# 2. Caminhos (Compatível com Windows, Linux)
if (dir.exists("/opt/fca")) {
  # Caminho no Linux
  pasta_base <- "/opt/fca"
} else {
  # Caminho no Windows: busca a pasta que contém o arquivo do projeto
  pasta_base <- normalizePath(file.path(getwd(), "..", ".."), mustWork = FALSE)
  
  # Se não achar a pasta simulator, volta para a pasta atual
  if (!dir.exists(file.path(pasta_base, "simulator"))) {
    pasta_base <- getwd() 
  }
}

arquivo_entrada <- file.path(pasta_base, "simulator", "vendas.csv")
pasta_saida     <- file.path(pasta_base, "etl")

# 3. Verificação do arquivo
if (!file.exists(arquivo_entrada)) {
  stop("ERRO: Arquivo vendas.csv não encontrado no caminho: ", arquivo_entrada)
}

# 4. Leitura
cat("Iniciando leitura dos dados brutos...\n")
dados_brutos <- read.csv2(arquivo_entrada, stringsAsFactors = FALSE, check.names = FALSE)
cat("Linhas lidas:", nrow(dados_brutos), "| Colunas:", ncol(dados_brutos), "\n\n")

# 5. Diagnóstico Inicial
cat("--- DIAGNÓSTICO INICIAL ---\n")
cat("Total de valores nulos no arquivo:", sum(is.na(dados_brutos)), "\n")
cat("Linhas duplicadas:", sum(duplicated(dados_brutos)), "\n\n")

# 6. Limpeza e Padronização
dados_limpos <- dados_brutos %>%
  clean_names() %>%
  remove_empty(c("rows", "cols")) %>%
  distinct() %>%
  mutate(
    vr_unit = as.numeric(as.character(vr_unit)),
    total_liquido = as.numeric(as.character(total_liquido)),
    qnt = as.numeric(as.character(qnt)),
    tot_desc = as.numeric(as.character(tot_desc))
  )

# 7. Salvar dados limpos (Big Data / Colab)
if (!dir.exists(pasta_saida)) dir.create(pasta_saida, recursive = TRUE)
arquivo_saida <- file.path(pasta_saida, "vendas_tratadas.csv")
write.csv(dados_limpos, arquivo_saida, row.names = FALSE)
cat("Dados limpos salvos em:", arquivo_saida, "\n\n")

# 8. GRÁFICOS (Mostra na tela)

grafico1 <- dados_limpos %>%
  group_by(produto) %>%
  summarise(total_qnt = sum(qnt, na.rm = TRUE)) %>%
  arrange(desc(total_qnt)) %>%
  slice(1:10) %>%
  ggplot(aes(x = reorder(produto, total_qnt), y = total_qnt)) +
  geom_col(fill = "steelblue") + coord_flip() + theme_minimal() +
  labs(title = "Top 10 Produtos Mais Vendidos", x = "Produto", y = "Qtd.")
print(grafico1)

grafico2 <- ggplot(dados_limpos, aes(x = vr_unit)) +
  geom_histogram(fill = "darkgreen", color = "black", bins = 30) +
  theme_minimal() + labs(title = "Distribuição de Preços", x = "Preço", y = "Frequência")
print(grafico2)

grafico3 <- dados_limpos %>%
  group_by(vendedor) %>%
  summarise(faturamento = sum(total_liquido, na.rm = TRUE)) %>%
  ggplot(aes(x = reorder(vendedor, faturamento), y = faturamento)) +
  geom_col(fill = "orange") + coord_flip() + theme_minimal() +
  labs(title = "Faturamento por Vendedor", x = "Vendedor", y = "R$")
print(grafico3)

grafico4 <- ggplot(dados_limpos, aes(y = total_liquido)) +
  geom_boxplot(fill = "lightblue", color = "darkblue") +
  theme_minimal() + labs(title = "Outliers no Total Líquido", y = "Total Líquido")
print(grafico4)

# Matriz de Correlação (Gráfico 5) no ggplot
dados_numericos <- dados_limpos %>% select(qnt, vr_unit, total_liquido, tot_desc)
matriz_cor <- cor(dados_numericos, use = "complete.obs")
dados_cor_long <- as.data.frame(as.table(matriz_cor))

grafico5 <- ggplot(dados_cor_long, aes(x = Var1, y = Var2, fill = Freq)) +
  geom_tile(color = "white") +
  geom_text(aes(label = round(Freq, 2)), color = "black", size = 4) +
  scale_fill_gradient2(low = "blue", high = "red", mid = "white", midpoint = 0, 
                       limit = c(-1,1), name = "Correlação") +
  theme_minimal() +
  labs(title = "Matriz de Correlação", x = "", y = "") +
  theme(axis.text.x = element_text(angle = 45, hjust = 1))
print(grafico5)

# 9. SALVAR AS IMAGENS 

cat("\nSalvando as 5 imagens na pasta etl...\n")

ggsave(file.path(pasta_saida, "grafico1_top10.png"), plot = grafico1, width = 8, height = 5)
ggsave(file.path(pasta_saida, "grafico2_precos.png"), plot = grafico2, width = 8, height = 5)
ggsave(file.path(pasta_saida, "grafico3_vendedores.png"), plot = grafico3, width = 8, height = 5)
ggsave(file.path(pasta_saida, "grafico4_boxplot.png"), plot = grafico4, width = 8, height = 5)
ggsave(file.path(pasta_saida, "grafico5_correlacao.png"), plot = grafico5, width = 8, height = 6)

cat("\nSucesso! EDA concluída e os 5 gráficos foram salvos na pasta 'etl'.\n")