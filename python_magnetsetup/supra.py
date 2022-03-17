from typing import List, Optional

import yaml

from python_magnetgeo import Supra
from python_magnetgeo import python_magnetgeo

from .jsonmodel import create_params_supra, create_bcs_supra, create_materials_supra
from .utils import Merge

from .file_utils import MyOpen, findfile

def Supra_simfile(MyEnv, confdata: dict, cad: Supra):
    print("Supra_simfile: %s" % cad.name)

    from .file_utils import MyOpen, findfile

    files = []

    yamlfile = confdata["geom"]
    with MyOpen(yamlfile, 'r', paths=[ os.getcwd(), default_pathes["geom"]]) as f:
        files.append(f.name)

    structfile = cad.struct # + '.json'
    with MyOpen(structfile, 'r', paths=[ os.getcwd(), default_pathes["geom"]]) as f:
        files.append(f.name)

    return files

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

    name = cad.name.replace('Supra_','')
    # TODO eventually get details
    part_electric.append(name)
        
    gdata = (name, snames, cad.struct)

    if debug:
        print("supra part_thermic:", part_thermic)
        print("supra part_electric:", part_electric)
        
    if  method_data[2] == "Axi" and ('el' in method_data[3] and  method_data[3] != 'thelec'):
        boundary_meca.append("{}_V0".format(name))
        boundary_meca.append("{}_V1".format(name))    
                
        boundary_maxwell.append("ZAxis")
        boundary_maxwell.append("Infty")
    
    # params section
    params_data = create_params_supra(gdata, method_data, debug)

    # bcs section
    bcs_data = create_bcs_supra(boundary_meca, 
                          boundary_maxwell,
                          boundary_electric,
                          gdata, confdata, templates, method_data, debug) # merge all bcs dict

    # build dict from geom for templates
    # TODO fix initfile name (see create_cfg for the name of output / see directory entry)
    # eg: $home/feel[ppdb]/$directory/cfpdes-heat.save

    main_data = {
        "part_thermic": part_thermic,
        "part_electric": part_electric,
        "index_V0": boundary_electric,
        "temperature_initfile": "tini.h5",
        "V_initfile": "Vini.h5"
    }
    mdict = NMerge( NMerge(main_data, params_data), bcs_data, debug, "supra_setup mdict")

    print("supra_setup: post-processing section")
    currentH_data = []
    meanT_data = []

    mpost = {}
    return (mdict, mmat, mpost)

