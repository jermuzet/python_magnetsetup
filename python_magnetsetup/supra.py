from typing import List, Optional

import yaml

from python_magnetgeo import Supra
from python_magnetgeo import python_magnetgeo

from .jsonmodel import create_params_supra, create_bcs_supra, create_materials_supra
from .utils import Merge

def Supra_setup(confdata: dict, cad: Supra, method_data: List, templates: dict, debug: bool=False):
    print("Supra_setup: %s" % cad.name)
    part_thermic = []
    part_electric = []
    
    boundary_meca = []
    boundary_maxwell = []
    boundary_electric = []
    
    
    mdict = {}
    mmat = {}
    mpost = {}

    return (mdict, mmat, mpost)

def Supra_simfile(confdata: dict, cad: Supra):
    print("Supra_simfile: %s" % cad.name)
    if cad.struct:
        return cad.struct
    return None