from typing import List, Optional

import yaml

from python_magnetgeo import Bitter
from python_magnetgeo import python_magnetgeo

from .jsonmodel import create_params_bitter, create_bcs_bitter, create_materials_bitter
from .utils import Merge, NMerge

import os

from .file_utils import MyOpen, findfile

def Bitter_simfile(MyEnv, confdata: dict, cad: Bitter):
    print("Bitter_simfile: %s" % cad.name)

    from .file_utils import MyOpen, findfile

    yamlfile = confdata["geom"]
    with MyOpen(yamlfile, 'r', paths=[ os.getcwd(), default_pathes["geom"]]) as cfgdata:
        return cfgdata

def Bitter_setup(MyEnv, confdata: dict, cad: Bitter, method_data: List, templates: dict, debug: bool=False):
    print("Bitter_setup: %s" % cad.name, "debug=", debug)
    if debug: print("Bitter_setup/Bitter confdata: %s" % confdata)

    part_thermic = []
    part_electric = []
    index_Bitters = ""

    boundary_meca = []
    boundary_maxwell = []
    boundary_electric = []

    yamlfile = confdata["geom"]
    if debug: print("Bitter_setup/Bitter yamlfile: %s" % yamlfile)
    
    name = ""
    snames = []
    cad = yaml.load(cfgdata, Loader = yaml.FullLoader)
    NSections = len(cad.axi.turns)
    if debug: print(cad)

    name = cad.name.replace('Bitter_','')
    if method_data[2] == "Axi":
        for i in range(len(cad.axi.turns)):
            snames.append(name + "_B%d" % (i+1))
            part_electric.append(snames[-1])
            if 'th' in method_data[3]:
                part_thermic.append(snames[-1])
        index_Bitters = f"1:{NSections}"
        if debug: print("sname:", snames)
    else:
        part_electric.append(cad.name)
        if 'th' in method_data[3]:
            part_thermic.append(cad.name)

    gdata = (name, snames, cad.axi.turns)

    if debug:
        print("bitter part_thermic:", part_thermic)
        print("bitter part_electric:", part_electric)
        
    if  method_data[2] == "Axi" and ('el' in method_data[3] and  method_data[3] != 'thelec'):
        boundary_meca.append("{}_V0".format(name))
        boundary_meca.append("{}_V1".format(name))    
                
        boundary_maxwell.append("ZAxis")
        boundary_maxwell.append("Infty")
    
    # params section
    params_data = create_params_bitter(gdata, method_data, debug)

    # bcs section
    bcs_data = create_bcs_bitter(boundary_meca, 
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
    mdict = NMerge( NMerge(main_data, params_data), bcs_data, debug, "bitter_setup mdict")

    print("bitter_setup: post-processing section")
    currentH_data = []
    powerH_data = []
    meanT_data = []
    
    currentH_data.append( {"part_electric": part_electric } )
        
    if method_data[2] == "Axi":
        powerH_data.append( {f"header": f"Power_{name}", "markers": { "name": f"{name}_B%1%", "index1": index_Bitters}} )
        meanT_data.append( {f"header": f"MeanT_{name}", "markers":  { "name": f"{name}_B%1%", "index1": index_Bitters}} )
    else:
        print("bitter3D post not implemented")
        
    if debug: print("meanT_data:", meanT_data)
    
    mpost = { } 
    if 'th' in method_data[3]:
        mpost = {  
            "meanT_H": meanT_data ,
            "power_H": powerH_data ,
            "current_H": currentH_data
        }
        
    # check mpost output
    # print(f"bitter {name}: mpost={mpost}")
    mmat = create_materials_bitter(gdata, confdata, templates, method_data, debug)

    return (mdict, mmat, mpost)
