from .vm_allocator import allocate_vm
def schedule_tasks(tasks,vms,hosts):
 for task,vm in zip(tasks,vms*max(1,len(tasks)//max(len(vms),1))): vm.cloudlets.append(task)
 for vm in vms: allocate_vm(vm,hosts)
 return vms
