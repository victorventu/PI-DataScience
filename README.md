# Automação e Escalabilidade de Pipelines de Big Data e Análise de Dados

**Subtítulo:** Previsão de Demanda e Gestão Inteligente de Estoque de Produtos Veterinários
**Empresa Beneficiada:** F.C.A. Serviços Pecuários e Comércio de Produtos Veterinários
**Módulo:** Data Science — DevOps / AED / Big Data / Estatística

---

## 1. Visão Geral (DevOps)

Este repositório contém a infraestrutura como código (IaC), os scripts de automação via **OpenTofu/Terraform** e **Ansible**, e a organização do pipeline de dados da F.C.A. Serviços Pecuários, garantindo **reprodutibilidade**, **automação** e **monitoramento**.

A infraestrutura é dividida em duas camadas:

- **Provisionamento (Terraform/OpenTofu):** cria as 4 VMs no libvirt/QEMU do zero, com disco, rede e usuário já configurados via cloud-init.
- **Configuração (Ansible):** instala dependências, configura rede interna e prepara os diretórios de trabalho dentro das VMs já existentes.

> **Se você é novo no projeto:** a seção [7. Onde encontro o quê?](#7-onde-encontro-o-quê) explica, passo a passo, onde mexer dependendo da sua parte do trabalho (simulador, ETL em R, Big Data/Colab ou monitoramento).

---

## 2. Arquitetura de Infraestrutura (Ambiente Linux & VMs)

O ecossistema roda sobre **Linux** (libvirt/QEMU) e é segmentado em 4 Máquinas Virtuais (VMs), provisionadas automaticamente via Terraform:

| VM | Papel | Responsável por |
|---|---|---|
| **VM 1 — `vm-simulator`** | Simulador de dados transacionais | Gerar os dados brutos (CSV) do negócio |
| **VM 2 — `vm-etl`** | Processamento e limpeza em R | Rodar os scripts de ETL sobre os dados brutos |
| **VM 3 — `vm-bigdata`** | Camada de Big Data | Ponto de apoio local; o processamento pesado roda no **Google Colab**, fora das VMs |
| **VM 4 — `vm-monitoring`** | Monitoramento com Docker e Kubernetes | Rodar Grafana/observabilidade do pipeline |

Cada VM é criada com 20GB de disco, 2 vCPUs e 2GB de RAM (ajustável em `terraform/variables.tf`).

**Formato de dados:** todo o pipeline utiliza **CSV** como formato padrão — desde a geração pelo simulador até os dados processados, inclusive na etapa que passa pelo Google Colab.

---

## 3. Pré-requisitos do Host

Antes de provisionar, a máquina host (o computador de quem vai rodar o projeto) precisa ter:

- **libvirt / QEMU-KVM** instalado e o serviço `libvirtd` ativo
- A rede `default` do libvirt ativa e em **modo NAT** (`virsh net-dumpxml default` deve mostrar `<forward mode='nat'/>`)
- **OpenTofu** (ou Terraform) instalado
- **Ansible** instalado
- Uma chave SSH pública em `~/.ssh/id_rsa.pub` (ou ajuste `ssh_public_key_path` em `terraform/variables.tf` se usar outro nome, ex: `id_ed25519.pub`)

Rode o script de checagem antes de continuar — ele valida esses pontos automaticamente e evita os problemas de rede mais comuns (rede sem NAT, ou regras de firewall sobrescritas por outro serviço como o Docker):

```bash
bash scripts/preflight.sh
```

---

## 4. Estrutura do Repositório

```
.
├── terraform/          # Provisionamento das VMs (IaC)
├── ansible/             # Configuração das VMs já criadas
├── scripts/             # Utilitários (ex: preflight.sh)
├── simulator/           # Gerador de dados transacionais (VM 1)
├── r-pipeline/           # Scripts de ETL em R (VM 2)
├── big-data/             # Notebook(s) do Google Colab e docs da camada de Big Data (VM 3)
├── monitoring/           # Configuração de Docker/Grafana (VM 4)
└── docs/                 # Documentação técnica (arquitetura.md, etc.)
```

* `terraform/`: Infraestrutura como Código (IaC) — cria as 4 VMs, discos, rede e cloud-init via OpenTofu/Terraform. Gera automaticamente o `ansible/inventory.ini` ao final do `apply`.
* `ansible/`: Playbook de provisionamento (`playbooks/setup.yml`). O `inventory.ini` é gerado automaticamente pelo Terraform — **não deve ser editado manualmente**.
* `scripts/`: Scripts utilitários, incluindo `preflight.sh` para validar os pré-requisitos do host antes do provisionamento.
* `simulator/`: Scripts do gerador de dados transacionais (VM 1).
* `r-pipeline/`: Scripts de tratamento de dados em R, camada de ETL (VM 2).
* `big-data/`: Notebooks do Google Colab e documentação da camada de Big Data (VM 3).
* `monitoring/`: Arquivos de configuração de Docker e monitoramento com Grafana (VM 4).
* `docs/`: Documentação técnica oficial do projeto, como o arquivo `arquitetura.md`.

---

## 5. Procedimento de Reprodução

```bash
# 1. Clone o repositório
git clone <url-do-repositorio>
cd <repositorio>

# 2. Valide os pré-requisitos do host
bash scripts/preflight.sh

# 3. Provisione as VMs (cria discos, rede, cloud-init e as 4 VMs)
cd terraform
tofu init
tofu apply
# Isso já gera automaticamente ansible/inventory.ini com os IPs corretos das VMs

# 4. Configure as VMs via Ansible
cd ../ansible
ansible-playbook -i inventory.ini playbooks/setup.yml --ask-become-pass
```

> **Nota 1:** logo após o `tofu apply`, as VMs podem levar de 30 a 60 segundos para finalizar o boot via cloud-init (criação de usuário, SSH, expansão de disco). Se o Ansible falhar na primeira tentativa por SSH indisponível, aguarde alguns segundos e rode o comando novamente.
>
> **Nota 2:** depois que o playbook adiciona seu usuário ao grupo `docker` na VM de monitoramento, é preciso abrir uma **nova sessão SSH** para o comando `docker` funcionar sem `sudo` — é assim que grupos do Linux funcionam, não é um erro.

Para desprovisionar todo o ambiente:

```bash
cd terraform
tofu destroy
```

---

## 6. O que o Ansible configura em cada VM

O playbook (`ansible/playbooks/setup.yml`) roda em todas as VMs e, adicionalmente, instala pacotes específicos conforme o papel de cada uma:

- **Todas as VMs:** rede/DNS, fonte do APT, `git`, `curl`, `python3-pip`, `python3-venv`, `docker.io`, diretórios padronizados (`/opt/fca/...`).
- **Apenas `vm-etl`:** instala `r-base` (R), necessário para os scripts de ETL.
- **Todas as VMs:** garante que o serviço Docker está ativo/habilitado e adiciona o usuário ao grupo `docker`.

Diretórios criados em todas as VMs:

| Caminho | Uso |
|---|---|
| `/opt/fca/simulator` | Onde o gerador de dados roda e grava saída local |
| `/opt/fca/data/raw` | Dados brutos gerados pelo simulador (CSV) |
| `/opt/fca/data/processed` | Dados já tratados pelo pipeline de ETL/Big Data (CSV) |
| `/opt/fca/logs` | Logs de execução dos serviços |

---

## 7. Onde encontro o quê?

Um guia rápido para não se perder, dependendo da parte do projeto em que você está trabalhando:

- **"Eu trabalho no gerador/simulador de dados"** → seu código vai em `simulator/`. Ele deve gravar os arquivos `.csv` em `/opt/fca/data/raw` dentro da `vm-simulator`. Não precisa mexer em Terraform/Ansible, a menos que precise de uma nova dependência do sistema — nesse caso, avise quem cuida do DevOps para adicionar no `ansible/playbooks/setup.yml`.
- **"Eu trabalho no ETL em R"** → seu código vai em `r-pipeline/`. Ele roda na `vm-etl`, que já vem com `r-base` instalado. Deve ler de `/opt/fca/data/raw` e gravar o resultado tratado em `/opt/fca/data/processed`.
- **"Eu trabalho na camada de Big Data / Google Colab"** → seus notebooks e documentação vão em `big-data/`. O processamento pesado roda no Colab (fora das VMs); a `vm-bigdata` serve como ponto de apoio local, se necessário.
- **"Eu trabalho em monitoramento/observabilidade"** → sua configuração vai em `monitoring/` (Grafana, etc.), rodando via Docker na `vm-monitoring`, que já vem com o Docker ativo e configurado.
- **"Eu quero só subir o ambiente do zero para testar"** → siga a seção [5. Procedimento de Reprodução](#5-procedimento-de-reprodução). Não precisa entender Terraform/Ansible em detalhe, só rodar os comandos na ordem.
- **"Preciso mexer na infraestrutura (VMs, rede, pacotes do sistema)"** → isso é `terraform/` (criação das VMs) e `ansible/` (configuração/pacotes). Fale com quem está com a parte de DevOps antes de alterar, para manter tudo documentado e reprodutível.

---

## 8. Explicação técnica das pastas de infraestrutura

- **`terraform/`**: Centraliza o provisionamento da infraestrutura. Define o tamanho de disco, memória e vCPUs de cada VM (`variables.tf`), o template de cloud-init (`cloud_init.cfg`) que cria o usuário e autoriza a chave SSH, e o template (`inventory.tpl`) que gera o inventário do Ansible automaticamente a partir dos IPs reais retornados pelas VMs.
- **`ansible/`**: Contém o playbook de automação (`playbooks/setup.yml`) responsável por configurar rede/DNS, fontes do APT, instalar dependências (git, curl, Docker, Python, R) e criar a estrutura de diretórios de trabalho em cada VM. O `inventory.ini` desta pasta é gerado automaticamente pelo Terraform — não deve ser versionado com IPs fixos (está no `.gitignore`).
- **`scripts/`**: Scripts auxiliares, como o `preflight.sh`, que valida o ambiente do host antes de provisionar.