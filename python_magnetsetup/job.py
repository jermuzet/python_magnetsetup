import enum
from dataclasses import dataclass, field


class JobManagerType(str, enum.Enum):
    none = "none"
    slurm = "slurm"
    oar = "oar"


@dataclass
class JobManager:
    otype: JobManagerType = JobManagerType.none
    queues: list = field(default_factory=list)
