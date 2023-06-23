import os
import json
import enum
from dataclasses import dataclass

from .job import JobManager, JobManagerType


class NodeType(str, enum.Enum):
    compute = "compute"
    visu = "visu"


@dataclass
class NodeSpec:
    name: str
    dns: str
    otype: NodeType = NodeType.compute
    smp: bool = True
    manager: JobManager = JobManager(JobManagerType.none)
    cores: int = 2
    multithreading: bool = True
    mgkeydir: str = r"/opt/MeshGems"


def load_machines(debug: bool = False):
    """
    load machines definition as a dict
    """
    if debug:
        print("load_machines")

    default_path = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(default_path, "machines.json"), "r") as cfg:
        if debug:
            print(f"load_machines from: {cfg.name}")
        data = json.load(cfg)
        if debug:
            print(f"data={data}")

    machines = {}
    for item, value in data.items():
        if debug:
            print(f"server: {item} type={value['type']}")
        server = NodeSpec(
            name=item,
            otype=NodeType[value["type"]],
            smp=value["smp"],
            dns=value["dns"],
            cores=value["cores"],
            multithreading=value["multithreading"],
            manager=JobManager(
                otype=JobManagerType[value["jobmanager"]["type"]],
                queues=value["jobmanager"]["queues"],
            ),
            mgkeydir=value["mgkeydir"],
        )
        machines[item] = server

    return machines


def loadmachines(server: str):
    """
    Load app server config (aka machines.json)
    """

    server_defs = load_machines()
    if server in server_defs:
        return server_defs[server]
    else:
        raise ValueError(f"loadmachine: {server} no such server defined")
    pass
