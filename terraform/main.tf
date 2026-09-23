terraform {
  required_providers {
    libvirt = {
      source  = "dmacvicar/libvirt"
      version = "0.8.3"
    }
    local = {
      source  = "hashicorp/local"
      version = "~> 2.5"
    }
  }
}

provider "libvirt" {
  uri = "qemu:///system"
}

resource "libvirt_volume" "ubuntu_base" {
  name   = "ubuntu-24.04-base.qcow2"
  pool   = "default"
  source = "https://cloud-images.ubuntu.com/noble/current/noble-server-cloudimg-amd64.img"
  format = "qcow2"
}

resource "libvirt_volume" "vm_disk" {
  for_each = toset(var.vm_names)

  name           = "${each.key}.qcow2"
  pool           = "default"
  base_volume_id = libvirt_volume.ubuntu_base.id
  format         = "qcow2"
  size           = var.disk_size_gb * 1024 * 1024 * 1024 # bytes
}

resource "libvirt_cloudinit_disk" "init" {
  for_each = toset(var.vm_names)

  name = "${each.key}.cloudinit.iso"
  pool = "default"

  user_data = templatefile("${path.module}/cloud_init.cfg", {
    hostname = each.key
    ssh_key  = trimspace(file(pathexpand(var.ssh_public_key_path)))
  })
}

resource "libvirt_domain" "vm" {
  for_each = toset(var.vm_names)

  name   = each.key
  memory = var.memory_mb
  vcpu   = var.vcpu

  cloudinit = libvirt_cloudinit_disk.init[each.key].id

  network_interface {
    network_name   = var.network_name
    wait_for_lease = true
  }

  disk {
    volume_id = libvirt_volume.vm_disk[each.key].id
  }

  console {
    type        = "pty"
    target_type = "serial"
    target_port = "0"
  }
}

output "ips" {
  value = { 
    for name, vm in libvirt_domain.vm : 
    name => try(vm.network_interface[0].addresses[0], "") 
  }
}

# Gera o inventory.ini do Ansible automaticamente, sempre com os IPs certos.
resource "local_file" "ansible_inventory" {
  filename = "${path.module}/../ansible/inventory.ini"
  content = templatefile("${path.module}/inventory.tpl", {
    vms          = { 
      for name, vm in libvirt_domain.vm : 
      name => try(vm.network_interface[0].addresses[0], "") 
    }
    ansible_user = var.ansible_user
    ssh_key_path = trimsuffix(var.ssh_public_key_path, ".pub")
  })
}