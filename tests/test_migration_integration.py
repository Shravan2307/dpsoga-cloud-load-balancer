import pytest
from src.simulation.entities import VM, Host
from src.resource_monitor.utilization import ResourceVector, integrated_utilization
from src.resource_monitor.machine_classifier import classify_machine
from src.scheduler.migration import migrate_one

def test_migration_end_to_end_overload(capsys):
    host1 = Host(0)
    host2 = Host(1)
    hosts = [host1, host2]
    
    # Place 4 VMs on Host 1 to overload it
    for i in range(4):
        vm = VM(id=i, mips=2200, ram=3500, storage=20000, bandwidth=2200, host_id=0)
        host1.vms.append(vm)
        
    def get_score(h):
        rv = ResourceVector(h.used_cpu()/h.cpu_mips, h.used_ram()/h.ram, h.used_storage()/h.storage, h.used_bandwidth()/h.bandwidth)
        return integrated_utilization(rv)
        
    score1_before = get_score(host1)
    score2_before = get_score(host2)
    state1_before = classify_machine(score1_before)
    
    # Verify overload condition
    assert state1_before == 'OL', f"Host 1 state {state1_before}, score {score1_before} is not >= 0.80"
    
    # Print before state
    print("Before:")
    print(f"Host 1 VMs = 4")
    print(f"Host 1 integrated utilization = {score1_before:.4f}")
    
    # Perform migration
    event = migrate_one(host1, hosts)
    
    # Print migration event
    print("\nMigration:")
    print(event)
    
    assert event is not None
    assert event.source_host == 0
    assert event.destination_host == 1
    
    score1_after = get_score(host1)
    score2_after = get_score(host2)
    state1_after = classify_machine(score1_after)
    
    # Print after state
    print("\nAfter:")
    print(f"Host 1 VMs = {len(host1.vms)}")
    print(f"Host 2 VMs = {len(host2.vms)}")
    print(f"Host 1 integrated utilization = {score1_after:.4f} ({state1_after})")
    print(f"Host 2 integrated utilization = {score2_after:.4f}")
    
    assert score1_after < score1_before
    assert score2_after > score2_before
    assert len(host1.vms) == 3
    assert len(host2.vms) == 1
    assert event.migration_time > 0

def test_migration_no_destination():
    host1 = Host(0)
    for i in range(4):
        vm = VM(id=i, mips=2200, ram=3500, storage=20000, bandwidth=2200, host_id=0)
        host1.vms.append(vm)
        
    hosts = [host1] # Only one host
    event = migrate_one(host1, hosts)
    assert event is None

def test_normal_placement_no_migration():
    host1 = Host(0)
    host2 = Host(1)
    hosts = [host1, host2]
    
    # Place 2 VMs on Host 1 and 2 VMs on Host 2 (balanced)
    for i in range(2):
        host1.vms.append(VM(id=i, mips=2200, ram=3500, storage=20000, bandwidth=2200, host_id=0))
    for i in range(2, 4):
        host2.vms.append(VM(id=i, mips=2200, ram=3500, storage=20000, bandwidth=2200, host_id=1))
        
    def get_score(h):
        rv = ResourceVector(h.used_cpu()/h.cpu_mips, h.used_ram()/h.ram, h.used_storage()/h.storage, h.used_bandwidth()/h.bandwidth)
        return integrated_utilization(rv)
        
    score1 = get_score(host1)
    state1 = classify_machine(score1)
    
    assert state1 != 'OL'
    event = None
    if state1 == 'OL':
        event = migrate_one(host1, hosts)
        
    assert event is None

