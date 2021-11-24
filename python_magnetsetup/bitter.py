from typing import List, Optional

import yaml

from python_magnetgeo import Bitter
from python_magnetgeo import python_magnetgeo

from .jsonmodel import create_params, create_bcs, create_materials
from .utils import Merge

def Bitter_setup(confdata: dict, cad: Bitter, method_data: List, templates: dict, debug: bool=False):
    print("Bitter_setup: %s" % cad.name)
    part_thermic = []
    part_electric = []
    
    boundary_meca = []
    boundary_maxwell = []
    boundary_electric = []
    
    
    mdict = {}
    mmat = {}
    mpost = {}

    return (mdict, mmat, mpost)
