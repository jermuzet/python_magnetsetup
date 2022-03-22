"""Console script for python_magnetsetup."""
import argparse
from argparse import RawTextHelpFormatter

import sys
import os

from .setup import setup, setup_cmds
from .objects import load_object, load_object_from_db
from .config import appenv, loadconfig, supported_methods, supported_models

def fabric(machine: str, workingdir: str, args, cfgfile: str, jsonfile: str, meshfile: str, tarfilename:str, cmds: dict):
    """
    run cmds on machine
    """
    from fabric import Connection

    cwd = os.getcwd()
    
    # test fabric
    # TODO inhibit auto mode for Transient and 3D cases
    if args.auto:
        print(f"\n\n=== Testing automatic run on {machine} ===")
        connection_ = Connection(f'{machine}')
        if connection_.run('hostname').exited != 0:
            raise Exception(f"cannot connect to {machine}")
        result = connection_.run('hostname', hide=True)
        result = connection_.run('lsb_release -cs', hide=True)
        result = connection_.run('pwd', hide=True)
        homedir = result.stdout.strip()
        print(f"{machine}: homedir={homedir}")
        result = connection_.run(f'[ -d {homedir}/{workingdir} ] && echo 0 || echo 1')
    
        if result.stdout.strip() == '1':
            connection_.run(f'mkdir -p {workingdir}')
            connection_.put(f'{tarfilename}', remote=f'{homedir}/{workingdir}')
            connection_.run(f'cd {homedir}/{workingdir} && tar -zxvf {tarfilename}')
            for cmd in cmds:
                if not cmd in ['Pre', 'Run', 'Python', 'Workflow']:
                    connection_.run(f"cd {homedir}/{workingdir} && {cmds['Pre']} && {cmds[cmd]}")

            connection_.run(f'ls -lrth {homedir}/{workingdir}/data/geometries/{meshfile}')
            
            # TODO change NP for cmds Run depending on method and meshfile size
            connection_.run(f"cd {homedir}/{workingdir} && {cmds['Run']}")

            #
            # could also do something like:
            # if cmd in ['CAD', 'Mesh']:
            #    connection_.run(f"cd {homedir}/{workingdir} && {cmds[cmd]}", env={'HIFIMAGNET': f'{hifimagnet}'})

            # TODO some basic post operation
            # TODO store simu in db????
        else:
            raise Exception(f'python_magnetsetup/cli: {workingdir} already exists on {machine}')

        print("pwd", os.getcwd())
        for f in [cfgfile, jsonfile, tarfilename]:
            print(f'Remove {f} ({type(f)}')
            os.unlink(os.path.join(cwd, f))

    return 0
    
def main():

    # TODO get available model from magnetsetup.json

    #  
    # epilog = "The choice of model is actually linked with the choosen method following this table\n" \
    #          f"cfpdes (Axi, Static): {supported_models(MyEnv, 'cfpdes', 'Axi', 'static')}\n" \
    #          f"cfpdes (Axi, Transient): {supported_models(MyEnv, 'cfpdes', 'Axi', 'transient')}\n" \
    #          f"cfpdes (3D, Static): {supported_models(MyEnv, 'cfpdes', '3D', 'transient')}\n" \
    #          f"cfpdes (3D, Transient): {supported_models(MyEnv, 'cfpdes', 'Axi', 'transient')}\n" \
    #          "CG (3D only): thelec\n" \
    #          "HDG (3D only): thelec\n" \
    #          "" \
    #          "NB: for cfpdes you must use a linear case as a starting point for a nonlinear case"    

    # load appenv
    AppCfg = loadconfig()
    
    comment = ""
    actual_models = []
    for m in supported_methods(AppCfg):
        for g in ['Axi', '3D']:
            for t in ['static', 'transient']:
                l_ = supported_models(AppCfg, m, g, t)
                if l_:
                    actual_models += l_
                    comment += f"{m} ({g}, {t}): {l_}\n"  
    #  
    epilog = "The choice of model is actually linked with the choosen method following this table\n" \
             f"{comment}\n" \
             "" \
             "NB: for cfpdes you must use a linear case as a starting point for a nonlinear case"    


    # Manage Options
    command_line = None
    parser = argparse.ArgumentParser(formatter_class=RawTextHelpFormatter,
                                     description="Create json modelfiles for Feelpp/HiFiMagnet simu from templates",
                                     epilog=epilog)
    parser.add_argument("--datafile", help="input data file (ex. HL-34-data.json)", default=None)
    parser.add_argument("--wd", help="set a working directory", type=str, default="")
    parser.add_argument("--magnet", help="Magnet name from magnetdb (ex. HL-34)", default=None)
    parser.add_argument("--msite", help="MSite name from magnetdb (ex. HL-34)", default=None)

    parser.add_argument("--method", help="choose method (default is cfpdes)", type=str,
                    choices=supported_methods(AppCfg), default='cfpdes')
    parser.add_argument("--time", help="choose time type", type=str,
                    choices=['static', 'transient'], default='static')
    parser.add_argument("--geom", help="choose geom type", type=str,
                    choices=['Axi', '3D'], default='Axi')
    parser.add_argument("--model", help="choose model type (default is thelec)", type=str,
                    choices=actual_models, default='thelec')
    parser.add_argument("--nonlinear", help="force non-linear", action='store_true')
    parser.add_argument("--cooling", help="choose cooling type", type=str,
                    choices=['mean', 'grad', 'meanH', 'gradH'], default='mean')
    parser.add_argument("--scale", help="scale of geometry", type=float, default=1e-3)

    parser.add_argument("--auto", help="activate auto mode", action='store_true')
    parser.add_argument("--debug", help="activate debug", action='store_true')
    parser.add_argument("--verbose", help="activate verbose", action='store_true')
    args = parser.parse_args()

    # if args.debug:
    #    print("Arguments: " + str(args._))
    
    # Get current dir
    cwd = os.getcwd()
    if args.wd:
        os.chdir(args.wd)

    # make datafile/[magnet|msite] exclusive one or the other
    if args.magnet != None and args.msite:
        print("cannot specify both magnet and msite")
        sys.exit(1)
    if args.datafile != None:
        if args.magnet != None or args.msite != None:
            print("cannot specify both datafile and magnet or msite")
            sys.exit(1)

    # load appenv
    MyEnv = appenv()
    if args.debug: print(MyEnv.template_path())

    # Get Object
    if args.datafile != None:
        confdata = load_object(MyEnv, args.datafile, args.debug)
        jsonfile = args.datafile.replace("-data.json","")

    if args.magnet != None:
        confdata = load_object_from_db(MyEnv, "magnet", args.magnet, args.debug)
        jsonfile = args.magnet

    if args.msite != None:
        confdata = load_object_from_db(MyEnv, "msite", args.msite, args.debug)
        jsonfile = args.msite

    (yamlfile, cfgfile, jsonfile, xaofile, meshfile, tarfilename) = setup(MyEnv, args, confdata, jsonfile)
    cmds = setup_cmds(MyEnv, args, yamlfile, cfgfile, jsonfile, xaofile, meshfile)
    
    # Print command to run
    machine = MyEnv.compute_server

    workingdir = cfgfile.replace(".cfg", "")

    print("\n\n=== Guidelines for running a simu on {machine} ===")
    print(f"Edit {cfgfile} to fix the meshfile, scale, partition and solver props")
    print(f"If you do change {cfgfile}, remember to include the new file in {tarfilename}")
    # TODO re-create a tgz archive if you modify cfgfile or jsonfile
    print(f"Create a {workingdir} directory on {machine}: ssh {machine} mkdir -p {workingdir}")
    print(f"Transfert {tarfilename} to {machine}: scp {tarfilename} {machine}:./{workingdir}")
    print(f"Install worflow in {machine}: scp -r {os.path.dirname(os.path.abspath(__file__))}'/workflows {machine}:./{workingdir}")
    print(f"Connect on {machine}: ssh -Y {machine}")
    print(f"Once connected on {machine} run the following commands")
    print(f"cd {workingdir}")
    for key in cmds:
        print(key, ':', cmds[key])
    print("==================================================")

    # post-processing
    print("\n\n=== Guidelines for postprocessing a simu on your host ===")
    print(f"Start pvdataserver on {machine}")
    print(f"Connect on {machine}: ssh -Y -L 11111:{machine}:11111")
    print(f"Start Paraview dataserver in {machine}: pvdataserver")
    print("In a new terminal on your host, start Paraview render server: pvrenderserver")
    print("In a new terminal on your host, start Paraview: paraview")
    print("==================================================")

    status = 0
    if args.auto:
        status = fabric(machine, workingdir, args, cfgfile, jsonfile, meshfile, tarfilename, cmds)
        # TODO 
        # print out some stats
        # start post-processing
        # what about jobmanager??
        # start a workflow??

    return status

if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
