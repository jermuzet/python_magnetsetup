import enum
from dataclasses import dataclass
from typing import Optional


class JobManagerType(str, enum.Enum):
    none = "none"
    slurm = "slurm"
    oar = "oar"


@dataclass
class JobManager:
    otype: JobManagerType = JobManagerType.none
    queues: Optional[list] = None
