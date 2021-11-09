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
from python_magnetgeo import python_magnetgeo #import get_main_characteristics

import chevron
import json

import argparse
import pathlib

def Merge(dict1, dict2):
    """
    Merge dict1 and dict2 to form a new dictionnary
    """
    res = {**dict1, **dict2}
    return res

def export_table(table: str):
    """
    Return the pd.DataFrame correspondant to table of database from localhost:8000/api
    """

    # Connect to "http://localhost:8000/api/table/"
    base_url_db_api="http://localhost:8000/api/" + table + "/"

    page = requests.get(url=base_url_db_api)

    print("connect :", page.url, page.status_code)

    if page.status_code != 200 :
        print("cannot logging to %s" % base_url_db_api)
        sys.exit(1)
    
    # Create the DataFrame
    list_table = ast.literal_eval(page.text)
    n = len(list_table)

    keys = list_table[0].keys()
    data_table = pd.DataFrame(columns=keys)

    for id in range(n):
        serie = pd.Series(list_table[id])
        data_table= data_table.append(serie, ignore_index=True)
    
    return data_table

def create_confdata_magnet(magnet: str, debug=False):
    """
    Return confdata the dictionnary of configuration of magnet.
    """

    # Export magnets table
    data_magnets = export_table('magnets')
    #data_magnets = export_table('mpartmagnetlink')
    
    # Search magnet
    names = data_magnets['name']
    if  magnet not in names.values :
        print("magnet : " + magnet + " isn\'t in database.")
        exit(1)
    
    if debug:
        print("magnet : " + magnet + " is in database.")

    serie_magnet = data_magnets[ data_magnets['name']==magnet ]

    # Export mparts of magnet
    data_mparts = export_table('mparts')
    data_mparts = data_mparts[ data_mparts['be']==serie_magnet['be'][0] ]

    # Recuperate the materials
    data_materials = export_table('materials')

    # Create dictionnary of magnet's configuration
    confdata = {}

    confdata['geom'] = serie_magnet['geom'][0]
    confdata['Helix'] = []
    confdata['Ring'] = []
    confdata['Lead'] = []
    for id in data_mparts['id']:
        mpart = data_mparts[ data_mparts['id'] == id ]
        material = data_materials[ data_materials['id'] == mpart['material_id'].values[0] ]
        
        material = material.drop( labels=['name', 'id'], axis=1 )

        dict_mpart = {'geo': mpart['geom'].values[0] }
        dict_material = {}
        for column in material.columns :
            dict_material[column] = material[column].values[0]
        dict_mpart['material'] = dict_material

        confdata[ mpart['mtype'].values[0] ].append(dict_mpart)
    
    return confdata

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
    
    return params_dict

def create_materials_dict(confdata, finsulator, fconductor, NHelices, Nsections, NRings):
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
    parser = argparse.ArgumentParser("Create template json model files for Feelpp/HiFiMagnet simu")
    parser.add_argument("--datafile", help="input data file (ex. HL-34-data.json)", default=None)
    parser.add_argument("--magnet", help="Magnet name (ex. HL-34)", default=None)

    parser.add_argument("--method", help="choose method (default is cfpdes", type=str,
                    choices=['cfpdes', 'CG', 'HDG', 'CRB'], default='cfpdes')
    parser.add_argument("--time", help="choose time type", type=str,
                    choices=['static', 'transient'], default='static')
    parser.add_argument("--geom", help="choose geom type", type=str,
                    choices=['Axi', '3D'], default='Axi')
    parser.add_argument("--model", help="choose model type", type=str,
                    choices=['th', 'mag', 'thmag', 'thmagel'], default='thmagel')
    parser.add_argument("--phytype", help="choose the type of physics", type=str,
                    choices=['linear', 'nonlinear'], default='linear')
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
            print(confdata['Helix'])

    # Recuperate the data of configuration with the direct name of magnet
    if args.magnet != None:
        magnet = args.magnet
        confdata = create_confdata_magnet(magnet, args.debug)

    yamlfile = confdata["geom"]

    if args.debug:
        print("yamlfile=%s" % yamlfile)
    with open(yamlfile, 'r') as cfgdata:
        cad = yaml.load(cfgdata, Loader = yaml.FullLoader)
        if isinstance(cad, Insert):
            (NHelices, NRings, NChannels, Nsections, index_h, 
                R1, R2, Z1, Z2, Zmin, Zmax, Dh, Sh) = python_magnetgeo.get_main_characteristics(cad)
        else:
            raise Exception("expected Insert yaml file")

    # TODO : manage the scale
    for i in range(len(Zmin)): Zmin[i] *= args.scale
    for i in range(len(Zmax)): Zmax[i] *= args.scale
    for i in range(len(Dh)): Dh[i] *= args.scale
    for i in range(len(Sh)): Sh[i] *= args.scale

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

    part_withoutAir = []  # list of name of all parts without Air
    for i in range(NHelices):
        for j in range(Nsections[i]+2):
            part_withoutAir.append("H{}_Cu{}".format(i+1,j))
    for i in range(1,NRings+1):
        part_withoutAir.append("R{}".format(i))

    boundary_Ring = [ "H1_HP","H_HP" ] # list of name of boundaries of Ring for elastic part
    for i in range(1,NRings+1):
        if i % 2 == 1 :
            boundary_Ring.append("R{}_BP".format(i))
        else :
            boundary_Ring.append("R{}_HP".format(i))

    # load mustache template file
    # cfg_model  = magnetsetup[args.method][args.time][args.geom][args.model]["cfg"]
    json_model = magnetsetup[args.method][args.time][args.geom][args.model]["model"]
    if args.phytype == 'linear':
        conductor_model = magnetsetup[args.method][args.time][args.geom][args.model]["conductor-linear"]
    elif args.phytype == 'nonlinear':
        conductor_model = magnetsetup[args.method][args.time][args.geom][args.model]["conductor-nonlinear"]
    insulator_model = magnetsetup[args.method][args.time][args.geom][args.model]["insulator"]
    if args.model != 'mag':
        cooling_model = magnetsetup[args.method][args.time][args.geom][args.model]["cooling"][args.cooling]
        flux_model = magnetsetup[args.method][args.time][args.geom][args.model]["cooling-post"][args.cooling]

    # TODO create default path to mustache according to method, geom
    template_path = os.path.join(default_path, "templates", args.method, args.geom)
    fmodel = os.path.join(template_path, json_model)
    fconductor = os.path.join(template_path, conductor_model)
    finsulator = os.path.join(template_path, insulator_model)
    if args.model != 'mag':
        fcooling = os.path.join(template_path, cooling_model)
        fflux = os.path.join(template_path, flux_model)

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
        jsonfile = chevron.render(ftemplate, {'index_h': index_h, 'index_conductor':index_conductor, 'imin': 0, 'imax': NHelices+1, 'part_withoutAir':part_withoutAir, 'boundary_Ring':boundary_Ring })
        jsonfile = jsonfile.replace("\'", "\"")
        # shall get rid of comments: //*
        # now tweak obtained json
        data = json.loads(jsonfile)
        
        # Fill parameters
        params_dict = create_params_dict(args, Zmin, Zmax, Sh, Dh, NHelices, Nsections)

        for key in params_dict:
            data["Parameters"][key] = params_dict[key]

        # Fill materials (Axi specific)
        materials_dict = create_materials_dict(confdata, finsulator, fconductor, NHelices, Nsections, NRings)

        if "Materials" in data:
            for key in materials_dict:
                data["Materials"][key] = materials_dict[key]
        else:
            data["Materials"] = materials_dict
        
        # TODO add BCs for elasticity

        # loop for Cooling BCs
        if args.model != 'mag':
            data["BoundaryConditions"]["heat"]["Robin"] = create_bcs_dict(NChannels, fcooling)

        #if args.model != 'thmagel':
        #    data["BoundaryConditions"]["elastic"]["Dirichlet"] = {"elasdir":{"markers" : boundary_Ring, "expr":0 }}

        if args.model != 'mag':
            # add flux_model for Flux_Channel calc
            with open(fflux, "r") as ftemplate:
                jsonfile = chevron.render(ftemplate, {'index_h': "0:%s" % str(NChannels)})
                jsonfile = jsonfile.replace("\'", "\"")
                mdata = json.loads(jsonfile)
                data["PostProcess"]["heat"]["Measures"]["Statistics"]["Flux_Channel%1%"] = mdata["Flux"]["Flux_Channel%1%"]
                for i in range(NHelices) :
                    data["PostProcess"]["heat"]["Measures"]["Statistics"]["MeanT_H{}".format(i+1)] = {"type" : ["min","max","mean"], "field":"temperature", "markers": {"name": "H{}_Cu%1%".format(i+1),"index1":index_Helices[i]}}

        if args.model != 'th':
            # Add Electrical Power by Helix
            for i in range(NHelices) :
                data["PostProcess"]["magnetic"]["Measures"]["Statistics"]["Power_H{}".format(i+1)] = {"type" : "integrate",
                    "expr":"2*pi*materials_sigma*(materials_U/2/pi)*(materials_U/2/pi)/x:materials_sigma:materials_U:x".format(i+1),
                    "markers": {"name": "H{}_Cu%1%".format(i+1),"index1":index_HelicesConductor[i]}}


        # save json (NB use x to avoid overwrite file)
        if args.datafile != None :
            outfilename = args.datafile.replace(".json","")
        if args.magnet != None :
            outfilename = magnet
        outfilename += "-" + args.method
        outfilename += "-" + args.model
        outfilename += "-" + args.phytype
        outfilename += "-" + args.geom
        outfilename += "-sim.json"

        with open(outfilename, "w") as out:
            out.write(json.dumps(data, indent = 4))

if __name__ == "__main__":
    main()
