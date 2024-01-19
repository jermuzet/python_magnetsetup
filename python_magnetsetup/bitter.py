from typing import List, Optional

import yaml
import copy

from python_magnetgeo.Bitter import Bitter

from .jsonmodel import (
    create_params_bitter,
    create_params_csvfiles_bitter,
    create_bcs_bitter,
    create_materials_bitter,
    create_models_bitter,
)
from .utils import Merge, NMerge

import os

from .file_utils import MyOpen, findfile, search_paths


def Bitter_simfile(MyEnv, confdata: dict, cad: Bitter, debug: bool = False):
    print(f"Bitter_simfile: cad={cad.name}")

    from .file_utils import MyOpen, findfile

    yamlfile = confdata["geom"]
    with MyOpen(yamlfile, "r", paths=search_paths(MyEnv, "geom")) as cfgdata:
        return cfgdata


def Bitter_setup(
    MyEnv,
    mname: str,
    confdata: dict,
    cad: Bitter,
    method_data: List,
    templates: dict,
    current: float = 31.0e3,
    debug: bool = False,
):
    print(f"Bitter_setup: magnet={mname}, cad={cad.name}")
    if debug:
        print(f"Bitter_setup/Bitter confdata: {confdata}")

    prefix = ""
    if mname:
        prefix = mname + "_"

    print(f"Bitter_setup:  magnet={mname}, cad={cad.name}")
    print(f"cad={cad}")
    print(f"cad.get_params={cad.get_params(MyEnv.yaml_repo)}")
    (NCoolingSlits, Dh, Sh, Zh, fillingfactor) = cad.get_params(MyEnv.yaml_repo)

    part_thermic = []
    part_electric = []

    part_conductors = []
    part_insulators = []

    index_ABitters = ""
    index_Bitters = ""

    boundary_meca = []
    boundary_maxwell = []
    boundary_electric = []

    yamlfile = confdata["geom"]
    if debug:
        print(f"Bitter_setup/Bitter yamlfile: {yamlfile}")

    NSections = len(cad.axi.turns)
    if debug:
        print(f"cad: {cad} tpe: {type(cad)}")

    ignore_index = []
    snames = []
    name = f"{prefix}{cad.name}"  # .replace('Bitter_','')
    if method_data[2] == "Axi":
        if cad.z[0] < -cad.axi.h:
            snames.append(f"{name}_B0")
            part_thermic.append(snames[-1])
            ignore_index.append(len(snames) - 1)
        for i in range(NSections):
            snames.append(f"{name}_B{i+1}")
            part_electric.append(snames[-1])
            part_thermic.append(snames[-1])
        if cad.z[1] > cad.axi.h:
            snames.append(f"{name}_B{NSections+1}")
            part_thermic.append(snames[-1])
            ignore_index.append(len(snames) - 1)
        start = int(snames[0].replace(f"{name}_B", ""))
        end = len(snames)
        if end == start:
            end = end + 1
        index_ABitters = f"{start}:{end}"
        index_Bitters = f"{1}:{NSections+1}"

        part_conductors.append(f"Conductor_{name}")
        if list(set(part_thermic) - set(part_electric)):
            part_insulators.append(f"Insulator_{name}")
        if debug:
            print("sname:", snames)
    else:
        part_electric.append(cad.name)
        if "th" in method_data[3]:
            part_thermic.append(cad.name)

    if debug:
        print("bitter part_thermic:", part_thermic)
        print("bitter part_electric:", part_electric)

    if method_data[2] == "Axi" and (
        "el" in method_data[3] and method_data[3] != "thelec"
    ):
        boundary_meca.append(f"{name}_HP")
        boundary_meca.append(f"{name}_BP")

        boundary_maxwell.append("ZAxis")
        boundary_maxwell.append("Infty")

    # params section
    gdata = (
        name,
        snames,
        cad.axi.turns,
        NCoolingSlits,
        Dh,
        Sh,
        Zh,
        fillingfactor,
        ignore_index,
    )
    params_data = create_params_bitter(mname, gdata, method_data, debug)
    # print(f"bitter: params_data: {params_data}")
    if "Z" in method_data[4]:
        params_csv_files = create_params_csvfiles_bitter(
            mname, gdata, method_data, debug
        )
        for key, value in params_csv_files.items():
            # print(f"save {key}.csv")
            value.to_csv(f"{key}.csv", index=False)  # with index add: index=True

    # bcs section
    bcs_data = create_bcs_bitter(
        boundary_meca,
        boundary_maxwell,
        boundary_electric,
        gdata,
        confdata,
        templates,
        method_data,
        debug,
    )  # merge all bcs dict
    # print(f'bcs_data({mname}): {bcs_data}')

    # build dict from geom for templates
    # TODO fix initfile name (see create_cfg for the name of output / see directory entry)
    # eg: $home/feel[ppdb]/$directory/cfpdes-heat.save

    mdict = {}
    print("bitter_setup: merge params_data")
    NMerge(params_data, mdict, debug, "bitter_setup params")
    print("bitter_setup: merge bcs_data")
    NMerge(bcs_data, mdict, debug, "bitter_setup bcs_data")
    # mdict = NMerge( NMerge(main_data, params_data), bcs_data, debug, "bitter_setup mdict")

    # add init data:
    init_name = mname
    if not init_name:
        init_name = "Bitter"
    init_temp_data = []
    # init_temp_data.append( {'name': f'{mname}', "part_thermic_part": part_thermic } )
    print(f"bitter: init_temp: name={init_name}")
    init_temp_data.append(
        {
            "name": init_name,
            "prefix": prefix,
            "magnet_parts": copy.deepcopy(part_thermic),
        }
    )
    init_temp_dict = {"init_temp": init_temp_data}
    NMerge(init_temp_dict, mdict, debug, name="bitter_setup init")
    print(f'bitter_setup: add init_temp mdict[init_temp] = {mdict["init_temp"]}')
    # print(f'init_tem_data({mname}): {init_temp_data}')

    # add power per magnet data: mdict = NMerge( mdict, {'power_magnet': power_data}, debug, "bitter_setup mdict")
    print("bitter_setup: add power_magnet")
    power_data = []
    power_data.append(
        {"name": f"{mname}", "magnet_parts": copy.deepcopy(part_electric)}
    )
    power_dict = {"power_magnet": power_data}
    NMerge(power_dict, mdict, debug, "bitter_setup power")
    # print(f'power_data({mname}): {power_data}')

    # add T per magnet data: mdict = NMerge( mdict, {'T_magnet': T_data}, debug, "bitter_setup mdict")
    print("bitter_setup: add T_magnet")
    T_data = []
    T_data.append({"name": f"{mname}", "magnet_parts": copy.deepcopy(part_thermic)})
    T_dict = {"T_magnet": T_data}
    NMerge(T_dict, mdict, debug, "bitter_setup T")
    # print(f'T_data({mname}): {T_data}')

    # print(f"mdict[init_temp]={mdict['init_temp']}")
    # print(f"mdict[power_magnet]={mdict['power_magnet']}")

    main_data = {
        "part_thermic": part_thermic,
        "part_electric": part_electric,
        "part_insulators": part_insulators,
        "part_conductors": part_conductors,
        "index_V0": boundary_electric,
        "temperature_initfile": "tini.h5",
        "V_initfile": "Vini.h5",
    }
    print("bitter_setup: add main_data")
    NMerge(main_data, mdict, debug, "bitter_setup params")
    # print(f"mdict[init_temp]={mdict['init_temp']}")
    # print(f"mdict[power_magnet]={mdict['power_magnet']}")

    print("bitter_setup: post-processing section")
    currentH_data = []
    powerH_data = []
    meanT_data = []
    Stress_data = []
    VonMises_data = []

    from .units import load_units, convert_data

    unit_Length = method_data[5]  # "meter"
    units = load_units(unit_Length)
    # print(f"Rinf={cad.r[-1]}, Zinf={cad.z[-1]}")
    plotB_data = {
        "Rinf": convert_data(units, cad.r[-1], "Length"),
        "Zinf": convert_data(units, cad.z[-1], "Length"),
    }

    if method_data[2] == "Axi":
        currentH_data.append({"part_electric": part_electric})
        powerH_data.append(
            {
                "header": f"Power_{name}",
                "markers": {"name": f"{name}_B%1%", "index1": index_Bitters},
            }
        )
        meanT_data.append(
            {
                "header": f"T_{name}",
                "markers": {"name": f"{name}_B%1%", "index1": index_ABitters},
            }
        )
        Stress_data.append(
            {
                "header": f"Stress_{name}",
                "markers": {"name": f"{name}_B%1%", "index1": index_ABitters},
            }
        )
        VonMises_data.append(
            {
                "header": f"VonMises_{name}",
                "markers": {"name": f"{name}_B%1%", "index1": index_ABitters},
            }
        )

    else:
        print("bitter3D post not implemented")

    flux_data = []
    fluxZ_data = []
    Zh = convert_data(units, Zh, "Length")
    # print(f"Zh: {Zh}")
    for i in range(NCoolingSlits + 2):
        markers = f'["{name}_Slit{i}"]'
        filling_factor = 1

        if method_data[2] == "Axi":
            filling_factor = fillingfactor[i]  # get filling factor from magnetgeo??
            if i != 0 and i != NCoolingSlits + 1:
                markers = f'["{name}_Slit{i}_l","{name}_Slit{i}_r"]'
            flux_data.append([i, filling_factor])

        index_data = []
        for s in range(len(Zh) - 1):
            # print(f"index_data: i={i}, Zh[{s}]={Zh[s]}, Zh[{s+1}]={Zh[s+1]}")

            """
            index_data:
            %1_1%: s
            %1_2%: nslit
            %1_3%: slit.r
            %1_4%: rslit
            -> group them in fillingfactor
            %1_5%: Zh[s]
            %1_6% : Zh[s+1]
            %1_7%: f"[{name}_Slit{i}_l,{name}_Slit{i}_r]" ??

            f"[{name}_Slit{i}_l,{name}_Slit{i}_r]"
            """

            index_data.append([s, Zh[s], Zh[s + 1]])

        data = {
            "prefix": f"{name}_Slit{i}",
            "hw": f"hw_{name}_Slit{i}",
            "Tw": f"Tw_{name}_Slit{i}",
            "markers": markers,
            "index_h": [flux_data[-1]],
            "index_z": index_data,
        }

        fluxZ_data.append(data)

    # TODO change for slit0 and latest slit
    bcname = name
    bcname_first = name
    bcname_last = name
    if "H" in method_data[4]:
        bcname = f"{name}_Slit%1_1%"
        bcname_first = f"{name}_Slit0"
        bcname_last = f"{name}_Slit{NCoolingSlits+1}"

    # markers_dict = {"name": f"{name}_Slit%1_1%%2%", "index2": ["_l", "_r"]}

    mpost = {
        "Power": currentH_data,
        "PowerH": powerH_data,
        "Current": currentH_data,
        # add id, fillingfactor, markers list to index_h
        # and change template stats_Flux-gradZ
        "Flux": [
            {
                "prefix": f"{name}_Slit0",
                "markers": f'["{name}_Slit0"]',
                "hw": f"hw_{bcname_first}",
                "Tw": f"Tw_{bcname_first}",
                "dTw": f"dTw_{bcname_first}",
                "Zmin": f"Zmin_{bcname_first}",
                "Zmax": f"Zmax_{bcname_first}",
                "index_h": [flux_data[0]],
            },
            {
                "prefix": f"{name}_Slit%1_1%",
                "markers": f'["{name}_Slit{i}_l","{name}_Slit{i}_r"]',
                "hw": f"hw_{bcname}",
                "Tw": f"Tw_{bcname}",
                "dTw": f"dTw_{bcname}",
                "Zmin": f"Zmin_{bcname}",
                "Zmax": f"Zmax_{bcname}",
                "index_h": flux_data[1:-1],
            },
            {
                "prefix": f"{name}_Slit{NCoolingSlits+1}",
                "markers": f'["{name}_Slit{NCoolingSlits+1}"]',
                "hw": f"hw_{bcname_last}",
                "Tw": f"Tw_{bcname_last}",
                "dTw": f"dTw_{bcname_last}",
                "Zmin": f"Zmin_{bcname_last}",
                "Zmax": f"Zmax_{bcname_last}",
                "index_h": [flux_data[-1]],
            },
        ],
        "T": meanT_data,
        "Stress": Stress_data,
        "VonMises": VonMises_data,
    }

    if "Z" in method_data[4]:
        mpost["Flux"] = fluxZ_data

    if "mag" in method_data[3] or "mqs" in method_data[3]:
        mpost["B"] = plotB_data

    # check mpost output
    # print(f"bitter {name}: mpost={mpost}")
    mmat = create_materials_bitter(
        gdata, main_data, confdata, templates, method_data, debug
    )

    mmodels = {}
    for physic in templates["physic"]:
        mmodels[physic] = create_models_bitter(
            gdata,
            main_data,
            confdata,
            templates,
            method_data,
            physic,
            debug,
        )

    # update U and hw, dTw param
    print(f"{mname}: Update U for I0={current}A")
    # print(f"insert: mmat: {mmat}")
    # print(f"insert: mdict['Parameters']: {mdict['Parameters']}")
    I0 = current  # 31.e+3
    if method_data[2] == "Axi":
        import math

        params = params_data["Parameters"]

        mat = mmat[f"Conductor_{name}"]  ### ??? A VOIR

        for j in range(NSections):
            marker = f"{name}_B{j+1}"
            # print("marker:", marker)
            item = {"name": f"U_{marker}", "value": "1"}
            index = params.index(item)

            # print("U=", params[index], mat['sigma'], R1[i], pitch_h[i][j])
            if method_data[6]:
                sigma = float(mat["sigma0"])
            else:
                sigma = float(mat["sigma"])
            I_s = I0 * cad.axi.turns[j]
            j1 = I_s / (
                math.log(cad.r[1] / cad.r[0])
                * (cad.r[0] * 1.0e-3)
                * (cad.axi.pitch[j] * 1.0e-3)
                * cad.axi.turns[j]
            )
            U_s = 2 * math.pi * (cad.r[0] * 1.0e-3) * j1 / sigma
            # print("U=", params[index]['name'], cad.r[0], cad.axi.pitch[j], mat['sigma'], "U_s=", U_s, "j1=", j1)
            item = {"name": f"U_{marker}", "value": str(U_s)}
            params[index] = item

    return (mdict, mmat, mmodels, mpost)
