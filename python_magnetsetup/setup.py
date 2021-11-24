"""
Create template json model files for Feelpp/HiFiMagnet simu
From a yaml definition file of an insert

Inputs:
* method : method of solve, with feelpp cfpdes, getdp...
* time: stationnary or transient case
* geom: geometry of solve, 3D or Axi
* model: physic solved, thermic, thermomagnetism, thermomagnetism-elastic
* phytype: if the materials are linear or non-linear
* cooling: what type of cooling, mean or grad

Output: 
* tmp.json

App setup is stored in a json file that defines
the mustache template to be used.

Default path:
magnetsetup.json
mustache templates
"""

# TODO check for unit consistency
# depending on Length base unit

from typing import List, Optional

import sys
import os
import json
import yaml

from python_magnetgeo import Insert, MSite, Bitter, Supra
from python_magnetgeo import python_magnetgeo

from .config import appenv, loadconfig, loadtemplates
from .objects import load_object, load_object_from_db
from .utils import Merge
from .cfg import create_cfg
from .jsonmodel import create_json

from .insert import Insert_setup
from .bitter import Bitter_setup
from .supra import Supra_setup
    
def msite_setup(confdata: str, method_data: List, templates: dict, debug: bool=False):
    """
    Creating dict for setup for magnet
    """

    mdict = None
    mmat = None
    mpost = None

    for mtype in ["Insert", "Bitter", "Supra"]:
        if mtype in confdata:
            if isinstance(confdata[mtype], List):
                for object in confdata[mtype]:
                    print("object[geom]:", object["geom"])
                    magnet_setup(object, method_data, templates, debug)
            else:
                print("object[geom]:", confdata[mtype]["geom"])
                magnet_setup(confdata[mtype], method_data, templates, debug)
    
    return (mdict, mmat, mpost)

def magnet_setup(confdata: str, method_data: List, templates: dict, debug: bool=False):
    """
    Creating dict for setup for magnet
    """
    
    mdict = None
    mmat = None
    mpost = None

    yamlfile = confdata["geom"]
    if debug:
        print("magnet_setup:", yamlfile)
    
    cad = None
    with open(yamlfile, 'r') as cfgdata:
        cad = yaml.load(cfgdata, Loader = yaml.FullLoader)
        
    if isinstance(cad, Insert):
        (mdict, mmat, mpost) = Insert_setup(confdata, cad, method_data, templates, debug)
    elif isinstance(cad, Bitter.Bitter):
        (mdict, mmat, mpost) = Bitter_setup(confdata, cad, method_data, templates, debug)
    elif isinstance(cad, Supra):
        (mdict, mmat, mpost) = Supra_setup(confdata, cad, method_data, templates, debug)
    else:
        print("setup: unexpected cad type")
        sys.exit(1)

    return (mdict, mmat, mpost)

def main():
    """
    """
    print("setup/main")
    import argparse

    # Manage Options
    command_line = None
    parser = argparse.ArgumentParser(description="Create template json model files for Feelpp/HiFiMagnet simu")
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
                    choices=['thelec', 'mag', 'thmag', 'thmagel'], default='thmagel')
    parser.add_argument("--nonlinear", help="force non-linear", action='store_true')
    parser.add_argument("--cooling", help="choose cooling type", type=str,
                    choices=['mean', 'grad', 'meanH', 'gradH'], default='mean')
    parser.add_argument("--scale", help="scale of geometry", type=float, default=1e-3)

    parser.add_argument("--debug", help="activate debug", action='store_true')
    parser.add_argument("--verbose", help="activate verbose", action='store_true')
    args = parser.parse_args()

    if args.debug:
        print(args)
    
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

    # loadconfig
    AppCfg = loadconfig()

    # Get current dir
    cwd = os.getcwd()
    if args.wd:
        os.chdir(args.wd)
    
    # load appropriate templates
    method_data = [args.method, args.time, args.geom, args.model, args.cooling, "meter"]
    # TODO: if HDG meter -> millimeter
    templates = loadtemplates(MyEnv, AppCfg, method_data, (not args.nonlinear) )

    # Get Object
    if args.datafile != None:
        confdata = load_object(MyEnv, args.datafile, args.debug)
        jsonfile = args.datafile.replace(".json","")

    if args.magnet != None:
        confdata = load_object_from_db(MyEnv, "magnet", args.magnet, args.debug)
        jsonfile = args.magnet
    
    if args.msite != None:
        confdata = load_object_from_db(MyEnv, "msite", args.msite, args.debug)
        jsonfile = args.msite

    print("confdata:", confdata)
    if "geom" in confdata:
        print("Load a magnet %s " % jsonfile)
        (mdict, mmat, mpost) = magnet_setup(confdata, method_data, templates, args.debug)
    else:
        print("Load a msite %s" % confdata["name"])
        for magnet in confdata["magnets"]:
            print("magnet:", magnet)
            mconfdata = load_object_from_db(MyEnv, "magnet", magnet, args.debug)
            (mdict, mmat, mpost) = msite_setup(mconfdata, method_data, templates, args.debug)
        print("msite not implemented")
        sys.exit(1)
    

    # create cfg
    if args.datafile: 
        jsonfile = args.datafile.replace("-data.json","")
    if args.magnet: 
        jsonfile = args.magnet
    jsonfile += "-" + args.method
    jsonfile += "-" + args.model
    if args.nonlinear:
        jsonfile += "-nonlinear"
    jsonfile += "-" + args.geom
    jsonfile += "-sim.json"
    cfgfile = jsonfile.replace(".json", ".cfg")

    name = confdata["name"]
    # TODO create_mesh() or load_mesh()
    create_cfg(cfgfile, name, args.nonlinear, jsonfile, templates["cfg"], method_data, args.debug)
            
    # create json
    create_json(jsonfile, mdict, mmat, mpost, templates, method_data, args.debug)

    # copy some additional json file 
    material_generic_def = ["conductor", "insulator"]

    if args.time == "transient":
        material_generic_def.append("conductor-nosource") # only for transient with mqs

    if args.method == "cfpdes":
        if args.debug: print("cwd=", cwd)
        from shutil import copyfile
        for jsonfile in material_generic_def:
            filename = AppCfg[args.method][args.time][args.geom][args.model]["filename"][jsonfile]
            src = os.path.join(MyEnv.template_path(), args.method, args.geom, args.model, filename)
            dst = os.path.join(jsonfile + "-" + args.method + "-" + args.model + "-" + args.geom + ".json")
            if args.debug:
                print(jsonfile, "filename=", filename, "src=%s" % src, "dst=%s" % dst)
            copyfile(src, dst)
     
    # Print command to run
    print("\n\n=== Commands to run (ex pour cfpdes/Axi) ===")
    salome = "/home/singularity/hifimagnet-salome-9.7.0.sif"
    feelpp = "/home/singularity/feelpp-toolboxes-v0.109.0.sif"
    partitioner = 'feelpp_mesh_partitioner'
    exec = 'feelpp_toolbox_coefficientformpdes'
    pyfeel = 'cfpdes_insert_fixcurrent.py'
    if args.geom == "Axi" and args.method == "cfpdes" :
        xaofile = confdata["name"] + "-Axi_withAir.xao"
        geocmd = "salome -w1 -t $HIFIMAGNET/HIFIMAGNET_Cmd.py args:%s,--axi,--air,2,2,--wd,$PWD" % (name)
        
        # if gmsh:
        meshcmd = "python3 -m python_magnetgeo.xao %s --wd $PWD mesh --group CoolingChannels --geo %s --lc=1" % (xaofile, name)
        meshfile = xaofile.replace(".xao", ".msh")

        # if MeshGems:
        #meshcmd = "salome -w1 -t $HIFIMAGNET/HIFIMAGNET_Cmd.py args:%s,--axi,--air,2,2,mesh,--group,CoolingChannels" % yamlfile
        #meshfile = xaofile.replace(".xao", ".med")
        
        h5file = xaofile.replace(".xao", "_p.json")
        partcmd = "feelpp_mesh_partition --ifile %s --ofile %s [--part NP] [--mesh.scale=0.001]" % (meshfile, h5file)
        feelcmd = "[mpirun -np NP] %s --config-file %s" % (exec, cfgfile)
        pyfeelcmd = "[mpirun -np NP] python %s" % pyfeel
    
        print("Guidelines for running a simu")
        print("export HIFIMAGNET=/opt/SALOME-9.7.0-UB20.04/INSTALL/HIFIMAGNET/bin/salome")
        print("workingdir:", args.wd)
        print("CAD:", "singularity exec %s %s" % (salome,geocmd) )
        # if gmsh
        print("Mesh:", meshcmd)
        # print("Mesh:", "singularity exec -B /opt/DISTENE:/opt/DISTENE:ro %s %s" % (salome,meshcmd))
        print("Partition:", "singularity exec %s %s" % (feelpp, partcmd) )
        print("Feel:", "singularity exec %s %s" % (feelpp, feelcmd) )
        print("pyfeel:", "singularity exec %s %s" % (feelpp, pyfeel))
    pass

if __name__ == "__main__":
    main()
