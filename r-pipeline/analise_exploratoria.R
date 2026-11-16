# Instale os pacotes caso não os tenha:
# install.packages(c("tidyverse", "lubridate", "zoo", "scales", "reshape2"))

library(tidyverse)
library(lubridate)
library(zoo)
library(scales)
library(reshape2)

# ==========================================
# 1. CARREGAMENTO E CONFIGURAÇÕES INICIAIS
# ==========================================

# Caminho ajustado para a pasta 'simulator' (com 't')[cite: 2]
caminho_arquivo <- "simulator/vendas.csv" 
df <- read_delim(caminho_arquivo, delim = ";", locale = locale(encoding = "UTF-8"))

# Diagnóstico inicial
glimpse(df)
summary(df)
colSums(is.na(df))

# ==========================================
# 2. LIMPEZA E PADRONIZAÇÃO DE DADOS
# ==========================================

# 2.1 Padronização de Datas
colunas_data <- c('Dt.Ped.', 'Dt.NF Lcto.', 'Dt.NF.Emis.', 'Dt.Cupom', 'Dt.Cup.Sat.', 'Venc. Cupom', 'Venc. Pedido')

df <- df %>%
  mutate(across(any_of(colunas_data), 
                ~ parse_date_time(.x, orders = c("dmy", "Ymd", "dmy HMS", "Ymd HMS", "d/m/Y", "Y-m-d")))) %>%
  mutate(across(any_of(colunas_data), as.Date))

# 2.2 Padronização de Textos (strip e upper)
colunas_texto <- c('Cliente', 'Vendedor', 'Fornecedor', 'Cidade')
df <- df %>%
  mutate(across(any_of(colunas_texto), ~ str_trim(toupper(.x))))

# 2.3 Remoção Segura de Colunas Extras (Ignora se não existirem)
colunas_remover <- c('Nº NF.', 'Nº Cup.', 'Nº Cup.Sat.', 'Dt.NF Lcto.', 
                     'Dt.NF.Emis.', 'Dt.Cupom', 'Dt.Cup.Sat.', 'Venc. Cupom', 
                     'Venc. Pedido', 'Peso Br. Un.', 'Peso Líq. Un.', 'Vr.Comiss.')

df <- df %>%
  select(-any_of(colunas_remover))

# ==========================================
# 3. ENGENHARIA DE FEATURES
# ==========================================

df <- df %>%
  mutate(
    Ano = year(`Dt.Ped.`),
    Mes = month(`Dt.Ped.`),
    # Margem Bruta %
    Margem_Pct = (`Total Líquido` - (`Qnt.` * `Preço Compra.`)) / `Total Líquido` * 100
  ) %>%
  group_by(Grupo) %>%
  mutate(
    mediana_grupo = median(`Total Líquido`, na.rm = TRUE),
    p90_grupo = quantile(`Total Líquido`, 0.90, na.rm = TRUE),
    Porte_Venda = case_when(
      `Total Líquido` <= mediana_grupo ~ "Pequena",
      `Total Líquido` <= p90_grupo ~ "Média",
      TRUE ~ "Grande"
    )
  ) %>%
  ungroup() %>%
  select(-mediana_grupo, -p90_grupo)

# Remoção de duplicados
df <- distinct(df)

# Representatividade de cada porte de venda
porte_resumo <- df %>%
  group_by(Porte_Venda) %>%
  summarise(
    Linhas = n(),
    Receita = sum(`Total Líquido`, na.rm = TRUE)
  ) %>%
  mutate(
    `% das Linhas` = round((Linhas / sum(Linhas)) * 100, 1),
    `% da Receita` = round((Receita / sum(Receita)) * 100, 1)
  )
print("--- Resumo por Porte de Venda ---")
print(porte_resumo)

# ==========================================
# 4. VISUALIZAÇÕES E EXPORTAÇÃO DE GRÁFICOS
# ==========================================

# Garante que a pasta 'simulator/graficos' existe[cite: 2]
pasta_graficos <- "simulator/graficos"
if (!dir.exists(pasta_graficos)) {
  dir.create(pasta_graficos, recursive = TRUE)
}

# 4.1 Distribuição da Quantidade (Histograma - Log)
g1 <- ggplot(df, aes(x = `Qnt.`)) +
  geom_histogram(bins = 30, fill = "steelblue", color = "white") +
  scale_x_log10(labels = label_number(big.mark = ".", decimal.mark = ",")) +
  labs(title = "Distribuição das Quantidades de Venda (escala logarítmica)", x = "Quantidade", y = "Frequência") +
  theme_minimal()
print(g1)
ggsave(file.path(pasta_graficos, "01_distribuicao_quantidade.png"), g1, width = 8, height = 5, bg = "white")

# 4.2 Volume de Linhas por Grupo (Countplot)
g2 <- ggplot(df, aes(x = fct_infreq(Grupo))) +
  geom_bar(fill = "steelblue") +
  labs(title = "Volume de Linhas de Pedido por Grupo de Produto", x = "Grupo", y = "count") +
  theme_minimal() +
  theme(axis.text.x = element_text(angle = 45, hjust = 1))
print(g2)
ggsave(file.path(pasta_graficos, "02_volume_por_grupo.png"), g2, width = 8, height = 5, bg = "white")

# 4.3 Distribuição do Total Líquido (Boxplot - Log)
g3 <- ggplot(df, aes(x = `Total Líquido`)) +
  geom_boxplot(fill = "steelblue", outlier.alpha = 0.3) +
  scale_x_log10(labels = label_dollar(prefix = "R$ ", big.mark = ".", decimal.mark = ",")) +
  labs(title = "Distribuição do Total Líquido por Linha (escala logarítmica)", x = "Total Líquido (R$)") +
  theme_minimal()
print(g3)
ggsave(file.path(pasta_graficos, "03_boxplot_total_liquido.png"), g3, width = 8, height = 4, bg = "white")

# 4.4 Total Líquido por Grupo (Boxplot ordenado - Log)
df_boxplot <- df %>% mutate(Grupo = fct_reorder(Grupo, `Total Líquido`, .fun = median, .desc = TRUE))
g4 <- ggplot(df_boxplot, aes(x = Grupo, y = `Total Líquido`)) +
  geom_boxplot(fill = "steelblue", outlier.size = 1, outlier.alpha = 0.3) +
  scale_y_log10(labels = label_dollar(prefix = "R$ ", big.mark = ".", decimal.mark = ",")) +
  labs(title = "Distribuição do Total Líquido por Grupo (escala logarítmica)", x = "Grupo", y = "Total Líquido (R$)") +
  theme_minimal() +
  theme(axis.text.x = element_text(angle = 45, hjust = 1))
print(g4)
ggsave(file.path(pasta_graficos, "04_boxplot_por_grupo.png"), g4, width = 9, height = 5, bg = "white")

# 4.5 Média x Mediana por Grupo (Barplot)
resumo_grupo <- df %>%
  group_by(Grupo) %>%
  summarise(
    Média = mean(`Total Líquido`, na.rm = TRUE),
    Mediana = median(`Total Líquido`, na.rm = TRUE)
  ) %>%
  arrange(desc(Média)) %>%
  pivot_longer(cols = c(Média, Mediana), names_to = "Medida", values_to = "Total Líquido") %>%
  mutate(Grupo = factor(Grupo, levels = unique(Grupo)))

g5 <- ggplot(resumo_grupo, aes(x = Grupo, y = `Total Líquido`, fill = Medida)) +
  geom_col(position = "dodge") +
  scale_fill_manual(values = c("Média" = "steelblue", "Mediana" = "chocolate")) +
  labs(title = "Média x Mediana do Total Líquido por Grupo", x = "Grupo", y = "Total Líquido (R$)") +
  theme_minimal() +
  theme(axis.text.x = element_text(angle = 45, hjust = 1))
print(g5)
ggsave(file.path(pasta_graficos, "05_media_vs_mediana.png"), g5, width = 9, height = 5, bg = "white")

# 4.6 Densidade do Valor (KDE Plot - Log)
g6 <- ggplot(df, aes(x = `Total Líquido`)) +
  geom_density(fill = "steelblue", alpha = 0.5) +
  scale_x_log10(labels = label_dollar(prefix = "R$ ", big.mark = ".", decimal.mark = ",")) +
  labs(title = "Densidade do Valor Total Líquido por Transação (escala logarítmica)", x = "Total Líquido (R$)", y = "Density") +
  theme_minimal()
print(g6)
ggsave(file.path(pasta_graficos, "06_densidade_valor.png"), g6, width = 8, height = 5, bg = "white")

# 4.7 Matriz de Correlação (Heatmap com log1p e StandardScaler)
colunas_corr <- c('Qnt.', 'Vr.Unit.', 'Preço Compra.', 'Tot.Desc.', 'Total Líquido')
df_corr <- df %>%
  select(all_of(colunas_corr)) %>%
  drop_na() %>%
  mutate(across(everything(), log1p)) %>%
  scale() %>%
  as.data.frame()

matriz_corr <- cor(df_corr)
melted_corr <- melt(matriz_corr)

g7 <- ggplot(melted_corr, aes(x=Var1, y=Var2, fill=value)) +
  geom_tile(color = "white") +
  geom_text(aes(label = round(value, 2)), color = "black", size = 4) +
  scale_fill_gradient2(low = "blue", high = "red", mid = "white", midpoint = 0, limit = c(-1,1)) +
  labs(title = "Matriz de Correlação (valores em log e padronizados)", x="", y="") +
  theme_minimal()
print(g7)
ggsave(file.path(pasta_graficos, "07_matriz_correlacao.png"), g7, width = 7, height = 6, bg = "white")

# 4.8 Crosstab: Condição x Grupo
tabela_cruzada <- table(df$Grupo, df$Condição)
print("--- Preferência de Condição de Pagamento por Grupo ---")
print(tabela_cruzada)

# 4.9 Evolução no Tempo (Gráfico de Linhas com Média Móvel)
receita_mes <- df %>%
  mutate(AnoMes = floor_date(`Dt.Ped.`, "month")) %>%
  group_by(AnoMes) %>%
  summarise(Receita = sum(`Total Líquido`, na.rm = TRUE) / 1e6) %>%
  arrange(AnoMes) %>%
  mutate(Media_Movel_12 = zoo::rollmean(Receita, k = 12, fill = NA, align = "right"))

g9 <- ggplot(receita_mes, aes(x = AnoMes)) +
  geom_line(aes(y = Receita, color = "Receita do mês"), alpha = 0.7) +
  geom_line(aes(y = Media_Movel_12, color = "Média móvel de 12 meses"), linewidth = 1.2) +
  scale_color_manual(values = c("Receita do mês" = "steelblue", "Média móvel de 12 meses" = "chocolate")) +
  labs(title = "Evolução Mensal da Receita (R$ milhões)", x = "Mês", y = "Receita (R$ milhões)", color = "") +
  theme_minimal() +
  theme(legend.position = "bottom")
print(g9)
ggsave(file.path(pasta_graficos, "08_evolucao_receita.png"), g9, width = 10, height = 5, bg = "white")

# 4.10 Sazonalidade por Grupo (Heatmap)
pivo <- df %>%
  filter(Ano <= 2025) %>%
  group_by(Grupo, Mes) %>%
  summarise(Receita = sum(`Total Líquido`, na.rm = TRUE), .groups = 'drop') %>%
  pivot_wider(names_from = Mes, values_from = Receita, values_fill = 0)

pivo_matriz <- as.matrix(pivo[,-1])
indice_sazonal <- (pivo_matriz / rowMeans(pivo_matriz)) * 100
indice_sazonal_df <- as.data.frame(indice_sazonal) %>%
  mutate(Grupo = pivo$Grupo) %>%
  pivot_longer(cols = -Grupo, names_to = "Mes", values_to = "Indice") %>%
  mutate(Mes = factor(Mes, levels = 1:12, labels = c('Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez')))

g10 <- ggplot(indice_sazonal_df, aes(x = Mes, y = Grupo, fill = Indice)) +
  geom_tile(color = "white") +
  geom_text(aes(label = round(Indice, 0)), color = "black", size = 3) +
  scale_fill_gradient2(low = "royalblue", high = "firebrick", mid = "white", midpoint = 100) +
  labs(title = "Índice de Sazonalidade por Grupo (100 = mês médio)", x = "", y = "", fill = "") +
  theme_minimal()
print(g10)
ggsave(file.path(pasta_graficos, "09_sazonalidade_grupo.png"), g10, width = 10, height = 6, bg = "white")

# 4.11 Receita Total por Produto (Bar Chart Horizontal)
receita_produto <- df %>%
  group_by(Produto) %>%
  summarise(Receita = sum(`Total Líquido`, na.rm = TRUE) / 1e6) %>%
  arrange(desc(Receita)) %>%
  slice(1:15) %>% 
  arrange(Receita) %>%
  mutate(Produto = factor(Produto, levels = Produto))

g11 <- ggplot(receita_produto, aes(x = Receita, y = Produto)) +
  geom_col(fill = "steelblue") +
  labs(title = "Receita Total por Produto (R$ milhões, Top 15)", x = "Receita (R$ milhões)", y = "") +
  theme_minimal()
print(g11)
ggsave(file.path(pasta_graficos, "10_receita_por_produto.png"), g11, width = 9, height = 6, bg = "white")

# ==========================================
# 5. EXPORTAÇÃO DA BASE LIMPA
# ==========================================

# Salva o CSV tratado diretamente dentro da pasta 'simulator'[cite: 2]
caminho_saida_csv <- "simulator/vendas_limpa.csv"
write_delim(df, caminho_saida_csv, delim = ";", na = "")

cat(sprintf("\nBase limpa salva com sucesso em: %s\n", caminho_saida_csv))
cat(sprintf("Gráficos salvos com sucesso na pasta: %s\n", pasta_graficos))
cat(sprintf("Linhas: %d | Colunas: %d\n", nrow(df), ncol(df)))