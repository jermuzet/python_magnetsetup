"""
Json file
"""
from typing import List, Union, Optional

import json

import math

from .utils import Merge
from .units import load_units, convert_data


def create_params_csvfiles_supra(
    mname: str, gdata: tuple, method_data: List[str], debug: bool = False
) -> dict:
    """
    Return params_dict, the dictionnary of section \"Parameters\" for JSON file.
    """
    print("create_params_csvfiles_supra for mname={mname}")
    return {}


def create_params_supra(
    mname: str, gdata: tuple, method_data: List[str], debug: bool = False
) -> dict:
    """
    Return params_dict, the dictionnary of section \"Parameters\" for JSON file.
    """
    print("create_params_supra")

    (name, snames, r, z, n, detail, struct)=gdata

    # TODO: length data are written in mm should be in SI instead
    unit_Length = method_data[5]  # "meter"
    units = load_units(unit_Length)

    # Tini, Aini for transient cases??
    params_data = {"Parameters": []}
    # for cfpdes only
    # if method_data[0] == "cfpdes" and method_data[3] in [
    #     "thmagel",
    #     "thmagel_hcurl",
    #     "thmqsel",
    #     "thmqsel_hcurl",
    # ]:
    #     params_data["Parameters"].append({"name": "bool_laplace", "value": 1})
    #     params_data["Parameters"].append({"name": "bool_dilatation", "value": 1})

    # TODO : initialization of parameters with cooling model
    prefix = ""
    if mname:
        prefix = f"{mname}_"

    params_data["Parameters"].append({"name": f"{prefix}Tinit", "value": 4})
    if "mag" in method_data[3] or "mqs" in method_data[3]:
        params_data["Parameters"].append(
            {"name": "mu0", "value": convert_data(units, 4 * math.pi * 1e-7, "mu0")}
        )

    # TODO: get Nturns/Area where Nturns and Area depend on detail
    # eg. detail=None: Nturns total number of tapes, Area
    #     detail=dblpancake Nturns number of tapes per dblpancake, Area of a dblpancake
    #     and so on for detail=pancake and detail=tape (NB turns=1)
    if detail is None:
        Area=convert_data(units,(r[1]-r[0])*(z[1]-z[0]), "Area")
        
        params_data["Parameters"].append({"name": f"{prefix}Nturns", "value": n})
        params_data["Parameters"].append({"name": f"{prefix}Area", "value": Area})
        
        params_data["Parameters"].append({"name": f"{prefix}ec", "value": 1e-4})
        params_data["Parameters"].append({"name": f"{prefix}n", "value": 25})
        params_data["Parameters"].append({"name": f"{prefix}thickness_tape", "value": 1e-6})
        params_data["Parameters"].append({"name": f"{prefix}thickness_cell", "value": 0.07616438356164383e-3})
        params_data["Parameters"].append({"name": f"{prefix}height_tape", "value": 6e-3})
        params_data["Parameters"].append({"name": f"{prefix}I0", "value": 300})


    elif detail == "dblpancake":
        pass
    elif detail == "pancake":
        pass
    elif detail == "tape":
        # open HTS json file to retrieve data for some parameters
        with open(struct) as file:
            data_struct = json.load(file)

        Area=convert_data(units,(r[1]-r[0])*(z[1]-z[0]), "Area")
        #data from HTS json :
        thickness_cell=convert_data(units,data_struct["pancake"]["tape"]["w"], "Length")
        height_tape=convert_data(units,data_struct["pancake"]["tape"]["h"], "Length")
        
        tapes_spacing=convert_data(units,height_tape+data_struct["pancake"]["tape"]["e"], "Length")
        inner_radius=convert_data(units,data_struct["pancake"]["r0"], "Length")
        
        npancakes=2*data_struct["dblpancakes"]["n"]
        ntapes=data_struct["pancake"]["ntapes"]

        params_data["Parameters"].append({"name": f"{prefix}Nturns", "value": n})
        params_data["Parameters"].append({"name": f"{prefix}Area", "value": Area})
        
        params_data["Parameters"].append({"name": f"{prefix}thickness_tape", "value": 1e-6})
        params_data["Parameters"].append({"name": f"{prefix}thickness_cell", "value": thickness_cell})
        params_data["Parameters"].append({"name": f"{prefix}height_tape", "value": height_tape})
        params_data["Parameters"].append({"name": f"{prefix}tapes_spacing", "value": tapes_spacing})
        params_data["Parameters"].append({"name": f"{prefix}inner_radius", "value": inner_radius})
        
        params_data["Parameters"].append({"name": f"{prefix}npancakes", "value": npancakes})
        params_data["Parameters"].append({"name": f"{prefix}ntapes", "value": ntapes})
        
        params_data["Parameters"].append({"name": f"{prefix}ec", "value": 1e-4})
        params_data["Parameters"].append({"name": f"{prefix}n", "value": 25})
        params_data["Parameters"].append({"name": f"{prefix}I0", "value": 300})

    else:
        raise RuntimeError(
            f"Supra_Setup: {snames} - cad.detail unsupported value {detail}- expected None|dblpancake|pancake|tape"
        )
    
    
    if debug:
        print(params_data)

    return params_data


def create_params_csvfiles_bitter(
    mname: str, gdata: tuple, method_data: List[str], debug: bool = False
):
    """
    Return params_dict, the dictionnary of section \"Parameters\" for JSON file.

    method_data:
    """
    print(f"create_params_csvfiles_bitter for mname={mname} gdata[0]={gdata[0]}")

    # TODO: length data are written in mm should be in SI instead
    unit_Length = method_data[5]  # "meter"
    units = load_units(unit_Length)

    (
        name,
        snames,
        nturns,
        NCoolingSlits,
        Dh,
        Sh,
        Zh,
        fillingfactor,
        ignore_index,
    ) = gdata
    Zh = convert_data(units, Zh, "Length")

    res = {}
    import pandas as pd

    for i in range(NCoolingSlits + 2):
        bcname = f"{name}_Slit{i}"
        Tw = [290.671] * len(Zh)
        data = pd.DataFrame(list(zip(Zh, Tw)), columns=["Z", "Tw"])
        res[f"Tw_{bcname}"] = data

    return res


def create_params_csvfiles_insert(
    mname: str, gdata: tuple, method_data: List[str], debug: bool = False
):
    """
    Return params_dict, the dictionnary of section \"Parameters\" for JSON file.

    method_data:
    """
    print(f"create_params_csvfiles_insert for mname={mname} gdata[0]={gdata[0]}")

    # !!! unit conversion already done !!!

    (
        NHelices,
        NRings,
        NChannels,
        Nsections,
        R1,
        R2,
        Dh,
        Sh,
        Zh,
        turns_h,
    ) = gdata

    # TODO : initialization of parameters with cooling model
    prefix = ""
    if mname:
        prefix = f"{mname}_"

    res = {}
    import pandas as pd

    for i in range(NChannels):
        bcname = f"{prefix}Channel{i}"
        Tw = [290.671] * len(Zh[i])
        data = pd.DataFrame(list(zip(Zh[i], Tw)), columns=["Z", "Tw"])
        res[f"Tw_{bcname}"] = data

    return res


def create_params_bitter(
    mname: str, gdata: tuple, method_data: List[str], debug: bool = False
):
    """
    Return params_dict, the dictionnary of section \"Parameters\" for JSON file.

    method_data:
    """
    print(f"create_params_bitter for mname={mname} gdata[0]={gdata[0]}")

    # TODO: length data are written in mm should be in SI instead
    unit_Length = method_data[5]  # "meter"
    units = load_units(unit_Length)

    # Tini, Aini for transient cases??
    params_data = {"Parameters": []}

    # for cfpdes only
    if method_data[0] == "cfpdes" and method_data[3] in [
        "thmagel",
        "thmagel_hcurl",
        "thmqsel",
        "thmqsel_hcurl",
    ]:
        params_data["Parameters"].append({"name": "bool_laplace", "value": "1"})
        params_data["Parameters"].append({"name": "bool_dilatation", "value": "1"})

    # TODO : initialization of parameters with cooling model
    prefix = ""
    if mname:
        prefix = f"{mname}_"

    params_data["Parameters"].append({"name": f"{prefix}Tinit", "value": 293})

    (
        name,
        snames,
        nturns,
        NCoolingSlits,
        Dh,
        Sh,
        Zh,
        fillingfactor,
        ignore_index,
    ) = gdata
    Zmin = min(Zh)
    Zmax = max(Zh)
    if debug:
        print("unit_Length", unit_Length)
        print("Zmax:", Zmax)
        print("Zmin:", Zmin)
    if unit_Length == "meter":
        Zmin = convert_data(units, Zmin, "Length")
        Zmax = convert_data(units, Zmax, "Length")
        Dh = convert_data(units, Dh, "Length")
        Sh = convert_data(units, Sh, "Area")
        Zh = convert_data(units, Zh, "Length")

    # depending on method_data[4] (aka args.cooling)
    if not "H" in method_data[4]:
        params_data["Parameters"].append(
            {"name": f"hw_{name}", "value": convert_data(units, 58222.1, "h")}
        )
        params_data["Parameters"].append({"name": f"Tw_{name}", "value": 290.671})
        params_data["Parameters"].append({"name": f"dTw_{name}", "value": 12.74})
        params_data["Parameters"].append(
            {"name": f"Dh_{name}", "value": sum(Dh) / len(Dh)}
        )
        params_data["Parameters"].append({"name": f"Sh_{name}", "value": sum(Sh)})
        params_data["Parameters"].append({"name": f"Zmin_{name}", "value": Zmin})
        params_data["Parameters"].append({"name": f"Zmax_{name}", "value": Zmax})

    else:
        for i in range(NCoolingSlits + 2):
            bcname = f"{name}_Slit{i}"
            params_data["Parameters"].append(
                {"name": f"hw_{bcname}", "value": convert_data(units, 58222.1, "h")}
            )
            # y for Axi, z for 3D
            zcoord = "y"
            if method_data[2] == "3D":
                zcoord = "z"
            if "Z" in method_data[4]:
                csv_data = {
                    "type": "fit",
                    "filename": f"$cfgdir/Tw_{bcname}.csv",
                    "abscissa": "Z",
                    "ordinate": "Tw",
                    "interpolation": "P1",
                    "expr": f"{zcoord}:{zcoord}",
                }
                params_data["Parameters"].append(
                    {"name": f"Tw_{bcname}", "value": csv_data}
                )
                print(f'{method_data[4]} {bcname}: {params_data["Parameters"][-1]}')
            else:
                params_data["Parameters"].append(
                    {"name": f"Tw_{bcname}", "value": 290.671}
                )
                print(f'{method_data[4]} {bcname}: {params_data["Parameters"][-1]}')
                params_data["Parameters"].append(
                    {"name": f"dTw_{bcname}", "value": 12.74}
                )
            params_data["Parameters"].append({"name": f"Sh_{bcname}", "value": Sh[i]})
            params_data["Parameters"].append({"name": f"Dh_{bcname}", "value": Dh[i]})
            params_data["Parameters"].append({"name": f"Zmin_{bcname}", "value": Zmin})
            params_data["Parameters"].append({"name": f"Zmax_{bcname}", "value": Zmax})
            """
            params_data["Parameters"].append(
                {"name": f"Zh_{bcname}", "value": Zh}
            )  # convert Zh to vector {...}
            """

    # init values for U (Axi specific)
    print(f"create_params_bitter/nturns: {nturns}")
    print(f"create_params_bitter/snames: {snames}")
    print(f"create_params_bitter/ignore_index: {ignore_index}")
    if method_data[2] == "Axi":
        num = 0
        for i, sname in enumerate(snames):
            if not i in ignore_index:
                print(f"N_{sname}: i={i}")
                params_data["Parameters"].append({"name": f"U_{sname}", "value": "1"})
                params_data["Parameters"].append(
                    {"name": f"N_{sname}", "value": nturns[num]}
                )
                num += 1

    if "mag" in method_data[3] or "mqs" in method_data[3]:
        params_data["Parameters"].append(
            {"name": "mu0", "value": convert_data(units, 4 * math.pi * 1e-7, "mu0")}
        )

    if debug:
        print(params_data)

    return params_data


def create_params_insert(
    mname: str, gdata: tuple, method_data: List[str], debug: bool = False
) -> dict:
    """
    Return params_dict, the dictionnary of section \"Parameters\" for JSON file.
    """
    print(f"create_params_insert: mname={mname}")

    # TODO: length data are written in mm should be in SI instead
    unit_Length = method_data[5]  # "meter"
    units = load_units(unit_Length)

    # TDO how to get insert name?
    # is it provided by mname??
    (
        NHelices,
        NRings,
        NChannels,
        Nsections,
        R1,
        R2,
        Dh,
        Sh,
        Zh,
        turns_h,
    ) = gdata

    if debug:
        print("unit_Length", unit_Length)
    if unit_Length == "meter":
        R1 = convert_data(units, R1, "Length")
        R2 = convert_data(units, R2, "Length")
        for i, z in enumerate(Zh):
            Zh[i] = convert_data(units, z, "Length")
        Dh = convert_data(units, Dh, "Length")
        Sh = convert_data(units, Sh, "Area")

    Zmin = []
    Zmax = []
    for i, z in enumerate(Zh):
        Zmin.append(min(Zh[i]))
        Zmax.append(max(Zh[i]))

    # chech dim
    if debug:
        print("corrected R1:", R1)
        print("unit_Length", unit_Length)
        print("R1:", R1, "R2:", R2, "Zmin:", Zmin, "Zmax:", Zmax)

    # Tini, Aini for transient cases??
    params_data = {"Parameters": []}

    # for cfpdes only
    if method_data[0] == "cfpdes" and method_data[3] in [
        "thmagel",
        "thmagel_hcurl",
        "thmqsel",
        "thmqsel_hcurl",
    ]:
        params_data["Parameters"].append({"name": "bool_laplace", "value": "1"})
        params_data["Parameters"].append({"name": "bool_dilatation", "value": "1"})

    # TODO : initialization of parameters with cooling model
    prefix = ""
    if mname:
        prefix = f"{mname}_"

    params_data["Parameters"].append({"name": f"{prefix}Tinit", "value": 293})
    for i in range(NHelices):
        params_data["Parameters"].append(
            {
                "name": f"Area_{prefix}H{i+1}",
                "value": abs((R2[i] - R1[i]) * (Zmax[i] - Zmin[i])),
            }
        )

    # get value from coolingmethod and Flow(I) value
    if not "H" in method_data[4]:
        params_data["Parameters"].append(
            {"name": f"hw_{prefix}Channel", "value": convert_data(units, 58222.1, "h")}
        )
        params_data["Parameters"].append(
            {"name": f"Tw_{prefix}Channel", "value": 290.671}
        )
        params_data["Parameters"].append(
            {"name": f"dTw_{prefix}Channel", "value": 12.74}
        )
        params_data["Parameters"].append(
            {"name": f"Dh_{prefix}Channel", "value": sum(Dh) / len(Dh)}
        )
        params_data["Parameters"].append(
            {"name": f"Sh_{prefix}Channel", "value": sum(Sh)}
        )
        params_data["Parameters"].append(
            {"name": f"Zmin_{prefix}Channel", "value": min(Zmin)}
        )
        params_data["Parameters"].append(
            {"name": f"Zmax_{prefix}Channel", "value": max(Zmax)}
        )

    # params per cooling channels
    # h%d, Tw%d, dTw%d, Dh%d, Sh%d, Zmin%d, Zmax%d :
    else:
        for i in range(NHelices + 1):
            # get value from coolingmethod and Flow(I) value
            params_data["Parameters"].append(
                {
                    "name": f"hw_{prefix}Channel{i}",
                    "value": convert_data(units, 58222.1, "h"),
                }
            )
            # y for Axi, z for 3D
            zcoord = "y"
            if method_data[2] == "3D":
                zcoord = "z"
            if "Z" in method_data[4]:
                csv_data = {
                    "type": "fit",
                    "filename": f"$cfgdir/Tw_{prefix}Channel{i}.csv",
                    "abscissa": "Z",
                    "ordinate": "Tw",
                    "interpolation": "P1",
                    "expr": f"{zcoord}:{zcoord}",
                }
                params_data["Parameters"].append(
                    {"name": f"Tw_{prefix}Channel{i}", "value": csv_data}
                )
            else:
                params_data["Parameters"].append(
                    {"name": f"Tw_{prefix}Channel{i}", "value": 290.671}
                )
                params_data["Parameters"].append(
                    {"name": f"dTw_{prefix}Channel{i}", "value": 12.74}
                )
            params_data["Parameters"].append(
                {"name": f"Zmin_{prefix}Channel{i}", "value": Zmin[i]}
            )
            params_data["Parameters"].append(
                {"name": f"Zmax_{prefix}Channel{i}", "value": Zmax[i]}
            )
            params_data["Parameters"].append(
                {"name": f"Sh_{prefix}Channel{i}", "value": Sh[i]}
            )
            params_data["Parameters"].append(
                {"name": f"Dh_{prefix}Channel{i}", "value": Dh[i]}
            )

    # init values for U (Axi specific)
    if method_data[2] == "Axi":
        for i in range(NHelices):
            for j in range(Nsections[i]):
                # TODO set more realistic value for I0 = 31kA ??
                params_data["Parameters"].append(
                    {"name": f"U_{prefix}H{i+1}_Cu{j+1}", "value": "1"}
                )

            turns = turns_h[i]
            for j in range(Nsections[i]):
                params_data["Parameters"].append(
                    {"name": f"N_{prefix}H{i+1}_Cu{j+1}", "value": turns[j]}
                )
        # for i in range(NHelices):
        #     for j in range(Nsections[i]):
        #         params_data['Parameters'].append({"name":f"S_H{i+1}_Cu{j+1}", "value":convert_data(units, distance_unit, Ssections[i], "Area")})

    if "mag" in method_data[3] or "mqs" in method_data[3]:
        params_data["Parameters"].append(
            {"name": "mu0", "value": convert_data(units, 4 * math.pi * 1e-7, "mu0")}
        )
    # TODO: CG: U_H%d%
    # TODO: HDG: U_H%d% if no ibc    # TODO: length data are written in mm should be in SI instead

    if debug:
        print(params_data)

    return params_data


def create_materials_supra(
    mname:str,
    gdata: tuple,
    maindata: dict,
    confdata: dict,
    templates: dict,
    method_data: List[str],
    debug: bool = False,
) -> dict:
    materials_dict = {}
    if debug:
        print("create_material_supra:", confdata)
    (name, snames, r, z, n, detail, struct) =gdata
    print("template materials : ",templates)
    #use different tempalte for conductor : superconductor
    fconductor = templates["superconductor"]
    finsulator = templates["insulator"]

    prefix = ""
    if mname:
        prefix = f"{mname}_"

    # TODO: length data are written in mm should be in SI instead
    unit_Length = method_data[5]  # "meter"
    units = load_units(unit_Length)
    for prop in [
        "ThermalConductivity",
        "Young",
        "VolumicMass",
        "ElectricalConductivity",
    ]:
        confdata["material"][prop] = convert_data(
            units, confdata["material"][prop], prop
        )

    if method_data[2] == "Axi":
        if debug:
            print("create_material_supra: Conductor_", name)
        mdata = entry(
            fconductor,
            Merge(
                {
                    "name": f"Conductor_{name}",
                    "part_mat_conductor": maindata["part_electric"],
                    "thickness_tape": f"{prefix}thickness_tape",
                    "thickness_cell": f"{prefix}thickness_cell",
                    "height": f"{prefix}height_tape",
                },
                confdata["material"],
            ),
            debug,
        )
        materials_dict[f"Conductor_{name}"] = mdata[f"Conductor_{name}"]


        if maindata["part_mat_insulator"]:
            if debug:
                print("create_material_supra: Insulator_", name)
            mdata = entry(
                finsulator,
                Merge(
                    {
                        "name": f"Insulator_{name}",
                        "part_mat_insulator": maindata["part_mat_insulator"],
                    },
                    confdata["material"],
                ),
                debug,
            )
            materials_dict[f"Insulator_{name}"] = mdata[f"Insulator_{name}"]
    else:
        return {}

    if debug:
        print(materials_dict)
    return materials_dict


def create_materials_bitter(
    gdata: tuple,
    maindata: dict,
    confdata: dict,
    templates: dict,
    method_data: List[str],
    debug: bool = False,
) -> dict:
    materials_dict = {}
    if debug:
        print("create_material_bitter:", confdata)

    fconductor = templates["conductor"]
    finsulator = templates["insulator"]

    # TODO: length data are written in mm should be in SI instead
    unit_Length = method_data[5]  # "meter"
    units = load_units(unit_Length)

    for prop in [
        "ThermalConductivity",
        "Young",
        "VolumicMass",
        "ElectricalConductivity",
    ]:
        confdata["material"][prop] = convert_data(
            units, confdata["material"][prop], prop
        )

    (
        name,
        snames,
        turns,
        NCoolingSlits,
        Dh,
        Sh,
        Zh,
        fillingfactor,
        ignore_index,
    ) = gdata

    if method_data[2] == "Axi":
        if debug:
            print("create_material_bitter: Conductor_", name)
        mdata = entry(
            fconductor,
            Merge(
                {
                    "name": f"Conductor_{name}",
                    "part_mat_conductor": maindata["part_electric"],
                },
                confdata["material"],
            ),
            debug,
        )
        materials_dict[f"Conductor_{name}"] = mdata[f"Conductor_{name}"]

        bitter_insulator = list(
            set(maindata["part_thermic"]) - set(maindata["part_electric"])
        )

        if bitter_insulator:
            if debug:
                print("create_material_bitter: Insulator_", name)
            mdata = entry(
                finsulator,
                Merge(
                    {
                        "name": f"Insulator_{name}",
                        "part_mat_insulator": list(
                            set(maindata["part_thermic"])
                            - set(maindata["part_electric"])
                        ),
                    },
                    confdata["material"],
                ),
                debug,
            )
            materials_dict[f"Insulator_{name}"] = mdata[f"Insulator_{name}"]
    else:
        return {}

    if debug:
        print(materials_dict)
    return materials_dict


def create_materials_insert(
    gdata: tuple,
    maindata: dict,
    idata: Optional[List],
    confdata: dict,
    templates: dict,
    method_data: List[str],
    debug: bool = False,
) -> dict:
    # TODO loop for Plateau (Axi specific)
    materials_dict = {}
    if debug:
        print("create_material_insert:", confdata)

    fconductor = templates["conductor"]
    finsulator = templates["insulator"]

    (mname, NHelices, NRings, NChannels, Nsections, R1, R2, Dh, Sh, Zh) = gdata

    prefix = ""
    if mname:
        prefix = f"{mname}_"

    # TODO: length data are written in mm should be in SI instead
    unit_Length = method_data[5]  # "meter"
    units = load_units(unit_Length)
    for mtype in ["Helix", "Ring", "Lead"]:
        if mtype in confdata:
            for i in range(len(confdata[mtype])):
                for prop in [
                    "ThermalConductivity",
                    "Young",
                    "VolumicMass",
                    "ElectricalConductivity",
                ]:
                    confdata[mtype][i]["material"][prop] = convert_data(
                        units, confdata[mtype][i]["material"][prop], prop
                    )

    # Loop for Helix
    for i in range(NHelices):
        if method_data[2] == "3D":
            mdata = entry(
                fconductor,
                Merge(
                    {"name": f"{prefix}H{i+1}", "marker": f"{prefix}H{i+1}_Cu"},
                    confdata["Helix"][i]["material"],
                ),
                debug,
            )
            materials_dict[f"{prefix}H{i+1}"] = mdata[f"{prefix}H{i+1}"]

            if idata:
                for item in idata:
                    if item[0] == "Glue":
                        name = f"{prefix}Isolant{i+1}"
                        mdata = entry(
                            finsulator,
                            Merge(
                                {"name": name, "marker": f"{prefix}H{i+1}_Isolant"},
                                confdata["Helix"][i]["insulator"],
                            ),
                            debug,
                        )
                    else:
                        name = f"{prefix}Kaptons{i+1}"
                        kapton_dict = {
                            "name": '[f"{prefix}Kapton%1%"]',
                            "index1": f"0:{item(1)}",
                        }
                        mdata = entry(
                            finsulator,
                            Merge(
                                {"name": name, "marker": kapton_dict},
                                confdata["Helix"][i]["insulator"],
                            ),
                            debug,
                        )
                    materials_dict[name] = mdata[name]
        else:
            # section j==0:  treated as insulator in Axi
            # load conductor template
            # for j in range(1, Nsections[i] + 1):
            # print("load conductor[{j}]: mat:", confdata["Helix"][i]["material"])
            mdata = entry(
                fconductor,
                Merge(
                    {
                        "name": f"Conductor_{prefix}H{i+1}",
                        "part_mat_conductor": maindata["part_mat_conductors"][i],
                    },
                    confdata["Helix"][i]["material"],
                ),
                debug,
            )
            # print("load conductor[{j}]:", mdata)
            materials_dict[f"Conductor_{prefix}H{i+1}"] = mdata[
                f"Conductor_{prefix}H{i+1}"
            ]

            # section j==Nsections+1:  treated as insulator in Axi
            mdata = entry(
                finsulator,
                Merge(
                    {
                        "name": f"Insulator_{prefix}H{i+1}",
                        "part_mat_insulator": maindata["part_mat_insulators"][i],
                    },
                    confdata["Helix"][i]["material"],
                ),
                debug,
            )
            materials_dict[f"Insulator_{prefix}H{i+1}"] = mdata[
                f"Insulator_{prefix}H{i+1}"
            ]

    # loop for Rings
    for i in range(NRings):
        if method_data[2] == "3D":
            mdata = entry(
                fconductor,
                Merge({"name": f"{prefix}R{i+1}"}, confdata["Ring"][i]["material"]),
                debug,
            )
        else:
            mdata = entry(
                finsulator,
                Merge(
                    {
                        "name": f"{prefix}R{i+1}",
                        "part_mat_insulator": maindata["part_mat_insulators"][
                            NHelices + i
                        ],
                    },
                    confdata["Ring"][i]["material"],
                ),
                debug,
            )
        materials_dict[f"{prefix}R{i+1}"] = mdata[f"{prefix}R{i+1}"]

    # Leads:
    if method_data[2] == "3D" and "Lead" in confdata:
        mdata = entry(
            fconductor,
            Merge({"name": f"{prefix}iL1"}, confdata["Lead"][0]["material"]),
            debug,
        )
        materials_dict[f"{prefix}iL1"] = mdata[f"{prefix}iL1"]

        mdata = entry(
            fconductor,
            Merge({"name": f"{prefix}oL2"}, confdata["Lead"][1]["material"]),
            debug,
        )
        materials_dict[f"{prefix}oL2"] = mdata[f"{prefix}oL2"]

    return materials_dict


def create_models_supra(
    gdata: tuple,
    maindata: dict,
    confdata: dict,
    templates: dict,
    method_data: List[str],
    equation: str,
    debug: bool = False,
) -> dict:
    models_dict = {}
    if debug:
        print("create_models_supra:", confdata)

    (name, snames, r, z, n, detail, struct) =gdata
    fconductor = templates[equation + "-conductor"]
    finsulator = templates[equation + "-insulator"]

    # TODO: length data are written in mm should be in SI instead
    unit_Length = method_data[5]  # "meter"
    units = load_units(unit_Length)
    for prop in [
        "ThermalConductivity",
        "Young",
        "VolumicMass",
        "ElectricalConductivity",
    ]:
        confdata["material"][prop] = convert_data(
            units, confdata["material"][prop], prop
        )

    if method_data[2] == "Axi" and equation=="magnetic" :
        if maindata["part_insulators"]:
            mdata = entry(
                finsulator,
                {
                    "name": f"Insulator_{name}",
                    "part_insulator": maindata["part_insulators"],
                },
                debug,
            )
            models_dict[f"Insulator_{name}"] = mdata

        mdata = entry(
            fconductor,
            {
                "name": f"Conductor_{name}",
                "part_conductor": maindata["part_conductors"],
            },
            debug,
        )
        models_dict[f"Conductor_{name}"] = mdata
    else:
        return {}

    if debug:
        print(models_dict)
    return models_dict


def create_models_bitter(
    gdata: tuple,
    maindata: dict,
    confdata: dict,
    templates: dict,
    method_data: List[str],
    equation: str,
    debug: bool = False,
) -> dict:
    models_dict = {}
    if debug:
        print("create_model_bitter:", confdata)

    fconductor = templates[equation + "-conductor"]
    finsulator = templates[equation + "-insulator"]

    # TODO: length data are written in mm should be in SI instead
    unit_Length = method_data[5]  # "meter"
    units = load_units(unit_Length)

    (
        name,
        snames,
        turns,
        NCoolingSlits,
        Dh,
        Sh,
        Zh,
        fillingfactor,
        ignore_index,
    ) = gdata
    if method_data[2] == "Axi":
        if maindata["part_insulators"]:
            mdata = entry(
                finsulator,
                {
                    "name": f"Insulator_{name}",
                    "part_insulator": maindata["part_insulators"],
                },
                debug,
            )
            models_dict[f"Insulator_{name}"] = mdata

        mdata = entry(
            fconductor,
            {
                "name": f"Conductor_{name}",
                "part_conductor": maindata["part_conductors"],
            },
            debug,
        )
        models_dict[f"Conductor_{name}"] = mdata
    else:
        return {}

    if debug:
        print(models_dict)
    return models_dict


def create_models_insert(
    prefix: str,
    maindata: dict,
    confdata: dict,
    templates: dict,
    method_data: List[str],
    equation: str,
    debug: bool = False,
) -> dict:
    # TODO loop for Plateau (Axi specific)
    models_dict = {}
    # "physic":equation }
    if debug:
        print("create_models_insert:", confdata)

    fconductor = templates[equation + "-conductor"]
    finsulator = templates[equation + "-insulator"]
    # print('\n\nfconductor :', fconductor)
    if method_data[2] == "Axi":
        mdata = entry(
            finsulator,
            {
                "name": f"Insulator_{prefix}Insert",
                "part_insulator": maindata["part_insulators"],
            },
            debug,
        )
        models_dict[f"Insulator_{prefix}Insert"] = mdata

        mdata = entry(
            fconductor,
            {
                "name": f"Conductor_{prefix}Insert",
                "part_conductor": maindata["part_conductors"],
            },
            debug,
        )
        models_dict[f"Conductor_{prefix}Insert"] = mdata
    else:
        return {}
    # Loop for Helix
    # for i in range(NHelices):
    #     # section j==0:  treated as insulator in Axi
    #     mdata = entry(finsulator, {"name": f"H{i+1}_Cu0"}, debug)
    #     models_dict[f"H{i+1}_Cu0"] = mdata

    #     # load conductor template
    #     for j in range(1, Nsections[i] + 1):
    #         mdata = entry(fconductor, {"name": f"H{i+1}_Cu{j}"}, debug)
    #         models_dict[f"H{i+1}_Cu{j}"] = mdata

    #     # section j==Nsections+1:  treated as insulator in Axi
    #     mdata = entry(finsulator, {"name": f"H{i+1}_Cu{Nsections[i]+1}"}, debug)
    #     models_dict[f"H{i+1}_Cu{Nsections[i]+1}"] = mdata

    # loop for Rings
    # for i in range(NRings):
    #     mdata = entry(finsulator, {"name": f"R{i+1}"}, debug)
    #     models_dict[f"R{i+1}"] = mdata

    return models_dict


def create_bcs_supra(
    boundary_meca: List,
    boundary_maxwell: List,
    boundary_electric: List,
    gdata: tuple,
    confdata: dict,
    templates: dict,
    method_data: List[str],
    debug: bool = False,
) -> dict:
    print("create_bcs_supra from templates")
    electric_bcs_dir = {"boundary_Electric_Dir": []}  # name, value, vol
    electric_bcs_neu = {"boundary_Electric_Neu": []}  # name, value
    thermic_bcs_rob = {"boundary_Therm_Robin": []}  # name, expr1, expr2
    thermic_bcs_neu = {"boundary_Therm_Neu": []}  # name, value
    meca_bcs_dir = {"boundary_Meca_Dir": []}  # name, value
    maxwell_bcs_dir = {"boundary_Maxwell_Dir": []}  # name, value

    if "th" in method_data[3]:
        fcooling = templates["cooling"]

    return {}


def create_bcs_bitter(
    boundary_meca: List,
    boundary_maxwell: List,
    boundary_electric: List,
    gdata: tuple,
    confdata: dict,
    templates: dict,
    method_data: List[str],
    debug: bool = False,
) -> dict:
    (
        name,
        snames,
        turns,
        NCoolingSlits,
        Dh,
        Sh,
        Zh,
        fillingfactor,
        ignore_index,
    ) = gdata
    print(f"create_bcs_bitter from templates for {name}")
    print(f"snames={snames}")

    electric_bcs_dir = {"boundary_Electric_Dir": []}  # name, value, vol
    electric_bcs_neu = {"boundary_Electric_Neu": []}  # name, value
    thermic_bcs_rob = {"boundary_Therm_Robin": []}  # name, expr1, expr2
    thermic_bcs_neu = {"boundary_Therm_Neu": []}  # name, value
    meca_bcs_dir = {"boundary_Meca_Dir": []}  # name, value
    maxwell_bcs_dir = {"boundary_Maxwell_Dir": []}  # name, value

    if "th" in method_data[3]:
        fcooling = templates["cooling"]
        for i in range(NCoolingSlits + 2):
            bcname = name
            if "H" in method_data[4]:
                bcname = f"{name}_Slit{i}"

            markers = f'["{name}_Slit{i}"]'
            if method_data[2] == "Axi":
                if i != 0 and i != NCoolingSlits + 1:
                    markers = f'["{name}_Slit{i}_l","{name}_Slit{i}_r"]'

            # change template
            # add: %1_1%: s, %1_2%: nslit, %1_3%: slit.r, %1_4%: rslit
            # change "markers" to a list: f"[{name}_Slit{i}_l, {name}_Slit{i}_r]"
            # if i ==0 or i == NCooling+1: "markers" : f"{name}_Slit{i}"
            mdata = entry(
                fcooling,
                {
                    "name": f"{name}_Slit{i}",
                    "markers": markers,
                    "fillingfactor": fillingfactor[i],
                    "hw": f"hw_{bcname}",
                    "Tw": f"Tw_{bcname}",
                    "dTw": f"dTw_{bcname}",
                    "Zmin": f"Zmin_{bcname}",
                    "Zmax": f"Zmax_{bcname}",
                },
                debug,
            )

            thermic_bcs_rob["boundary_Therm_Robin"].append(
                Merge({"name": f"{name}_Slit{i}"}, mdata[f"{name}_Slit{i}"])
            )

        th_ = Merge(thermic_bcs_rob, thermic_bcs_neu)

    if "el" in method_data[3] and method_data[3] != "thelec":
        for bc in boundary_meca:
            meca_bcs_dir["boundary_Meca_Dir"].append({"name": bc, "value": "{0,0}"})

    if method_data[3] == "thelec":
        if method_data[2] == "Axi":
            return th_
        else:
            return {}
    elif method_data[3] == "mag" or method_data[3] == "mag_hcurl":
        return {}
    elif method_data[3] == "thmag" or method_data[3] == "thmag_hcurl":
        th_ = Merge(thermic_bcs_rob, thermic_bcs_neu)
        if method_data[2] == "Axi":
            return Merge(maxwell_bcs_dir, th_)
        else:
            return {}
    else:
        th_ = Merge(thermic_bcs_rob, thermic_bcs_neu)
        elec_ = Merge(electric_bcs_dir, electric_bcs_neu)
        thelec_ = Merge(th_, elec_)
        thelecmeca_ = Merge(thelec_, meca_bcs_dir)
        return Merge(maxwell_bcs_dir, thelecmeca_)

    return {}


def create_bcs_insert(
    boundary_meca: List,
    boundary_maxwell: List,
    boundary_electric: List,
    gdata: tuple,
    confdata: dict,
    templates: dict,
    method_data: List[str],
    debug: bool = False,
) -> dict:
    print("create_bcs_insert from templates")
    electric_bcs_dir = {"boundary_Electric_Dir": []}  # name, value, vol
    electric_bcs_neu = {"boundary_Electric_Neu": []}  # name, value
    thermic_bcs_rob = {"boundary_Therm_Robin": []}  # name, expr1, expr2
    thermic_bcs_neu = {"boundary_Therm_Neu": []}  # name, value
    meca_bcs_dir = {"boundary_Meca_Dir": []}  # name, value
    maxwell_bcs_dir = {"boundary_Maxwell_Dir": []}  # name, value

    (mname, NHelices, NRings, NChannels, Nsections, R1, R2, Dh, Sh, Zh) = gdata

    prefix = ""
    if mname:
        prefix = f"{mname}_"

    if "th" in method_data[3]:
        fcooling = templates["cooling"]

        if "H" in method_data[4]:
            for i in range(NChannels):
                # load insulator template for j==0
                mdata = entry(
                    fcooling,
                    {
                        "name": f"{prefix}Channel{i}",
                        "markers": f'["{prefix}Channel{i}"]',
                        "fillingfactor": 1,
                        "hw": f"hw_{prefix}Channel{i}",
                        "Tw": f"Tw_{prefix}Channel{i}",
                        "dTw": f"dTw_{prefix}Channel{i}",
                        "Zmin": f"Zmin_{prefix}Channel{i}",
                        "Zmax": f"Zmax_{prefix}Channel{i}",
                    },
                    debug,
                )
                thermic_bcs_rob["boundary_Therm_Robin"].append(
                    Merge({"name": f"{prefix}Channel{i}"}, mdata[f"{prefix}Channel{i}"])
                )
        else:
            for i in range(NChannels):
                # load insulator template for j==0
                mdata = entry(
                    fcooling,
                    {
                        "name": f"{prefix}Channel{i}",
                        "markers": f'["{prefix}Channel{i}"]',
                        "fillingfactor": 1,
                        "hw": f"hw_{prefix}Channel",
                        "Tw": f"Tw_{prefix}Channel",
                        "dTw": f"dTw_{prefix}Channel",
                        "Zmin": f"Zmin_{prefix}Channel",
                        "Zmax": f"Zmax_{prefix}Channel",
                    },
                    debug,
                )
                thermic_bcs_rob["boundary_Therm_Robin"].append(
                    Merge({"name": f"{prefix}Channel{i}"}, mdata[f"{prefix}Channel{i}"])
                )

    if "el" in method_data[3] and method_data[3] != "thelec":
        for bc in boundary_meca:
            meca_bcs_dir["boundary_Meca_Dir"].append({"name": bc, "value": "{0,0}"})

    if "mag" in method_data[3]:
        for bc in boundary_maxwell:
            if method_data[2] == "3D":
                maxwell_bcs_dir["boundary_Maxwell_Dir"].append(
                    {"name": bc, "value": "{0,0}"}
                )
            else:
                maxwell_bcs_dir["boundary_Maxwell_Dir"].append(
                    {"name": bc, "value": "0"}
                )

    if method_data[3] != "mag" and method_data[3] != "mag_hcurl":
        for bc in boundary_electric:
            electric_bcs_dir["boundary_Electric_Dir"].append(
                {"name": bc[0], "value": bc[2]}
            )

    if method_data[3] == "thelec":
        th_ = Merge(thermic_bcs_rob, thermic_bcs_neu)
        if method_data[2] == "Axi":
            return th_
        else:
            elec_ = Merge(electric_bcs_dir, electric_bcs_neu)
            return Merge(th_, elec_)
    elif method_data[3] == "mag" or method_data[3] == "mag_hcurl":
        return maxwell_bcs_dir
    elif method_data[3] == "thmag" or method_data[3] == "thmag_hcurl":
        th_ = Merge(thermic_bcs_rob, thermic_bcs_neu)
        if method_data[2] == "Axi":
            return Merge(maxwell_bcs_dir, th_)
        else:
            elec_ = Merge(electric_bcs_dir, electric_bcs_neu)
            thelec_ = Merge(th_, elec_)
            return Merge(maxwell_bcs_dir, thelec_)
    elif method_data[3] == "thmqs" or method_data[3] == "thmqs_hcurl":
        th_ = Merge(thermic_bcs_rob, thermic_bcs_neu)
        if method_data[2] == "Axi":
            return Merge(maxwell_bcs_dir, th_)
        else:
            elec_ = Merge(electric_bcs_dir, electric_bcs_neu)
            thelec_ = Merge(th_, elec_)
            return Merge(maxwell_bcs_dir, thelec_)
    else:
        th_ = Merge(thermic_bcs_rob, thermic_bcs_neu)
        elec_ = Merge(electric_bcs_dir, electric_bcs_neu)
        thelec_ = Merge(th_, elec_)
        thelecmeca_ = Merge(thelec_, meca_bcs_dir)
        return Merge(maxwell_bcs_dir, thelecmeca_)

    return {}


def create_json(
    jsonfile: str,
    mdict: dict,
    mmat: dict,
    mmodels: dict,
    mpost: dict,
    templates: dict,
    method_data: List[str],
    debug: bool = False,
):
    """
    Create a json model file
    """

    if debug:
        print("create_json jsonfile=", jsonfile)
        print("create_json mdict=", mdict)
    data = entry(templates["model"], mdict, debug)
    if debug:
        print(f"create_json/data model: {data}")

    # material section
    if "Materials" in data:
        for key in mmat:
            data["Materials"][key] = mmat[key]
    else:
        data["Materials"] = mmat
    if debug:
        print("create_json/Materials data:", data)

    # models section from templates['physic']
    if debug:
        print(f"mmodels: {mmodels}")
    for physic in templates["physic"]:
        _model = mmodels[physic]
        for key in _model:
            data["Models"][physic]["models"].append(_model[key])

    # init values
    # mpost init: {name: mname, value: Tinit param}
    # init_heat['init_Temperature'] = mpost['init']

    # postprocess
    if debug:
        for field in templates["stats"]:
            print(f"stats: {field}")

    post_keywords = {}

    if debug:
        print("templates[stats]")
        for field in templates["stats"]:
            print(field)

    for field in templates["stats"]:
        _data = templates["stats"][field]
        _name = f"Stats_{field}"
        post_keywords[_name] = {
            "name": field,  # _data['name'],
            "template": _data["template"],
            "physic": _data["physic"],
            "data": {_name: mpost[field] if field in mpost else {}},
        }

    if debug:
        print(f"method_data[3]: {method_data[3]}")
        print(f"post_keywords: {post_keywords.keys()}")
    if "th" in method_data[3] and "Stats_Flux" in post_keywords:
        templatefile = templates["flux"]
        post_keywords["Stats_Flux"]["template"] = templatefile
        if debug:
            print(f"cooling={method_data[4]}")
            print(f"templates keywords: {templates.keys()}")
            print(f"templates[flux]: {templatefile}")
            print(
                f'post_keywords[Stats_Flux][template]={post_keywords["Stats_Flux"]["template"]}'
            )

    if debug:
        print("post_keywords")
        for key in post_keywords:
            msg = key
            field = post_keywords[key]
            if field["physic"] in data["PostProcess"]:
                msg += " - written to {field['physic']}"
            print(msg)

    for key in post_keywords:
        field = post_keywords[key]
        if field["physic"] in data["PostProcess"]:
            _data = field["data"]
            if debug:
                print(f"{key}: field={field}")
                if key == "Stats_Flux":
                    print(f"{key} (type={type(_data)}): {_data}")
                print(f"{key} (type={type(_data)}): {_data}")
            add = data["PostProcess"][field["physic"]]["Measures"]["Statistics"]
            # print(f"{key}: add={add}")
            odata = entry(field["template"], _data, debug)
            if debug:
                print(f"{key}: odata={odata}")
                if field == "Stats_Flux":
                    print(f"{key}: odata={odata}")
            for md in odata[key]:
                # print(f'{key}: add[{md}], odata[{key}][{md}]={odata[key][md]}')
                add[md] = odata[key][md]
            # print(f"{key}: add={add}")

    # TODO: add data for B plots, aka Rinf, Zinf, NR and Nz?
    if "B" in mpost:
        plotB_data = mpost["B"]
        if debug:
            print("plotB")
            print("section:", "magnetic")
            print("templates[plots]:", templates["plots"])
            print(f"plotB_data:{plotB_data}")
        add = data["PostProcess"]["magnetic"]["Measures"]["Points"]
        odata = entry(
            templates["plots"]["B"],
            {
                "Rinf": plotB_data["Rinf"],
                "Zinf": plotB_data["Zinf"],
                "NR": 100,
                "NZ": 100,
            },
            debug,
        )
        # print(f"data[PostProcess][magnetic][Measures][Points]: {add}")
        if debug:
            print(f"plot_B odata: {odata}")
        for md in odata:
            if debug:
                print(f"odata[{md}]: {odata[md]}")
            add[md] = odata[md]
        # print(f"data[PostProcess][magnetic][Measures][Points]: {add}")

    mdata = json.dumps(data, indent=4)

    with open(jsonfile, "w+") as out:
        out.write(mdata)
    return


def entry(template: str, rdata: List, debug: bool = False) -> str:
    import chevron
    import re

    if debug:
        print("entry/loading {str(template)}", type(template))
        print("entry/rdata:", rdata)
    with open(template, "r") as f:
        jsonfile = chevron.render(f, rdata)
    jsonfile = jsonfile.replace("'", '"')
    # print("jsonfile:", jsonfile)

    corrected = re.sub(r"},\s+},\n", "}\n},\n", jsonfile)
    corrected = re.sub(r"},\s+}\n", "}\n}\n", corrected)
    # corrected = re.sub(r'},\s+}\n', '}\n}\n', corrected)
    corrected = corrected.replace("&quot;", '"')
    corrected = corrected.replace("&lt;", "<")
    corrected = corrected.replace("&gt;", ">")
    if debug:
        print(f"entry/jsonfile: {jsonfile}")
        print(f"corrected: {corrected}")
    try:
        mdata = json.loads(corrected)
    except json.decoder.JSONDecodeError:
        # ??how to have more info on the pb??
        # save corrected to tmp file and run jsonlint-php tmp??
        raise Exception(f"entry: json.decoder.JSONDecodeError in {corrected}")

    if debug:
        print("entry/data (json):\n", mdata)

    return mdata
