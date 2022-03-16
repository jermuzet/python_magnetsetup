from lib2to3.pgen2.pgen import DFAState
from typing import List, Union

import sys
import os
import re


import feelpp
import feelpp.toolboxes.core as tb
import feelpp.toolboxes.cfpdes as cfpdes

import pandas as pd
import math
import csv
import numpy as np
import json

import yaml

from python_magnetgeo import MSite, Insert, Bitter, Supra
from python_magnetgeo import python_magnetgeo

import tabulate
import itertools

import argparse

def Merge(dict1: dict, dict2: dict, debug: bool = False) -> dict:

    if debug : 
        print(f"dict1: {dict1}")
        print(f"dict2: {dict2}")

    if isinstance(dict2, type(None)):
        return dict1

    for key1 in dict1:
        if key1 in dict2:
            dict2[key1].update(dict1[key1])
        else:
            dict2[key1] = dict1[key1]

    if debug : 
        print(f"dict1: {dict1}")
        print(f"dict2: {dict2}")
            

    if debug : 
        print(f"res: {dict2}")
    return dict2

def getparam(param:str, parameters: dict, rmatch: str, debug: bool = False ):
    """
    """
    if debug:
        print(f"getparam: {param} ====== Start")
    
    n = 0
    val = {}

    regex_match = re.compile(rmatch)
    for p in parameters.keys() :
        if regex_match.fullmatch(p):
            marker = p.split(param + '_')[-1]
            if debug:
                print(f"match {p}: {marker}")
            val[marker] = { param: parameters[p]}
            if debug:
                print(f"{p}: {parameters[p]}")
    
    if debug:
        print(f"val: {val}")
        print(f"getparam: {param} ====== Done")
    return (val)

def setTargets(params: dict, current: float, debug: bool = False):
    targets = {}
    for key in params:
        I_target = float(params[key]['N']) * current
        if debug:
            print(f"{key} turns: {params[key]['N']} target: {I_target}")
        targets[key] = I_target
    
    if debug: print(f"targets: {targets}")
    return targets

def init(args):
    e = feelpp.Environment(sys.argv, opts=tb.toolboxes_options("coefficient-form-pdes","cfpdes"))
    e.setConfigFile(args.cfgfile)

    print("Create cfpdes")
    f = cfpdes.cfpdes(dim=2)

    print("Init problem")
    f.init()
    
    return (e, f)

def solve(e, f: str, args, paramsdict: dict, params: List[str], targets: dict):
    it = 0
    err_max = 0

    U = []
    table = []
    while err_max > args.eps and it < args.itmax :

        # Update new value of U_Hi_Cuj on feelpp's senvironment
        num = 0
        for key in paramsdict:
            for p in params:
                entry = f'{p}_{key}'
                f.addParameterInModelProperties(entry, paramsdict[entry])
                U[num] = paramsdict[entry]
                num += 1
        f.updateParameterValues()

        # Need to flatten U:
        U_ = list(itertools.chain.from_iterable(U))
        table_ = [it]
        for d in U_:
            table_.append(d)

        if args.debug and e.isMasterRank():
            print("Parameters after change :", f.modelProperties().parameters())

        # Solve and export the simulation
        f.solve()
        f.exportResults()

        filtered_df = post(["cfpdes.heat.measures.csv", "cfpdes.magnetic.measures.csv"], "Intensity_\w+_integrate")
        if args.debug and e.isMasterRank():
            print(filtered_df)
        # df.select(lambda col: col.startswith('d'), axis=1)
        I = filtered_df.to_numpy()
        I = np.array( filtered_df.iloc[it] )

        # TODO: define a function to handle error calc
        err_max = 0
        num = 0
        for key in targets:
            val = filtered_df[f"Intensity_{key}_integrate"]
            target = targets[key]
            err_max = max(abs(1 - val/target), err_max)
            params[key]['U'] *= target/val

        if e.isMasterRank():
            print(f"it={it}, err_max={err_max}")
        table.append(err_max)
        table.append(table_)

        it += 1

    # Save results
    print("Export result to csv")

    data_U = list(itertools.chain.from_iterable(U))
    data_U = pd.DataFrame(data_U)

    with open("U.csv","w+") as resfile:
        resfile.write(data_U.to_csv(index=False))

    return U

def update(jsonmodel: str, paramsdict: dict, params: List[str], debug: bool=False):
    # Update tensions U

    with open(jsonmodel, 'r') as jsonfile:
        dict_json = json.loads(jsonfile.read())
        parameters = dict_json['Parameters']
    
    for key in paramsdict:
        for p in params:
            if debug:
                print(f"param: {p}")
                print(f"init {p}_{key} = {parameters[f'{p}_{key}']}")
                print(f"after {p}_{key} = {paramsdict[key][p]}")
            parameters[f'{p}_{key}'] = paramsdict[key][p]

    new_name_json =  jsonmodel.replace('.json', '-fixcurrent.json')

    with open(new_name_json, 'w+') as jsonfile:
        jsonfile.write(json.dumps(dict_json, indent=4))

    return 0

def post(csv: List[str], rmatch: str):
    """
    extract data for csv result files
    
    eg: 
    rmatch= "Intensity_\w+_integrate"
    csv = ["cfpdes.heat.measures.csv", "cfpdes.magnetic.measures.csv"]
    """
    
    # Retreive current intensities
    df = pd.DataFrame()
    for f in csv:
        if os.path.isfile(f):
            tmp_df = pd.read_csv(f, sep=",\s+|\s+", engine='python')
        df = pd.concat([df, tmp_df], axis='columns')

    filtered_df = df.filter(regex=(rmatch))

    
def main():
    
    command_line = None
    parser = argparse.ArgumentParser(description="Cfpdes HiFiMagnet Fully Coupled model")
    parser.add_argument("cfgfile", help="input cfg file (ex. HL-31.cfg)")
    parser.add_argument("--wd", help="set a working directory", type=str, default="")
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

    # Load cfg as config
    import configparser
    feelpp_config = configparser.ConfigParser()
    with open(args.cfgfile, 'r') as inputcfg:
        feelpp_config.read_string('[DEFAULT]\n[main]\n' + inputcfg.read())
        if args.debug:
            print("feelpp_cfg:", feelpp_config['main'])
    
            for section in feelpp_config.sections():
                print("section:", section)

        # TODO get json for material def
        jsonmodel = feelpp_config['cfpdes']['filename']
        jsonmodel = jsonmodel.replace(r"$cfgdir/",'')
        if args.debug:
            print(f"jsonmodel={jsonmodel}")

    # Get Parameters from JSON model file
    params = {}
    with open(jsonmodel, 'r') as jsonfile:
        dict_json = json.loads(jsonfile.read())
        parameters = dict_json['Parameters']

        params = getparam("U", parameters, 'U_\w+', args.debug)
        
        tmp = getparam("N", parameters, 'N_\w+', args.debug)
        params = Merge(tmp, params, args.debug)
        
    # define targets
    targets = setTargets(params, args.current, True) # args.debug)
    
    # init feelpp env
    # (e, f) = init(args)
    
    # solve
    # solve(f, args, params, ["U"]  targets)
    
    # update
    update(jsonmodel, params, ["U"])

if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
