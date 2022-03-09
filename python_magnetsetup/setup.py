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

from .insert import Insert_setup, Insert_simfile
from .bitter import Bitter_setup, Bitter_simfile
from .supra import Supra_setup, Supra_simfile
    
from .file_utils import MyOpen, findfile, search_paths

def magnet_simfile(MyEnv, confdata: str):
    """
    """
    files = []
    yamlfile = confdata["geom"]
    if "Helix" in confdata:
        print("Load an insert")
        # Download or Load yaml file from data repository??
        cad = None
        with MyOpen(yamlfile, 'r', paths=search_paths(MyEnv, "geom")) as cfgdata:
            cad = yaml.load(cfgdata, Loader = yaml.FullLoader)
            files.append(cfgdata.name)
        tmp_files = Insert_simfile(MyEnv, confdata, cad)
        for tmp_f in tmp_files:
            files.append(tmp_f)

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
                    files.append(cfgdata.name)
                elif isinstance(cad, Supra):
                    files.append(cfgdata.name)
                    struct = Supra_simfile(MyEnv, obj, cad)
                    if struct:
                        files.append(struct)
                else:
                    print("setup: unexpected cad type %s" % str(type(cad)))
                    sys.exit(1)

    return files

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
                yamlfile = obj["geom"]
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

def msite_simfile(MyEnv, confdata: str, session=None):
    """
    Creating list of simulation files for msite
    """

    files = []
    for magnet in confdata["magnets"]:
        try:
            mconfdata = load_object(MyEnv, magnet + "-data.json")
        except:
            try:
                mconfdata = load_object_from_db(MyEnv, "magnet", magnet, False, session)
            except:
                print("msite_simfile: failed to load %s from magnetdb" % magnet)
                sys.exit(1)

        files += magnet_simfile(MyEnv, mconfdata)
    
    return files

def msite_setup(MyEnv, confdata: str, method_data: List, templates: dict, debug: bool=False, session=None):
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
            mconfdata = load_object(MyEnv, magnet + "-data.json", debug)
        except:
            print("setup: failed to load %s, look into magnetdb" % (magnet + "-data.json") )
            try:
                mconfdata = load_object_from_db(MyEnv, "magnet", magnet, debug, session)
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

def setup(MyEnv, args, confdata, jsonfile, session=None):
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
        (mdict, mmat, mpost) = msite_setup(MyEnv, confdata, method_data, templates, args.debug or args.verbose, session)        
        
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

    # create list of files to be archived
    sim_files = [cfgfile, jsonfile]
    if args.method == "cfpdes":
        if args.debug: print("cwd=", cwd)
        from shutil import copyfile
        for jfile in material_generic_def:
            filename = AppCfg[args.method][args.time][args.geom][args.model]["filename"][jfile]
            src = os.path.join(MyEnv.template_path(), args.method, args.geom, args.model, filename)
            dst = os.path.join(jfile + "-" + args.method + "-" + args.model + "-" + args.geom + ".json")
            if args.debug:
                print(jfile, "filename=", filename, "src=%s" % src, "dst=%s" % dst)
            copyfile(src, dst)
            sim_files.append(dst)

    # list files to be archived
    xaofile = name + ".xao"
    if "mqs" in args.model or "mag" in args.model:
        xaofile = name + "_withAir.xao"
    meshfile = xaofile.replace(".xao", ".med")
    
    if args.geom == "Axi" and args.method == "cfpdes" :
        xaofile = name + "-Axi_withAir.xao"
        if "mqs" in args.model or "mag" in args.model:
            xaofile = name + "-Axi.xao"
        
        # if gmsh:
        meshfile = xaofile.replace(".xao", ".msh")
        
    try:
        mesh = findfile(meshfile, search_paths(MyEnv, "mesh"))
        sim_files.append(mesh)

        #?? replace geo by med/msh in cfg ?? if 3D#
    except:
        if "geom" in confdata:
            print("geo:", name)
            yamlfile = confdata["geom"]
            sim_files += magnet_simfile(MyEnv, confdata)
        else:
            yamlfile = confdata["name"] + ".yaml"
            sim_files += msite_simfile(MyEnv, confdata, session)

    print("List of simulations files:", sim_files)
    import tarfile
    tarfilename = cfgfile.replace('cfg','tgz')
    if os.path.isfile(os.path.join(cwd, tarfilename)):
        raise FileExistError(f"{tarfilename} already exists")
    else:
        tar = tarfile.open(tarfilename, "w:gz")
        for filename in sim_files:
            print(f"add {filename} to {tarfilename}")  
            tar.add(filename)
            for mname in material_generic_def:
                if mname in filename:
                    print(f"remove {filename}")
                    os.unlink(filename)
        tar.close()

    return (yamlfile, cfgfile, jsonfile, xaofile, meshfile, tarfilename)

def setup_cmds(MyEnv, args, name, cfgfile, jsonfile, xaofile, meshfile):
    """
    create cmds 
    """

    # loadconfig
    AppCfg = loadconfig()

    # Get current dir
    cwd = os.getcwd()
    if args.wd:
        os.chdir(args.wd)
    
    # get server from MyEnv,
    # get NP from server (with an heuristic from meshsize)
    # TODO adapt NP to the size of the problem
    # if server is SMP mpirun outside otherwise inside singularity
    from .machines import load_machines

    machines = load_machines()
    print(f"machines: {machines} type={type(machines)}")
    print(f"machine={MyEnv.compute_server} type={type(MyEnv.compute_server)}")
    server = machines[MyEnv.compute_server]
    NP = server.cores
    if server.multithreading:
        NP = int(NP/2)
    print(f"NP={NP} {type(NP)}")

    simage_path = MyEnv.simage_path()
    hifimagnet = AppCfg["mesh"]["hifimagnet"]
    salome = AppCfg["mesh"]["salome"]
    feelpp = AppCfg[args.method]["feelpp"]
    partitioner = AppCfg["mesh"]["partitioner"]
    if "exec" in AppCfg[args.method]:
        exec = AppCfg[args.method]["exec"]
    if "exec" in AppCfg[args.method][args.time][args.geom][args.model]:
        exec = AppCfg[args.method][args.time][args.geom][args.model]
    pyfeel = 'cfpdes_insert_fixcurrent.py' # commisioning, fixcooling

    if "mqs" in args.model or "mag" in args.model:
        geocmd = f"salome -w1 -t $HIFIMAGNET/HIFIMAGNET_Cmd.py args:{name},--air,2,2,--wd,data/geometries"
        meshcmd = f"salome -w1 -t $HIFIMAGNET/HIFIMAGNET_Cmd.py args:{name},--air,2,2,--wd,$PWD,mesh,--group,CoolingChannels,Isolants"
    else:
        geocmd = f"salome -w1 -t $HIFIMAGNET/HIFIMAGNET_Cmd.py args:{name},2,2,--wd,data/geometries"
        meshcmd = f"salome -w1 -t $HIFIMAGNET/HIFIMAGNET_Cmd.py args:{name},2,2,--wd,$PWD,mesh,--group,CoolingChannels,Isolants"

    gmshfile = meshfile.replace(".med", ".msh")
    meshconvert = ""

    print(f"args.geom={args.geom} args.method={args.geom}")
    if args.geom == "Axi" and args.method == "cfpdes" :
        if "mqs" in args.model or "mag" in args.model:
            geocmd = f"salome -w1 -t $HIFIMAGNET/HIFIMAGNET_Cmd.py args:{name},--air,2,2,--wd,data/geometries"
        else:
            geocmd = f"salome -w1 -t $HIFIMAGNET/HIFIMAGNET_Cmd.py args:{name},--axi,--air,2,2,--wd,data/geometries"
        
        # if gmsh:
        meshcmd = f"python3 -m python_magnetgeo.xao {xaofile} --wd data/geometries mesh --group CoolingChannels --geo {name} --lc=1"
    else:
        gmshfile = meshfile.replace(".med", ".msh")
        meshconvert = f"gmsh -0 {meshfile} -bin -o {gmshfile}"

    # ?? if meshcmd need to replace geo by med/msh in cfg ??
        
    h5file = xaofile.replace(".xao", "_p.json")
    partcmd = f"{partitioner} --ifile {gmshfile} --ofile {h5file} --part {NP} [--mesh.scale=0.001]"

    # ?? if partition need to replace geo by h5 in cfg ??
    tarfile = cfgfile.replace("cfg", "tgz")
    cmds = {
        "Pre": f"export HIFIMAGNET={hifimagnet}",
        "Unpack": f"tar zxvf {tarfile}",
        "CAD": f"singularity exec {simage_path}/{salome} {geocmd}"
    }
    
    cmds["Mesh"] = f"singularity exec {simage_path}/{salome} {meshcmd}"
    if meshconvert:
        cmds["Convert"] = f"singularity exec {simage_path}/{salome} {meshconvert}"
    cmds["Partition"] = f"singularity exec {simage_path}/{feelpp} {partcmd}"
    
    if server.smp:
        feelcmd = f"{exec} --config-file {cfgfile}"
        pyfeelcmd = f"python {pyfeel}"
        cmds["Run"] = f"mpirun -np {NP} singularity exec {simage_path}/{feelpp} {feelcmd}"
        cmds["Python"] = f"mpirun -np {NP} singularity exec {simage_path}/{feelpp} {pyfeel}"
    
    else:
        feelcmd = f"mpirun -np {NP} {exec} --config-file {cfgfile}"
        pyfeelcmd = f"mpirun -np {NP} python {pyfeel}"
        cmds["Run"] = f"singularity exec {simage_path}/{feelpp} {feelcmd}"
        cmds["Python"] = f"singularity exec {simage_path}/{feelpp} {pyfeel}"
    
    # TODO jobmanager if server.manager != JobManagerType.none
    # Need user email at this point
    # Template for oar and slurm
    
    # TODO what about postprocess??
    
    return cmds

