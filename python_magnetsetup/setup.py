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
    
from .file_utils import MyOpen, findfile, search_paths

def magnet_setup(MyEnv, confdata: str, method_data: List, templates: dict, debug: bool=False):
    """
    Creating dict for setup for magnet
    """
    print("magnet_setup", "debug=", debug, confdata)
    
    yamlfile = confdata["geom"]
    if debug:
        print("magnet_setup:", yamlfile)
    
    mdict = {}
    mmat = {}
    mpost = {}
    
    if "Helix" in confdata:
        print("Load an insert")
        # Download or Load yaml file from data repository??
        cad = None
        with MyOpen(yamlfile, 'r', paths=search_paths(MyEnv, "geom")) as cfgdata:
            cad = yaml.load(cfgdata, Loader = yaml.FullLoader)
        # if isinstance(cad, Insert):
        (mdict, mmat, mpost) = Insert_setup(MyEnv, confdata, cad, method_data, templates, debug)

    for mtype in ["Bitter", "Supra"]:
        if mtype in confdata:
            print("load a %s insert" % mtype)

            # loop on mtype
            for obj in confdata[mtype]:
                print("obj:", obj)
                cad = None
                with MyOpen(yamlfile, 'r', paths=search_paths(MyEnv, "geom")) as cfgdata:
                    cad = yaml.load(cfgdata, Loader = yaml.FullLoader)
    
                if isinstance(cad, Bitter.Bitter):
                    (tdict, tmat, tpost) = Bitter_setup(MyEnv, obj, cad, method_data, templates, debug)
                elif isinstance(cad, Supra):
                    (tdict, tmat, tpost) = Supra_setup(MyEnv, obj, cad, method_data, templates, debug)
                else:
                    print("setup: unexpected cad type %s" % str(type(cad)))
                    sys.exit(1)

                print("tdict:", tdict)
                mdict = NMerge(tdict, mdict, debug)
                # print("mdict:", mdict)
            
                print("tmat:", tmat)
                mmat = NMerge(tmat, mmat, debug)
                # print("mmat:", mmat)
            
                print("tpost:", tpost)
                mpost = NMerge(tpost, mpost, debug)
                # print("mpost:", mpost)

    if debug:
        print("magnet_setup: mdict=", mdict)
    return (mdict, mmat, mpost)

def msite_setup(MyEnv, confdata: str, method_data: List, templates: dict, debug: bool=False):
    """
    Creating dict for setup for msite
    """
    print("msite_setup:", "debug=", debug)
    print("msite_setup:", "confdata=", confdata)
    print("miste_setup: confdata[magnets]=", confdata["magnets"])
    
    mdict = {}
    mmat = {}
    mpost = {}

    for magnet in confdata["magnets"]:
        print("magnet:", magnet, "type(magnet)=", type(magnet), "debug=", debug)
        try:
            mconfdata = load_object(MyEnv, magnet + "-data.json", magnet, debug)
        except:
            print("setup: failed to load %s, look into magnetdb" % (magnet + "-data.json") )
            try:
                mconfdata = load_object_from_db(MyEnv, "magnet", magnet, debug)
            except:
                print("setup: failed to load %s from magnetdb" % magnet)
                sys.exit(1)
                    
        if debug:
            print("mconfdata[geom]:", mconfdata["geom"])
        (tdict, tmat, tpost) = magnet_setup(MyEnv, mconfdata, method_data, templates, debug)
            
        print("tdict:", tdict)
        mdict = NMerge(tdict, mdict, debug)
        # print("mdict:", mdict)
            
        print("tmat:", tmat)
        mmat = NMerge(tmat, mmat, debug)
        # print("NewMerge:", NMerge(tmat, mmat))
        # print("mmat:", mmat)
            
        print("tpost:", tpost)
        mpost = NMerge(tpost, mpost, debug)
        # print("NewMerge:", NMerge(tpost, mpost))
        # print("mpost:", mpost)
    
    print("mdict:", mdict)
    return (mdict, mmat, mpost)

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
    
    # load appropriate templates
    # TODO force millimeter when args.method == "HDG"
    method_data = [args.method, args.time, args.geom, args.model, args.cooling, "meter"]
    
    # TODO: if HDG meter -> millimeter
    templates = loadtemplates(MyEnv, AppCfg, method_data, (not args.nonlinear) )

    mdict = {}
    mmat = {}
    mpost = {}

    if "geom" in confdata:
        print("Load a magnet %s " % jsonfile, "debug:", args.debug)
        (mdict, mmat, mpost) = magnet_setup(MyEnv, confdata, method_data, templates, args.debug or args.verbose)
    else:
        print("Load a msite %s" % confdata["name"], "debug:", args.debug)
        # print("confdata:", confdata)

        # why do I need that???
        if not findfile(confdata["name"] + ".yaml", search_paths(MyEnv, "geom")):
            with MyOpen(confdata["name"] + ".yaml", "x", paths=search_paths(MyEnv, "geom")) as out:
                out.write("!<MSite>\n")
                yaml.dump(confdata, out)
        (mdict, mmat, mpost) = msite_setup(MyEnv, confdata, method_data, templates, args.debug or args.verbose)        
        
    name = jsonfile
    if name in confdata:
        name = confdata["name"]
    
    # create cfg
    jsonfile += "-" + args.method
    jsonfile += "-" + args.model
    if args.nonlinear:
        jsonfile += "-nonlinear"
    jsonfile += "-" + args.geom
    jsonfile += "-sim.json"
    cfgfile = jsonfile.replace(".json", ".cfg")

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

    xaofile = name + "_withAir.xao"
    geocmd = "salome -w1 -t $HIFIMAGNET/HIFIMAGNET_Cmd.py args:%s,--air,2,2,--wd,$PWD" % (name)
    meshcmd = "salome -w1 -t $HIFIMAGNET/HIFIMAGNET_Cmd.py args:%s,--air,2,2,mesh,--group,CoolingChannels,Isolants" % (name)
    meshfile = xaofile.replace(".xao", ".med")
    
    if args.geom == "Axi" and args.method == "cfpdes" :
        xaofile = name + "-Axi_withAir.xao"
        geocmd = "salome -w1 -t $HIFIMAGNET/HIFIMAGNET_Cmd.py args:%s,--axi,--air,2,2,--wd,$PWD" % (name)
        
        # if gmsh:
        meshcmd = "python3 -m python_magnetgeo.xao %s --wd $PWD mesh --group CoolingChannels --geo %s --lc=1" % (xaofile, name)
        meshfile = xaofile.replace(".xao", ".msh")
        
    h5file = xaofile.replace(".xao", "_p.json")
    partcmd = "%s --ifile %s --ofile %s [--part NP] [--mesh.scale=0.001]" % (partitioner, meshfile, h5file)
    feelcmd = "[mpirun -np NP] %s --config-file %s" % (exec, cfgfile)
    pyfeelcmd = "[mpirun -np NP] python %s" % pyfeel
    
    # TODO what about postprocess??
    cmds = {
        "Pre": "export HIFIMAGNET=%s" % hifimagnet,
        "CAD:": "singularity exec %s %s" % (simage_path + "/" + salome,geocmd),
        "Mesh": meshcmd,
        "Partition": "singularity exec %s %s" % (simage_path + "/" + feelpp, partcmd),
        "Run": "singularity exec %s %s" % (simage_path + "/" + feelpp, feelcmd),
        "Python": "singularity exec %s %s" % (simage_path + "/" + feelpp, pyfeel)
    }

    # if gmsh
    if args.geom == "Axi":
        cmds["Mesh:"] = meshcmd
    else:
        cmds["Mesh:"] = "singularity exec -B /opt/DISTENE:/opt/DISTENE:ro %s %s" % (simage_path + "/" + salome,meshcmd)
    
    return (cfgfile, jsonfile, cmds)

