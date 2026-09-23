## 🚀 Automação e Pipeline de Dados (F.C.A. Serviços Pecuários)

O ambiente do laboratório de dados é totalmente provisionado e gerido via **Ansible**, garantindo reprodutibilidade e automação nas 4 VMs do projeto (`simulator`, `etl`, `bigdata`, `monitoring`).

### ⚙️ Arquitetura do Simulador e Agendamento (Cron)
A `vm-simulator` executa de forma autónoma um script em Python (`gerador.py`) que simula dados transacionais do agronegócio (registos de animais, vacinas e stocks) e os guarda na camada *raw* do data lake local.

* **Diretório do Código:** `/opt/fca/simulator/`
* **Diretório de Saída (Dados Brutos):** `/opt/fca/data/raw/dados_foco.csv`
* **Periodicidade (Automática):** Execução a cada hora via **Cron** do sistema (`0 * * * *`).

### 🕹️ Execução Manual
Caso precise de gerar novos dados imediatamente (sem esperar pelo ciclo automático do agendamento), aceda à `vm-simulator` via SSH e execute o script manualmente:

\`\`\`bash
sudo python3 /opt/fca/simulator/gerador.py --output /opt/fca/data/raw
\`\`\`

Para confirmar que o ficheiro `.csv` foi atualizado com sucesso, verifique a hora da última modificação:

\`\`\`bash
ls -lh /opt/fca/data/raw/dados_foco.csv
\`\`\`

### 📦 Como Executar o Provisionamento (Ansible)
Para subir ou atualizar toda a infraestrutura e configurar os agendamentos nas VMs do laboratório, execute o seguinte playbook a partir da máquina de controlo:

\`\`\`bash
cd ansible/
ansible-playbook -i inventory.ini playbooks/setup.yml --ask-become-pass
\`\`\`