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

import os
import re
import json
import yaml
import itertools
import math

from python_magnetgeo.Insert import Insert
from python_magnetgeo.MSite import MSite
from python_magnetgeo.Bitter import Bitter
from python_magnetgeo.Supra import Supra

from .config import appenv, loadconfig, loadtemplates

# from .objects import load_object, load_object_from_db
from .objects import load_object
from .utils import NMerge
from .cfg import create_cfg
from .jsonmodel import create_json

from .insert import Insert_setup, Insert_simfile
from .bitter import Bitter_setup, Bitter_simfile
from .supra import Supra_setup, Supra_simfile

from .file_utils import MyOpen, findfile, search_paths
from .units import load_units, convert_data
from glob import glob

from .node import NodeSpec


def magnet_simfile(
    MyEnv, confdata: str, addAir: bool = False, debug: bool = False, session=None
):
    """
    create sim files for magnet
    """
    files = []
    yamlfile = confdata["geom"]

    if "Helix" in confdata:
        print("Load an insert")
        # Download or Load yaml file from data repository??
        cad = None
        with MyOpen(yamlfile, "r", paths=search_paths(MyEnv, "geom")) as cfgdata:
            cad = yaml.load(cfgdata, Loader=yaml.FullLoader)
            files.append(cfgdata.name)
        tmp_files = Insert_simfile(MyEnv, confdata, cad, addAir)
        for tmp_f in tmp_files:
            files.append(tmp_f)

    for mtype in ["Bitter", "Supra"]:
        if mtype in confdata:
            print(f"load a {mtype} insert")
            try:
                with MyOpen(
                    yamlfile, "r", paths=search_paths(MyEnv, "geom")
                ) as cfgdata:
                    cad = yaml.load(cfgdata, Loader=yaml.FullLoader)
                    files.append(cfgdata.name)
            except:
                pass

            # loop on mtype
            for obj in confdata[mtype]:
                if debug:
                    print(f"obj: {obj}")
                cad = None
                yamlfile = obj["geom"]
                with MyOpen(
                    yamlfile, "r", paths=search_paths(MyEnv, "geom")
                ) as cfgdata:
                    cad = yaml.load(cfgdata, Loader=yaml.FullLoader)

                if isinstance(cad, Bitter):
                    files.append(cfgdata.name)
                elif isinstance(cad, Supra):
                    files.append(cfgdata.name)
                    struct = Supra_simfile(MyEnv, obj, cad)
                    if struct:
                        files.append(struct)
                else:
                    raise Exception(f"setup: unexpected cad type {type(cad)}")

    return files


def magnet_setup(
    MyEnv,
    mname: str,
    confdata: str,
    method_data: List,
    templates: dict,
    current: float = 31.0e3,
    debug: bool = False,
):
    """
    Creating dict for setup for magnet
    """

    print(f"magnet_setup: mname={mname}")
    print(f"magnet_setup: templates={templates}")
    if debug:
        print(f"magnet_setup: confdata={confdata}"),

    mdict = {}
    mmat = {}
    mmodels = {}
    mpost = {}

    yamlfile = confdata["geom"]
    if debug:
        print(f"magnet_setup: yamfile: {yamlfile}")

    # Download or Load yaml file from data repository??
    cad = None
    with MyOpen(yamlfile, "r", paths=search_paths(MyEnv, "geom")) as cfgdata:
        cad = yaml.load(cfgdata, Loader=yaml.FullLoader)
    innerbore = cad.innerbore
    outerbore = cad.outerbore
    print(
        f"Load magnet: mname={mname}, cad={cad.name}, innerbore={innerbore}, outerbore={outerbore}"
    )

    prefix = ""
    if mname:
        prefix = f"{mname}_"

    if "Helix" in confdata:
        print(f"Load an insert: mname={mname}")
        # if isinstance(cad, Insert):
        (mdict, mmat, mmodels, mpost) = Insert_setup(
            MyEnv, mname, confdata, cad, method_data, templates, current, debug
        )

    for mtype in ["Bitter", "Supra"]:
        if mtype in confdata:
            # TODO check case with only 1 Bitter???
            print(f"confdata[{mtype}]={confdata[mtype]}")

            # loop on mtype
            for i, obj in enumerate(confdata[mtype]):
                if debug:
                    print(f"obj: {obj}")
                yamlfile = obj["geom"]
                cad = None
                with MyOpen(
                    yamlfile, "r", paths=search_paths(MyEnv, "geom")
                ) as cfgdata:
                    cad = yaml.load(cfgdata, Loader=yaml.FullLoader)
                print(f"magnetsetup:magnet_setup: load a {mtype}: {cad.name}")

                if isinstance(cad, Bitter):
                    (tdict, tmat, tmodels, tpost) = Bitter_setup(
                        MyEnv, mname, obj, cad, method_data, templates, current, debug
                    )

                elif isinstance(cad, Supra):
                    (tdict, tmat, tmodels, tpost) = Supra_setup(
                        MyEnv, mname, obj, cad, method_data, templates, current, debug
                    )
                else:
                    raise Exception(
                        f"setup/agnet_setup: unexpected cad type {str(type(cad))}"
                    )

                if debug:
                    print(f"tdict: {tdict}")
                NMerge(
                    tdict,
                    mdict,
                    debug,
                    name=f"magnet_setup {mtype} mdict for {mname}/{yamlfile}",
                )
                # print(f"magnet_setup: {mtype}, mname={mname}, tdict={tdict}")
                # print(f"magnet_setup: {mtype}, mname={mname}, mdict={mdict}")
                if not isinstance(cad, Supra):
                    print(
                        f'magnet_setup: {mtype}, mname={mname}, mdict[init_temp]={mdict["init_temp"]}'
                    )
                # print(f"magnet_setup: {mtype}, mname={mname}, mdict[power_magnet]={mdict['power_magnet']}")
                # list_name = [item['name'] for item in mdict['int_temp']]

                if debug:
                    print(f"tmat: {tmat}")
                NMerge(tmat, mmat, debug, name="magnet_setup Bitter/Supra mmat")

                if debug:
                    print(f"tmodels: {tmodels}")
                for physic in tmodels:
                    if physic not in mmodels:
                        mmodels[physic] = {}
                    NMerge(
                        tmodels[physic],
                        mmodels[physic],
                        debug,
                        name="magnet_setup Bitter/Supra mmodels ",
                    )

                if debug:
                    print(f"tpost: {tpost}")
                NMerge(
                    tpost, mpost, debug, name="magnet_setup Bitter/Supra mpost"
                )  # debug)
                if debug:
                    print(f"magnet_setup: {mtype}, mname={mname}, tpost={tpost}")
                    print(f"magnet_setup: {mtype}, mname={mname}, mpost={mpost}")

                if not isinstance(cad, Supra):
                    for key in ["Current", "Power"]:
                        list_current = []
                        for item in mpost[key]:
                            if isinstance(item, dict) and "part_electric" in item:
                                list_current = list(
                                    set(list_current + item["part_electric"])
                                )
                        if list_current:
                            mpost[key] = [{"part_electric": list_current}]
                            if debug:
                                print(
                                    f"magnet_setup {mname}: force mpost[{key}]={mpost[key]}"
                                )

                tdict.clear()
                tmat.clear()
                tmodels.clear()
                tpost.clear()

                # fix init_temp and power_magnet entries in mdict
                print(f"mdict: key={mdict.keys()}")
                if not isinstance(cad, Supra):
                    for key in ["init_temp", "power_magnet", "T_magnet"]:
                        if len(mdict[key]) > 1:
                            # print(f"setup/magnet_setup mname={mname}: mdict[{key}]={mdict[key]}")
                            _key = [item["name"] for item in mdict[key]]
                            _keys = list(set(_key))
                            if key == "init_temp":
                                _pref = [item["prefix"] for item in mdict[key]]
                                _prefs = list(set(_pref))
                            if len(_keys) > 1:
                                raise Exception(
                                    f"setup/magnet_setup mname={mname}: mdict[{key}] seems broken - mdict[{key}]={mdict[key]}"
                                )

                            _list = [item["magnet_parts"] for item in mdict[key]]
                            _lists = list(set(list(itertools.chain(*_list))))
                            if key == "init_temp":
                                mdict[key] = [
                                    {
                                        "name": _keys[0],
                                        "prefix": _prefs[0],
                                        "magnet_parts": _lists,
                                    }
                                ]
                            else:
                                mdict[key] = [{"name": _keys[0], "magnet_parts": _lists}]
                            if debug:
                                print(
                                    f"setup/magnet_setup mname={mname}: force mdict[{key}] to = {{'name': _keys[0], 'magnet_parts': _lists}}"
                                )
        # else:
        #     print(f"{mtype} not in confdata={confdata}")

    if debug:
        print(f"magnet_setup: mdict={mdict}")
    return (mdict, mmat, mmodels, mpost)


def msite_simfile(MyEnv, confdata: str, addAir: bool = False, session=None):
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
        f = findfile(xaofile, paths=search_paths(MyEnv, "cad"))
        files.append(f)

        brepfile = confdata["name"] + ".brep"
        if addAir:
            brepfile = confdata["name"] + "_withAir.brep"
        f = findfile(brepfile, paths=search_paths(MyEnv, "cad"))
        files.append(f)
    except:
        for magnet in confdata["magnets"]:
            mconfdata = load_object(MyEnv, magnet + "-data.json")
            # try:
            #     mconfdata = load_object(MyEnv, magnet + "-data.json")
            # except:
            #     try:
            #         mconfdata = load_object_from_db(
            #             MyEnv, "magnet", magnet, False, session
            #         )
            #     except:
            #         raise Exception(
            #             f"msite_simfile: failed to load {magnet} from magnetdb"
            #         )

            files += magnet_simfile(MyEnv, mconfdata)

    return files


def msite_setup(
    MyEnv,
    confdata: str,
    method_data: List,
    templates: dict,
    currents: dict,
    debug: bool = False,
    session=None,
):
    """
    Creating dict for setup for msite
    """
    print(f"msite_setup: confdata={confdata}")
    if debug:
        print("msite_setup:", "confdata=", confdata)
        print("msite_setup: confdata[magnets]=", confdata["magnets"])

    mdict = {}
    mmat = {}
    mmodels = {}
    mpost = {}

    for magnet in confdata["magnets"]:
        mname = list(magnet.keys())[0]
        print(f"msite_setup: magnet_setup[{mname}]")
        if debug:
            print(f"msite_setup: magnet_setup[{mname}]: {magnet}, confdata={magnet}")

        mconfdata = magnet[mname]
        current = currents[mname]["value"]
        (tdict, tmat, tmodels, tpost) = magnet_setup(
            MyEnv, mname, mconfdata, method_data, templates, current, debug
        )
        # print(f"msite_setup({mname}): tdict={tdict}")
        # print(f"msite_setup({mname}): tdict[init_temp]={tdict['init_temp']}")
        # print(f"msite_setup({mname}): tdict[power_magnet]={tdict['power_magnet']}")
        if debug:
            print(f"tpost[{mname}][Current]: {tpost['Current']}")

        NMerge(tdict, mdict, debug, name=f"msite_setup: merge(mdict,tdict) for {mname}")
        # if debug:
        # print("tdict[part_electric]:", tdict['part_electric'])
        # print("tdict[part_thermic]:", tdict['part_thermic'])
        # print("mdict[part_electric]:", mdict['part_electric'])
        # print("mdict[part_thermic]:", mdict['part_thermic'])

        NMerge(tmat, mmat, debug, "msite_setup/tmat")
        if debug:
            print("mmat:", mmat)

        if debug:
            print(f"tmodels: {tmodels}")
        for physic in tmodels:
            if physic not in mmodels:
                mmodels[physic] = {}
            NMerge(
                tmodels[physic],
                mmodels[physic],
                debug,
                name="msite_setup mmodels ",
            )

        NMerge(tpost, mpost, debug, "msite_setup/tpost")

        tdict.clear()
        tmat.clear()
        tmodels.clear()
        tpost.clear()

        for key in ["Current", "Power"]:
            list_current = []
            for item in mpost[key]:
                if isinstance(item, dict) and "part_electric" in item:
                    list_current = list(set(list_current + item["part_electric"]))
            if list_current:
                mpost[key] = [{"part_electric": list_current}]
                if debug:
                    print(f"msite_setup {mname}: force mpost[{key}]={mpost[key]}")
        if debug:
            print("NewMerge:", mpost)

    # print(f"msite_setup: mdict={mdict}")
    # print(f"msite_setup: mdict[init_temp]={mdict['init_temp']}")
    # print(f"msite_setup: mdict[power_magnet]={mdict['power_magnet']}")

    if debug:
        print(f"mpost: {mpost}")

    if debug:
        print("mdict:", mdict)
    return (mdict, mmat, mmodels, mpost)


def setup(MyEnv, args, confdata, jsonfile: str, currents: dict, session=None):
    """
    generate sim files
    """
    print(f"setup: currents={currents}")

    # loadconfig
    AppCfg = loadconfig()

    # Get current dir
    cwd = os.getcwd()
    if args.wd:
        os.chdir(args.wd)
    print(f"setup/main: {os.getcwd()}")

    # load appropriate templates
    # TODO force millimeter when args.method == "HDG"
    method_data = [
        args.method,
        args.time,
        args.geom,
        args.model,
        args.cooling,
        "meter",
        args.nonlinear,
    ]

    # TODO: if HDG meter -> millimeter
    templates = loadtemplates(MyEnv, AppCfg, method_data)

    mdict = {}
    mmat = {}
    mpost = {}

    if args.debug:
        print(f"setup: confdata={confdata}")
    cad_basename = ""
    if "geom" in confdata:
        if args.debug:
            print(f"Load a magnet {jsonfile}")
        try:
            with MyOpen(confdata["geom"], "r", paths=search_paths(MyEnv, "geom")) as f:
                cad = yaml.load(f, Loader=yaml.FullLoader)
                cad_basename = cad.name
        except:
            cad_basename = confdata["geom"].replace(".yaml", "")
            if args.debug:
                print(f"confdata: {confdata}")
            for mtype in ["Bitter", "Supra"]:
                if mtype in confdata:
                    # why do I need that???
                    try:
                        findfile(confdata["geom"], search_paths(MyEnv, "geom"))
                    except FileNotFoundError as e:
                        pass

        [mname] = currents.keys()
        current = currents[mname]["value"]
        (mdict, mmat, mmodels, mpost) = magnet_setup(
            MyEnv,
            "",
            confdata,
            method_data,
            templates,
            current,
            args.debug or args.verbose,
        )
    else:
        if args.debug:
            print(f"Load a msite {confdata['name']}")
        cad_basename = confdata["name"]

        # why do I need that???
        try:
            findfile(confdata["name"] + ".yaml", search_paths(MyEnv, "geom"))
        except FileNotFoundError as e:
            if args.debug:
                print("confdata:", confdata)
            yamldata = {"name": confdata["name"]}
            todict = {}
            if "magnets" in confdata:
                for magnet in confdata["magnets"]:
                    if args.debug:
                        print(f"magnet(type={type(magnet)}: {magnet}")
                    mname = list(magnet.keys())[0]
                    mconfdata = magnet[mname]
                    if args.debug:
                        print(f"magnet[{mname}]: {mconfdata}")
                    # if "Helix" in mconfdata:
                    todict[mname] = mconfdata["geom"].replace(".yaml", "")
                    """
                    else:
                        todict[mname] = []
                        if "Bitter" in mconfdata:
                            for obj in mconfdata["Bitter"]:
                                todict[mname].append(obj["geom"].replace(".yaml", ""))
                        if "Supra" in mconfdata:
                            for obj in mconfdata["Supra"]:
                                todict[mname].append(obj["geom"].replace(".yaml", ""))
                    """
            else:
                raise Exception(f"setup: no magnet in site {confdata['name']}")

            if args.debug:
                print(f"todict: {todict}")
            yamldata["magnets"] = todict
            yamldata["screens"] = []
            yamldata["z_offset"] = [0 for key in todict]  # init to zero
            yamldata["r_offset"] = [0 for key in todict]
            yamldata["paralax"] = [0 for key in todict]

            # for obj in confdata[mtype]:
            with open(f"{MyEnv.yaml_repo}/{confdata['name']}.yaml", "x") as out:
                out.write("!<MSite>\n")
                yaml.dump(yamldata, out)
            print(f"create {MyEnv.yaml_repo}/{confdata['name']}.yaml done")

        # print(f"{confdata['name']}: {confdata}")
        (mdict, mmat, mmodels, mpost) = msite_setup(
            MyEnv,
            confdata,
            method_data,
            templates,
            currents,
            args.debug or args.verbose,
            session,
        )
    if args.debug:
        print(f"setup: mpost[]={mpost}")

    name = jsonfile
    if name in confdata:
        name = confdata["name"]
        if args.debug:
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
    if "mag" in args.model or "mqs" in args.model:
        addAir = True

    # retreive xaofile and meshfile
    xaofile = cad_basename + ".xao"
    if args.geom == "Axi" and args.method == "cfpdes":
        xaofile = cad_basename + "-Axi.xao"
        if "mqs" in args.model or "mag" in args.model:
            xaofile = cad_basename + "-Axi_withAir.xao"

    meshfile = xaofile.replace(".xao", ".med")
    if args.geom == "Axi" and args.method == "cfpdes":
        # # if gmsh:
        meshfile = xaofile.replace(".xao", ".msh")
    print(f"setup: meshfile={meshfile}")

    # TODO create_mesh() or load_mesh()
    # generate properly meshfile for cfg
    # generate solver section for cfg
    # here name is from args (aka name of magnet and/or msite if from db)
    create_cfg(
        cfgfile,
        os.path.basename(name),
        meshfile,
        args.nonlinear,
        jsonfile.replace(f"{os.path.dirname(name)}/", ""),
        templates["cfg"],
        method_data,
        args.debug,
    )

    # create json
    create_json(
        jsonfile, mdict, mmat, mmodels, mpost, templates, method_data, args.debug
    )

    if "geom" in confdata:
        print(f'magnet geo: {confdata["geom"]}')
        yamlfile = confdata["geom"]
    else:
        print(f'site geo: {confdata["name"]}')
        yamlfile = confdata["name"] + ".yaml"

    # copy some additional json file
    material_generic_def = ["conductor", "insulator"]
    if args.time == "transient":
        material_generic_def.append("conduct-nosource")  # only for transient with mqs

    fit=None
    if "geom" in confdata:  #Magnet
        if "Supra" in confdata :
            fit="hilton" #replace with value in args
    elif "magnets" in confdata: #Site
        for magnet in confdata["magnets"]: #browse Magnets
            if "Supra" in next(iter(magnet.values())) :
                fit="hilton" #replace with value in args

    if args.method == "cfpdes":
        if args.debug:
            print("cwd=", cwd)
        from shutil import copyfile

        for jfile in material_generic_def:
            filename = AppCfg[args.method][args.time][args.geom][args.model][
                "filename"
            ][jfile]
            src = os.path.join(
                MyEnv.template_path(), args.method, args.geom, args.model, filename
            )
            dst = os.path.join(
                os.getcwd(), f"{jfile}-{args.method}-{args.model}-{args.geom}.json"
            )
            if args.debug:
                print(f"{jfile}, filename={filename}, src={src}, dst={dst}")
            copyfile(src, dst)
        
        if fit :
            filename = "fit_" + fit + ".json"
            src = os.path.join(
                MyEnv.template_path(), args.method, args.geom, args.model, filename
            )
            dst = os.path.join(
                os.getcwd(), f"superconductor-{args.method}-{args.model}-{args.geom}.json"
            )
            if args.debug:
                print(f"superconductor, filename={filename}, src={src}, dst={dst}")
            copyfile(src, dst)


        csvfiles = glob("./*.csv")
        print(f"csvfiles: {csvfiles}")
        if args.debug:
            print(f"pwd: {os.getcwd()}, ls: {os.listdir(os.curdir)}")

    return (yamlfile, cfgfile, jsonfile, xaofile, meshfile, csvfiles)  # , tarfilename)


def setup_cmds(
    MyEnv,
    args,
    node_spec: NodeSpec,
    yamlfile: str,
    cfgfile: str,
    jsonfile: str,
    xaofile: str,
    meshfile: str,
    csvfiles: list,
    root_directory: str,
    currents: dict,
):
    """
    create cmds

    Watchout: gsmh/salome base mesh is always in millimeter
    For simulation it is madatory to use a mesh in meter except maybe for HDG
    """

    # loadconfig
    AppCfg = loadconfig()

    # TODO adapt NP to the size of the problem
    # if server is SMP mpirun outside otherwise inside singularity
    NP = node_spec.cores
    print(f"NP={NP}")
    if node_spec.multithreading:
        NP = int(NP / 2)
        print(f"NP={NP} multithreading on")
    if args.debug:
        print(f"NP={NP} {type(NP)}")
    if args.np > 0:
        if args.np > NP:
            print(
                f"requested number of cores {args.np} exceed {node_spec.name} capability (max: {NP})"
            )
            print(f"keep {NP} cores")
        else:
            NP = args.np
    print(f"NP={NP}, args.np={args.np}")

    simage_path = MyEnv.simage_path()
    hifimagnet = AppCfg["mesh"]["hifimagnet"]
    salome = AppCfg["mesh"]["salome"]
    gmsh = AppCfg["mesh"]["gmsh"]
    feelpp = AppCfg[args.method]["feelpp"]
    partitioner = AppCfg["mesh"]["partitioner"]
    if "exec" in AppCfg[args.method]:
        exec = AppCfg[args.method]["exec"]
    if "exec" in AppCfg[args.method][args.time][args.geom][args.model]:
        exec = AppCfg[args.method][args.time][args.geom][args.model]

    print(f"currents({type(currents)}): {currents}")
    # currents: {mname: {value: x, type: t}}

    pyfeel = " -m python_magnetworkflows.cli"  # fix-current, commisioning, fixcooling
    pyfeel_args = f"--current {currents} --cooling {args.cooling} --eps {1.e-5} --itermax {20} --flow_params {args.flow_params}"

    # TODO infty as params
    if "mqs" in args.model or "mag" in args.model:
        geocmd = (
            f"salome -w1 -t {hifimagnet}/HIFIMAGNET_Cmd.py args:{yamlfile},--air,8,6"
        )
        meshcmd = f"salome -w1 -t {hifimagnet}/HIFIMAGNET_Cmd.py args:{yamlfile},--air,8,6,--wd,$PWD,mesh,--group,CoolingChannels,Isolants"  # -wd ??
    else:
        geocmd = f"salome -w1 -t {hifimagnet}/HIFIMAGNET_Cmd.py args:{yamlfile},8,6"
        meshcmd = f"salome -w1 -t {hifimagnet}/HIFIMAGNET_Cmd.py args:{yamlfile},8,6,--wd,$PWD,mesh,--group,CoolingChannels,Isolants"  # -wd ??

    gmshfile = meshfile.replace(".med", ".msh")
    meshconvert = ""

    if args.geom == "Axi" and args.method == "cfpdes":
        if "mqs" in args.model or "mag" in args.model:
            geocmd = f"salome -w1 -t {hifimagnet}/HIFIMAGNET_Cmd.py args:{yamlfile},--axi,--air,8,6"
        else:
            geocmd = (
                f"salome -w1 -t {hifimagnet}/HIFIMAGNET_Cmd.py args:{yamlfile},--axi"
            )

        # let xao decide mesh caracteristic length ??:
        meshcmd = f"python3 -m python_magnetgmsh.xao2msh {xaofile} --wd data/geometries --geo {yamlfile} mesh --group CoolingChannels"

        # or use gmsh api (do not support Supra with details)
        # meshcmd = f"python3 -m python_magnetgmsh.cli {yamlfile} --wd data/geometries --tickslit --mesh --group CoolingChannels"

    else:
        gmshfile = meshfile.replace(".med", ".msh")
        meshconvert = f"gmsh -0 {meshfile} -bin -o {gmshfile}"

    scale = ""
    if args.method != "HDG":
        scale = "--mesh.scale=0.001"
    h5file = xaofile.replace(".xao", f"_p{NP}.json")

    partcmd = f"{partitioner} --ifile $PWD/data/geometries/{gmshfile} --odir $PWD/data/geometries --part {NP} {scale}"

    tarfile = cfgfile.replace("cfg", "tgz")
    # TODO if cad exist do not print CAD command
    cmds = {
        "Unpack": f"tar zxvf {tarfile}",
        "CAD": f"singularity exec {simage_path}/{salome} {geocmd}",
    }

    # TODO add mount specific point for selected node
    if args.geom == "Axi":
        cmds["Mesh"] = f"singularity exec {simage_path}/{gmsh} {meshcmd}"
    else:
        cmds["Mesh"] = f"singularity exec {simage_path}/{salome} {meshcmd}"

    if meshconvert:
        cmds["Convert"] = f"singularity exec {simage_path}/{salome} {meshconvert}"

    if args.geom == "3D":
        cmds["Partition"] = f"singularity exec {simage_path}/{feelpp} {partcmd}"
        meshfile = h5file
        update_partition = (
            f"perl -pi -e 's|gmsh.partition=.*|gmsh.partition = 0|' {cfgfile}"
        )
        cmds["Update_Partition"] = update_partition

    if args.geom == "Axi":
        cmds["Partition"] = f"singularity exec {simage_path}/{feelpp} {partcmd} --dim 2"
        meshfile = h5file

    update_cfgmesh = f"perl -pi -e 's|mesh.filename=.*|mesh.filename=\$cfgdir/data/geometries/{meshfile}|' {cfgfile}"
    cmds["Update_Mesh"] = update_cfgmesh

    # TODO add command to change mesh.filename in cfgfile

    feelcmd = f"{exec} --directory {root_directory} --config-file {cfgfile}"
    pyfeelcmd = f"python {pyfeel} {cfgfile} {pyfeel_args}"
    if node_spec.smp:
        feelcmd = f"mpirun -np {NP} {feelcmd}"
        pyfeelcmd = f"mpirun -np {NP} {pyfeelcmd}"
        # feelcmd = f"mpirun --allow-run-as-root -np {NP} {exec} --config-file {cfgfile}"
        # pyfeelcmd = f"mpirun --allow-run-as-root -np {NP} python {pyfeel} {cfgfile}"
        cmds["Run"] = f"singularity exec {simage_path}/{feelpp} {feelcmd}"
        cmds["Workflow"] = f"singularity exec {simage_path}/{feelpp} {pyfeelcmd}"
    else:
        cmds[
            "Run"
        ] = f"mpirun -np {NP} singularity exec {simage_path}/{feelpp} {feelcmd}"
        cmds[
            "Workflow"
        ] = f"mpirun -np {NP} singularity exec {simage_path}/{feelpp} {pyfeelcmd}"

    # compute resultdir:
    # with open(cfgfile, 'r') as f:
    #     directory = re.sub('directory=', '', f.readline(), flags=re.DOTALL)
    # home_env = 'HOME'
    # result_dir = f'{os.getenv(home_env)}/feelppdb/{directory.rstrip()}/np_{NP}'
    # result_arch = cfgfile.replace('.cfg', '_res.tgz')
    result_dir = f"{root_directory}/feelppdb/np_{NP}"
    print(f"result_dir={result_dir}")

    paraview = AppCfg["post"]["paraview"]

    # get expr and exprlegend from method/model/...
    if "post" in AppCfg[args.method][args.time][args.geom][args.model]:
        postdata = AppCfg[args.method][args.time][args.geom][args.model]["post"]

        # TODO: Get Path to pv-scalarfield.py:  /usr/lib/python3/dist-packages/python_magnetsetup/postprocessing/
        for key in postdata:
            pyparaview = f'/usr/lib/python3/dist-packages/python_magnetsetup/postprocessing//pv-scalarfield.py --cfgfile {cfgfile}  --jsonfile {jsonfile} --expr {key} --exprlegend "{postdata[key]}" --resultdir {result_dir}'
            # pyparaview = f'pv-scalarfield.py --cfgfile {cfgfile}  --jsonfile {jsonfile} --expr {key} --exprlegend \"{postdata[key]}\" --resultdir {result_dir}'
            pyparaviewcmd = f"pvpython {pyparaview}"
            cmds[
                "Postprocessing"
            ] = f"singularity exec {simage_path}/{paraview} {pyparaviewcmd}"

    # cmds["Save"] = f"pushd {result_dir}/.. && tar zcf {result_arch} np_{NP} && popd && mv {result_dir}/../{result_arch} ."

    # TODO jobmanager if node_spec.manager != JobManagerType.none
    # Need user email at this point
    # Template for oar and slurm

    # TODO what about postprocess??
    # TODO get results (value.csv, png, raw data) to magnetdb

    return cmds
