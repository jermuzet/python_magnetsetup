import sys
import os
import re
# import feelpp
# import feelpp.toolboxes.core as tb
# import feelpp.toolboxes.cfpdes as cfpdes

import pandas as pd
import math
import csv
import numpy as np
import json

import yaml

from python_magnetgeo import MSite, Insert, Bitter, Supra
from python_magnetgeo import get_main_characteristics, get_cut_characteristics

import tabulate
import itertools

import argparse

def getparam(param:str, parameters: dict, rsearch: str, rmatch: str,  ):
    """
    """
    print(f"getparam: {param} ====== Start")
    
    n = 0
    val = []

    regex_search = re.compile(rsearch)
    regex_match = re.compile(rmatch)
    for p in parameters.keys() :
        if regex_match.fullmatch(p):
            print(f"{p}: {parameters[p]}, {regex_search.findall(p)}")
            val.append(parameters[p])
            n = max(int(regex_search.findall(p)[0]), n)
    
    print(f"val: {val}")
    print(f"n: {n}")
    print(f"getparam: {param} ====== Done")
    return (val, n)

command_line = None
parser = argparse.ArgumentParser(description="Cfpdes HiFiMagnet Fully Coupled model")
parser.add_argument("cfgfile", help="input cfg file (ex. HL-31.cfg)")
parser.add_argument("--wd", help="set a working directory", type=str, default="")
parser.add_argument("--geo", help="specify geometry yaml file (use Auto to automatically retreive yaml filename from xao, default is None)", type=str, default="None")
parser.add_argument("--mtype", help="specify type (default: Magnet)", choices=["Msite", "Magnet"], default="Magnet")
parser.add_argument("--current", help="specify requested current (default: 31kA)", type=float, default=31000)
parser.add_argument("--eps", help="specify requested tolerance (default: 1.e-3)", type=float, default=1.e-3)
parser.add_argument("--itermax", help="specify maximum iteration (default: 10)", type=int, default=10)
parser.add_argument("--debug", help="activate debug", action='store_true')
parser.add_argument("--verbose", help="activate verbose", action='store_true')

args = parser.parse_args()
if args.debug:
    print(args)

cwd = os.getcwd()
if args.wd:
    os.chdir(args.wd)

eps = args.eps
itmax = args.itermax
I0 = args.current

# Load cfg as config
import configparser
feelpp_config = configparser.ConfigParser()
with open(args.cfgfile, 'r') as inputcfg:
    feelpp_config.read_string('[DEFAULT]\n[main]\n' + inputcfg.read())
    print("feelpp_cfg:", feelpp_config['main'])
    for section in feelpp_config.sections():
        print("section:", section)

    # TODO get json for material def
    jsonmodel = feelpp_config['cfpdes']['filename']
    jsonmodel = jsonmodel.replace(r"$cfgdir/",'')
    print(f"jsonmodel={jsonmodel}")

# Load yaml file for geo config
yamlfile = ""
if args.geo == 'Auto':
    yamlfile = args.cfgfile.replace(".cfg",".yaml")
else:
    yamlfile = args.geo
print("yamlfile=%s" % yamlfile)

U = []
U_headers = ["it"]
table = []

NHelices = 0
Sections = []
N_t = []
sigma = []

# Load yaml file for geo config
yamlfile = ""
if args.geo != "None":
    if args.geo == 'Auto':
        yamlfile = args.cfgfile.replace(".cfg",".yaml")
    else:
        yamlfile = args.geo
    print("yamlfile=%s" % yamlfile)

    with open(jsonmodel, 'r') as jsonfile:
        dict_json = json.loads(jsonfile.read())

    regex_search_sigma0 = re.compile('\d+(?=\/(1+alpha\*(heat_T\-T0)))')

    with open(yamlfile, 'r') as cfgdata:
        cad = yaml.load(cfgdata, Loader = yaml.FullLoader)
        if isinstance(cad, MSite): # MSite.MSite
            print(f"Load MSite: {cfgdata.name}")
            
        if isinstance(cad, Bitter): # Bitter.Bitter
            print(f"Load Bitter: {cfgdata.name}")
            
        if isinstance(cad, Supra): # Supra.Supra
            print(f"Load Supra: {cfgdata.name}")
            
        if isinstance(cad, Insert): # Insert.Insert
            print(f"Load Insert: {cfgdata.name}")
            gdata = get_main_characteristics(cad)
            (NHelices, NRings, NChannels, Nsections, R1, R2, Z1, Z2, Zmin, Zmax, Dh, Sh) = gdata
            (Nturns, Pitch) = get_cut_characteristics(cad)
            
            for i,helix in enumerate(cad.Helices):
                # Init value for U
                U_H = []
                sigma.append([])
                for j in range(n_sections):
                    sigmai = dict_json["Materials"][f"H{i+1}_Cu{j+1}"]['sigma0']
                    sigma[i].append(float(sigmai))
                    
                    I_s = I0 * Nturns_h[i][j]
                    j1 = I_s / (math.log(R2[i]/R1[i]) * (Pitch_h[i][j] * Nturns_h[i][j]) )
                    U_s = 2 * math.pi * R1[i] * j1 / sigma[i][j]
                    U_H.append(U_s)
                    U_headers.append(f"U_H{i+1}S{j+1}")
                    if args.debug:
                        print(f"I[{i}][{j}]={I_s}")
                
                U.append(U_H)
                N_t.append(hhelix.axi.turns)
        
        else:
            raise Exception(f"{type(cad)} unsupported type of geometry")

else:
    # Get Parameters from JSON model file
    with open(jsonmodel, 'r') as jsonfile:
        dict_json = json.loads(jsonfile.read())
        parameters = dict_json['Parameters']

    # Get number of Helices and number of Sections
    (Ut, NHelices) = getparam("U", parameters, '(?<=U_H)\d*(?=_Cu)', 'U_H\d*_Cu\d*') 
    print(f"Ut: {type(Ut)}")

    for p in parameters:
        regex_match= re.compile('U_H\d*_Cu\d*')
        if regex_match.fullmatch(p):
            index = re.findall(r'\d+', p)
            print(f"match {p}, findall {index}")
            
    for i in range(1,NHelices+1):
        regex_search = re.compile('(?<=U_H'+str(i)+'_Cu)\d*')
        regex_match= re.compile('U_H'+str(i)+'_Cu\d*')
        Sections.append(0)
        for param in parameters.keys() :
            if regex_match.fullmatch(param):
                Sections[-1] = max(int(regex_search.findall(param)[0]), Sections[-1])
    print(f"Sections: {Sections}")
    
    # Get U for Helices
    for i in range(NHelices):
        U.append([])
        N_t.append([])
        for j in range(0, Sections[i]):
            U[i].append(float(dict_json["Parameters"]["U_H{}_Cu{}".format(int(i+1),int(j+1))]))
            U_headers.append("U_H%dS%d" % (i+1, j+1))
            N_t.append(float(dict_json["Parameters"]["N_H{}_Cu{}".format(int(i+1),int(j+1))]))

U_headers.append("Error_max")

# For Axi model

# e = feelpp.Environment(sys.argv, opts=tb.toolboxes_options("coefficient-form-pdes","cfpdes"))
# e.setConfigFile(args.cfgfile)

# print("Create cfpdes")
# f = cfpdes.cfpdes(dim=2)

# print("Init problem")
# f.init()

os.chdir(cwd)

# err_max = 2*eps
# it = 0

# while err_max > eps and it < itmax :

#     # Update new value of U_Hi_Cuj on feelpp's senvironment
#     for i in range(NHelices):
#         for j in range(Sections[i]):
#             f.addParameterInModelProperties(f"U_H{int(i+1)}_Cu{int(j+1)}", U[i][j])
#     f.updateParameterValues()

#     # Need to flatten U:
#     U_ = list(itertools.chain.from_iterable(U))
#     table_ = [it]
#     for d in U_:
#         table_.append(d)

#     if args.debug and e.isMasterRank():
#         print("Parameters after change :", f.modelProperties().parameters())

#     # Solve and export the simulation
#     f.solve()
#     f.exportResults()

#     # Retreive current intensities
#     df = pd.DataFrame()
#     if os.path.isfile("cfpdes.heat.measures.csv"):
#         df = pd.read_csv("cfpdes.heat.measures.csv", sep=",\s+|\s+", engine='python')
#     if os.path.isfile("cfpdes.magnetic.measures.csv"):
#         df_magnetic = pd.read_csv("cfpdes.magnetic.measures.csv", sep=",\s+|\s+", engine='python')
#         df = pd.concat([df, df_magnetic], axis='columns')

#     filtered_df = df.filter(regex=("Statistics_Intensity_H\d+_Cu\d+_integrate"))
    
#     if args.debug and e.isMasterRank():
#         print(filtered_df)
#     # df.select(lambda col: col.startswith('d'), axis=1)
#     I = filtered_df.to_numpy()
#     I = np.array( filtered_df.iloc[it] )

#     err_max = 0
#     num = 0
#     for i in range(NHelices):
#         for j in range(Sections[i]):
#             I_s = I[num]
#             I_target = float(N_t[i][i]) * I0
#             err_max = max(abs(I_s/I_target-1), err_max)
#             U[i][j] *= I_target/I_s
#             num += 1

#     if e.isMasterRank():
#         print("it={}, err_max={}".format(it, err_max))
#     table_.append(err_max)
#     table.append(table_)

#     it += 1

# Save results
print("Export result to csv")

data_U = list(itertools.chain.from_iterable(U))
data_U = pd.DataFrame(data_U)

with open("U.csv","w+") as resfile:
    resfile.write(data_U.to_csv(index=False))

# Update tensions U
for i in range(NHelices):
    for j in range(Sections[i]):
        parameters[f"U_H{int(i+1)}_Cu{int(j+1)}"] = U[i][j]

# Create name of new JSON file
new_name_json =  jsonmodel.replace('.json', '-fixcurrent.json')

with open(new_name_json, 'w+') as jsonfile:
    jsonfile.write(json.dumps(data_json, indent=4))
