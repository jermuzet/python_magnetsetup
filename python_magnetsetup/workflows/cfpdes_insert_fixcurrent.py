from typing import List, Union, Optional

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

# import tabulate
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

def update_U(params: dict, marker: str, target: float, val: float):
    return float(params[marker]['U']) * target/val
    pass

def update_dT():
    # compute dT as Power / rho *Cp * Flow(I)
    pass

def update_h():
    # compute h as Montgomery()
    pass

def getCurrent(df: pd.DataFrame, marker: str):
    return df[f"Statistics_Intensity_{marker}_integrate"].iloc[-1]

# get Power to recompute dTw and h
targetdefs = {
    "I": {
        "csv": 'heat.measures/values.csv', 
        "rematch": 'Statistics_Intensity_\w+_integrate', 
        "params": [('N','N_\w+')],
        "control_params": [('U', 'U_\w+', update_U)],
        "bc_params": [("dTw", "dTw", update_dT), ("hw", "hw", update_h)],
        "value": getCurrent
        }
}

def setTarget(name: str, params: dict, current: float, debug: bool = False):
    print(f"getTarget: workingdir={ os.getcwd() } name={name}")
    targets = {}
    for key in params:
        I_target = float(params[key]['N']) * current
        if debug:
            print(f"{key} turns: {params[key]['N']} target: {I_target}")
        targets[key] = I_target
    
    if debug: print(f"targets: {targets}")
    return targets

def getTarget(name: str, e, debug: bool = False):

    cwd = os.getcwd()
    print(f"getTarget: workingdir={ os.getcwd() } name={name}")
    defs = targetdefs[name]
    print(f"defs: {defs}")
    print(f"csv: {defs['csv']}")
    print(f"rematch: {defs['rematch']}")

    filename = str(cwd) + '/' + defs['csv']
    with open(filename, "r") as f:
        print(f"csv: {f.name}")
        filtered_df = post(f.name, defs['rematch'], debug)
    
    if debug and e.isMasterRank(): 
        print(filtered_df)
        for key in filtered_df.columns.values.tolist():
            print(key)
    
    return filtered_df

def init(args):
    e = feelpp.Environment(sys.argv, opts=tb.toolboxes_options("coefficient-form-pdes","cfpdes"))
    e.setConfigFile(args.cfgfile)

    if e.isMasterRank(): print("Create cfpdes")
    f = cfpdes.cfpdes(dim=2)

    if e.isMasterRank(): print("Init problem")
    f.init()
    # f.printAndSaveInfo()

    return (e, f)

def solve(e, f: str, args, objectif: str, paramsdict: dict, params: List[str], bc_params: List[str], targets: dict):
    if e.isMasterRank(): print(f"solve: workingdir={ os.getcwd() }")
    it = 0
    err_max = 2 * args.eps

    table = []
    headers = ['it']
    for key in paramsdict:
        for p in params:
            headers.append(f'{p}_{key}')
    headers.append('err_max')


    while err_max > args.eps and it < args.itermax :
        
        # Update new value of U_Hi_Cuj on feelpp's senvironment
        for key in paramsdict:
            for p in params:
                entry = f'{p}_{key}'
                val = float(paramsdict[key][p])
                # print(f"{entry}: {val}")
                f.addParameterInModelProperties(entry, val)
        f.updateParameterValues()

        if args.debug and e.isMasterRank():
            print("Parameters after change :", f.modelProperties().parameters())

        # Solve and export the simulation
        # try:
        f.solve()
        f.exportResults()
        # except:
        #    raise RuntimeError("cfpdes solver or exportResults fails - check feelpp logs for more info")

        # TODO: get csv to look for depends on cfpdes model used
        filtered_df = getTarget(objectif, e, args.debug)

        # TODO: define a function to handle error calc
        # and update depending on param 
        
        # print("compute error and update params")
        err_max = 0
        num = 0

        # logging in table
        table_ = [it]
        for key in targets:
            # TODO get f"Statistics_Intensity_{key}_integrate" from targetdfs['I']
            val = targetdefs[objectif]['value'](filtered_df, key)
            target = targets[key]
            err_max = max(abs(1 - val/target), err_max)
            # print(f"{key}: target: {target} ({type(target)}) val: {val} ({type(val)}) error: {abs(1 - val/target)}")
            # print(f"paramsdict[key]['U'] = {paramsdict[key]['U']} ({type(paramsdict[key]['U'])}")
            for p in targetdefs[objectif]['control_params']:
                table_.append(float(paramsdict[key][p[0]]))
                # TODO method to update control_param from from targetdfs['I']
                paramsdict[key][p[0]] = p[2](paramsdict, key, target, val)
        
        table_.append(err_max)

        if e.isMasterRank():
            print(f"it={it}, err_max={err_max}")
        table.append(table_)

        it += 1

    # Save table (need headers)
    # print(tabulate(table, headers, tablefmt="simple"))

    resfile = args.cfgfile.replace('.cfg', '-fixcurrent.csv')
    if e.isMasterRank(): 
        print(f"Export result to csv: {os.getcwd() + '/' + resfile}")
    with open(resfile,"w+") as f:
        df = pd.DataFrame(table, columns = headers)
        df.to_csv(resfile, encoding='utf-8')
    
    return paramsdict

def post(csv: str, rmatch: str, debug: bool = False):
    """
    extract data for csv result files
    
    eg: 
    rmatch= "Intensity_\w+_integrate"
    csv = ["cfpdes.heat.measures.csv", "cfpdes.magnetic.measures.csv"]
    """
    if debug:
        print(f"post: workingdir={ os.getcwd() }")
        print(f"post: csv={csv}")

    # Retreive current intensities
    df = pd.DataFrame()
    if debug: print("post: loading {csv_}")
    with open(csv, 'r') as f:
        _df = pd.read_csv(f, sep=",", engine='python')
        if debug:
            for key in _df.columns.values.tolist():
                print(key)

        tmp_df = _df.filter(regex=(rmatch))
        if debug: print(f"tmp_df: {tmp_df}")
            
        df = pd.concat([df, tmp_df], axis='columns')

    return df

def update(cwd: str, jsonmodel: str, paramsdict: dict, params: List[str], debug: bool=False):
    # Update tensions U
     
    os.chdir(cwd)
    print(f"update: workingdir={ os.getcwd() }")

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
    parameters = {}
    with open(jsonmodel, 'r') as jsonfile:
        dict_json = json.loads(jsonfile.read())
        parameters = dict_json['Parameters']

    params = {}
    bc_params = {}
    control_params = []
    for p in targetdefs['I']['control_params']:
        print(f"extract control params for {p[0]}")
        control_params.append(p[0])
        tmp = getparam(p[0], parameters, p[1], args.debug)
        params = Merge(tmp, params, args.debug)

    for p in targetdefs['I']['params']:
        print(f"extract compute params for {p[0]}")
        tmp = getparam(p[0], parameters, p[1], args.debug)
        params = Merge(tmp, params, args.debug)

    for p in targetdefs['I']['bc_params']:
        print(f"extract bc params for {p[0]}")
        tmp = getparam(p[0], parameters, p[1], args.debug)
        bc_params = Merge(tmp, bc_params, args.debug)
    
    print("params:", params)
    print("bc_params:", bc_params)

    # define targets
    targets = setTarget('I', params, args.current, args.debug)
    print("targets:", targets)
    
    # init feelpp env
    (feelpp_env, feel_pb) = init(args)
    
    # solve (output params contains both control_params and bc_params values )
    params = solve(feelpp_env, feel_pb, args, 'I', params, control_params, bc_params, targets)
    
    # update
    update(cwd, jsonmodel, params, control_params, args.debug)
    # update(cwd, jsonmodel, params, ['hw', 'Tw', 'dTw'], args.debug) for bc

if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
