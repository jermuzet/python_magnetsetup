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

    if e.isMasterRank(): print("Create cfpdes")
    f = cfpdes.cfpdes(dim=2)

    if e.isMasterRank(): print("Init problem")
    f.init()
    # f.printAndSaveInfo()

    return (e, f)

def solve(e, f: str, args, paramsdict: dict, params: List[str], targets: dict):
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
        filtered_df = post(["heat.measures/values.csv"], "Statistics_Intensity_\w+_integrate", args.debug)
        if args.debug and e.isMasterRank(): 
            print(filtered_df)
            for key in filtered_df.columns.values.tolist():
                print(key)

        # df.select(lambda col: col.startswith('d'), axis=1)
        # I = filtered_df.to_numpy()
        # I = np.array( filtered_df.iloc[it] )

        # TODO: define a function to handle error calc
        # and update depending on param 
        
        # print("compute error and update params")
        err_max = 0
        num = 0

        # logging in table
        table_ = [it]
        for key in targets:
            val = filtered_df[f"Statistics_Intensity_{key}_integrate"].iloc[-1]
            target = targets[key]
            err_max = max(abs(1 - val/target), err_max)
            # print(f"{key}: target: {target} ({type(target)}) val: {val} ({type(val)}) error: {abs(1 - val/target)}")
            # print(f"paramsdict[key]['U'] = {paramsdict[key]['U']} ({type(paramsdict[key]['U'])}")
            table_.append(float(paramsdict[key]['U']))
            paramsdict[key]['U'] = float(paramsdict[key]['U']) * target/val
        
        table_.append(err_max)

        if e.isMasterRank():
            print(f"it={it}, err_max={err_max}")
        table.append(table_)

        it += 1

    # Save table (need headers)
    # print(tabulate(table, headers, tablefmt="simple"))
    if e.isMasterRank(): print("Export result to csv")

    resfile = args.cfgfile.replace('.cfg', '-fixcurrent.csv')
    with open(resfile,"w+") as f:
        df = pd.DataFrame(table, columns = headers)
        df.to_csv(resfile, encoding='utf-8')
    
    return paramsdict

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

def post(csv: List[str], rmatch: str, debug: bool = False):
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
    for csv_ in csv:
        if debug: print("post: loading {csv_}")
        with open(csv_, 'r') as f:
            _df = pd.read_csv(f, sep=",", engine='python')
            if debug:
                for key in _df.columns.values.tolist():
                    print(key)

            tmp_df = _df.filter(regex=(rmatch))
            if debug: print(f"tmp_df: {tmp_df}")
            
        df = pd.concat([df, tmp_df], axis='columns')

    return df

    
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
    targets = setTargets(params, args.current, args.debug)
    
    # init feelpp env
    (feelpp_env, feel_pb) = init(args)
    
    # solve
    params = solve(feelpp_env, feel_pb, args, params, ["U"],  targets)
    
    # update
    update(cwd, jsonmodel, params, ["U"], args.debug)

if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
