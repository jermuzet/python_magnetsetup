"""Console script for linking python_magnetsetup and python_magnettoos."""

from typing import List, Optional

import sys
import os
import json
import yaml

import argparse
from .objects import load_object, load_object_from_db
from .config import appenv

from python_magnetgeo import Insert, MSite, Bitter, Supra, SupraStructure
from python_magnetgeo import python_magnetgeo

import MagnetTools.MagnetTools as mt

def magnet_setup(confdata: str, debug: bool=False):
    """
    Load setup for magnet
    """
    print("magnet_setup", "debug=", debug)
    
    yamlfile = confdata["geom"]
    if debug:
        print("magnet_setup:", yamlfile)
    
    cad = None
    with open(yamlfile, 'r') as cfgdata:
        cad = yaml.load(cfgdata, Loader = yaml.FullLoader)
        
    if isinstance(cad, Insert):
        print("Load an Insert")
    elif isinstance(cad, Bitter.Bitter):
        print("Load an Bitter")
    elif isinstance(cad, Supra):
        print("Load an Supra")
    else:
        print("setup: unexpected cad type")
        sys.exit(1)

def msite_setup(confdata: str, debug: bool=False):
    """
    Load setup for msite
    """
    print("msite_setup:", "debug=", debug)
    
    for mtype in ["Insert", "Bitter", "Supra"]:
        if mtype in confdata:
            if isinstance(confdata[mtype], List):
                for object in confdata[mtype]:
                    if debug:
                        print("object[geom]:", object["geom"])
                    magnet_setup(object, debug)
            else:
                if debug:
                    print("object[geom]:", confdata[mtype]["geom"])
                magnet_setup(confdata[mtype], debug)
    

def setup(MyEnv, args, confdata, jsonfile):
    """
    """
    print("setup/main")
    
    # loadconfig
    AppCfg = loadconfig()

    # Get current dir
    cwd = os.getcwd()
    if args.wd:
        os.chdir(args.wd)

    if "geom" in confdata:
        print("Load a magnet %s " % jsonfile, "debug:", args.debug)
        if 'Helix' in mconfdata:
            print("Load an Insert")
            # create an Hstack
        elif 'Bitter' in mconfdata:
            print("Load a Bitter Magnet")
        elif 'Supra' in mconfdata:
            print("Load a Supra Magnet")
            # see SuperEMLF/geometry.py
        else:   
            print("Load others")
    else:
        print("Load a msite %s" % confdata["name"], "debug:", args.debug)
        # print("confdata:", confdata)

        # why do I need that???
        with open(confdata["name"] + ".yaml", "x") as out:
                out.write("!<MSite>\n")
                yaml.dump(confdata, out)
                
                    
def main():
    # Manage Options
    command_line = None
    parser = argparse.ArgumentParser(description="Create template json model files for Feelpp/HiFiMagnet simu")
    parser.add_argument("--datafile", help="input data file (ex. HL-34-data.json)", default=None)
    parser.add_argument("--wd", help="set a working directory", type=str, default="")
    parser.add_argument("--magnet", help="Magnet name from magnetdb (ex. HL-34)", default=None)
    parser.add_argument("--msite", help="MSite name from magnetdb (ex. HL-34)", default=None)

    parser.add_argument("--debug", help="activate debug", action='store_true')
    parser.add_argument("--verbose", help="activate verbose", action='store_true')
    args = parser.parse_args()

    if args.debug:
        print("Arguments: " + str(args._))
    
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


    setup(MyEnv, args, confdata, jsonfile)    
    return 0


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
