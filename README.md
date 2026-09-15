# Automação e Escalabilidade de Pipelines de Big Data e Análise de Dados
**Subtítulo:** Previsão de Demanda e Gestão Inteligente de Estoque de Produtos Veterinários  
**Empresa Beneficiada:** F.C.A. Serviços Pecuários e Comércio de Produtos Veterinários[cite: 3]  
**Módulo:** Data Science — DevOps / AED / Big Data / Estatística[cite: 1, 3]

---

## 1. Visão Geral (DevOps)
Este repositório contém a infraestrutura como código (IaC), os scripts de automação e o pipeline de dados desenvolvido para a F.C.A. Serviços Pecuários. O foco da engenharia DevOps neste módulo é assegurar a **reprodutibilidade**, **automação** e **monitoramento** de todo o fluxo de dados do negócio[cite: 1, 3].

---

## 2. Arquitetura de Infraestrutura (Ambiente Linux & VMs)
O ecossistema é executado sobre sistemas operacionais **Linux**, segmentado em 4 Máquinas Virtuais (VMs) principais, conforme o diagrama do projeto:

1. **VM 1 - Simulador / Gerador de Dados:** Responsável por gerar os dados transacionais brutos em CSV/JSON (vendas, estoque e clima)[cite: 3].
2. **VM 2 - Processamento em R:** Responsável por consumir os dados brutos, limpar, tratar valores ausentes e estruturar a base tratada[cite: 1, 3].
3. **VM 3 - Big Data:** Ambiente distribuído para armazenamento e processamento escalável de grandes volumes históricos[cite: 1, 3].
4. **VM 4 - Monitoramento:** Instância isolada para gerenciar a saúde dos serviços utilizando **Docker** e **Kubernetes**[cite: 1, 3].

---

## 3. Estrutura do Repositório
* `ansible/`: Inventário e playbooks para provisionamento automatizado das VMs.
* `simulator/`: Scripts do gerador de dados transacionais.
* `r-pipeline/`: Scripts em R para tratamento e qualidade de dados[cite: 1, 3].
* `big-data/`: Configurações da camada de Big Data[cite: 3].
* `monitoring/`: Configurações de Docker e rotinas de alerta[cite: 3].
* `docs/`: Documentações técnicas e diagramas da arquitetura.

---

## 4. Procedimento de Reprodução do Ambiente
Para provisionar o ambiente de forma automatizada via Ansible nas VMs Linux:
```bash
ansible-playbook -i ansible/inventory.ini ansible/playbooks/setup.yml
