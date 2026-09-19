# Automação e Escalabilidade de Pipelines de Big Data e Análise de Dados
**Subtítulo:** Previsão de Demanda e Gestão Inteligente de Estoque de Produtos Veterinários  
**Empresa Beneficiada:** F.C.A. Serviços Pecuários e Comércio de Produtos Veterinários
**Módulo:** Data Science — DevOps / AED / Big Data / Estatística

---

## 1. Visão Geral (DevOps)
Este repositório contém a infraestrutura como código (IaC), os scripts de automação via **Ansible** e a organização do pipeline de dados da F.C.A. Serviços Pecuários, garantindo **reprodutibilidade**, **automação** e **monitoramento**

---

## 2. Arquitetura de Infraestrutura (Ambiente Linux & VMs)
O ecossistema roda sobre **Linux** e é segmentado em 4 Máquinas Virtuais (VMs):
* **VM 1:** Simulador de dados transacionais
* **VM 2:** Processamento e limpeza em R
* **VM 3:** Camada de Big Data
* **VM 4:** Monitoramento com Docker e Kubernetes

---

## 3. Estrutura do Repositório
* `ansible/`: Inventário e playbooks de provisionamento automatizado das VMs.
* `simulator/`: Scripts do gerador de dados
* `r-pipeline/`: Scripts de tratamento de dados em R
* `big-data/`: Configurações da camada de Big Data
* `monitoring/`: Arquivos de configuração de Docker e monitoramento
* `docs/`: Documentação de arquitetura

---

## 4. Procedimento de Reprodução
Para provisionar o ambiente de forma automatizada nas VMs Linux:
```bash
ansible-playbook -i ansible/inventory.ini ansible/playbooks/setup.yml





## Explicação 
ansible/: Centraliza a Infraestrutura como Código (IaC). Contém o inventário (inventory.ini) com os IPs das 4 VMs e o playbook de automação (playbooks/setup.yml).   
simulator/: Destinada a abrigar os códigos e scripts do mini gerador de dados transacionais (que criará os arquivos .csv na VM 1).   
r-pipeline/: Onde ficarão os scripts em linguagem R responsáveis pela camada de ETL (Extração, Transformação e Carga) na VM 2.   big-data/: Espaço reservado para documentar ou armazenar os componentes de processamento de massa da VM 3.   
monitoring/: Contém as subpastas do Grafana e de provisionamento de observabilidade para supervisionar o pipeline na VM 4.   docs/: Guarda a documentação técnica oficial do projeto, como o arquivo arquitetura.md.  