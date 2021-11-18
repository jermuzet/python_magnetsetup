"""
Create template json model files for Feelpp/HiFiMagnet simu
From a yaml definition file of an insert

Inputs:
* method : method of solve, with feelpp cfpdes, getdp...
* time: stationnary or transient case
* geom: geometry of solve, 3D or Axi
* model: physic solved, thermic, thermomagnetism, thermomagnetism-elastic
* phytype: if the materials are linear or non-linear
* cooling: what type of cooling, mean or grad

Output: 
* tmp.json

App setup is stored in a json file that defines
the mustache template to be used.

Default path:
magnetsetup.json
mustache templates
"""

# TODO check for unit consistency
# depending on Length base unit

import sys
import os
import requests
import requests.exceptions
import ast
import pandas as pd

import math

import yaml
from python_magnetgeo import Helix
from python_magnetgeo import Ring
from python_magnetgeo import InnerCurrentLead
from python_magnetgeo import OuterCurrentLead
from python_magnetgeo import Insert
from python_magnetgeo import python_magnetgeo

import chevron
import json

import argparse
import pathlib

# Global variables stored in settings.env
from . import config
url_api = config.data.get('URL_API')
print("url_api=", url_api)
# url_api = 'http://localhost:8000/api'

def Merge(dict1, dict2):
    """
    Merge dict1 and dict2 to form a new dictionnary
    """
    res = {**dict1, **dict2}
    return res

def create_params_dict(args, Zmin, Zmax, Sh, Dh, NHelices, Nsections):
    """
    Return params_dict, the dictionnary of section \"Parameters\" for JSON file.
    """

    # Tini, Aini for transient cases??
    params_dict = {}

    # for cfpdes only
    if args.method == "cfpdes":
        params_dict["bool_laplace"] = "1"
        params_dict["bool_dilatation"] = "1"

    # TODO : initialization of parameters

    params_dict["Tinit"] = 293
    params_dict["h"] = 58222.1
    params_dict["Tw"] = 290.671
    params_dict["dTw"] = 12.74
    
    # params per cooling channels
    # h%d, Tw%d, dTw%d, Dh%d, Sh%d, Zmin%d, Zmax%d :

    for i in range(NHelices+1):
        params_dict["h%d" % i] = "h:h"
        params_dict["Tw%d" % i] = "Tw:Tw"
        params_dict["dTw%d" % i] = "dTw:dTw"
        params_dict["Zmin%d" % i] = Zmin[i]
        params_dict["Zmax%d" % i] = Zmax[i]
        params_dict["Sh%d" % i] = Sh[i]
        params_dict["Dh%d" % i] = Dh[i]

    # init values for U (Axi specific)
    if args.geom == "Axi":
        for i in range(NHelices):
            for j in range(Nsections[i]):
                params_dict["U_H%d_Cu%d" % (i+1, j+1)] = "1"
    
    # TODO: CG: U_H%d%
    # TODO: HDG: U_H%d% if no ibc

    return params_dict

def create_materials_dict(confdata):
    if confdata["Lead"]:
        pass

def create_materials_dict(confdata, finsulator, fconductor, NHelices, Nsections, NRings):
    """
    Return materials_dict, the dictionnary of section \"Materials\" for JSON file.
    """

    # TODO loop for Plateau (Axi specific)
    materials_dict = {}

    # Loop for Helix
    for i in range(NHelices):
        with open(fconductor, "r") as ftemplate:
            jsonfile = chevron.render(ftemplate, Merge({'name': "H%d" % (i+1)}, confdata["Helix"][i]["material"]))
            jsonfile = jsonfile.replace("\'", "\"")
            # shall get rid of comments: //*
            mdata = json.loads(jsonfile)
            materials_dict["H%d" % (i+1)] = mdata["H%d" % (i+1)]
        
            # TODO deal with Glue/Kaptons

    # loop for Rings
    for i in range(NRings):
        with open(fconductor, "r") as ftemplate:
            jsonfile = chevron.render(ftemplate, Merge({'name': "R%d" % (i+1)}, confdata["Ring"][i]["material"]))
            jsonfile = jsonfile.replace("\'", "\"")
            # shall get rid of comments: //*
            mdata = json.loads(jsonfile)
            materials_dict["R%d" % (i+1)] = mdata["R%d" % (i+1)]
        
    # Leads: 
    if confdata["Lead"]:
        with open(fconductor, "r") as ftemplate:
            jsonfile = chevron.render(ftemplate, Merge({'name': "iL1"}, confdata["Lead"][0]["material"]))
            jsonfile = jsonfile.replace("\'", "\"")
            # shall get rid of comments: //*
            mdata = json.loads(jsonfile)
            materials_dict["iL1"] = mdata["iL1"]

        # outer
        with open(fconductor, "r") as ftemplate:
            jsonfile = chevron.render(ftemplate, Merge({'name': "oL2"}, confdata["Lead"][1]["material"]))
            jsonfile = jsonfile.replace("\'", "\"")
            # shall get rid of comments: //*
            mdata = json.loads(jsonfile)
            materials_dict["oL2"] = mdata["oL2"]

    return materials_dict

def create_materials_axi_dict(confdata, finsulator, fconductor, NHelices, Nsections, NRings):
    """
    Return materials_dict, the dictionnary of section \"Materials\" for JSON file.
    """

    # TODO loop for Plateau (Axi specific)
    materials_dict = {}

    for i in range(NHelices):
        
        # section j==0:  treated as insulator in Axi
        with open(finsulator, "r") as ftemplate:
            jsonfile = chevron.render(ftemplate, Merge({'name': "H%d_Cu%d" % (i+1, 0)}, confdata["Helix"][i]["material"]))
            jsonfile = jsonfile.replace("\'", "\"")
            # shall get rid of comments: //*
            mdata = json.loads(jsonfile)
            materials_dict["H%d_Cu%d" % (i+1, 0)] = mdata["H%d_Cu%d" % (i+1, 0)]
        
        # load conductor template
        for j in range(1,Nsections[i]+1):
            with open(fconductor, "r") as ftemplate:
                jsonfile = chevron.render(ftemplate, Merge({'name': "H%d_Cu%d" % (i+1, j)}, confdata["Helix"][i]["material"]))
                jsonfile = jsonfile.replace("\'", "\"")
                # shall get rid of comments: //*
                mdata = json.loads(jsonfile)
                materials_dict["H%d_Cu%d" % (i+1, j)] = mdata["H%d_Cu%d" % (i+1, j)]

        # section j==Nsections+1:  treated as insulator in Axi
        with open(finsulator, "r") as ftemplate:
            jsonfile = chevron.render(ftemplate, Merge({'name': "H%d_Cu%d" % (i+1, Nsections[i]+1)}, confdata["Helix"][i]["material"]))
            jsonfile = jsonfile.replace("\'", "\"")
            # shall get rid of comments: //*
            mdata = json.loads(jsonfile)
            materials_dict["H%d_Cu%d" % (i+1, Nsections[i]+1)] = mdata["H%d_Cu%d" % (i+1, Nsections[i]+1)]

        # loop for Rings:  treated as insulator in Axi
        for i in range(NRings):
            with open(finsulator, "r") as ftemplate:
                jsonfile = chevron.render(ftemplate, Merge({'name': "R%d" % (i+1)}, confdata["Ring"][i]["material"]))
                jsonfile = jsonfile.replace("\'", "\"")
                # shall get rid of comments: //*
                mdata = json.loads(jsonfile)
                materials_dict["R%d" % (i+1)] = mdata["R%d" % (i+1)]
        
        # Leads: treated as insulator in Axi
        # inner
        '''
        with open(finsulator, "r") as ftemplate:
            jsonfile = chevron.render(ftemplate, Merge({'name': "iL1"}, confdata["Lead"][0]["material"]))
            jsonfile = jsonfile.replace("\'", "\"")
            # shall get rid of comments: //*
            mdata = json.loads(jsonfile)
            materials_dict["iL1"] = mdata["iL1"]

        # outer
        with open(finsulator, "r") as ftemplate:
            jsonfile = chevron.render(ftemplate, Merge({'name': "oL2"}, confdata["Lead"][1]["material"]))
            jsonfile = jsonfile.replace("\'", "\"")
            # shall get rid of comments: //*
            mdata = json.loads(jsonfile)
            materials_dict["oL2"] = mdata["oL2"]
        '''

    return materials_dict

def create_bcs_dict(NChannels, fcooling):
    """
    Return bcs_dict, the dictionnary of section \"BoundaryConditions\" for JSON file especially for cooling.
    """

    bcs_dict = {}

    for i in range(NChannels):
        # load insulator template for j==0
        with open(fcooling, "r") as ftemplate:
            jsonfile = chevron.render(ftemplate, {'i': i})
            jsonfile = jsonfile.replace("\'", "\"")
            # shall get rid of comments: //*
            mdata = json.loads(jsonfile)
            bcs_dict["Channel%d" % i] = mdata["Channel%d" % i]

    return bcs_dict

def main():

    
    # Manage Options
    command_line = None
    parser = argparse.ArgumentParser(description="Create template json model files for Feelpp/HiFiMagnet simu")
    parser.add_argument("--datafile", help="input data file (ex. HL-34-data.json)", default=None)
    parser.add_argument("--wd", help="set a working directory", type=str, default="")
    parser.add_argument("--magnet", help="Magnet name from magnetdb (ex. HL-34)", default=None)

    parser.add_argument("--method", help="choose method (default is cfpdes", type=str,
                    choices=['cfpdes', 'CG', 'HDG', 'CRB'], default='cfpdes')
    parser.add_argument("--time", help="choose time type", type=str,
                    choices=['static', 'transient'], default='static')
    parser.add_argument("--geom", help="choose geom type", type=str,
                    choices=['Axi', '3D'], default='Axi')
    parser.add_argument("--model", help="choose model type", type=str,
                    choices=['th', 'thel', 'mag', 'thmag', 'thmagel'], default='thmagel')
    parser.add_argument("--nonlinear", help="force non-linear", action='store_true')
    parser.add_argument("--cooling", help="choose cooling type", type=str,
                    choices=['mean', 'grad'], default='mean')
    parser.add_argument("--scale", help="scale of geometry", type=float, default=1e-3)

    parser.add_argument("--debug", help="activate debug", action='store_true')
    parser.add_argument("--verbose", help="activate verbose", action='store_true')

    args = parser.parse_args()
    if args.debug:
        print(args)

    if ( args.datafile == None ) and ( args.magnet == None ):
        print("You must enter datafile or magnet.")
        exit(1)

    if ( args.datafile != None ) and ( args.magnet != None ):
        print("You can't enter datafile and magnet together.")
        exit(1)

    # Get current dir
    cwd = os.getcwd()
    if args.wd:
        os.chdir(args.wd)

    # Load magnetsetup config
    default_path = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(default_path, 'magnetsetup.json'), 'r') as appcfg:
        magnetsetup = json.load(appcfg)

    # Recuperate the data of configuration with datafile
    if args.datafile != None :
        # Load yaml file for geo config
        with open(args.datafile, 'r') as cfgdata:
            confdata = json.load(cfgdata)

        if args.debug:
            print("confdata=%s" % args.datafile)
            if confdata['Helix']:
                print(confdata['Helix'])

    # Get data from magnet name using magnetdb
    if args.magnet != None:
        print(url_api + '/magnet/mdata/' + args.magnet)
        r = requests.get(url= url_api + '/magnet/mdata/' + args.magnet )
        confdata = ast.literal_eval(r.text)

    yamlfile = confdata["geom"]

    if args.debug:
        print("yamlfile=%s" % yamlfile)
    
    part_withoutAir = []  # list of name of all parts without Air
    part_conductor = []
    index_V0 = []
    # TODO init here is specific to geom==Axi
    boundary_meca = [ ] # list of boundaries name for elastic part
    boundary_maxwell = [ ] # list of boundaries name for maxwell part

    with open(yamlfile, 'r') as cfgdata:
        cad = yaml.load(cfgdata, Loader = yaml.FullLoader)
        if isinstance(cad, Insert):
            (NHelices, NRings, NChannels, Nsections, index_h, R1, R2, Z1, Z2, Zmin, Zmax, Dh, Sh) = python_magnetgeo.get_main_characteristics(cad)

            for i in range(NHelices):
                part_conductor.append("H{}".format(i+1))
                if args.geom == "Axi":
                    for j in range(Nsections[i]+2):
                        part_withoutAir.append("H{}_Cu{}".format(i+1,j))
                # else add Glue/Kaptons
            for i in range(NRings):
                part_withoutAir.append("R{}".format(i+1))
                part_conductor.append("R{}".format(i+1))

            # Add currentLeads
            if len(cad.CurrentLeads):
                part_withoutAir.append("iL1")
                part_withoutAir.append("oL2")
                part_conductor.append("iL1")
                part_conductor.append("oL2")
                index_V0.append(["Inner1_LV0", "iL1"])
                index_V0.append(["OuterL2_LV0", "oL2"])
                
                boundary_meca.append("Inner1_LV0")
                boundary_meca.append("OuterL2_LV0")

                boundary_maxwell.append("InfV00")
                boundary_maxwell.append("InfV01")

            else:
                index_V0.append(["H1_V0", "H1"])
                index_V0.append(["H%d_V0" % NHelices, "H%d" % NHelices])
                
                boundary_meca.append("H1_HP")
                boundary_meca.append("H_HP")    
                
            boundary_maxwell.append("InfV1")
            boundary_maxwell.append("InfR1")

            
            for i in range(1,NRings+1):
                if i % 2 == 1 :
                    boundary_meca.append("R{}_BP".format(i))
                else :
                    boundary_meca.append("R{}_HP".format(i))

            # 
            if args.debug:
                print("part_conductor:", part_conductor)

        else:
            raise Exception("expected Insert yaml file")

    # TODO : manage the scale
    for i in range(len(Zmin)): Zmin[i] *= args.scale
    for i in range(len(Zmax)): Zmax[i] *= args.scale
    for i in range(len(Dh)): Dh[i] *= args.scale
    for i in range(len(Sh)): Sh[i] *= args.scale

    if args.geom == "Axi":
        # Actually overwrite index_h from python_magnetgeo.get_main_characteristics(cad)
        index_h = []
        index_conductor = []
        index_Helices = []
        index_HelicesConductor = []
        for i in range(NHelices):
            for j in range(Nsections[i]+2):
                index_h.append( [str(i+1),str(j)] )
            for j in range(Nsections[i]):
                index_conductor.append( [str(i+1),str(j+1)] )
            index_Helices.append(["0:{}".format(Nsections[i]+2)])
            index_HelicesConductor.append(["1:{}".format(Nsections[i]+1)])
    
    
    # load mustache template file
    # cfg_model  = magnetsetup[args.method][args.time][args.geom][args.model]["cfg"]
    json_model = magnetsetup[args.method][args.time][args.geom][args.model]["model"]
    if not args.nonlinear:
        conductor_model = magnetsetup[args.method][args.time][args.geom][args.model]["conductor-linear"]
    else:
        if args.geom == "3D": 
            json_model = magnetsetup[args.method][args.time][args.geom][args.model]["model-nonlinear"]
        conductor_model = magnetsetup[args.method][args.time][args.geom][args.model]["conductor-nonlinear"]
    insulator_model = magnetsetup[args.method][args.time][args.geom][args.model]["insulator"]
    if args.model != 'mag':
        cooling_model = magnetsetup[args.method][args.time][args.geom][args.model]["cooling"][args.cooling]
        flux_model = magnetsetup[args.method][args.time][args.geom][args.model]["cooling-post"][args.cooling]
        stats_T_model = magnetsetup[args.method][args.time][args.geom][args.model]["stats_T"]
        stats_Power_model = magnetsetup[args.method][args.time][args.geom][args.model]["stats_Power"]

    # TODO create default path to mustache according to method, geom
    template_path = os.path.join(default_path, "templates", args.method, args.geom)
    fmodel = os.path.join(template_path, json_model)
    fconductor = os.path.join(template_path, conductor_model)
    finsulator = os.path.join(template_path, insulator_model)
    if args.model != 'mag':
        fcooling = os.path.join(template_path, cooling_model)
        fflux = os.path.join(template_path, flux_model)
        fstats_T = os.path.join(template_path, stats_T_model)
        fstats_Power = os.path.join(template_path, stats_Power_model)

    # copy json files to cwd (only for cfpdes)
    material_generic_def = ["conductor", "insulator"]

    if args.time == "transient":
        material_generic_def.append("conductor-nosource") # only for transient with mqs

    if args.method == "cfpdes":
        from shutil import copyfile
        for jsonfile in material_generic_def:
            filename = magnetsetup[args.method][args.time][args.geom][args.model]["filename"][jsonfile]
            src = os.path.join(template_path, filename)
            dst = os.path.join(cwd, jsonfile + "-" + args.method + "-" + args.model + "-" + args.geom + ".json")
            #print(jsonfile, "filename=", filename, src, dst)
            copyfile(src, dst)
    
    with open(fmodel, "r") as ftemplate:
        # TODO tell geom==Axi from geom==3D case
        if args.geom == "Axi":
            jsonfile = chevron.render(ftemplate, {'index_h': index_h, 'index_conductor':index_conductor, 'imin': 0, 'imax': NHelices+1, 'part_withoutAir':part_withoutAir, 'boundary_Meca':boundary_meca })
        else:
            jsonfile = chevron.render(ftemplate, {'index_V0':index_V0, 'part_conductor':part_conductor, 'part_withoutAir':part_withoutAir, 'boundary_Meca':boundary_meca })
        jsonfile = jsonfile.replace("\'", "\"")
        # shall get rid of comments: //*
        # now tweak obtained json
        if args.debug:
            print("jsonmodel:", jsonfile)
        data = json.loads(jsonfile)
        
        # Fill parameters
        params_dict = create_params_dict(args, Zmin, Zmax, Sh, Dh, NHelices, Nsections)

        for key in params_dict:
            data["Parameters"][key] = params_dict[key]

        # Fill materials
        if args.geom == "Axi":
            materials_dict = create_materials_axi_dict(confdata, finsulator, fconductor, NHelices, Nsections, NRings)
        else:
            materials_dict = create_materials_dict(confdata, finsulator, fconductor, NHelices, Nsections, NRings)

        if "Materials" in data:
            for key in materials_dict:
                data["Materials"][key] = materials_dict[key]
        else:
            data["Materials"] = materials_dict
        
        # geom=Axi: 
        #    BCs for mag are hardcoded in mustache
        # TODO BCs for electric, mag, elast when geom==3D
        
        # loop for Cooling BCs
        if args.model != 'mag':
            data["BoundaryConditions"]["heat"]["Robin"] = create_bcs_dict(NChannels, fcooling)

        # Postprocessing stuff
        if args.model != 'mag':
            # add flux_model for Flux_Channel calc
            with open(fflux, "r") as ftemplate:
                jsonfile = chevron.render(ftemplate, {'index_h': "0:%s" % str(NChannels)})
                jsonfile = jsonfile.replace("\'", "\"")
                mdata = json.loads(jsonfile)
                data["PostProcess"]["heat"]["Measures"]["Statistics"]["Flux_Channel%1%"] = mdata["Flux"]["Flux_Channel%1%"]

                
            # create a template for MeanT_H 
            with open(fstats_T, "r") as ftemplate:
                meanT_data = { "meanT_H": [] }
                # TODO geom depends
                if args.geom == "Axi":
                    for i in range(NHelices) :
                        meanT_data["meanT_H"].append( {"header": "MeanT_H{}".format(i+1), "name": "H{}_Cu%1%".format(i+1), "index": index_Helices[i]} )
                else:
                    for i in range(NHelices) :
                        meanT_data["meanT_H"].append( {"header": "MeanT_H{}".format(i+1), "name": "H{}".format(i+1)} )
                        # TODO add Glue/Kaptons
                    for i in range(NRings) :
                        meanT_data["meanT_H"].append( {"header": "MeanT_R{}".format(i+1), "name": "R{}".format(i+1)} )
                    # TODO add current Leads
                   
                jsonfile = chevron.render(ftemplate, meanT_data)
                jsonfile = jsonfile.replace("\'", "\"")
                
                # replace lat occurrence of },
                new = "}"
                result = new.join(jsonfile.rsplit("},", 1))
                if args.debug:
                    print("stats_T_data")
                    print(result)
                mdata = json.loads(result)
                #print(mdata)
                for md in mdata["Stats_T"]:
                    data["PostProcess"]["heat"]["Measures"]["Statistics"][md] = mdata["Stats_T"][md]

            # create a template for Power_H
            with open(fstats_Power, "r") as ftemplate:
                meanT_data = { "Power_H": [] }
                # TODO geom depends
                if args.geom == "Axi":
                    for i in range(NHelices) :
                        meanT_data["Power_H"].append( {"header": "Power_H{}".format(i+1), "name": "H{}_Cu%1%".format(i+1), "index": index_Helices[i]} )
                else:
                    for i in range(NHelices) :
                        meanT_data["Power_H"].append( {"header": "Power_H{}".format(i+1), "name": "H{}".format(i+1)} )
                        # TODO add Glue/Kaptons
                    for i in range(NRings) :
                        meanT_data["Power_H"].append( {"header": "Power_R{}".format(i+1), "name": "R{}".format(i+1)} )
                    # TODO add current Leads
                       
                jsonfile = chevron.render(ftemplate, meanT_data)
                jsonfile = jsonfile.replace("\'", "\"")
                
                # replace lat occurrence of },
                new = "}"
                result = new.join(jsonfile.rsplit("},", 1))
                if args.debug:
                    print("stats_Power_data")
                    print(result)
                
                mdata = json.loads(result)
                #print(mdata)

                # section heat or electric depending on method, geom and model
                section = "electric"
                if args.method == "cfpdes":
                    if args.geom == "Axi":
                        section = "heat" 
                for md in mdata["Stats_Power"]:
                    data["PostProcess"][section]["Measures"]["Statistics"][md] = mdata["Stats_Power"][md]

        
        # save json (NB use x to avoid overwrite file)
        if args.datafile != None :
            outfilename = args.datafile.replace(".json","")
        if args.magnet != None :
            outfilename = args.magnet
        outfilename += "-" + args.method
        outfilename += "-" + args.model
        if args.nonlinear:
            outfilename += "-nonlinear"
        outfilename += "-" + args.geom
        outfilename += "-sim.json"

        with open(outfilename, "w") as out:
            out.write(json.dumps(data, indent = 4))

if __name__ == "__main__":
    main()
