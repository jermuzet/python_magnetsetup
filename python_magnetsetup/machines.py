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
    otype: Enum(JobManagerType),
    queues: optional[list] = None
    
@dataclass
class machine():
    """
    machine definition
    """
    name: str,
    otype: Enum(MachineType),
    dns: str,
    smp: bool = True,
    jobmanager:,
    cores: int = 2,
    multithreading: bool = True


def load_machines():
    """
    load machines definition
    """
    
    default_path = os.path.dirname(os.path.abspath(__file__))
    with os.path.join(default_path, 'machines.json'), 'r') as cfg:
        data = json.load(cfg)

    machines = []
    for item in data:
        server = machine(
            name=item
            otype=item['type'],
            smp=item['smp'],
            dns=item['dns'],
            cores=item['cores'],
            multithreading=item['multithreading'],
            jobmanager=(otype=item['jobmanager']['type'], queues=item['jobmanager']['queues'])
        )
        machines.append(server)
                
    return machines

def dump_machines(data: list[machine]):
    with open('machines.json', 'w') as outfile:
        json.dump(data, outfile)
    pass

def mod_machine():
    pass

def add_machine():
    pass
