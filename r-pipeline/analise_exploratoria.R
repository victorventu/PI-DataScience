# ==========================================
# PROJETO INTEGRADO - DATA SCIENCE
# Análise Exploratória de Dados (EDA) Completa
# ==========================================

# 1. Pacotes
library(tidyverse)
library(janitor)
library(skimr)
library(ggplot2)
library(corrplot)
library(here) # Pacote mágico para caminhos perfeitos

# 2. Caminhos (Usando a raiz do projeto, funciona em qualquer PC)
arquivo_entrada <- here("simulator", "vendas.csv")
pasta_saida     <- here("etl")

# 3. Verificação do arquivo
if (!file.exists(arquivo_entrada)) {
  stop("ERRO: Arquivo vendas.csv não encontrado na pasta simulator!")
}

# 4. Leitura
cat("Iniciando leitura dos dados brutos...\n")
dados_brutos <- read.csv2(arquivo_entrada, stringsAsFactors = FALSE, check.names = FALSE)

# 5. Limpeza e Padronização
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

# 6. Salvar dados limpos
if (!dir.exists(pasta_saida)) dir.create(pasta_saida, recursive = TRUE)
arquivo_saida <- here("etl", "vendas_tratadas.csv")
write.csv(dados_limpos, arquivo_saida, row.names = FALSE)
cat("Dados limpos salvos em:", arquivo_saida, "\n\n")

# ==========================================
# 7. GRÁFICOS (Mostra na tela)
# ==========================================

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

# ==========================================
# 8. SALVAR AS IMAGENS (O que você pediu)
# ==========================================
cat("\nSalvando as imagens na pasta etl...\n")

ggsave(here("etl", "grafico1_top10.png"), plot = grafico1, width = 8, height = 5)
ggsave(here("etl", "grafico2_precos.png"), plot = grafico2, width = 8, height = 5)
ggsave(here("etl", "grafico3_vendedores.png"), plot = grafico3, width = 8, height = 5)
ggsave(here("etl", "grafico4_boxplot.png"), plot = grafico4, width = 8, height = 5)

# 9. Salvar a Matriz de Correlação (Usando método próprio)
dados_numericos <- dados_limpos %>% select(qnt, vr_unit, total_liquido, tot_desc)
matriz_cor <- cor(dados_numericos, use = "complete.obs")

# Mostra na tela
corrplot(matriz_cor, method = "color", type = "upper", addCoef.col = "black")

# Salva o arquivo diretamente na pasta certa
png(here("etl", "grafico5_correlacao.png"), width = 800, height = 800, res = 120)
corrplot(matriz_cor, method = "color", type = "upper", addCoef.col = "black")
dev.off()

cat("\nSucesso! Todos os 5 gráficos foram salvos como imagem na pasta 'etl'.\n")