"""Console script for python_magnetsetup."""
import argparse
from argparse import RawTextHelpFormatter

import sys

from .setup import setup, setup_cmds
from .objects import load_object, load_object_from_db
from .config import appenv

def main():

    epilog = "The choice of model is actually linked with the choosen method following this table\n" \
             "cfpes: thelec, mag, thmag_hcurl, thmagel_hcurl, mag_hcurl, thmag_hcurl, thmagel_hcurl\n" \
             "CG (3D only): thelec\n" \
             "HDG (3D only): thelec\n"

    # Manage Options
    command_line = None
    parser = argparse.ArgumentParser(formatter_class=RawTextHelpFormatter,
                                     description="Create json modelfiles for Feelpp/HiFiMagnet simu from templates",
                                     epilog=epilog)
    parser.add_argument("--datafile", help="input data file (ex. HL-34-data.json)", default=None)
    parser.add_argument("--wd", help="set a working directory", type=str, default="")
    parser.add_argument("--magnet", help="Magnet name from magnetdb (ex. HL-34)", default=None)
    parser.add_argument("--msite", help="MSite name from magnetdb (ex. HL-34)", default=None)

    parser.add_argument("--method", help="choose method (default is cfpdes", type=str,
                    choices=['cfpdes', 'CG', 'HDG', 'CRB'], default='cfpdes')
    parser.add_argument("--time", help="choose time type", type=str,
                    choices=['static', 'transient'], default='static')
    parser.add_argument("--geom", help="choose geom type", type=str,
                    choices=['Axi', '3D'], default='Axi')
    parser.add_argument("--model", help="choose model type", type=str,
                    choices=['thelec', 'mag', 'thmag', 'thmagel', 'thmqs', 'mag_hcurl', 'thmag_hcurl', 'thmagel_hcurl', 'thmqs_hcurl'], default='thmagel')
    parser.add_argument("--nonlinear", help="force non-linear", action='store_true')
    parser.add_argument("--cooling", help="choose cooling type", type=str,
                    choices=['mean', 'grad', 'meanH', 'gradH'], default='mean')
    parser.add_argument("--scale", help="scale of geometry", type=float, default=1e-3)

    parser.add_argument("--debug", help="activate debug", action='store_true')
    parser.add_argument("--verbose", help="activate verbose", action='store_true')
    args = parser.parse_args()

    # if args.debug:
    #    print("Arguments: " + str(args._))
    
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
    workingdir = cfgfile.replace(".cfg","")

    print("\n\n=== Guidelines for running a simu on {machine} ===")
    print(f"Edit {cfgfile} to fix the meshfile, scale, partition and solver props")
    print(f"If you do change {cfgfile}, remember to include the new file in {tarfilename}")
    # TODO re-create a tgz archive if you modify cfgfile or jsonfile
    print(f"Connect to {machine}: ssh -Y {machine}")
    print(f"Create a {workingdir} directory on {machine}: mkdir -p {workingdir}")
    print(f"Return to your host : exit")
    print(f"Transfert {tarfilename} to {machine}: scp {tarfilename} {machine}:./{workingdir}")
    print(f"Connect once more to {machine}: ssh -Y {machine}")
    print(f"Go to {workingdir} directory on {machine}: cd {workingdir}")
    # print(f"Untar {tarfilename} on {machine}: cd {workingdir}; tar zxvf {tarfilename}")
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


    
    return 0


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
