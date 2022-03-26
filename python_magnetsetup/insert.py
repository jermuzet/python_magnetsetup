from importlib.machinery import SOURCE_SUFFIXES
import os
from typing import List, Optional

import yaml

from python_magnetgeo import Insert
from python_magnetgeo import python_magnetgeo

from .jsonmodel import create_params_insert, create_bcs_insert, create_materials_insert
from .utils import Merge, NMerge
from .file_utils import MyOpen, findfile, search_paths

import os

def Insert_simfile(MyEnv, confdata: dict, cad: Insert, addAir: bool = False):
    print("Insert_simfile: %s" % cad.name)

    files = []

    # TODO: get xao and brep if they exist, otherwise go on
    # TODO: add suffix _Air if needed ??
    try:
        xaofile = cad.name + ".xao"
        if addAir:
            xaofile = cad.name + "_withAir.xao"
        f = findfile(xaofile, paths=search_paths(MyEnv, "cad"))
        files.append(f)

        brepfile = cad.name + ".brep"
        if addAir:
            brepfile = cad.name + "_withAir.brep"
        f = findfile(brepfile, paths=search_paths(MyEnv, "cad"))
        files.append(f)
    except:
        for helix in cad.Helices:
            with MyOpen(helix+".yaml", "r", paths=search_paths(MyEnv, "geom")) as f:
                hhelix = yaml.load(f, Loader = yaml.FullLoader)
                files.append(f.name)

            # TODO: get xao and brep if they exist otherwise _salome.data
            try:
                xaofile = hhelix.name + ".xao"
                f = findfile(xaofile, paths=search_paths(MyEnv, 'cad'))
                files.append(f)
                
                brepfile = hhelix.name + ".brep"
                f = findfile(brepfile, paths=search_paths(MyEnv, "cad"))
                files.append(f)

            except:
                if hhelix.m3d.with_shapes:
                    with MyOpen(hhelix.name + str("_cut_with_shapes_salome.dat"), "r", paths=search_paths(MyEnv, "geom")) as fcut:
                        files.append(fcut.name)
                    with MyOpen(hhelix.shape.profile, "r", paths=search_paths(MyEnv, "geom")) as fshape:
                        files.append(fshape.name)
                else:
                    with MyOpen(hhelix.name + str("_cut_salome.dat"), "r", paths=search_paths(MyEnv, "geom")) as fcut:
                        files.append(fcut.name)

            for ring in cad.Rings:
                try:
                    xaofile = ring.name + ".xao"
                    f = findfile(xaofile, paths=search_paths(MyEnv, "cad"))
                    files.append(f)
                
                    brepfile = ring.name + ".brep"
                    f = findfile(brepfile, paths=search_paths(MyEnv, "cad"))
                    files.append(f)

                except:
                    with MyOpen(ring+".yaml", "r", paths=search_paths(MyEnv, "geom")) as f:
                        files.append(f.name)

        if cad.CurrentLeads:
            for lead in cad.CurrentLeads:
                try:
                    xaofile = lead.name + ".xao"
                    f = findfile(xaofile, paths=search_paths(MyEnv, "cad"))
                    files.append(f)

                    brepfile = lead.name + ".brep"
                    f = findfile(brepfile, paths=search_paths(MyEnv, "cad"))
                    files.append(f)

                except:
                    with MyOpen(lead+".yaml", "r", paths=search_paths(MyEnv, "geom")) as f:
                        files.append(f.name)

    return files

def Insert_setup(MyEnv, confdata: dict, cad: Insert, method_data: List, templates: dict, debug: bool=False):
    print("Insert_setup: %s" % cad.name)
    part_thermic = []
    part_electric = []
    index_Helices = []
    index_Helices_e = []
    index_Insulators = []
    
    boundary_meca = []
    boundary_maxwell = []
    boundary_electric = []

    gdata = python_magnetgeo.get_main_characteristics(cad, MyEnv)
    (NHelices, NRings, NChannels, Nsections, R1, R2, Z1, Z2, Zmin, Zmax, Dh, Sh) = gdata

    print("Insert: %s" % cad.name, "NHelices=%d NRings=%d NChannels=%d" % (NHelices, NRings, NChannels))

    pitch_h = []
    turns_h = []

    for i in range(NHelices):
        with MyOpen(cad.Helices[i]+".yaml", "r", paths=search_paths(MyEnv, "geom")) as f:
            hhelix = yaml.load(f, Loader = yaml.FullLoader)
            pitch_h.append(hhelix.axi.pitch)
            turns_h.append(hhelix.axi.turns)
        
        if method_data[2] == "Axi":
            for j in range(1, Nsections[i]+1):
                part_electric.append("H{}_Cu{}".format(i+1,j))
            if 'th' in method_data[3]:
                for j in range(Nsections[i]+2):
                    part_thermic.append("H{}_Cu{}".format(i+1,j))
            for j in range(Nsections[i]):
                index_Helices.append(["0:{}".format(Nsections[i]+2)])
                index_Helices_e.append(["1:{}".format(Nsections[i]+1)])
                
        else:
            part_electric.append("H{}".format(i+1))
            if 'th' in method_data[3]:
                part_thermic.append("H{}".format(i+1))

            (insulator_name, insulator_number) = hhelix.insulators()
            index_Insulators.append((insulator_name, insulator_number))
            if 'th' in method_data[3]:
                part_thermic.append(insulator_name)

    for i in range(NRings):
        if 'th' in method_data[3]:
            part_thermic.append("R{}".format(i+1))
        if method_data[2] == "3D":
            part_electric.append("R{}".format(i+1))

    # Add currentLeads
    if  method_data[2] == "3D":
        if cad.CurrentLeads:
            if 'th' in method_data[3]:
                part_thermic.append("iL1")
                part_thermic.append("oL2")
            part_electric.append("iL1")
            part_electric.append("oL2")
            boundary_electric.append(["Inner1_LV0", "iL1", "0"])
            boundary_electric.append(["OuterL2_LV0", "oL2", "V0:V0"])
                
            if 'el' in method_data[3] and  method_data[3] != 'thelec':
                boundary_meca.append("Inner1_LV0")
                boundary_meca.append("OuterL2_LV0")

            if 'mag' in method_data[3]:
                boundary_maxwell.append("InfV00")
                boundary_maxwell.append("InfV01")
        else:
            boundary_electric.append(["H1_V0", "H1", "0"])
            boundary_electric.append(["H%d_V0" % NHelices, "H%d" % NHelices, "V0:V0"])
        
        if 'mag' in method_data[3]:
            boundary_maxwell.append("InfV1")
            boundary_maxwell.append("InfR1")

    else:    
        boundary_meca.append("H1_HP")
        boundary_meca.append("H_HP")    
                
        if 'mag' in method_data[3]:
            boundary_maxwell.append("ZAxis")
            boundary_maxwell.append("Infty")

    if 'el' in method_data[3] and  method_data[3] != 'thelec':
        for i in range(1,NRings+1):
            if i % 2 == 1 :
                boundary_meca.append("R{}_BP".format(i))
            else :
                boundary_meca.append("R{}_HP".format(i))

    if debug:
        print("insert part_electric:", part_electric)
        print("insert part_thermic:", part_thermic)

    # params section
    params_data = create_params_insert(gdata + (turns_h,), method_data, debug)

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
        "index_V0": boundary_electric,
        "temperature_initfile": "tini.h5",
        "V_initfile": "Vini.h5"
    }
    mdict = NMerge( NMerge(main_data, params_data), bcs_data, debug, "insert_setup mdict")

    print("insert_setup: post-processing section")
    currentH_data = []
    powerH_data = []
    power_data = []
    meanT_data = []

    currentH_data.append( {"part_electric": part_electric } )
    power_data.append( {"part_electric": part_electric } )
        
    # if method_data[3] != 'mag' and method_data[3] != 'mag_hcurl':
    if method_data[2] == "Axi":
        for i in range(NHelices) :
            meanT_data.append( {"header": "MeanT_H{}".format(i+1), "markers": { "name": "H{}_Cu%1%".format(i+1), "index1": index_Helices[i]} } )
            powerH_data.append( {"header": "Power_H{}".format(i+1), "markers": { "name": "H{}_Cu%1%".format(i+1), "index1": index_Helices_e[i]} } )
        
        for i in range(NRings) :
            meanT_data.append( {"header": "MeanT_R{}".format(i+1), "markers": { "name": "R{}".format(i+1)} } )

    else:
        for i in range(NHelices) :
            powerH_data.append( {"header": "Power_H{}".format(i+1), "markers": { "name": "H{}_Cu".format(i+1)} } )
            meanT_data.append( {"header": "MeanT_H{}".format(i+1), "markers": { "name": "H{}_Cu".format(i+1)} } )

        if cad.CurrentLeads:
            print("insert: 3D currentH, powerH, meanT for leads")
            currentH_data.append( {"header": "Current_iL1", "markers": { "name:": "iL1_V0" } } )
            currentH_data.append( {"header": "Current_oL2", "markers": { "name:": "oL2_V0" } } )
            powerH_data.append( {"header": "Power_iL1", "markers": { "name": "iL1"} } )
            powerH_data.append( {"header": "Power_oL2", "markers": { "name": "oL2"} } )
            meanT_data.append( {"header": "MeanT_iL1", "markers": { "name": "iL1" } } )
            meanT_data.append( {"header": "MeanT_oL2", "markers": { "name": "oL2" } } )
        else:
            currentH_data.append( {"header": "Current_H1", "markers": { "name:": "H1_V0" } } )
            currentH_data.append( {"header": "Current_H{}".format(NHelices), "markers": { "name:": "H{}_V0".format(NHelices) } } )

        print(f"insert: 3D powerH for {NRings} rings")
        for i in range(NRings) :
            powerH_data.append( {"header": "Power_R{}".format(i+1), "markers": { "name": "R{}".format(i+1)} } )
            meanT_data.append( {"header": "MeanT_R{}".format(i+1), "markers": { "name": "R{}".format(i+1)} } )

    mpost = { 
        "power_H": powerH_data ,
        "current_H": currentH_data        
    } 
    if 'th' in method_data[3]:
        mpost["flux"] = {'index_h': "0:%s" % str(NChannels)}
        mpost["meanT_H"] = meanT_data

        
    # check mpost output
    # print(f"insert: mpost={mpost}")
    mmat = create_materials_insert(gdata, index_Insulators, confdata, templates, method_data, debug)

    # update U and hw, dTw param
    print("Update U for I0=31kA")
    # print(f"insert: mmat: {mmat}")
    # print(f"insert: mdict['Parameters']: {mdict['Parameters']}")
    I0 = 31.e+3
    if method_data[2] == "Axi":
        import math
        params = params_data['Parameters']
        for i in range(NHelices):
            pitch = pitch_h[i]
            turns = turns_h[i]
            for j in range(Nsections[i]):
                marker = "H%d_Cu%d" % (i+1, j+1)
                item = {"name": "U_" + marker, "value":"1"}
                index = params.index(item)
                mat = mmat[marker]
                print(f"mat[{marker}]: {mat}")
                # print("U=", params[index], mat['sigma'], R1[i], pitch_h[j])
                sigma = float(mat['sigma'])
                I_s = I0 * turns_h[i][j]
                j1 = I_s / (math.log(R2[i]/R1[i]) * (R1[i] * 1.e-3) *(pitch[j]*1.e-3) * turns[j] )
                U_s = 2 * math.pi * (R1[i] * 1.e-3) * j1 / sigma  
                # print("U=", params[index]['name'], R1[i], R2[i], pitch[j], turns[j], mat['sigma'], "U_s=", U_s, "j1=", j1)
                item = {"name": "U_" + marker, "value":str(U_s)}
                params[index] = item
                
    
    return (mdict, mmat, mpost)
