from typing import List, Optional

import yaml

from python_magnetgeo import Bitter
from python_magnetgeo import python_magnetgeo

from .jsonmodel import create_params_bitter, create_bcs_bitter, create_materials_bitter
from .utils import Merge

def Bitter_setup(confdata: dict, cad: Bitter, method_data: List, templates: dict, debug: bool=False):
    print("Bitter_setup: %s" % cad.name, "debug=", debug)
    if debug: print("Bitter_setup/Bitter confdata: %s" % confdata)

    part_thermic = []
    part_electric = []
    
    boundary_meca = []
    boundary_maxwell = []
    boundary_electric = []
    
    yamlfile = confdata["geom"]
    if debug: print("Bitter_setup/Bitter yamlfile: %s" % yamlfile)
    name = ""
    snames = []
    with open(yamlfile, "r") as cfgdata:
        cad = yaml.load(cfgdata, Loader = yaml.FullLoader)
        if debug: print(cad)

        name = cad.name.replace('Bitter_','')
        for i in range(len(cad.axi.turns)):
            snames.append(cad.name + "_B%d" % (i+1))
        if debug: print("sname:", snames)
    
    gdata = (name, snames, cad.axi.turns)

    for sname in snames:
        part_thermic.append(sname)
        part_electric.append(sname)

    if debug:
        print("part_thermic:", part_thermic)
        print("part_electric:", part_electric)
        
    if  method_data[2] == "Axi":
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
    mdict = Merge( Merge(main_data, params_data), bcs_data)

    powerH_data = []
    meanT_data = []
    
    if method_data[2] == "Axi":
        for sname in snames :
            powerH_data.append( {"header": "Power_{}".format(sname), "markers": sname} )
            meanT_data.append( {"header": "MeanT_{}".format(sname), "markers": sname} )
    if debug: print("meanT_data:", meanT_data)
    mpost = { 
        "meanT_H": meanT_data ,
        "power_H": powerH_data 
    }
    
        
    mmat = create_materials_bitter(gdata, confdata, templates, method_data, debug)

    return (mdict, mmat, mpost)
