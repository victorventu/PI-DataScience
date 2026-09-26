%{ for name, ip in vms ~}
[${replace(name, "vm-", "")}]
${name} ansible_host=${ip}

%{ endfor ~}
[all:vars]
ansible_user=${ansible_user}
ansible_python_interpreter=/usr/bin/python3
ansible_ssh_private_key_file=${ssh_key_path}