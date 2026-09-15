# Arquitetura de Infraestrutura - F.C.A. Serviços Pecuários
O ambiente de execução do pipeline de dados é estruturado sobre **Linux**, dividido em 4 Máquinas Virtuais (VMs) isoladas:
1. **VM 1 (Simulador):** Geração de dados transacionais em CSV/JSON (vendas, estoque, clima).
2. **VM 2 (Processamento em R):** Limpeza, tratamento de valores ausentes e padronização dos dados.
3. **VM 3 (Big Data):** Armazenamento e processamento distribuído de grandes volumes históricos.
4. **VM 4 (Monitoramento):** Gerenciamento da saúde do pipeline utilizando **Docker** e **Kubernetes**.
