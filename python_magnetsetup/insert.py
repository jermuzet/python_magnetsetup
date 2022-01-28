import os
from typing import List, Optional

import yaml

from python_magnetgeo import Insert
from python_magnetgeo import python_magnetgeo

from .jsonmodel import create_params_insert, create_bcs_insert, create_materials_insert
from .utils import Merge

import os

def Insert_setup(MyEnv, confdata: dict, cad: Insert, method_data: List, templates: dict, debug: bool=False):
    print("Insert_setup: %s" % cad.name)
    part_thermic = []
    part_electric = []
    index_electric = []
    index_Helices = []
    index_Insulators = []
    
    boundary_meca = []
    boundary_maxwell = []
    boundary_electric = []

    from .file_utils import MyOpen, findfile
    default_pathes={
        "geom" : MyEnv.yaml_repo,
        "cad" : MyEnv.cad_repo,
        "mesh" : MyEnv.mesh_repo
    }
    gdata = python_magnetgeo.get_main_characteristics(cad)
    (NHelices, NRings, NChannels, Nsections, R1, R2, Z1, Z2, Zmin, Zmax, Dh, Sh) = gdata

    print("Insert: %s" % cad.name, "NHelices=%d NRings=%d NChannels=%d" % (NHelices, NRings, NChannels))

    for i in range(NHelices):
        part_electric.append("H{}".format(i+1))
        if method_data[2] == "Axi":
            for j in range(Nsections[i]+2):
                part_thermic.append("H{}_Cu{}".format(i+1,j))
            for j in range(Nsections[i]):
                index_electric.append( [str(i+1),str(j+1)] )
                index_Helices.append(["0:{}".format(Nsections[i]+2)])
                
        else:
            with MyOpen(cad.Helices[i]+".yaml", "r", paths=[ os.getcwd(), default_pathes["geom"]]) as f:
                hhelix = yaml.load(f, Loader = yaml.FullLoader)
                (insulator_name, insulator_number) = hhelix.insulators()
                index_Insulators.append((insulator_name, insulator_number))

    for i in range(NRings):
        part_thermic.append("R{}".format(i+1))
        part_electric.append("R{}".format(i+1))

    # Add currentLeads
    if  method_data[2] == "3D":
        if cad.CurrentLeads:
            part_thermic.append("iL1")
            part_thermic.append("oL2")
            part_electric.append("iL1")
            part_electric.append("oL2")
            boundary_electric.append(["Inner1_LV0", "iL1", "0"])
            boundary_electric.append(["OuterL2_LV0", "oL2", "V0:V0"])
                
            boundary_meca.append("Inner1_LV0")
            boundary_meca.append("OuterL2_LV0")

            boundary_maxwell.append("InfV00")
            boundary_maxwell.append("InfV01")
        else:
            boundary_electric.append(["H1_V0", "H1", "0"])
            boundary_electric.append(["H%d_V0" % NHelices, "H%d" % NHelices, "V0:V0"])
        
        boundary_maxwell.append("InfV1")
        boundary_maxwell.append("InfR1")

    else:    
        boundary_meca.append("H1_HP")
        boundary_meca.append("H_HP")    
                
        boundary_maxwell.append("ZAxis")
        boundary_maxwell.append("Infty")

            
    for i in range(1,NRings+1):
        if i % 2 == 1 :
            boundary_meca.append("R{}_BP".format(i))
        else :
            boundary_meca.append("R{}_HP".format(i))

    if debug:
        print("part_electric:", part_electric)
        print("part_thermic:", part_thermic)

    # params section
    params_data = create_params_insert(gdata, method_data, debug)

    # bcs section
    bcs_data = create_bcs_insert(boundary_meca, 
                          boundary_maxwell,
                          boundary_electric,
                          gdata, confdata, templates, method_data, debug) # merge all bcs dict

    # build dict from geom for templates
    # TODO fix initfile name (see create_cfg for the name of output / see directory entry)
    # eg: $home/feel[ppdb]/$directory/cfpdes-heat.save

    main_data = {
        "part_thermic": part_thermic,
        "part_electric": part_electric,
        "index_electric": index_electric,
        "index_V0": boundary_electric,
        "temperature_initfile": "tini.h5",
        "V_initfile": "Vini.h5"
    }
    mdict = Merge( Merge(main_data, params_data), bcs_data)

    currentH_data = []
    powerH_data = []
    meanT_data = []
    if method_data[2] == "Axi":
        for i in range(NHelices) :
            currentH_data.append( {"header": "Current_H{}".format(i+1), "markers": { "name:": "H{}_Cu%1%".format(i+1), "index1": index_Helices[i]} } )
            powerH_data.append( {"header": "Power_H{}".format(i+1), "markers": { "name:": "H{}_Cu%1%".format(i+1), "index1": index_Helices[i]} } )
            meanT_data.append( {"header": "MeanT_H{}".format(i+1), "markers": { "name": "H{}_Cu%1%".format(i+1), "index1": index_Helices[i]} } )
    else:
        for i in range(NHelices) :
            powerH_data.append( {"header": "Power_H{}".format(i+1), "markers": { "name": "H{}_Cu".format(i+1)} } )
            meanT_data.append( {"header": "MeanT_H{}".format(i+1), "markers": { "name": "H{}_Cu".format(i+1)} } )

        if cad.CurrentLeads:
            currentH_data.append( {"header": "Current_iL1", "markers": { "name:": "iL1_V0" } } )
            currentH_data.append( {"header": "Current_oL2", "markers": { "name:": "oL2_V0" } } )
            powerH_data.append( {"header": "Power_iL1", "markers": { "name": "iL1"} } )
            powerH_data.append( {"header": "Power_oL2", "markers": { "name": "oL2"} } )
            meanT_data.append( {"header": "MeanT_iL1", "markers": { "name": "iL1" } } )
            meanT_data.append( {"header": "MeanT_oL2", "markers": { "name": "oL2" } } )
        else:
            currentH_data.append( {"header": "Current_H1", "markers": { "name:": "H1_V0" } } )
            currentH_data.append( {"header": "Current_H{}".format(NHelices), "markers": { "name:": "H{}_V0".format(NHelices) } } )
            

    for i in range(NRings) :
        powerH_data.append( {"header": "Power_R{}".format(i+1), "markers": { "name": "R{}".format(i+1)} } )
        meanT_data.append( {"header": "MeanT_R{}".format(i+1), "markers": { "name": "R{}".format(i+1)} } )

    # print("meanT_data:", meanT_data)
    mpost = { 
        "flux": {'index_h': "0:%s" % str(NChannels)},
        "meanT_H": meanT_data ,
        "power_H": powerH_data ,
        "current_H": currentH_data
    }
    mmat = create_materials_insert(gdata, index_Insulators, confdata, templates, method_data, debug)

    return (mdict, mmat, mpost)
