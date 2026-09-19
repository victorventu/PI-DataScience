terraform {
  required_providers {
    libvirt = {
      source  = "dmacvicar/libvirt"
      version = "0.8.3"
    }
  }
}

provider "libvirt" {
  uri = "qemu:///system"
}

locals {
  vm_count = 4 # 4 nós: Simulador, ETL, Big Data, Monitoramento
}

resource "libvirt_volume" "ubuntu_base" {
  name   = "ubuntu-24.04-base.qcow2"
  pool   = "default"
  source = "https://cloud-images.ubuntu.com/noble/current/noble-server-cloudimg-amd64.img"
  format = "qcow2"
}

resource "libvirt_volume" "vm_disk" {
  count = local.vm_count

  name           = "devops-${count.index + 1}.qcow2"
  pool           = "default"
  base_volume_id = libvirt_volume.ubuntu_base.id
  format         = "qcow2"
}

resource "libvirt_cloudinit_disk" "init" {
  count = local.vm_count

  name = "devops-${count.index + 1}.cloudinit.iso"
  pool = "default"

  user_data = templatefile("${path.module}/cloud_init.cfg", {
    hostname = "devops-${count.index + 1}"
    ssh_key  = trimspace(file(pathexpand("~/.ssh/id_rsa.pub")))
  })
}

resource "libvirt_domain" "vm" {
  count = local.vm_count

  name   = "devops-${count.index + 1}"
  memory = 1024
  vcpu   = 1

  cloudinit = libvirt_cloudinit_disk.init[count.index].id

  network_interface {
    network_name   = "default"
    wait_for_lease = true
  }

  disk {
    volume_id = libvirt_volume.vm_disk[count.index].id
  }

  console {
    type        = "pty"
    target_type = "serial"
    target_port = "0"
  }
}

output "ips" {
  value = {
    for vm in libvirt_domain.vm : vm.name => vm.network_interface[0].addresses[0]
  }
}