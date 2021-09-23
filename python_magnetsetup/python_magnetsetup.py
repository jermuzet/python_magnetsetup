"""
Create template json model files for Feelpp/HiFiMagnet simu
From a yaml defintion file of an insert

Inputs:
* method: 
* time:
* model:
* cooling:

Output: 
* tmp.json

App setup is stored in a json file that defines
the mustache template to be used.

Default path:
magnetsetup.json
mustache templates
"""

import sys
import os

import math

import yaml
from python_magnetgeo import Helix
from python_magnetgeo import Ring
from python_magnetgeo import InnerCurrentLead
from python_magnetgeo import OuterCurrentLead
from python_magnetgeo import Insert

import chevron
import json

import argparse
import pathlib

command_line = None
parser = argparse.ArgumentParser("Create template json model files for Feelpp/HiFiMagnet simu")
parser.add_argument("yamlfile", help="input yaml file (ex. HL-31.yaml)")

parser.add_argument("--method", help="choose method (default is cfpdes", type=str,
                    choices=['cfpdes', 'CG', 'HDG', 'CRB'], default='cfpdes')
parser.add_argument("--time", help="choose time type", type=str,
                    choices=['static', 'transient'], default='static')
parser.add_argument("--geom", help="choose geom type", type=str,
                    choices=['Axi', '3D'], default='Axi')
parser.add_argument("--model", help="choose model type", type=str,
                    choices=['th', 'mag', 'thmag', 'thmagel'], default='thmagel')
parser.add_argument("--cooling", help="choose cooling type", type=str,
                    choices=['mean', 'grad'], default='mean')

parser.add_argument("--debug", help="activate debug", action='store_true')
parser.add_argument("--verbose", help="activate verbose", action='store_true')

args = parser.parse_args()
if args.debug:
    print(args)


# Get current dir
cwd = os.getcwd()

# Load magnetsetup config
default_path = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(default_path, 'magnetsetup.json'), 'r') as appcfg:
    magnetsetup = json.load(appcfg)

# Load yaml file for geo config
yamlfile = args.yamlfile
# print("yamlfile=%s" % yamlfile)

index_h = []
Nsections = []
Zmin = []
Zmax = []
Dh = []
Sh = []

with open(yamlfile, 'r') as cfgdata:
    cad = yaml.load(cfgdata, Loader = yaml.FullLoader)
    if isinstance(cad, Insert.Insert):
        NHelices = len(cad.Helices)
        R1 = []
        R2 = []
        Z1 = []
        Z2 = []
        for i,helix in enumerate(cad.Helices):
            hhelix = None
            with open(helix+".yaml", 'r') as f:
                hhelix = yaml.load(f, Loader = yaml.FullLoader)
            n_sections = len(hhelix.axi.turns)
            Nsections.append(n_sections)
            index_h.append([str(i+1), "1:%s" % str(n_sections+1), "[0,%s]" % str(n_sections+2)])

            R1.append(hhelix.r[0])
            R2.append(hhelix.r[1])
            Z1.append(hhelix.z[0])
            Z2.append(hhelix.z[1])

        Ri = cad.innerbore
        Re = cad.outerbore
        
        zm1 = Z1[0]
        zm2 = Z2[0]

        for i in range(NHelices):

            Zmin.append(min(Z1[i],zm1))
            Zmax.append(min(Z2[i],zm2))

            Dh.append(2*(R1[i]-Ri))
            Sh.append(math.pi*(R1[i]-Ri)*(R1[i]+Ri))

            Ri = R1[i]
            zm1 = Z1[i]
            zm2 = Z2[i]

        Zmin.append(zm1)
        Zmax.append(zm2)

        Dh.append(2*(Re-Ri))
        Sh.append(math.pi*(Re-Ri)*(Re+Ri))

        
        
    else:
        raise Exception("expected Insert yaml file")

# load mustache template file
json_model = magnetsetup[args.method][args.time][args.geom][args.model]["model"]
conductor_model = magnetsetup[args.method][args.time][args.geom][args.model]["conductor"]
insulator_model = magnetsetup[args.method][args.time][args.geom][args.model]["insulator"]
cooling_model = magnetsetup[args.method][args.time][args.geom][args.model]["cooling"][args.cooling]
flux_model = magnetsetup[args.method][args.time][args.geom][args.model]["cooling-post"][args.cooling]

# TODO create default path to mustache according to method, geom
template_path = os.path.join(default_path, "templates", args.method)
fmodel = os.path.join(template_path, json_model)
fconductor = os.path.join(template_path, conductor_model)
finsulator = os.path.join(template_path, insulator_model)
fcooling = os.path.join(template_path, cooling_model)
fflux = os.path.join(template_path, flux_model)

# copy json files to cwd (only for cfpdes)
from shutil import copyfile
material_generic_def = ["conductor", "insulator"]
material_generic_def.append("conductor-nosource") # only for transient with mqs
for jsonfile in material_generic_def:
    filename = magnetsetup[args.method][args.time][args.geom][args.filename][jsonfile]
    src = os.path.join(template_path, filename)
    dst = os.path.join(cwd, jsonfile + ".json")
    copyfile(src, dst)

with open(fmodel, "r") as ftemplate:
    jsonfile = chevron.render(ftemplate, {'index_h': index_h, 'imin': 0, 'imax': NHelices+1})
    jsonfile = jsonfile.replace("\'", "\"")
    # shall get rid of comments: //*
    
    # now tweak obtained json
    data = json.loads(jsonfile)
    
    # global parameters
    # Tini, Aini for transient cases??

    params_dict = {}

    # for cfpdes only
    if args.method == "cfpdes":
        params_dict["bool_laplace"] = "1"
        params_dict["bool_dilatation"] = "1"
    
    params_dict["h"] = "h"
    params_dict["Tw"] = "Tin:Tin"
    params_dict["dTw"] = "(Tout-Tin)/2.:Tin:Tout"

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
                params_dict["H%d_Cu%d" % (i+1, j+1)] = "1"

    for key in params_dict:
        data["Parameters"][key] = params_dict[key]

    # materials (Axi specific)
    materials_dict = {}
    for i in range(NHelices):
        # section j==0:  treated as insulator in Axi
        with open(finsulator, "r") as ftemplate:
            jsonfile = chevron.render(ftemplate, {'name': "H%d_Cu%d" % (i+1, 0)})
            jsonfile = jsonfile.replace("\'", "\"")
            # shall get rid of comments: //*
            mdata = json.loads(jsonfile)
            materials_dict["H%d_Cu%d" % (i+1, 0)] = mdata["H%d_Cu%d" % (i+1, 0)]

        # load conductor template
        for j in range(1,Nsections[i]+1):
            with open(fconductor, "r") as ftemplate:
                jsonfile = chevron.render(ftemplate, {'name': "H%d_Cu%d" % (i+1, j)})
                jsonfile = jsonfile.replace("\'", "\"")
                # shall get rid of comments: //*
                mdata = json.loads(jsonfile)
                materials_dict["H%d_Cu%d" % (i+1, j)] = mdata["H%d_Cu%d" % (i+1, j)]

        # section j==Nsections+1:  treated as insulator in Axi
        with open(finsulator, "r") as ftemplate:
            jsonfile = chevron.render(ftemplate, {'name': "H%d_Cu%d" % (i+1, Nsections[i]+1)})
            jsonfile = jsonfile.replace("\'", "\"")
            # shall get rid of comments: //*
            mdata = json.loads(jsonfile)
            materials_dict["H%d_Cu%d" % (i+1, 0)] = mdata["H%d_Cu%d" % (i+1, Nsections[i]+1)]

    # loop for Rings:  treated as insulator in Axi
    for i in range(NHelices):
        with open(finsulator, "r") as ftemplate:
            jsonfile = chevron.render(ftemplate, {'name': "R%d" % (i+1)})
            jsonfile = jsonfile.replace("\'", "\"")
            # shall get rid of comments: //*
            mdata = json.loads(jsonfile)
            materials_dict["R%d" % (i+1)] = mdata["R%d" % (i+1)]

    # TDO loop for Plateau (Axi specific)
    
    data["Materials"] = materials_dict

    # loop for Cooling BCs
    bcs_dict = {}
    for i in range(NHelices+1):
        # load insulator template for j==0
        with open(fcooling, "r") as ftemplate:
            jsonfile = chevron.render(ftemplate, {'i': i})
            jsonfile = jsonfile.replace("\'", "\"")
            # shall get rid of comments: //*
            mdata = json.loads(jsonfile)
            bcs_dict["Channel%d" % i] = mdata["Channel%d" % i]
    data["BoundaryConditions"]["heat"]["Robin"] = bcs_dict

    # TODO add BCs for elasticity
    # TODO add flux_model for Flux_Channel calc

# save json
# temporary save json: NB use x to avoid overwrite file
    out = open("tmp.json", "w")
    out.write(json.dumps(data, indent = 4))

    
