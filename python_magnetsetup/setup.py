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
import re

from python_magnetgeo import Insert, MSite, Bitter, Supra
from python_magnetgeo import python_magnetgeo

from .machines import load_machines
from .config import appenv, loadconfig, loadtemplates, loadmachine
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
        print(f"magnet_setup: confdata: {confdata}")

    mdict = {}
    mmat = {}
    mmodels = {}
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
        (mdict, mmat, mmodels, mpost) = Insert_setup(MyEnv, confdata, cad, method_data, templates, debug)

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
                    (tdict, tmat, tmodels, tpost) = Bitter_setup(MyEnv, obj, cad, method_data, templates, debug)
                    # print("Bitter tpost:", tpost)
                elif isinstance(cad, Supra.Supra):
                    (tdict, tmat, tmodels, tpost) = Supra_setup(MyEnv, obj, cad, method_data, templates, debug)
                else:
                    raise Exception(f"setup: unexpected cad type {str(type(cad))}")

                if debug: print("tdict:", tdict)
                mdict = NMerge(tdict, mdict, debug, "magnet_setup Bitter/Supra mdict")
            
                if debug: print("tmat:", tmat)
                mmat = NMerge(tmat, mmat, debug, "magnet_setup Bitter/Supra mmat")

                if debug: print("tmodels:", tmodels)
                if 'th' in method_data[3]:
                    if "heat" in mmodels :
                        mmodels["heat"] = NMerge(tmodels["heat"], mmodels["heat"], debug, "magnet_setup Bitter/Supra mmodels heat")
                    else :
                        mmodels["heat"] = tmodels["heat"]

                if 'mag' in method_data[3] or 'mqs' in method_data[3] :
                    if "magnetic" in mmodels :
                        mmodels["magnetic"] = NMerge(tmodels["magnetic"], mmodels["magnetic"], debug, "magnet_setup Bitter/Supra mmodels magnetic")
                    else :
                        mmodels["magnetic"] = tmodels["magnetic"]
                
                if 'magel' in method_data[3] :
                    if "elastic" in mmodels :
                        mmodels["elastic"] = NMerge(tmodels["elastic"], mmodels["elastic"], debug, "magnet_setup Bitter/Supra mmodels elastic")
                    else :
                        mmodels["elastic"] = tmodels["elastic"]

                if 'mqsel' in method_data[3] :
                    if "elastic1" in mmodels :
                        mmodels["elastic1"] = NMerge(tmodels["elastic1"], mmodels["elastic1"], debug, "magnet_setup Bitter/Supra mmodels elastic1")
                    else :
                        mmodels["elastic1"] = tmodels["elastic1"]
                    if "elastic2" in mmodels :
                        mmodels["elastic2"] = NMerge(tmodels["elastic2"], mmodels["elastic2"], debug, "magnet_setup Bitter/Supra mmodels elastic2")
                    else :
                        mmodels["elastic2"] = tmodels["elastic2"]
            
                if debug: print("tpost:", tpost)
                # print(f"magnet_setup {cad.name}: tpost[current_H]={tpost['current_H']}")
                mpost = NMerge(tpost, mpost, debug, "magnet_setup Bitter/Supra mpost") # debug)
                # print(f"magnet_setup {cad.name}: mpost[current_H]={mpost['current_H']}")

    if debug:
        print("magnet_setup: mdict=", mdict)
    return (mdict, mmat, mmodels, mpost)

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
    mmodels = {}
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

        (tdict, tmat, tmodels, tpost) = magnet_setup(MyEnv, mconfdata, method_data, templates, debug)
            
        # print("tdict[part_electric]:", tdict['part_electric'])
        # print("tdict[part_thermic]:", tdict['part_thermic'])
        mdict = NMerge(tdict, mdict, debug, "msite_setup/tdict")
        # print("mdict[part_electric]:", mdict['part_electric'])
        # print("mdict[part_thermic]:", mdict['part_thermic'])
            
        # print("tmat:", tmat)
        mmat = NMerge(tmat, mmat, debug, "msite_setup/tmat")
        # print("NewMerge:", NMerge(tmat, mmat))
        # print("mmat:", mmat)
        
        mmodels = NMerge(tmodels, mmodels, debug, "msite_setup/tmodels")

        # print("tpost:", tpost)
        mpost = NMerge(tpost, mpost, debug, "msite_setup/tpost") #debug)
        # print("NewMerge:", mpost)
    
    # print("mdict:", mdict)
    return (mdict, mmat, mmodels, mpost)

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

        (mdict, mmat, mmodels, mpost) = magnet_setup(MyEnv, confdata, method_data, templates, args.debug or args.verbose)
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
        
        (mdict, mmat, mmodels, mpost) = msite_setup(MyEnv, confdata, method_data, templates, args.debug or args.verbose, session)
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
    create_json(jsonfile, mdict, mmat, mmodels, mpost, templates, method_data, args.debug)

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

    # TODO create a flow_params from records data
    sdir = os.path.dirname(os.path.abspath(__file__))
    # print("sdir:", sdir)
    src = os.path.join(sdir, 'flow_params.json')
    dst = 'flow_params.json'
    copyfile(src, dst)

    if args.debug:
        print("List of simulations files:", sim_files)
    import tarfile
    tarfilename = cfgfile.replace('cfg','tgz')
    if os.path.isfile(os.path.join(cwd, tarfilename)):
        raise FileExistsError(f"{tarfilename} already exists")
    else:
        tar = tarfile.open(tarfilename, "w:gz")
        for filename in sim_files:
            # TODO skip xao and brep if Axi args.geom?
            if args.geom == 'Axi' and ( filename.endswith('.xao') or filename.endswith('.brep') ) :
                if args.debug:
                    print(f"skip {filename}")  
            else:
                if args.debug:
                    print(f"add {filename} to {tarfilename}")  
                tar.add(filename)
                for mname in material_generic_def:
                    if mname in filename:
                        if args.debug: print(f"remove {filename}")
                        os.unlink(filename)
        tar.add('flow_params.json')
        os.unlink('flow_params.json')
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

    server = loadmachine(args.machine)
    # print(f'setup_cmds: {server}')
    NP = server.cores
    if server.multithreading:
        NP = int(NP/2)
    if args.debug:
        print(f"NP={NP} {type(NP)}")
    if args.np > 0:
        if args.np > NP:
            print(f'requested number of cores {args.np} exceed {server.name} capability (max: {NP})')
        else:
            NP = args.np

    simage_path = MyEnv.simage_path()
    hifimagnet = AppCfg["mesh"]["hifimagnet"]
    salome = AppCfg["mesh"]["salome"]
    feelpp = AppCfg[args.method]["feelpp"]
    partitioner = AppCfg["mesh"]["partitioner"]
    workingdir = MyEnv.yaml_repo
    if workingdir.startswith('/'):
        workingdir = MyEnv.yaml_repo.replace('/','',1)
    print(f"setup_cmds: workingdir={workingdir}")

    if "exec" in AppCfg[args.method]:
        exec = AppCfg[args.method]["exec"]
    if "exec" in AppCfg[args.method][args.time][args.geom][args.model]:
        exec = AppCfg[args.method][args.time][args.geom][args.model]
    pyfeel = ' -m workflows.cli' # commisioning, fixcooling
    # TODO add current specs, depends on 

    if "mqs" in args.model or "mag" in args.model:
        geocmd = f"salome -w1 -t $HIFIMAGNET/HIFIMAGNET_Cmd.py args:{name},--air,2,2,--wd,{workingdir}"
        meshcmd = f"salome -w1 -t $HIFIMAGNET/HIFIMAGNET_Cmd.py args:{name},--air,2,2,--wd,$PWD,mesh,--group,CoolingChannels,Isolants"
    else:
        geocmd = f"salome -w1 -t $HIFIMAGNET/HIFIMAGNET_Cmd.py args:{name},2,2,--wd,{workingdir}"
        meshcmd = f"salome -w1 -t $HIFIMAGNET/HIFIMAGNET_Cmd.py args:{name},2,2,--wd,$PWD,mesh,--group,CoolingChannels,Isolants"

    gmshfile = meshfile.replace(".med", ".msh")
    meshconvert = ""

    if args.geom == "Axi" and args.method == "cfpdes" :
        if "mqs" in args.model or "mag" in args.model:
            geocmd = f"salome -w1 -t $HIFIMAGNET/HIFIMAGNET_Cmd.py args:{name},--axi,--air,2,2,--wd,{workingdir}"
        else:
            geocmd = f"salome -w1 -t $HIFIMAGNET/HIFIMAGNET_Cmd.py args:{name},--axi,--wd,{workingdir}"
        
        # if gmsh:
        meshcmd = f"python3 -m python_magnetgeo.xao {xaofile} --wd {workingdir} mesh --group CoolingChannels --geo {name} --lc=1"
    else:
        gmshfile = meshfile.replace(".med", ".msh")
        meshconvert = f"gmsh -0 {meshfile} -bin -o {gmshfile}"

    scale = ""
    if args.method != "HDG":
        scale = "--mesh.scale=0.001"
    h5file = xaofile.replace(".xao", f"_p{NP}.json")

    partcmd = f"{partitioner} --ifile $PWD/{workingdir}/{gmshfile} --odir $PWD/{workingdir} --part {NP} {scale}"
        
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
    
    if args.geom == '3D':
        cmds["Partition"] = f"singularity exec {simage_path}/{feelpp} {partcmd}"
        meshfile = h5file
        update_partition = f"perl -pi -e \'s|gmsh.partition=.*|gmsh.partition = 0|\' {cfgfile}" 
        cmds["Update_Partition"] = update_partition
    if args.geom =="Axi":
        update_cfg = f"perl -pi -e 's|# mesh.scale =|mesh.scale =|' {cfgfile}"
        cmds["Update_cfg"] = update_cfg
        

    # TODO add command to change mesh.filename in cfgfile    
    update_cfgmesh = f"perl -pi -e \'s|mesh.filename=.*|mesh.filename=\$cfgdir/{workingdir}/{meshfile}|\' {cfgfile}"

    cmds["Update_Mesh"] = update_cfgmesh

    if server.smp:
        feelcmd = f"mpirun -np {NP} {exec} --config-file {cfgfile}"
        pyfeelcmd = f"mpirun -np {NP} python {pyfeel} {cfgfile}"
        cmds["Run"] = f"singularity exec {simage_path}/{feelpp} {feelcmd}"
        cmds["Workflow"] = f"singularity exec {simage_path}/{feelpp} {pyfeelcmd}"
    
    else:
        feelcmd = f"{exec} --config-file {cfgfile}"
        pyfeelcmd = f"python {pyfeel}"
        cmds["Run"] = f"mpirun -np {NP} singularity exec {simage_path}/{feelpp} {feelcmd}"
        cmds["Workflow"] = f"mpirun -np {NP} singularity exec {simage_path}/{feelpp} {pyfeelcmd} {cfgfile}"

    # compute resultdir:
    with open(cfgfile, 'r') as f:
        directory = re.sub('directory=', '', f.readline(),  flags=re.DOTALL)
    home_env = 'HOME'
    result_dir = f'{os.getenv(home_env)}/feelppdb/{directory.rstrip()}/np_{NP}'
    result_arch = cfgfile.replace('.cfg', f'_res.tgz')
    print(f'result_dir={result_dir}')

    paraview = AppCfg["post"]["paraview"]

    # get expr and exprlegend from method/model/...
    if "post" in AppCfg[args.method][args.time][args.geom][args.model]:
        postdata = AppCfg[args.method][args.time][args.geom][args.model]["post"]
        for key in postdata:
            pyparaview = f'pv-scalarfield.py --cfgfile {cfgfile}  --jsonfile {jsonfile} --expr {key} --exprlegend \"{postdata[key]}\" --resultdir ${result_dir}'
            pyparaviewcmd = f"pvpython {pyparaview}"
            cmds["Postprocessing"] = f"singularity exec {simage_path}/{paraview} {pyparaviewcmd}"


    cmds["Save"] = f"tmpdir=$(pwd) && pushd {result_dir}/.. && tar zcf $tmpdir/{result_arch} np_{NP} && popd"

    # TODO jobmanager if server.manager != JobManagerType.none
    # Need user email at this point
    # Template for oar and slurm

    # TODO get results (value.csv, png, raw data) to magnetdb 
    
    return cmds

