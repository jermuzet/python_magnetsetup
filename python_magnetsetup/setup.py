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

def magnet_simfile(MyEnv, confdata: str, addAir: bool = False):
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
        tmp_files = Insert_simfile(MyEnv, confdata, cad, addAir)
        for tmp_f in tmp_files:
            files.append(tmp_f)

    for mtype in ["Bitter", "Supra"]:
        if mtype in confdata:
            print("load a %s insert" % mtype)
            try:
                with MyOpen(yamlfile, 'r', paths=search_paths(MyEnv, "geom")) as cfgdata:
                    cad = yaml.load(cfgdata, Loader = yaml.FullLoader)
                    files.append(cfgdata.name)
            except:
                pass

            # loop on mtype
            for obj in confdata[mtype]:
                print("obj:", obj)
                cad = None
                yamlfile = obj["geom"]
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
                    raise Exception(f"setup: unexpected cad type {type(cad)}")

    return files

def magnet_setup(MyEnv, confdata: str, method_data: List, templates: dict, debug: bool=False):
    """
    Creating dict for setup for magnet
    """
    
    print("magnet_setup")
    if debug:
        print(f"magnet_setup: confdata: {confdata}"),
    
    mdict = {}
    mmat = {}
    mpost = {}
    
    if "Helix" in confdata:
        print("Load an insert")
        yamlfile = confdata["geom"]
        if debug:
            print(f"magnet_setup: yamfile: {yamlfile}")
    
        # Download or Load yaml file from data repository??
        cad = None
        with MyOpen(yamlfile, 'r', paths=search_paths(MyEnv, "geom")) as cfgdata:
            cad = yaml.load(cfgdata, Loader = yaml.FullLoader)
        # if isinstance(cad, Insert):
        (mdict, mmat, mpost) = Insert_setup(MyEnv, confdata, cad, method_data, templates, debug)

    for mtype in ["Bitter", "Supra"]:
        if mtype in confdata:
            # TODO check case with only 1 Bitter???
            
            # loop on mtype
            for obj in confdata[mtype]:
                if debug: print("obj:", obj)
                yamlfile = obj["geom"]
                cad = None
                with MyOpen(yamlfile, 'r', paths=search_paths(MyEnv, "geom")) as cfgdata:
                    cad = yaml.load(cfgdata, Loader = yaml.FullLoader)
                print(f"load a {mtype} insert: {cad.name} ****")
    
                if isinstance(cad, Bitter.Bitter):
                    (tdict, tmat, tpost) = Bitter_setup(MyEnv, obj, cad, method_data, templates, debug)
                    # print("Bitter tpost:", tpost)
                elif isinstance(cad, Supra):
                    (tdict, tmat, tpost) = Supra_setup(MyEnv, obj, cad, method_data, templates, debug)
                else:
                    raise Exception(f"setup: unexpected cad type {str(type(cad))}")

                if debug: print("tdict:", tdict)
                mdict = NMerge(tdict, mdict, debug, "magnet_setup Bitter/Supra mdict")
            
                if debug: print("tmat:", tmat)
                mmat = NMerge(tmat, mmat, debug, "magnet_setup Bitter/Supra mmat")
            
                if debug: print("tpost:", tpost)
                # print(f"magnet_setup {cad.name}: tpost[current_H]={tpost['current_H']}")
                mpost = NMerge(tpost, mpost, debug, "magnet_setup Bitter/Supra mpost") # debug)
                # print(f"magnet_setup {cad.name}: mpost[current_H]={mpost['current_H']}")

    if debug:
        print("magnet_setup: mdict=", mdict)
    return (mdict, mmat, mpost)

def msite_simfile(MyEnv, confdata: str, session=None, addAir: bool = False):
    """
    Creating list of simulation files for msite
    """

    files = []

    # TODO: get xao and brep if they exist, otherwise go on
    # TODO: add suffix _Air if needed ??
    try:
        xaofile = confdata["name"] + ".xao"
        if addAir:
            xaofile = confdata["name"] + "_withAir.xao"
        f =findfile(xaofile, paths=search_paths(MyEnv, "cad"))
        files.append(f)

        brepfile = confdata["name"] + ".brep"
        if addAir:
            brepfile = confdata["name"] + "_withAir.brep"
        f = findfile(brepfile, paths=search_paths(MyEnv, "cad"))
        files.append(f)
    except:
        for magnet in confdata["magnets"]:
            try:
                mconfdata = load_object(MyEnv, magnet + "-data.json")
            except:
                try:
                    mconfdata = load_object_from_db(MyEnv, "magnet", magnet, False, session)
                except:
                    raise Exception(f"msite_simfile: failed to load {magnet} from magnetdb")

            files += magnet_simfile(MyEnv, mconfdata)
    
    return files

def msite_setup(MyEnv, confdata: str, method_data: List, templates: dict, debug: bool=False, session=None):
    """
    Creating dict for setup for msite
    """
    print("msite_setup:", "debug=", debug)
    print("msite_setup:", "confdata=", confdata)
    print("msite_setup: confdata[magnets]=", confdata["magnets"])
    
    mdict = {}
    mmat = {}
    mpost = {}

    for magnet in confdata["magnets"]:
        print(f"magnet:  {magnet}")
        try:
            mconfdata = load_object(MyEnv, magnet + "-data.json", debug)
        except:
            print(f"setup: failed to load {magnet}-data.json look into magnetdb")
            try:
                mconfdata = load_object_from_db(MyEnv, "magnet", magnet, debug, session)
            except:
                raise Exception(f"setup: failed to load {magnet} from magnetdb")
                    
        if debug:
            print("mconfdata[geom]:", mconfdata["geom"])

        (tdict, tmat, tpost) = magnet_setup(MyEnv, mconfdata, method_data, templates, debug)
            
        # print("tdict[part_electric]:", tdict['part_electric'])
        # print("tdict[part_thermic]:", tdict['part_thermic'])
        mdict = NMerge(tdict, mdict, debug, "msite_setup/tdict")
        # print("mdict[part_electric]:", mdict['part_electric'])
        # print("mdict[part_thermic]:", mdict['part_thermic'])
            
        # print("tmat:", tmat)
        mmat = NMerge(tmat, mmat, debug, "msite_setup/tmat")
        # print("NewMerge:", NMerge(tmat, mmat))
        # print("mmat:", mmat)
            
        # print("tpost:", tpost)
        mpost = NMerge(tpost, mpost, debug, "msite_setup/tpost") #debug)
        # print("NewMerge:", mpost)
    
    # print("mdict:", mdict)
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

    if args.debug:
        print("confdata:", confdata)
    cad_basename = ""
    if "geom" in confdata:
        print(f"Load a magnet {jsonfile} ", f"debug: {args.debug}")
        try :
            with MyOpen(confdata["geom"], "r", paths=search_paths(MyEnv, "geom")) as f:
                cad = yaml.load(f, Loader = yaml.FullLoader)
                cad_basename = cad.name
        except:
            cad_basename = confdata["geom"].replace(".yaml","")
            print("confdata:", confdata)
            for mtype in ["Bitter", "Supra"]:
                if mtype in confdata:
                    # why do I need that???
                    try:
                        findfile(confdata["geom"], search_paths(MyEnv, "geom"))
                    except FileNotFoundError as e:
                        # print(f"try to create {MyEnv.yaml_repo + '/' + confdata['geom']}")
                        # magnets = {}
                        # magnets[mtype] = []
                        # for obj in confdata[mtype]:
                        #    magnets[mtype].append( obj["geom"] )

                        # with open(MyEnv.yaml_repo + '/' + confdata["geom"], "x") as out:
                        #    out.write(f"!<{mtype}>\n")
                        #    yaml.dump(magnets, out)
                        # print(f"try to create {confdata['geom']} done")
                        pass

        (mdict, mmat, mpost) = magnet_setup(MyEnv, confdata, method_data, templates, args.debug or args.verbose)
    else:
        print("Load a msite %s" % confdata["name"], "debug:", args.debug)
        # print("confdata:", confdata)
        cad_basename = confdata["name"]

        # why do I need that???
        try:
            findfile(confdata["name"] + ".yaml", search_paths(MyEnv, "geom"))
        except FileNotFoundError as e:
            print("confdata:", confdata)
            print(f"try to create {MyEnv.yaml_repo + '/' + confdata['name'] + '.yaml'}")
            # for obj in confdata[mtype]:
            with open(MyEnv.yaml_repo + '/' + confdata["name"] + ".yaml", "x") as out:
                out.write("!<MSite>\n")
                yaml.dump(confdata, out)
            print(f"try to create {confdata['name']}.yaml done")
        
        (mdict, mmat, mpost) = msite_setup(MyEnv, confdata, method_data, templates, args.debug or args.verbose, session)
        # print(f"setup: msite mpost={mpost['current_H']}")        
        
    name = jsonfile
    if name in confdata:
        name = confdata["name"]
        print(f"name={name} from confdata")
    
    # create cfg
    jsonfile += "-" + args.method
    jsonfile += "-" + args.model
    if args.nonlinear:
        jsonfile += "-nonlinear"
    jsonfile += "-" + args.geom
    jsonfile += "-sim.json"
    cfgfile = jsonfile.replace(".json", ".cfg")

    addAir = False
    if 'mag' in args.model or 'mqs' in args.model:
        addAir = True

    # retreive xaofile and meshfile
    xaofile = cad_basename + ".xao"
    if args.geom == "Axi" and args.method == "cfpdes" :
        xaofile = cad_basename + "-Axi.xao"
        if "mqs" in args.model or "mag" in args.model:
            xaofile = cad_basename + "-Axi_withAir.xao"
        
    meshfile = xaofile.replace(".xao", ".med")
    if args.geom == "Axi" and args.method == "cfpdes" :
        # # if gmsh:
        meshfile = xaofile.replace(".xao", ".msh")
    print(f"setup: meshfile={meshfile}")

    # TODO create_mesh() or load_mesh()
    # generate properly meshfile for cfg
    # generate solver section for cfg
    # here name is from args (aka name of magnet and/or msite if from db)
    create_cfg(cfgfile, name, meshfile, args.nonlinear, jsonfile, templates["cfg"], method_data, args.debug)
            
    # create json
    create_json(jsonfile, mdict, mmat, mpost, templates, method_data, args.debug)

    # copy some additional json file 
    material_generic_def = ["conductor", "insulator"]
    if args.time == "transient":
        material_generic_def.append("conduct-nosource") # only for transient with mqs

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
    
    try:
        mesh = findfile(meshfile, search_paths(MyEnv, "mesh"))
        sim_files.append(mesh)
    except:
        if "geom" in confdata:
            print("geo:", name)
            yamlfile = confdata["geom"]
            sim_files += magnet_simfile(MyEnv, confdata, addAir)
        else:
            yamlfile = confdata["name"] + ".yaml"
            sim_files += msite_simfile(MyEnv, confdata, session, addAir)

    if args.debug:
        print("List of simulations files:", sim_files)
    import tarfile
    tarfilename = cfgfile.replace('cfg','tgz')
    if os.path.isfile(os.path.join(cwd, tarfilename)):
        raise FileExistsError(f"{tarfilename} already exists")
    else:
        tar = tarfile.open(tarfilename, "w:gz")
        for filename in sim_files:
            if args.debug:
                print(f"add {filename} to {tarfilename}")  
            tar.add(filename)
            for mname in material_generic_def:
                if mname in filename:
                    if args.debug: print(f"remove {filename}")
                    os.unlink(filename)
        tar.add('flow_param.json')
        tar.close()

    return (yamlfile, cfgfile, jsonfile, xaofile, meshfile, tarfilename)

def setup_cmds(MyEnv, args, name, cfgfile, jsonfile, xaofile, meshfile):
    """
    create cmds

    Watchout: gsmh/salome base mesh is always in millimeter
    For simulation it is madatory to use a mesh in meter except maybe for HDG
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
    if args.debug:
        print(f"machine={MyEnv.compute_server} type={type(MyEnv.compute_server)}")
    server = machines[MyEnv.compute_server]
    NP = server.cores
    if server.multithreading:
        NP = int(NP/2)
    if args.debug:
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
    pyfeel = ' -m workflows.cli' # commisioning, fixcooling

    if "mqs" in args.model or "mag" in args.model:
        geocmd = f"salome -w1 -t $HIFIMAGNET/HIFIMAGNET_Cmd.py args:{name},--air,2,2,--wd,data/geometries"
        meshcmd = f"salome -w1 -t $HIFIMAGNET/HIFIMAGNET_Cmd.py args:{name},--air,2,2,--wd,$PWD,mesh,--group,CoolingChannels,Isolants"
    else:
        geocmd = f"salome -w1 -t $HIFIMAGNET/HIFIMAGNET_Cmd.py args:{name},2,2,--wd,data/geometries"
        meshcmd = f"salome -w1 -t $HIFIMAGNET/HIFIMAGNET_Cmd.py args:{name},2,2,--wd,$PWD,mesh,--group,CoolingChannels,Isolants"

    gmshfile = meshfile.replace(".med", ".msh")
    meshconvert = ""

    if args.geom == "Axi" and args.method == "cfpdes" :
        if "mqs" in args.model or "mag" in args.model:
            geocmd = f"salome -w1 -t $HIFIMAGNET/HIFIMAGNET_Cmd.py args:{name},--axi,--air,2,2,--wd,data/geometries"
        else:
            geocmd = f"salome -w1 -t $HIFIMAGNET/HIFIMAGNET_Cmd.py args:{name},--axi,--wd,data/geometries"
        
        # if gmsh:
        meshcmd = f"python3 -m python_magnetgeo.xao {xaofile} --wd data/geometries mesh --group CoolingChannels --geo {name} --lc=1"
    else:
        gmshfile = meshfile.replace(".med", ".msh")
        meshconvert = f"gmsh -0 {meshfile} -bin -o {gmshfile}"

    scale = ""
    if args.method != "HDG":
        scale = "--mesh.scale=0.001"
    h5file = xaofile.replace(".xao", "_p.json")
    partcmd = f"{partitioner} --ifile {gmshfile} --ofile {h5file} --part {NP} {scale}"

    tarfile = cfgfile.replace("cfg", "tgz")
    # TODO if cad exist do not print CAD command
    cmds = {
        "Pre": f"export HIFIMAGNET={hifimagnet}",
        "Unpack": f"tar zxvf {tarfile}",
        "CAD": f"singularity exec {simage_path}/{salome} {geocmd}"
    }
    
    # TODO add mount point for MeshGems if 3D otherwise use gmsh for Axi 
    # to be changed in the future by using an entry from magnetsetup.conf MeshGems or gmsh
    MeshGems_licdir = server.mgkeydir
    cmds["Mesh"] = f"singularity exec -B {MeshGems_licdir}:/opt/DISTENE/license:ro {simage_path}/{salome} {meshcmd}"
    # if gmsh:
    #    cmds["Mesh"] = f"singularity exec -B /opt/MeshGems:/opt/DISTENE/license:ro {simage_path}/{salome} {meshcmd}"
        
    if meshconvert:
        cmds["Convert"] = f"singularity exec {simage_path}/{salome} {meshconvert}"
    
    if args.geom == "3D":
        cmds["Partition"] = f"singularity exec {simage_path}/{feelpp} {partcmd}"
        meshfile = h5file
        update_partition = f"perl -pi -e \'s|gmsh.partition=.*|gmsh.partition = 0|\' {cfgfile}" 

    # TODO add command to change mesh.filename in cfgfile    
    update_cfgmesh = f"perl -pi -e \'s|mesh.filename=.*|mesh.filename=\$cfgdir/data/geometries/{meshfile}|\' {cfgfile}"
    if args.geom =="Axi":
        update_cfg = f"perl -pi -e 's|# mesh.scale =|mesh.scale =|' {cfgfile}"
        cmds["Update_cfg"] = update_cfg

    cmds["Update_Mesh"] = update_cfgmesh
    if args.geom == "3D":
        cmds["Update_Partition"] = update_partition

    if server.smp:
        feelcmd = f"{exec} --config-file {cfgfile}"
        pyfeelcmd = f"python {pyfeel}"
        cmds["Run"] = f"mpirun -np {NP} singularity exec {simage_path}/{feelpp} {feelcmd}"
        cmds["Workflow"] = f"mpirun -np {NP} singularity exec {simage_path}/{feelpp} {pyfeelcmd} {cfgfile}"
    
    else:
        feelcmd = f"mpirun -np {NP} {exec} --config-file {cfgfile}"
        pyfeelcmd = f"mpirun -np {NP} python {pyfeel} {cfgfile}"
        cmds["Run"] = f"singularity exec {simage_path}/{feelpp} {feelcmd}"
        cmds["Workflow"] = f"singularity exec {simage_path}/{feelpp} {pyfeelcmd}"
    
    # TODO jobmanager if server.manager != JobManagerType.none
    # Need user email at this point
    # Template for oar and slurm
    
    # TODO what about postprocess??
    
    return cmds

