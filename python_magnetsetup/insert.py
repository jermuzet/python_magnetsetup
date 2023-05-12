from typing import List, Type

import yaml
import copy

from python_magnetgeo.Insert import Insert

from .jsonmodel import (
    create_params_insert,
    create_bcs_insert,
    create_materials_insert,
    create_models_insert,
)
from .utils import Merge, NMerge
from .file_utils import MyOpen, findfile, search_paths

import os


# MyEnv: Union[Type[appenv]|None]
def Insert_simfile(
    MyEnv, confdata: dict, cad: Insert, addAir: bool = False, debug: bool = False
):
    print(f"Insert_simfile: cad={cad.name}")

    files = []

    # TODO: get xao and brep if they exist, otherwise go on
    # TODO: add suffix _Air if needed ??
    try:
        xaofile = cad.name + ".xao"
        if addAir:
            xaofile = cad.name + "_withAir.xao"
        f = findfile(xaofile, paths=search_paths(MyEnv, "cad"))
        files.append(f)

        brepfile = cad.name + ".brep"
        if addAir:
            brepfile = cad.name + "_withAir.brep"
        f = findfile(brepfile, paths=search_paths(MyEnv, "cad"))
        files.append(f)
    except:
        pass

    for helix in cad.Helices:
        with MyOpen(helix + ".yaml", "r", paths=search_paths(MyEnv, "geom")) as f:
            hhelix = yaml.load(f, Loader=yaml.FullLoader)
            files.append(f.name)

            # TODO: get xao and brep if they exist otherwise _salome.data
            try:
                xaofile = hhelix.name + ".xao"
                f = findfile(xaofile, paths=search_paths(MyEnv, "cad"))
                files.append(f)

                brepfile = hhelix.name + ".brep"
                f = findfile(brepfile, paths=search_paths(MyEnv, "cad"))
                files.append(f)
            except:
                pass

            # TODO: get _salome.data if they exist otherwise ??
            try:
                if hhelix.m3d.with_shapes:
                    with MyOpen(
                        hhelix.name + str("_cut_with_shapes_salome.dat"),
                        "r",
                        paths=search_paths(MyEnv, "geom"),
                    ) as fcut:
                        files.append(fcut.name)
                    with MyOpen(
                        hhelix.shape.profile, "r", paths=search_paths(MyEnv, "geom")
                    ) as fshape:
                        files.append(fshape.name)
                else:
                    with MyOpen(
                        hhelix.name + str("_cut_salome.dat"),
                        "r",
                        paths=search_paths(MyEnv, "geom"),
                    ) as fcut:
                        files.append(fcut.name)
            except:
                pass

    for ring in cad.Rings:
        with MyOpen(ring + ".yaml", "r", paths=search_paths(MyEnv, "geom")) as f:
            files.append(f.name)
        try:
            xaofile = ring.name + ".xao"
            f = findfile(xaofile, paths=search_paths(MyEnv, "cad"))
            files.append(f)

            brepfile = ring.name + ".brep"
            f = findfile(brepfile, paths=search_paths(MyEnv, "cad"))
            files.append(f)
        except:
            pass

    if cad.CurrentLeads:
        for lead in cad.CurrentLeads:
            with MyOpen(lead + ".yaml", "r", paths=search_paths(MyEnv, "geom")) as f:
                files.append(f.name)
            try:
                xaofile = lead.name + ".xao"
                f = findfile(xaofile, paths=search_paths(MyEnv, "cad"))
                files.append(f)

                brepfile = lead.name + ".brep"
                f = findfile(brepfile, paths=search_paths(MyEnv, "cad"))
                files.append(f)
            except:
                pass

    return files


# MyEnv: Type[config.appenv]
def Insert_setup(
    MyEnv,
    mname: str,
    confdata: dict,
    cad: Insert,
    method_data: List,
    templates: dict,
    current: float = 31.0e3,
    debug: bool = False,
):
    print(f"Insert_setup: mname={mname}, cad={cad.name}")
    print(f"MyEnv: {type(MyEnv)}")

    part_thermic = []
    part_electric = []
    part_conductors = []
    part_mat_conductors = []
    part_insulators = []
    part_mat_insulators = []
    index_Helices = []
    index_Helices_e = []
    index_Insulators = []

    boundary_meca = []
    boundary_maxwell = []
    boundary_electric = []

    gdata = cad.get_params(MyEnv.yaml_repo)
    (NHelices, NRings, NChannels, Nsections, R1, R2, Z1, Z2, Zmin, Zmax, Dh, Sh) = gdata

    print(
        f"Insert: {cad.name}, NHelices={NHelices}, NRings={NRings}, NChannels={NChannels}"
    )

    pitch_h = []
    turns_h = []

    prefix = ""
    if mname:
        prefix = f"{mname}_"

    for i in range(NHelices):
        part_helix = []
        with MyOpen(
            cad.Helices[i] + ".yaml", "r", paths=search_paths(MyEnv, "geom")
        ) as f:
            hhelix = yaml.load(f, Loader=yaml.FullLoader)
            pitch_h.append(hhelix.axi.pitch)
            turns_h.append(hhelix.axi.turns)

        if method_data[2] == "Axi":
            part_insulator = []
            part_insulator.append(f"{prefix}H{i+1}_Cu{0}")
            part_insulator.append(f"{prefix}H{i+1}_Cu{Nsections[i] + 1}")
            part_mat_insulators.append(part_insulator)

            part_conductors.append(f"Conductor_{prefix}H{i+1}")
            part_insulators.append(f"Insulator_{prefix}H{i+1}")
            for j in range(1, Nsections[i] + 1):
                part_helix.append(f"{prefix}H{i+1}_Cu{j}")
            for j in range(Nsections[i]):
                index_Helices.append([f"0:{Nsections[i]+2}"])
                index_Helices_e.append([f"1:{Nsections[i]+1}"])
            part_mat_conductors.append(part_helix)
        else:
            part_electric.append(f"{prefix}H{i+1}")
            if "th" in method_data[3]:
                part_thermic.append(f"{prefix}H{i+1}")

            (insulator_name, insulator_number) = hhelix.insulators()
            insulator_name = f"{prefix}{insulator_name}"
            index_Insulators.append((insulator_name, insulator_number))
            if "th" in method_data[3]:
                part_thermic.append(insulator_name)

    if method_data[2] == "Axi":
        import numpy as np

        part_electric = part_electric + list(np.concatenate(part_mat_conductors).flat)
        if "th" in method_data[3]:
            part_thermic = (
                part_thermic
                + part_electric
                + list(np.concatenate(part_mat_insulators).flat)
            )

    for i in range(NRings):
        if "th" in method_data[3]:
            part_thermic.append(f"{prefix}R{i+1}")

        if method_data[2] == "3D":
            part_electric.append(f"{prefix}R{i+1}")
        else:
            part_mat_insulators.append([f"{prefix}R{i+1}"])
            part_insulators.append(f"{prefix}R{i+1}")

    # Add currentLeads
    if method_data[2] == "3D":
        if cad.CurrentLeads:
            if "th" in method_data[3]:
                part_thermic.append(f"{prefix}iL1")
                part_thermic.append(f"{prefix}oL2")
            part_electric.append(f"{prefix}iL1")
            part_electric.append(f"{prefix}oL2")
            boundary_electric.append([f"{prefix}Inner1_LV0", f"{prefix}iL1", "0"])
            boundary_electric.append([f"{prefix}OuterL2_LV0", f"{prefix}oL2", "V0:V0"])

            if "el" in method_data[3] and method_data[3] != "thelec":
                boundary_meca.append(f"{prefix}Inner1_LV0")
                boundary_meca.append(f"{prefix}OuterL2_LV0")

            if "mag" in method_data[3]:
                boundary_maxwell.append("InfV00")
                boundary_maxwell.append("InfV01")
        else:
            boundary_electric.append([f"{prefix}H1_V0", "H1", "0"])
            boundary_electric.append(
                [f"{prefix}H{NHelices}_V0", f"{prefix}H{NHelices}", "V0:V0"]
            )

        if "mag" in method_data[3]:
            boundary_maxwell.append("InfV1")
            boundary_maxwell.append("InfR1")

    else:
        boundary_meca.append(f"{prefix}H1_HP")
        boundary_meca.append(f"{prefix}H_HP")

        if "mag" in method_data[3]:
            boundary_maxwell.append("ZAxis")
            boundary_maxwell.append("Infty")

    if "el" in method_data[3] and method_data[3] != "thelec":
        for i in range(1, NRings + 1):
            if i % 2 == 1:
                boundary_meca.append(f"{prefix}R{i}_BP")
            else:
                boundary_meca.append(f"{prefix}R{i}_HP")

    if debug:
        print("insert part_electric:", part_electric)
        print("insert part_thermic:", part_thermic)
        print("insert part_insulators:", part_insulators)
        print("insert part_mat_insulators:", part_mat_insulators)
        print("insert part_conductors:", part_conductors)
        print("insert part_mat_conductors:", part_mat_conductors)

    # params section
    params_data = create_params_insert(mname, gdata + (turns_h,), method_data, debug)

    # bcs section
    bcs_data = create_bcs_insert(
        boundary_meca,
        boundary_maxwell,
        boundary_electric,
        (mname,) + gdata,
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
    NMerge(params_data, mdict, debug, "insert_setup params")
    NMerge(bcs_data, mdict, debug, "insert_setup bcs_data")
    # mdict = NMerge( NMerge(main_data, params_data), bcs_data, debug, "insert_setup mdict")

    # add power per magnet data: mdict = NMerge( mdict, {'power_ma    # add init data:
    iname = cad.name
    if prefix:
        iname = mname
    init_temp_data = []
    init_temp_data.append(
        {
            "name": f"{mname}",
            "prefix": f"{prefix}",
            "magnet_parts": copy.deepcopy(part_thermic),
        }
    )
    init_temp_dict = {"init_temp": init_temp_data}
    NMerge(init_temp_dict, mdict, debug, "insert_setup mdict")
    # print('insert_setup: add init_temp mdict[init_temp] = {mdict["init_temp"]}')
    # print(f'init_tem_data({mname}): {init_temp_data}')

    # add power per magnet data: mdict = NMerge( mdict, {'power_magnet': power_data}, debug, "bitter_setup mdict")
    power_data = []
    power_data.append(
        {"name": f"{mname}", "magnet_parts": copy.deepcopy(part_electric)}
    )
    power_dict = {"power_magnet": power_data}
    NMerge(power_dict, mdict, debug, "insert_setup mdict")
    # print(f'power_data({mname}): {power_data}')

    main_data = {
        "part_thermic": part_thermic,
        "part_electric": part_electric,
        "part_insulators": part_insulators,
        "part_mat_insulators": part_mat_insulators,
        "part_conductors": part_conductors,
        "part_mat_conductors": part_mat_conductors,
        "index_V0": boundary_electric,
        "temperature_initfile": "tini.h5",
        "V_initfile": "Vini.h5",
    }
    NMerge(main_data, mdict, debug, "insert_setup params")

    print("insert_setup: post-processing section")
    currentH_data = []
    powerH_data = []
    meanT_data = []
    Stress_data = []
    VonMises_data = []

    from .units import load_units, convert_data

    unit_Length = method_data[5]  # "meter"
    units = load_units(unit_Length)
    plotB_data = {
        "Rinf": convert_data(units, R2[-1], "Length"),
        "Zinf": convert_data(units, Zmax[-1], "Length"),
    }

    if prefix:
        meanT_data.append(
            {"header": f"T_{prefix}", "markers": copy.deepcopy(part_thermic)}
        )

    # if method_data[3] != 'mag' and method_data[3] != 'mag_hcurl':
    if method_data[2] == "Axi":
        currentH_data.append({"part_electric": part_electric})
        for i in range(NHelices):
            meanT_data.append(
                {
                    "header": f"T_{prefix}H{i+1}",
                    "markers": {
                        "name": f"{prefix}H{i+1}_Cu%1%",
                        "index1": index_Helices[i],
                    },
                }
            )
            powerH_data.append(
                {
                    "header": f"Power_{prefix}H{i+1}",
                    "markers": {
                        "name": f"{prefix}H{i+1}_Cu%1%",
                        "index1": index_Helices_e[i],
                    },
                }
            )
            Stress_data.append(
                {
                    "header": f"Stress_{prefix}H{i+1}",
                    "markers": {
                        "name": f"{prefix}H{i+1}_Cu%1%",
                        "index1": index_Helices[i],
                    },
                }
            )
            VonMises_data.append(
                {
                    "header": f"VonMises_{prefix}H{i+1}",
                    "markers": {
                        "name": f"{prefix}H{i+1}_Cu%1%",
                        "index1": index_Helices[i],
                    },
                }
            )

        for i in range(NRings):
            meanT_data.append(
                {"header": f"T_{prefix}R{i+1}", "markers": {"name": f"{prefix}R{i+1}"}}
            )

    else:
        for i in range(NHelices):
            powerH_data.append(
                {
                    "header": f"Power_{prefix}H{i+1}",
                    "markers": {"name": f"{prefix}H{i+1}_Cu"},
                }
            )
            meanT_data.append(
                {
                    "header": f"T_{prefix}H{i+1}",
                    "markers": {"name": f"{prefix}H{i+1}_Cu"},
                }
            )
            Stress_data.append(
                {
                    "header": f"Stress_{prefix}H{i+1}",
                    "markers": {"name": f"{prefix}H{i+1}_Cu"},
                }
            )
            VonMises_data.append(
                {
                    "header": f"VonMises_{prefix}H{i+1}",
                    "markers": {
                        "name": f"{prefix}H{i+1}_Cu%1%",
                        "index1": index_Helices[i],
                    },
                }
            )

        if cad.CurrentLeads:
            print("insert: 3D currentH, powerH, meanT for leads")
            currentH_data.append(
                {
                    "header": f"Intensity_{prefix}iL1",
                    "markers": {"name:": f"{prefix}iL1_V0"},
                }
            )
            currentH_data.append(
                {
                    "header": f"Intensity_{prefix}oL2",
                    "markers": {"name:": f"{prefix}oL2_V0"},
                }
            )
            powerH_data.append(
                {"header": f"Power_{prefix}iL1", "markers": {"name": f"{prefix}iL1"}}
            )
            powerH_data.append(
                {"header": f"Power_{prefix}oL2", "markers": {"name": f"{prefix}oL2"}}
            )
            meanT_data.append(
                {"header": f"T_{prefix}iL1", "markers": {"name": f"{prefix}iL1"}}
            )
            meanT_data.append(
                {"header": f"T_{prefix}oL2", "markers": {"name": f"{prefix}oL2"}}
            )
        else:
            currentH_data.append(
                {
                    "header": f"Intensity_{prefix}H1",
                    "markers": {"name:": f"{prefix}H1_V0"},
                }
            )
            currentH_data.append(
                {
                    "header": f"Intensity_{prefix}H{NHelices}",
                    "markers": {"name:": f"{prefix}H{NHelices}_V0"},
                }
            )

        print(f"insert: 3D powerH for {NRings} rings")
        for i in range(NRings):
            powerH_data.append(
                {
                    "header": f"Power_{prefix}R{i+1}",
                    "markers": {"name": f"{prefix}R{i+1}"},
                }
            )
            meanT_data.append(
                {"header": f"T_{prefix}R{i+1}", "markers": {"name": f"{prefix}R{i+1}"}}
            )

    suffix = ""
    if "H" in method_data[4]:
        suffix = "%1%"

    mpost = {
        "Power": powerH_data,
        "Current": currentH_data,
        "Flux": [
            {
                "prefix": f"{prefix}Channel",
                "hw": f"{prefix}hw{suffix}",
                "Tw": f"{prefix}Tw{suffix}",
                "dTw": f"{prefix}dTw{suffix}",
                "Zmin": f"{prefix}Zmin{suffix}",
                "Zmax": f"{prefix}Zmax{suffix}",
                "index_h": f"0:{str(NChannels)}",
            }
        ],
        "T": meanT_data,
        "Stress": Stress_data,
        "VonMises": VonMises_data,
    }

    if "mag" in method_data[3] or "mqs" in method_data[3]:
        mpost["B"] = plotB_data

    # check mpost output
    # print(f"insert: mpost={mpost}")
    mmat = create_materials_insert(
        (mname,) + gdata,
        main_data,
        index_Insulators,
        confdata,
        templates,
        method_data,
        debug,
    )

    mmodels = {}
    if "th" in method_data[3]:
        mmodels["heat"] = create_models_insert(
            gdata,
            main_data,
            index_Insulators,
            confdata,
            templates,
            method_data,
            "heat",
            debug,
        )

    if "mag" in method_data[3] or "mqs" in method_data[3]:
        mmodels["magnetic"] = create_models_insert(
            gdata,
            main_data,
            index_Insulators,
            confdata,
            templates,
            method_data,
            "magnetic",
            debug,
        )

    if "magel" in method_data[3]:
        mmodels["elastic"] = create_models_insert(
            gdata,
            main_data,
            index_Insulators,
            confdata,
            templates,
            method_data,
            "elastic",
            debug,
        )

    if "mqsel" in method_data[3]:
        mmodels["elastic1"] = create_models_insert(
            gdata,
            main_data,
            index_Insulators,
            confdata,
            templates,
            method_data,
            "elastic1",
            debug,
        )
        mmodels["elastic2"] = create_models_insert(
            gdata,
            main_data,
            index_Insulators,
            confdata,
            templates,
            method_data,
            "elastic2",
            debug,
        )

    # update U and hw, dTw param
    print(f"{iname}: Update U for I0={current}A")  # ?? mname
    # print(f"insert: mmat: {mmat}")
    # print(f"insert: mdict['Parameters']: {mdict['Parameters']}")
    I0 = current  # 31.e+3
    if method_data[2] == "Axi":
        import math

        params = params_data["Parameters"]
        for i in range(NHelices):
            pitch = pitch_h[i]
            turns = turns_h[i]
            mat = mmat[f"Conductor_{prefix}H{i+1}"]
            for j in range(Nsections[i]):
                marker = f"{prefix}H{i+1}_Cu{j+1}"
                item = {"name": f"U_{marker}", "value": "1"}
                index = params.index(item)
                # print(f"mat[{marker}]: {mat}")
                # print("U=", params[index], mat['sigma'], R1[i], pitch_h[j])
                if method_data[6]:
                    sigma = float(mat["sigma0"])
                else:
                    sigma = float(mat["sigma"])
                I_s = I0 * turns_h[i][j]
                j1 = I_s / (
                    math.log(R2[i] / R1[i])
                    * (R1[i] * 1.0e-3)
                    * (pitch[j] * 1.0e-3)
                    * turns[j]
                )
                U_s = 2 * math.pi * (R1[i] * 1.0e-3) * j1 / sigma
                # print("U=", params[index]['name'], R1[i], R2[i], pitch[j], turns[j], mat['sigma'], "U_s=", U_s, "j1=", j1)
                item = {"name": f"U_{marker}", "value": str(U_s)}
                params[index] = item

    return (mdict, mmat, mmodels, mpost)
