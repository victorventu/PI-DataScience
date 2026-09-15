# Automação e Escalabilidade de Pipelines de Big Data e Análise de Dados
**Subtítulo:** Previsão de Demanda e Gestão Inteligente de Estoque de Produtos Veterinários  
**Empresa Beneficiada:** F.C.A. Serviços Pecuários e Comércio de Produtos Veterinários[cite: 3]  
**Módulo:** Data Science — DevOps / AED / Big Data / Estatística[cite: 1, 3]

---

## 1. Visão Geral (DevOps)
Este repositório contém a infraestrutura como código (IaC), os scripts de automação via **Ansible** e a organização do pipeline de dados da F.C.A. Serviços Pecuários, garantindo **reprodutibilidade**, **automação** e **monitoramento**[cite: 1, 3].

---

## 2. Arquitetura de Infraestrutura (Ambiente Linux & VMs)
O ecossistema roda sobre **Linux** e é segmentado em 4 Máquinas Virtuais (VMs):
* **VM 1:** Simulador de dados transacionais[cite: 3].
* **VM 2:** Processamento e limpeza em R[cite: 1, 3].
* **VM 3:** Camada de Big Data[cite: 3].
* **VM 4:** Monitoramento com Docker e Kubernetes[cite: 3].

---

## 3. Estrutura do Repositório
* `ansible/`: Inventário e playbooks de provisionamento automatizado das VMs.
* `simulator/`: Scripts do gerador de dados[cite: 3].
* `r-pipeline/`: Scripts de tratamento de dados em R[cite: 1, 3].
* `big-data/`: Configurações da camada de Big Data[cite: 3].
* `monitoring/`: Arquivos de configuração de Docker e monitoramento[cite: 3].
* `docs/`: Documentação de arquitetura[cite: 3].

---

## 4. Procedimento de Reprodução
Para provisionar o ambiente de forma automatizada nas VMs Linux:
```bash
ansible-playbook -i ansible/inventory.ini ansible/playbooks/setup.yml
