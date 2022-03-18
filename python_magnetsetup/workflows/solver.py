from typing import List, Union, Optional

import feelpp
import feelpp.toolboxes.core as tb
import feelpp.toolboxes.cfpdes as cfpdes

import sys
import os
import pandas as pd

from .params import targetdefs, getTarget
from .real_methods import pressure, umean, montgomery

def init(args):
    e = feelpp.Environment(sys.argv, opts=tb.toolboxes_options("coefficient-form-pdes","cfpdes"))
    e.setConfigFile(args.cfgfile)

    if e.isMasterRank(): print("Create cfpdes")
    f = cfpdes.cfpdes(dim=2)

    if e.isMasterRank(): print("Init problem")
    f.init()
    # f.printAndSaveInfo()

    return (e, f)

def solve(e, f: str, args, objectif: str, paramsdict: dict, params: List[str], bcs_params: dict, targets: dict):
    if e.isMasterRank(): print(f"solve: workingdir={ os.getcwd() }")
    it = 0
    err_max = 2 * args.eps

    table = []
    headers = ['it']
    for key in paramsdict:
        for p in params:
            headers.append(f'{p}_{key}')
    headers.append('err_max')

    bcparams = {}
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
        if e.isMasterRank():
            print(f"Compute error on {objectif}")
        table_ = [it]
        for key in targets:
            # TODO get f"Statistics_Intensity_{key}_integrate" from targetdfs['I']
            val = targetdefs[objectif]['value'][0](filtered_df, key)
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

                
        # update bcs 
        if e.isMasterRank():
            print("Update Bcs")
        flux_df = getTarget('Flux', e, args.debug)
        power_df = getTarget('PowerH', e, args.debug)
        Power = power_df.iloc[-1].sum()
        if args.debug and e.isMasterRank():
            print('PowerH:', Power, "df:", power_df)
            print('Power: df:', getTarget('Power', e, args.debug))
        Pressure = pressure(args.current[0])

        Dh = []
        Sh = []
        for p in bcs_params:
            if "Dh" in p: Dh.append(float(bcs_params[p]['Dh']))
            if "Sh" in p: Sh.append(float(bcs_params[p]['Sh']))

        Umean = umean(args.current[0], sum(Sh)/len(Sh))
        for i,(d, s) in enumerate(zip(Dh, Sh)):
            PowerCh = flux_df[f'Statistics_Flux_Channel{i}_integrate'].iloc[-1]
            if args.debug and e.isMasterRank():
                print(f"Channel{i}: umean={Umean}, Dh={d}, Sh={s}, Power={PowerCh}")
            Tw = float(bcs_params[f'Tw{i}']['TwH'])
            dTwi = targetdefs['DT']['value'][1](args.current[0], PowerCh, Tw, Pressure)
            hi = targetdefs['HeatCoeff']['value'][1](d, Umean, Tw)
            f.addParameterInModelProperties(f'dTw{i}', dTwi)
            f.addParameterInModelProperties(f'h{i}', hi)        
            if args.debug and e.isMasterRank():
                print(f'dTw{i}:', dTwi)
                print(f'hw{i}:', hi)
            bcparams[f'dTw{i}'] = dTwi
            bcparams[f'h{i}'] = hi

        Tw = float(bcs_params['Tw']['Tw'])
        dTw = targetdefs['DT']['value'][1](args.current[0], Power, Tw, Pressure)
        hw = montgomery(Tw, Umean, sum(Dh)/len(Dh))
        f.addParameterInModelProperties("dTw", dTw)
        f.addParameterInModelProperties("hw", hw )        
        if args.debug and e.isMasterRank():
            print('dTw:', targetdefs['DT']['value'][1](args.current[0], Power, Tw, Pressure))
            print('hw:', montgomery(Tw, Umean, sum(Dh)/len(Dh) ))
        bcparams['dTw'] = dTw
        bcparams['hw'] = hw

        f.updateParameterValues()


        it += 1

    # Save table (need headers)
    # print(tabulate(table, headers, tablefmt="simple"))

    resfile = args.cfgfile.replace('.cfg', '-fixcurrent.csv')
    if e.isMasterRank(): 
        print(f"Export result to csv: {os.getcwd() + '/' + resfile}")
    with open(resfile,"w+") as f:
        df = pd.DataFrame(table, columns = headers)
        df.to_csv(resfile, encoding='utf-8')
    
    return (paramsdict, bcparams)

