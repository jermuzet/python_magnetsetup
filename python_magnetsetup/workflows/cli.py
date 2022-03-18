import sys
import os
import argparse
import configparser

import json

from .params import targetdefs, setTarget, getparam, update, Merge
from .solver import init, solve

def main():
    
    # TODO: current several args depending of cfgfile nature (aka magnet or msite)
    epilog = "Only work for magnet of insert type\n" \
             "This workflow actually fix current and compute cooling BCs using Montgomery correlation with an average water velocity\n"
    
    command_line = None
    parser = argparse.ArgumentParser(description="Cfpdes HiFiMagnet Fully Coupled model")
    parser.add_argument("cfgfile", help="input cfg file (ex. HL-31.cfg)")
    parser.add_argument("--wd", help="set a working directory", type=str, default="")
    parser.add_argument("--current", help="specify requested current (default: 31kA)", nargs='?', metavar='Current', type=float, default=[31.e+3])
    parser.add_argument("--cooling", help="choose cooling type", type=str,
                    choices=['mean', 'grad', 'meanH', 'gradH'], default='mean')
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

    print("Current:", args.current)

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

    # Get Bc params
    for p in [ 'HeatCoeff', 'DT' ]:
        print(f"extract bc params for {p}")
        for bc_p in targetdefs[p]['params']:
            print(f"{bc_p[0]}")
            tmp = getparam(bc_p[0], parameters, bc_p[1], args.debug)
            bc_params = Merge(tmp, bc_params, args.debug)
        print(f"extract bc control_params for {p}")
        for bc_p in targetdefs[p]['control_params']:
            print(f"{bc_p[0]}")
            tmp = getparam(bc_p[0], parameters, bc_p[1], args.debug)
            bc_params = Merge(tmp, bc_params, args.debug)
    
    # print("params:", params)
    print("bc_params:", bc_params)

    # define targets
    # TODO for insert + bitter [ + supra] ???
    # shall build targetdefs on the fly
    # insert: IH, params N_H\* control_params U_H\* 'Statistics_Intensity_H\w+_integrate'
    # bitter: IB, 
    targets = setTarget('I', params, args.current[0], args.debug)
    # print("targets:", targets)
    
    # init feelpp env
    (feelpp_env, feel_pb) = init(args)
    
    # solve (output params contains both control_params and bc_params values )
    (params, bcparams) = solve(feelpp_env, feel_pb, args, 'I', params, control_params, bc_params, targets)
    
    # update
    update(cwd, jsonmodel, params, control_params, bcparams, args.current[0], args.debug)
    # update(cwd, jsonmodel, params, ['hw', 'Tw', 'dTw'], args.debug) for bc

if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
