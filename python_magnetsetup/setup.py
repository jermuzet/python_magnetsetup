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
from .utils import Merge, NMerge
from .cfg import create_cfg
from .jsonmodel import create_json

from .insert import Insert_setup
from .bitter import Bitter_setup
from .supra import Supra_setup
    

def msite_setup(confdata: str, method_data: List, templates: dict, debug: bool=False):
    """
    Creating dict for setup for msite
    """
    print("msite_setup:", "debug=", debug)
    
    mdict = None
    mmat = None
    mpost = None

    for mtype in ["Insert", "Bitter", "Supra"]:
        if mtype in confdata:
            if isinstance(confdata[mtype], List):
                for object in confdata[mtype]:
                    if debug:
                        print("object[geom]:", object["geom"])
                    (mdict, mmat, mpost) = magnet_setup(object, method_data, templates, debug)
                    return (mdict, mmat, mpost)
            else:
                if debug:
                    print("object[geom]:", confdata[mtype]["geom"])
                (mdict, mmat, mpost) = magnet_setup(confdata[mtype], method_data, templates, debug)
                return (mdict, mmat, mpost)
    
    print("mdict:", mdict)
    return (mdict, mmat, mpost)

def magnet_setup(confdata: str, method_data: List, templates: dict, debug: bool=False):
    """
    Creating dict for setup for magnet
    """
    print("magnet_setup", "debug=", debug)
    
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

    if debug:
        print("magnet_setup: mdict=", mdict)
    return (mdict, mmat, mpost)

def setup(args):
    """
    """
    print("setup/main")
    
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

    mdict = {}
    mmat = {}
    mpost = {}

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

    if "geom" in confdata:
        print("Load a magnet %s " % jsonfile, "debug:", args.debug)
        (mdict, mmat, mpost) = magnet_setup(confdata, method_data, templates, args.debug)
    else:
        print("Load a msite %s" % confdata["name"], "debug:", args.debug)
        # print("confdata:", confdata)

        # why do I need that???
        with open(confdata["name"] + ".yaml", "x") as out:
                out.write("!<MSite>\n")
                yaml.dump(confdata, out)
                
        for magnet in confdata["magnets"]:
            print("magnet:", magnet, "debug=", args.debug)
            try:
                mconfdata = load_object(MyEnv, magnet + "-data.json", magnet, args.debug)
            except:
                print("setup: failed to load %s, look into magnetdb" % (magnet + "-data.json") )
                try:
                    mconfdata = load_object_from_db(MyEnv, "magnet", magnet, args.debug)
                except:
                    print("setup: failed to load %s from magnetdb" % magnet)
                    sys.exit(1)
                    
            if 'Helix' in mconfdata:
                print("Load an Insert")
                (tdict, tmat, tpost) = magnet_setup(mconfdata, method_data, templates, args.debug)
            else:
                print("Load others")
                (tdict, tmat, tpost) = msite_setup(mconfdata, method_data, templates, args.debug)
            
            # print("tdict:", tdict)
            mdict = NMerge(tdict, mdict, args.debug)
            # print("mdict:", mdict)
            
            # print("tmat:", tmat)
            mmat = NMerge(tmat, mmat, args.debug)
            # print("NewMerge:", NMerge(tmat, mmat))
            # print("mmat:", mmat)
            
            # print("tpost:", tpost)
            mpost = NMerge(tpost, mpost, args.debug)
            # print("NewMerge:", NMerge(tpost, mpost))
            # print("mpost:", mpost)
            

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
    # generate properly meshfile for cfg
    # generate solver section for cfg
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
     
    # TODO prepare a directory that contains every files needed to run simulation ??

    # Print command to run
    print("\n\n=== Guidelines for running a simu ===")
    simage_path = MyEnv.simage_path()
    hifimagnet = AppCfg["mesh"]["hifimagnet"]
    salome = AppCfg["mesh"]["salome"]
    feelpp = AppCfg[args.method]["feelpp"]
    partitioner = AppCfg["mesh"]["partitioner"]
    if "exec" in AppCfg[args.method]:
        exec = AppCfg[args.method]["exec"]
    if "exec" in AppCfg[args.method][args.time][args.geom][args.model]:
        exec = AppCfg[args.method][args.time][args.geom][args.model]
    pyfeel = 'cfpdes_insert_fixcurrent.py'

    xaofile = confdata["name"] + "_withAir.xao"
    geocmd = "salome -w1 -t $HIFIMAGNET/HIFIMAGNET_Cmd.py args:%s,--air,2,2,--wd,$PWD" % (name)
    meshcmd = "salome -w1 -t $HIFIMAGNET/HIFIMAGNET_Cmd.py args:%s,--air,2,2,mesh,--group,CoolingChannels,Isolants" % (name)
    meshfile = xaofile.replace(".xao", ".med")
    
    if args.geom == "Axi" and args.method == "cfpdes" :
        xaofile = confdata["name"] + "-Axi_withAir.xao"
        geocmd = "salome -w1 -t $HIFIMAGNET/HIFIMAGNET_Cmd.py args:%s,--axi,--air,2,2,--wd,$PWD" % (name)
        
        # if gmsh:
        meshcmd = "python3 -m python_magnetgeo.xao %s --wd $PWD mesh --group CoolingChannels --geo %s --lc=1" % (xaofile, name)
        meshfile = xaofile.replace(".xao", ".msh")
        
    h5file = xaofile.replace(".xao", "_p.json")
    partcmd = "%s --ifile %s --ofile %s [--part NP] [--mesh.scale=0.001]" % (partitioner, meshfile, h5file)
    feelcmd = "[mpirun -np NP] %s --config-file %s" % (exec, cfgfile)
    pyfeelcmd = "[mpirun -np NP] python %s" % pyfeel
    
    print("Edit %s to fix the meshfile, scale, partition and solver props" % cfgfile)
    print("export HIFIMAGNET=%s" % hifimagnet)
    print("workingdir:", args.wd)
    print("CAD:", "singularity exec %s %s" % (simage_path + "/" + salome,geocmd) )
        
    # if gmsh
    if args.geom == "Axi":
        print("Mesh:", meshcmd)
    else:
        print("Mesh:", "singularity exec -B /opt/DISTENE:/opt/DISTENE:ro %s %s" % (simage_path + "/" + salome,meshcmd))
    
    # eventually convertmeshcmd if feelpp since it is build without med support
    print("Partition:", "singularity exec %s %s" % (simage_path + "/" + feelpp, partcmd) )
    print("Feel:", "singularity exec %s %s" % (simage_path + "/" + feelpp, feelcmd) )
    print("pyfeel:", "singularity exec %s %s" % (simage_path + "/" + feelpp, pyfeel))

    # TODO what about postprocess??
    pass

