from typing import List, Optional

import os
import yaml
import copy
import re

from python_magnetgeo.Supra import Supra

from .jsonmodel import (
    create_params_supra,
    create_bcs_supra,
    create_materials_supra,
    create_models_supra,
)
from .utils import NMerge

from .file_utils import MyOpen, findfile, search_paths


def Supra_simfile(MyEnv, confdata: dict, cad: Supra, debug: bool = False):
    print(f"Supra_simfile: cad={cad.name}")
    print(f"Supra_simfile: confdata={confdata}")

    files = []

    yamlfile = confdata["geom"]
    with MyOpen(yamlfile, "r", paths=search_paths(MyEnv, "geom")) as f:
        files.append(f.name)

    if not cad.detail is None:
        structfile = cad.struct
        with MyOpen(structfile, "r", paths=search_paths(MyEnv, "geom")) as f:
            files.append(f.name)

    return files


def Supra_setup(
    MyEnv,
    mname: str,
    confdata: dict,
    cad: Supra,
    method_data: List,
    templates: dict,
    current: float = 31.0e3,
    debug: bool = False,
):
    print(f"Supra_setup: magnet={mname}, cad={cad.name}")
    part_thermic = []
    part_electric = []

    boundary_meca = []
    boundary_maxwell = []
    boundary_electric = []

    mdict = {}
    mmat = {}
    mmodels = {}
    mpost = {}

    snames = []
    name = f"{mname}_{cad.name}"
    # TODO eventually get details

    gdata = (name, snames, cad.detail, cad.struct)
    print(f"supra: cad.Struct={cad.struct}")
    if cad.detail is None:
        part_electric.append(name)
        part_thermic.append(name)
    else:
        # print(f'pwd={os.getcwd()}')
        # print(f"ls={os.system('ls -lrth')}")
        # print(f'cad.Struct: {os.path.isfile(cad.struct)}')
        # print(f'paths={search_paths(MyEnv, "geom")}')
        insert = cad.get_magnet_struct("data/geometries")
        snames = insert.get_names(name, cad.detail, verbose=debug)
        part_thermic = snames

        if cad.detail == "dblpancake":
            search_pattern = f"{name}_{cad.name}_dp_\\d"
            part_eletric = [
                name for name in snames if re.search(search_pattern, name)
            ]  # find all dblpancake in
        elif cad.detail == "pancake":
            search_pattern = f"{name}_{cad.name}_dp_\\d_p[01]"
            part_electric = [
                name for name in snames if re.search(search_pattern, name)
            ]  # find all pancake
        elif cad.detail == "tape":
            part_electric = [
                name for name in snames if name.endswith("_SC")
            ]  # find all _SC in snames
        else:
            raise RuntimeError(
                f"Supra_Setup: {cad.name} - cad.detail unsupported value {cad.detail}- expected dblpancake|pancake|tape"
            )
    print(f"supra: part_electric={part_electric}")

    if debug:
        print("supra part_thermic:", part_thermic)
        print("supra part_electric:", part_electric)

    if method_data[2] == "Axi" and (
        "el" in method_data[3] and method_data[3] != "thelec"
    ):
        boundary_meca.append("{}_V0".format(name))
        boundary_meca.append("{}_V1".format(name))

        boundary_maxwell.append("ZAxis")
        boundary_maxwell.append("Infty")

    # params section
    params_data = create_params_supra(mname, gdata, method_data, debug)

    # bcs section
    bcs_data = create_bcs_supra(
        boundary_meca,
        boundary_maxwell,
        boundary_electric,
        gdata,
        confdata,
        templates,
        method_data,
        debug,
    )  # merge all bcs dict

    # build dict from geom for templates
    # TODO fix initfile name (see create_cfg for the name of output / see directory entry)
    # eg: $home/feel[ppdb]/$directory/cfpdes-heat.save

    mdict = {}
    print("supra_setup: merge params_data")
    NMerge(params_data, mdict, debug, "supra_setup params")
    print("supra_setup: merge bcs_data")
    NMerge(bcs_data, mdict, debug, "supra_setup bcs_data")
    # mdict = NMerge( NMerge(main_data, params_data), bcs_data, debug, "supra_setup mdict")

    # add init data:
    # print("supra_setup: add init_temp")
    init_temp_data = []
    init_temp_data.append(
        {"name": f"{mname}", "magnet_parts": copy.deepcopy(part_thermic)}
    )
    init_temp_dict = {"init_temp": init_temp_data}
    NMerge(init_temp_dict, mdict, debug, name="supra_setup init")
    print('supra_setup: add init_temp mdict[init_temp] = {mdict["init_temp"]}')

    print("supra_setup: add power_magnet")
    power_data = []
    power_data.append(
        {"name": f"{mname}", "magnet_parts": copy.deepcopy(part_electric)}
    )
    power_dict = {"power_magnet": power_data}
    NMerge(power_dict, mdict, debug, "supra_setup power")

    # add T per magnet data: mdict = NMerge( mdict, {'T_magnet': T_data}, debug, "bitter_setup mdict")
    T_data = []
    T_data.append(
        {"name": f"{mname}", "magnet_parts": copy.deepcopy(part_thermic)}
    )
    T_dict = {"T_magnet": T_data}
    NMerge(T_dict, mdict, debug, "insert_setup mdict")

    main_data = {
        "part_thermic": part_thermic,
        "part_electric": part_electric,
        "index_V0": boundary_electric,
        "temperature_initfile": "tini.h5",
        "V_initfile": "Vini.h5",
    }
    print("supra_setup: add main_data")
    NMerge(main_data, mdict, debug, "supra_setup params")

    print("supra_setup: post-processing section")
    currentH_data = []
    meanT_data = []
    Stress_data = []
    VonMises_data = []

    from .units import load_units, convert_data

    unit_Length = method_data[5]  # "meter"
    units = load_units(unit_Length)
    plotB_data = {
        "Rinf": convert_data(units, cad.r[-1], "Length"),
        "Zinf": convert_data(units, cad.z[-1], "Length"),
    }

    if method_data[2] == "Axi":
        currentH_data.append({"part_electric": part_electric})
        meanT_data.append({"header": f"T_{name}", "markers": part_electric})
        Stress_data.append({"header": f"Stress_{name}", "markers": part_electric})
        VonMises_data.append({"header": f"VonMises_{name}", "markers": part_electric})

    mpost = {
        "Power": currentH_data,
        "Current": currentH_data,
        "Stress": Stress_data,
        "VonMises": VonMises_data,
    }
    if "mag" in method_data[3] or "mqs" in method_data[3]:
        mpost["B"] = plotB_data

    # check mpost output
    # print(f"supra {name}: mpost={mpost}")
    mmat = create_materials_supra(gdata, confdata, templates, method_data, debug)

    mmodels = {}
    for physic in templates["physic"]:
        mmodels[physic] = create_models_supra(
            gdata, confdata, templates, method_data, physic, debug
        )

    print(f"{mname}: Update Js for I0={current}A")
    if method_data[2] == "Axi":
        import math

        params = params_data["Parameters"]
        # Js= I0*Nturns/Area where Nturns and Area depend on detail
        # eg. detail=None: Nturns total number of tapes, Area
        #     detail=dblpancake Nturns number of tapes per dblpancake, Area of a dblpancake
        #     and so on for detail=pancake and detail=tape (NB turns=1)

    return (mdict, mmat, mmodels, mpost)
