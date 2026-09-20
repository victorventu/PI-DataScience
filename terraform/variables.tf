variable "vm_names" {
  description = "Nomes lógicos das VMs, na ordem dos papéis do laboratório"
  type        = list(string)
  default     = ["vm-simulator", "vm-etl", "vm-bigdata", "vm-monitoring"]
}

variable "disk_size_gb" {
  description = "Tamanho do disco virtual de cada VM, em GB"
  type        = number
  default     = 20
}

variable "memory_mb" {
  description = "Memória RAM de cada VM, em MB"
  type        = number
  default     = 2048
}

variable "vcpu" {
  description = "Número de vCPUs de cada VM"
  type        = number
  default     = 2
}

variable "ssh_public_key_path" {
  description = "Caminho da chave pública SSH a autorizar nas VMs (ajuste se usar outra, ex: ~/.ssh/id_ed25519.pub)"
  type        = string
  default     = "~/.ssh/id_rsa.pub"
}

variable "network_name" {
  description = "Rede libvirt a usar (precisa já existir e estar em modo NAT)"
  type        = string
  default     = "default"
}

variable "ansible_user" {
  description = "Usuário SSH criado via cloud-init, usado pelo Ansible"
  type        = string
  default     = "aluno"
}