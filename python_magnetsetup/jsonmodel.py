from typing import List, Union, Optional

import sys
import os
import json
import yaml

import math

from .utils import Merge
from .units import load_units, convert_data

def create_params_supra(gdata: tuple, method_data: List[str], debug: bool=False) -> dict:
    """
    Return params_dict, the dictionnary of section \"Parameters\" for JSON file.
    """
    print("create_params_supra")
    
    # TODO: length data are written in mm should be in SI instead
    unit_Length = method_data[5] # "meter"
    units = load_units(unit_Length)

    # Tini, Aini for transient cases??
    params_data = { 'Parameters': []}
    if "mag" in method_data[3] or "mqs" in method_data[3] :
        params_data['Parameters'].append({"name":"mu0", "value":convert_data(units,  4*math.pi*1e-7, "mu0")})

    if debug:
        print(params_data)
        
    return params_data

def create_params_bitter(gdata: tuple, method_data: List[str], debug: bool=False):
    """
    Return params_dict, the dictionnary of section \"Parameters\" for JSON file.
    """
    print("create_params_bitter for %s" % gdata[0])
    
    # TODO: length data are written in mm should be in SI instead
    unit_Length = method_data[5] # "meter"
    units = load_units(unit_Length)

    # Tini, Aini for transient cases??
    params_data = { 'Parameters': []}

    # for cfpdes only
    if method_data[0] == "cfpdes" and method_data[3] == "thmagel" :
        params_data['Parameters'].append({"name":"bool_laplace", "value":"1"})
        params_data['Parameters'].append({"name":"bool_dilatation", "value":"1"})

    # TODO : initialization of parameters with cooling model

    params_data['Parameters'].append({"name":"Tinit", "value":293})
    
    (name, snames, nturns) = gdata
    for thbc in ["rInt", "rExt"]:
        params_data['Parameters'].append({"name":"%s_%s_hw" % (name, thbc), "value":convert_data(units, 58222.1, "h")})
        params_data['Parameters'].append({"name":"%s_%s_Tw" % (name, thbc), "value":290.671})
        params_data['Parameters'].append({"name":"%s_%s_dTw" % (name, thbc), "value":12.74})
    # for sname in snames:
    #    params_data['Parameters'].append({"name":"%s_hw" % sname, "value":convert_data(units, 58222.1, "h")})
    #    params_data['Parameters'].append({"name":"%s_Tw" % sname, "value":290.671})
    #    params_data['Parameters'].append({"name":"%s_dTw" % sname, "value":12.74})

    # init values for U (Axi specific)
    if method_data[2] == "Axi":
        for i,sname in enumerate(snames):
            params_data['Parameters'].append({"name":"U_%s" % sname, "value":"1"})
            params_data['Parameters'].append({"name":"N_%s" % sname, "value":nturns[i]})
            # params_data['Parameters'].append({"name":"S_%s" % sname, "value":convert_data(units, Ssections[i], "Area")})

    if "mag" in method_data[3] or "mqs" in method_data[3] :
        params_data['Parameters'].append({"name":"mu0", "value":convert_data(units,  4*math.pi*1e-7, "mu0")})

    if debug:
        print(params_data)
        
    return params_data

def create_params_insert(gdata: tuple, method_data: List[str], debug: bool=False) -> dict:
    """
    Return params_dict, the dictionnary of section \"Parameters\" for JSON file.
    """
    print("create_params_insert")

    # TODO: length data are written in mm should be in SI instead
    unit_Length = method_data[5] # "meter"
    units = load_units(unit_Length)
    print("unit_Length", unit_Length)

    (NHelices, NRings, NChannels, Nsections, R1, R2, Z1, Z2, Zmin, Zmax, Dh, Sh, turns_h) = gdata
    
    if debug: print("R1:", R1)
    print("Zmin:", Zmin)
    if unit_Length == 'meter':
        R1 = convert_data(units, R1, "Length")
        R2 = convert_data(units, R2, "Length")
        Z1 = convert_data(units, Z1, "Length")
        Z2 = convert_data(units, Z2, "Length")
        Zmin = convert_data(units, Zmin, "Length")
        Zmax = convert_data(units, Zmax, "Length")
        Dh = convert_data(units, Dh, "Length")
        Sh  = convert_data(units, Sh, "Area")
    print("Zmin:", Zmin)
    
    # chech dim
    if debug: print("corrected R1:", R1)
    
    # Tini, Aini for transient cases??
    params_data = { 'Parameters': []}

    # for cfpdes only
    if method_data[0] == "cfpdes" and method_data[3] == "thmagel" :
        params_data['Parameters'].append({"name":"bool_laplace", "value":"1"})
        params_data['Parameters'].append({"name":"bool_dilatation", "value":"1"})

    # TODO : initialization of parameters with cooling model

    params_data['Parameters'].append({"name":"Tinit", "value":293})
    # get value from coolingmethod and Flow(I) value
    params_data['Parameters'].append({"name":"hw", "value":convert_data(units, 58222.1, "h")})
    params_data['Parameters'].append({"name":"Tw", "value":290.671})
    params_data['Parameters'].append({"name":"dTw", "value":12.74})
    
    # params per cooling channels
    # h%d, Tw%d, dTw%d, Dh%d, Sh%d, Zmin%d, Zmax%d :

    for i in range(NHelices+1):
        # get value from coolingmethod and Flow(I) value
        params_data['Parameters'].append({"name":"h%d" % i, "value":convert_data(units, 58222.1, "h")})
        params_data['Parameters'].append({"name":"Tw%d" % i, "value":290.671})
        params_data['Parameters'].append({"name":"dTw%d" % i, "value":12.74})
        params_data['Parameters'].append({"name":"Zmin%d" % i, "value": Zmin[i]})
        params_data['Parameters'].append({"name":"Zmax%d" % i, "value": Zmax[i]})
        params_data['Parameters'].append({"name":"Sh%d" % i, "value": Sh[i]})
        params_data['Parameters'].append({"name":"Dh%d" % i, "value": Dh[i]})

    # init values for U (Axi specific)
    if method_data[2] == "Axi":
        for i in range(NHelices):
            for j in range(Nsections[i]):
                # TODO set more realistic value for I0 = 31kA ??
                params_data['Parameters'].append({"name":"U_H%d_Cu%d" % (i+1, j+1), "value":"1"})

            turns = turns_h[i]
            for j in range(Nsections[i]):
                params_data['Parameters'].append({"name":"N_H%d_Cu%d" % (i+1, j+1), "value":turns[j]})
        # for i in range(NHelices):
        #     for j in range(Nsections[i]):
        #         params_data['Parameters'].append({"name":"S_H%d_Cu%d" % (i+1, j+1), "value":convert_data(units, distance_unit, Ssections[i], "Area")})
    
    if "mag" in method_data[3] or "mqs" in method_data[3] :
        params_data['Parameters'].append({"name":"mu0", "value":convert_data(units, 4*math.pi*1e-7, "mu0")})
    # TODO: CG: U_H%d%
    # TODO: HDG: U_H%d% if no ibc    # TODO: length data are written in mm should be in SI instead
    
    if debug:
        print(params_data)
        
    return params_data


def create_materials_supra(gdata: tuple, confdata: dict, templates: dict, method_data: List[str], debug: bool = False) -> dict:
    materials_dict = {}
    if debug: print("create_material_supra:", confdata)

    fconductor = templates["conductor"]
    
    # TODO: length data are written in mm should be in SI instead
    unit_Length = method_data[5] # "meter"
    units = load_units(unit_Length)
    for prop in ["ThermalConductivity", "Young", "VolumicMass", "ElectricalConductivity"]:
        confdata["material"][prop] = convert_data(units, confdata["material"][prop], prop)

    if method_data[2] == "Axi":
        pass
    else:
        pass

    return materials_dict

def create_materials_bitter(gdata: tuple, confdata: dict, templates: dict, method_data: List[str], debug: bool = False) -> dict:
    materials_dict = {}
    if debug: print("create_material_bitter:", confdata)

    fconductor = templates["conductor"]
    
    # TODO: length data are written in mm should be in SI instead
    unit_Length = method_data[5] # "meter"
    units = load_units(unit_Length)
    
    for prop in ["ThermalConductivity", "Young", "VolumicMass", "ElectricalConductivity"]:
        confdata["material"][prop] = convert_data(units, confdata["material"][prop], prop)

    (name, snames, turns) = gdata
    for sname in snames:
        if method_data[2] == "Axi":
            if debug: print("create_material_bitter:", sname)
            mdata = entry(fconductor, Merge({'name': "%s" % sname}, confdata["material"]) , debug)
            materials_dict["%s" % sname] = mdata["%s" % sname]
        else:
            return {}

    if debug:
        print(materials_dict)
    return materials_dict

def create_materials_insert(gdata: tuple, idata: Optional[List], confdata: dict, templates: dict, method_data: List[str], debug: bool = False) -> dict:
    # TODO loop for Plateau (Axi specific)
    materials_dict = {}
    if debug: print("create_material_insert:", confdata)

    fconductor = templates["conductor"]
    finsulator = templates["insulator"]

    (NHelices, NRings, NChannels, Nsections, R1, R2, Z1, Z2, Zmin, Zmax, Dh, Sh) = gdata

    # TODO: length data are written in mm should be in SI instead
    unit_Length = method_data[5] # "meter"
    units = load_units(unit_Length)
    for mtype in ["Helix", "Ring", "Lead"]:
        if mtype in confdata:
            for i in range(len(confdata[mtype])):            
                for prop in ["ThermalConductivity", "Young", "VolumicMass", "ElectricalConductivity"]:
                    confdata[mtype][i]["material"][prop] = convert_data(units, confdata[mtype][i]["material"][prop], prop)
            
    # Loop for Helix
    for i in range(NHelices):
        if method_data[2] == "3D":
            mdata = entry(fconductor, Merge({'name': "H%d" % (i+1), 'marker': "H%d_Cu" % (i+1)}, confdata["Helix"][i]["material"]) , debug)
            materials_dict["H%d" % (i+1)] = mdata["H%d" % (i+1)]

            if idata:
                for item in idata:
                    if item[0] == "Glue":
                        name = "Isolant%d" % (i+1)
                        mdata = entry(finsulator, Merge({'name': name, 'marker': "H%d_Isolant" % (i+1)}, confdata["Helix"][i]["insulator"]), debug)
                    else:
                        name = "Kaptons%d" % (i+1)
                        kapton_dict = { "name": "[\"Kapton%1%\"]", "index1": "0:%d" % item(1)}
                        mdata = entry(finsulator, Merge({'name': name, 'marker': kapton_dict}, confdata["Helix"][i]["insulator"]), debug)
                    materials_dict[name] = mdata[name]
        else:
            # section j==0:  treated as insulator in Axi
            mdata = entry(finsulator, Merge({'name': "H%d_Cu%d" % (i+1, 0)}, confdata["Helix"][i]["material"]), debug)
            materials_dict["H%d_Cu%d" % (i+1, 0)] = mdata["H%d_Cu%d" % (i+1, 0)]
        
            # load conductor template
            for j in range(1,Nsections[i]+1):
                # print("load conductor[%d]: mat:" % j, confdata["Helix"][i]["material"])
                mdata = entry(fconductor, Merge({'name': "H%d_Cu%d" % (i+1, j)}, confdata["Helix"][i]["material"]), debug)
                # print("load conductor[%d]:" % j, mdata)
                materials_dict["H%d_Cu%d" % (i+1, j)] = mdata["H%d_Cu%d" % (i+1, j)]

            # section j==Nsections+1:  treated as insulator in Axi
            mdata = entry(finsulator, Merge({'name': "H%d_Cu%d" % (i+1, Nsections[i]+1)}, confdata["Helix"][i]["material"]), debug)
            materials_dict["H%d_Cu%d" % (i+1, Nsections[i]+1)] = mdata["H%d_Cu%d" % (i+1, Nsections[i]+1)]

    # loop for Rings
    for i in range(NRings):
        if method_data[2] == "3D":
            mdata = entry(fconductor, Merge({'name': "R%d" % (i+1)}, confdata["Ring"][i]["material"]), debug)
        else:
            mdata = entry(finsulator, Merge({'name': "R%d" % (i+1)}, confdata["Ring"][i]["material"]), debug)
        materials_dict["R%d" % (i+1)] = mdata["R%d" % (i+1)]
        
    # Leads: 
    if method_data[2] == "3D" and "Lead" in confdata:
        mdata = entry(fconductor, Merge({'name': "iL1"}, confdata["Lead"][0]["material"]), debug)
        materials_dict["iL1"] = mdata["iL1"]

        mdata = entry(fconductor, Merge({'name': "oL2"}, confdata["Lead"][1]["material"]), debug)
        materials_dict["oL2"] = mdata["oL2"]

    return materials_dict


def create_bcs_supra(boundary_meca: List, 
               boundary_maxwell: List,
               boundary_electric: List,
               gdata: tuple, confdata: dict, templates: dict, method_data: List[str], debug: bool = False) -> dict:

    print("create_bcs_supra from templates")
    electric_bcs_dir = { 'boundary_Electric_Dir': []} # name, value, vol
    electric_bcs_neu = { 'boundary_Electric_Neu': []} # name, value
    thermic_bcs_rob = { 'boundary_Therm_Robin': []} # name, expr1, expr2
    thermic_bcs_neu = { 'boundary_Therm_Neu': []} # name, value
    meca_bcs_dir = { 'boundary_Meca_Dir': []} # name, value
    maxwell_bcs_dir = { 'boundary_Maxwell_Dir': []} # name, value
    
    fcooling = templates["cooling"]
    
    return {}

def create_bcs_bitter(boundary_meca: List, 
               boundary_maxwell: List,
               boundary_electric: List,
               gdata: tuple, confdata: dict, templates: dict, method_data: List[str], debug: bool = False) -> dict:

    (name, snames, nturns) = gdata
    print("create_bcs_bitter from templates for %s" % name)
    # print("snames=", snames)
    
    electric_bcs_dir = { 'boundary_Electric_Dir': []} # name, value, vol
    electric_bcs_neu = { 'boundary_Electric_Neu': []} # name, value
    thermic_bcs_rob = { 'boundary_Therm_Robin': []} # name, expr1, expr2
    thermic_bcs_neu = { 'boundary_Therm_Neu': []} # name, value
    meca_bcs_dir = { 'boundary_Meca_Dir': []} # name, value
    maxwell_bcs_dir = { 'boundary_Maxwell_Dir': []} # name, value
    
    if 'th' in method_data[3]:
        fcooling = templates["robin"]

        # TODO make only one Bc for rInt and on for RExt
        for thbc in ["rInt", "rExt"]:
            bcname =  name + "_" + thbc
            # Add markers list
            mdata = entry(fcooling, {'name': bcname, "markers": snames, 'hw': '%s_hw' % bcname, 'Tw': '%s_Tw' % bcname, 'dTw':'%s_dTw' % bcname},  debug)
            thermic_bcs_rob['boundary_Therm_Robin'].append( Merge({"name": bcname}, mdata[bcname]) )
    
        th_ = Merge(thermic_bcs_rob, thermic_bcs_neu)

    if method_data[3] == "thelec":
        if method_data[2] == "Axi":
            return th_
        else:
            return {}
    elif method_data[3] == 'mag' or method_data[3] == 'mag_hcurl':
        return {}
    elif method_data[3] == 'thmag' or method_data[3] == 'thmag_hcurl':
        th_ = Merge(thermic_bcs_rob, thermic_bcs_neu)
        if method_data[2] == "Axi":
            return Merge(maxwell_bcs_dir, th_)
        else:
            return {}
    else:
        th_ = Merge(thermic_bcs_rob, thermic_bcs_neu)
        elec_ = Merge(electric_bcs_dir, electric_bcs_neu)
        thelec_ = Merge(th_, elec_)
        thelecmeca_ = Merge(thelec_, meca_bcs_dir)
        return Merge(maxwell_bcs_dir, thelecmeca_)
    
    return {}

def create_bcs_insert(boundary_meca: List, 
               boundary_maxwell: List,
               boundary_electric: List,
               gdata: tuple, confdata: dict, templates: dict, method_data: List[str], debug: bool = False) -> dict:

    print("create_bcs_insert from templates")
    electric_bcs_dir = { 'boundary_Electric_Dir': []} # name, value, vol
    electric_bcs_neu = { 'boundary_Electric_Neu': []} # name, value
    thermic_bcs_rob = { 'boundary_Therm_Robin': []} # name, expr1, expr2
    thermic_bcs_neu = { 'boundary_Therm_Neu': []} # name, value
    meca_bcs_dir = { 'boundary_Meca_Dir': []} # name, value
    maxwell_bcs_dir = { 'boundary_Maxwell_Dir': []} # name, value
    
    (NHelices, NRings, NChannels, Nsections, R1, R2, Z1, Z2, Zmin, Zmax, Dh, Sh) = gdata

    if 'th' in method_data[3]:
        fcooling = templates["cooling"]
    
        for i in range(NChannels):
            # load insulator template for j==0
            mdata = entry(fcooling, {'i': i}, debug)
            thermic_bcs_rob['boundary_Therm_Robin'].append( Merge({"name": "Channel%d" % i}, mdata["Channel%d" % i]) )

    if 'el' in method_data[3] and method_data[3] != 'thelec':
        for bc in boundary_meca:
            meca_bcs_dir['boundary_Meca_Dir'].append({"name":bc, "value":"{0,0}"})

    if 'mag' in method_data[3]:
        for bc in boundary_maxwell:
            if method_data[2] == "3D":
                maxwell_bcs_dir['boundary_Maxwell_Dir'].append({"name":bc, "value":"{0,0}"})
            else:
                maxwell_bcs_dir['boundary_Maxwell_Dir'].append({"name":bc, "value":"0"})

    if method_data[3] != 'mag' and method_data[3] != 'mag_hcurl':
        for bc in boundary_electric:
            electric_bcs_dir['boundary_Electric_Dir'].append({"name":bc[0], "value":bc[2]})
        

    if method_data[3] == "thelec":
        th_ = Merge(thermic_bcs_rob, thermic_bcs_neu)
        if method_data[2] == "Axi":
            return th_
        else:
            elec_ = Merge(electric_bcs_dir, electric_bcs_neu)
            return Merge(th_, elec_)
    elif method_data[3] == 'mag' or method_data[3] == 'mag_hcurl':
        return maxwell_bcs_dir
    elif method_data[3] == 'thmag' or method_data[3] == 'thmag_hcurl':
        th_ = Merge(thermic_bcs_rob, thermic_bcs_neu)
        if method_data[2] == "Axi":
            return Merge(maxwell_bcs_dir, th_)
        else:
            elec_ = Merge(electric_bcs_dir, electric_bcs_neu)
            thelec_ = Merge(th_, elec_)
            return Merge(maxwell_bcs_dir, thelec_)
    elif method_data[3] == 'thmqs' or method_data[3] == 'thmqs_hcurl':
        th_ = Merge(thermic_bcs_rob, thermic_bcs_neu)
        if method_data[2] == "Axi":
            return Merge(maxwell_bcs_dir, th_)
        else:
            elec_ = Merge(electric_bcs_dir, electric_bcs_neu)
            thelec_ = Merge(th_, elec_)
            return Merge(maxwell_bcs_dir, thelec_)
    else:
        th_ = Merge(thermic_bcs_rob, thermic_bcs_neu)
        elec_ = Merge(electric_bcs_dir, electric_bcs_neu)
        thelec_ = Merge(th_, elec_)
        thelecmeca_ = Merge(thelec_, meca_bcs_dir)
        return Merge(maxwell_bcs_dir, thelecmeca_)
            
    return {}

def create_json(jsonfile: str, mdict: dict, mmat: dict, mpost: dict, templates: dict, method_data: List[str], debug: bool = False):
    """
    Create a json model file
    """
    
    if debug: 
        print("create_json jsonfile=", jsonfile)
        print("create_json mdict=", mdict)
    data = entry(templates["model"], mdict, debug)   
    if debug: print("create_json/data model:", data)
    
    # material section
    if "Materials" in data:
        for key in mmat:
            data["Materials"][key] = mmat[key]
    else:
        data["Materials"] = mmat
    if debug: print("create_json/Materials data:", data)

    # postprocess
    # print("=== FORCE DEBUG to True ===")
    # debug = True
    if "flux" in mpost:
        if "heat" in data["PostProcess"]:
            flux_data = mpost["flux"]
            if debug: 
                print("flux", type(flux_data))
            add = data["PostProcess"]["heat"]["Measures"]["Statistics"]
            odata = entry(templates["flux"], flux_data, debug)
            if debug: print(odata)
            for md in odata["Flux"]:
                data["PostProcess"]["heat"]["Measures"]["Statistics"][md] = odata["Flux"][md]
    
    if "meanT_H" in mpost:
        if "heat" in data["PostProcess"]:
            meanT_data = mpost["meanT_H"]
            if debug: 
                print("meanT_H", type(meanT_data))
            add = data["PostProcess"]["heat"]["Measures"]["Statistics"]
            odata = entry(templates["stats"][0], {'meanT_H': meanT_data}, debug)
            if debug: print("odata:", odata)
            for md in odata["Stats_T"]:
                data["PostProcess"]["heat"]["Measures"]["Statistics"][md] = odata["Stats_T"][md]

    index_post_ = 0
    section = "electric"
    if method_data[0] == "cfpdes" and method_data[2] == "Axi":
        if 'th' in method_data[3]: 
            section = "heat"
            index_post_ = 1 
        elif method_data[3] in ['mag', 'mag_hcurl', 'mqs', 'mqs_hcurl'] :
            section = "magnetic" 

    
    if "current_H" in mpost:
        if debug:
            print("current_H")
            print("section:", section)
            print("templates[stats]:", templates["stats"])
        currentH_data = mpost["current_H"]
        add = data["PostProcess"][section]["Measures"]["Statistics"]
        odata = entry(templates["stats"][index_post_+1], {'Current_H': currentH_data}, debug)
        if debug: print(odata)
        for md in odata["Stats_Current"]:
            data["PostProcess"][section]["Measures"]["Statistics"][md] = odata["Stats_Current"][md]
    
    if "power_H" in mpost:
        if debug:
            print("power_H")
            print("section:", section)
            print("templates[stats]:", templates["stats"])
        powerH_data = mpost["power_H"]
        add = data["PostProcess"][section]["Measures"]["Statistics"]
        odata = entry(templates["stats"][index_post_], {'Power_H': powerH_data}, debug)
        if debug: print(odata)
        for md in odata["Stats_Power"]:
            data["PostProcess"][section]["Measures"]["Statistics"][md] = odata["Stats_Power"][md]
    
    mdata = json.dumps(data, indent = 4)

    with open(jsonfile, "x") as out:
        out.write(mdata)
    return

def entry(template: str, rdata: List, debug: bool = False) -> str:
    import chevron
    import re
    
    if debug:
        print("entry/loading %s" % str(template), type(template))
        print("entry/rdata:", rdata)
    with open(template, "r") as f:
        jsonfile = chevron.render(f, rdata)
    jsonfile = jsonfile.replace("\'", "\"")
    # print("jsonfile:", jsonfile)

    corrected = re.sub(r'},\s+},\n', '}\n},\n', jsonfile)
    corrected = re.sub(r'},\s+}\n', '}\n}\n', corrected)
    # corrected = re.sub(r'},\s+}\n', '}\n}\n', corrected)
    corrected = corrected.replace("&quot;", "\"")
    if debug:
        print(f"entry/jsonfile: {jsonfile}")
        print(f"corrected: {corrected}")
    try:
        mdata = json.loads(corrected)
    except json.decoder.JSONDecodeError:
        # ??how to have more info on the pb??
        # save corrected to tmp file and run jsonlint-php tmp?? 
        raise Exception(f"entry: json.decoder.JSONDecodeError in {corrected}")

    if debug:
        print("entry/data (json):\n", mdata)
   
    return mdata
