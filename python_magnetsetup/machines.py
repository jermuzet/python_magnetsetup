from typing import List, Optional

import sys
import os
import json

import enum

from dataclasses import dataclass

class JobManagerType(str, enum.Enum):
    none = "none"
    slurm = "slurm"
    oar = "oar"

class MachineType(str, enum.Enum):
    compute = "compute"
    visu = "visu"
    
@dataclass
class jobmanager():
    """
    jobmanager definition
    """
    otype: JobManagerType = JobManagerType.none
    queues: Optional[list] = None
    
@dataclass
class machine():
    """
    machine definition
    """
    name: str
    dns: str
    otype: MachineType = MachineType.compute
    smp: bool = True
    manager: jobmanager = jobmanager(JobManagerType.none)
    cores: int = 2
    multithreading: bool = True
    mgkeydir: str = r"/opt/MeshGems"


def load_machines(debug: bool = False):
    """
    load machines definition as a dict
    """
    if debug: print("load_machines")

    default_path = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(default_path, 'machines.json'), 'r') as cfg:
        if debug: print(f"load_machines from: {cfg.name}")
        data = json.load(cfg)
        if debug: print(f"data={data}")

    machines = {}
    for item in data:
        if debug: print(f"server: {item} type={data[item]['type']}")
        server = machine(
            name=item,
            otype=MachineType[data[item]['type']],
            smp=data[item]['smp'],
            dns=data[item]['dns'],
            cores=data[item]['cores'],
            multithreading=data[item]['multithreading'],
            manager=jobmanager(otype=JobManagerType[data[item]['jobmanager']['type']], queues=data[item]['jobmanager']['queues']),
            mgkeydir=data[item]['mgkeydir']
        )
        machines[item]=server
                
    return machines

def dump_machines(data: List[machine]):
    with open('machines.json', 'w') as outfile:
        json.dump(data, outfile)
    pass

def mod_machine():
    pass

def add_machine():
    pass


