# Automação e Escalabilidade de Pipelines de Big Data e Análise de Dados
**Subtítulo:** Previsão de Demanda e Gestão Inteligente de Estoque de Produtos Veterinários  
**Empresa Beneficiada:** F.C.A. Serviços Pecuários e Comércio de Produtos Veterinários[cite: 3]  
**Módulo:** Data Science — DevOps / AED / Big Data / Estatística[cite: 3]

---

## 1. Visão Geral do Projeto (DevOps)
Este repositório contém a infraestrutura como código (IaC), scripts de automação e o pipeline de dados desenvolvido para a F.C.A. Serviços Pecuários. O objetivo de DevOps neste módulo é garantir a **reprodutibilidade**, **automação** e **monitoramento** do fluxo de dados, que vai desde a geração de dados transacionais até o armazenamento e análise escalável[cite: 3].

---

## 2. Arquitetura de Infraestrutura (Ambiente Linux)
O ambiente de execução do projeto é estruturado sobre sistemas operacionais **Linux**, dividido em Máquinas Virtuais (VMs) isoladas para cada responsabilidade do pipeline (conforme o diagrama oficial do grupo):

1. **VM 1 - Simulador / Gerador de Dados:**
   * Responsável por gerar automaticamente dados transacionais em formato CSV/JSON (vendas, estoque e clima simulados)[cite: 3].
2. **VM 2 - Processamento em R:**
   * Responsável por consumir os arquivos CSV brutos, executar rotinas de limpeza, tratamento de valores ausentes e estruturação da base tratada[cite: 3].
3. **VM 3 - Big Data:**
   * Ambiente escalável dedicado ao armazenamento e processamento distribuído de grandes volumes de dados históricos da empresa[cite: 3].
4. **VM 4 - Monitoramento:**
   * Instância dedicada ao acompanhamento da saúde dos serviços utilizando **Docker** e **Kubernetes** para gerenciar logs e falhas no pipeline.

---

## 3. Ferramentas e Tecnologias Utilizadas
* **Controle de Versão:** Git e GitHub (para colaboração e histórico de commits)[cite: 3].
* **Automação e Provisionamento:** **Ansible** (para configuração automatizada e reprodutível das VMs Linux).
* **Orquestração e Contêineres:** Docker e Kubernetes (na camada de monitoramento).
* **Linguagens:** Python (simulador) e R (pipeline de tratamento).

---

## 4. Estrutura do Repositório
O projeto está organizado nas seguintes pastas:
* `ansible/`: Contém os arquivos de inventário e playbooks de provisionamento automatizado.
* `simulator/`: Scripts do gerador de dados transacionais.
* `r-pipeline/`: Scripts em R para tratamento e qualidade de dados.
* `big-data/`: Configurações da camada de Big Data.
* `monitoring/`: Configurações de Docker e scripts de alerta.
* `docs/`: Documentações técnicas e diagramas da arquitetura.

---

## 5. Procedimento de Reprodução do Ambiente
Para reproduzir o ambiente de desenvolvimento e infraestrutura de forma automatizada via Ansible, siga os passos abaixo:

1. **Pré-requisitos na máquina de controle:**
   * Git instalado.
   * Ansible instalado (`sudo apt install ansible` ou via pip).
   * Acesso SSH configurado para as Máquinas Virtuais Linux.

2. **Clonar o Repositório:**
   ```bash
   git clone [https://github.com/SEU-USUARIO/SEU-REPOSITORIO.git](https://github.com/SEU-USUARIO/SEU-REPOSITORIO.git)
   cd SEU-REPOSITORIO
