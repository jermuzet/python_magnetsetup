"""
Check for unit consistency
Depending on Length base unit
"""

from typing import List, Optional, Union

import sys
import os

import warnings
from pint import UnitRegistry, Unit, Quantity

from .config import appenv, loadconfig
from .objects import load_object, load_object_from_db

import yaml

from python_magnetgeo import Insert
from python_magnetgeo import python_magnetgeo

# Ignore warning for pint
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    Quantity([])

# Pint configuration
ureg = UnitRegistry()
ureg.default_system = 'SI'
ureg.autoconvert_offset_to_baseunit = True

def load_units(distance_unit: str):
    """
    returns units dict
    """

    # units: dict( Quantity: [ in_unit, out_unit ]
    units = {
        "VolumicMass": [ ureg.kilogram / ureg.meter**3 , ureg.kilogram / ureg.Unit(distance_unit)**3 ],
        "ThermalConductivity": [ ureg.watt / ureg.meter / ureg.kelvin, ureg.watt / ureg.Unit(distance_unit) / ureg.kelvin ],
        "ElectricalConductivity": [ ureg.siemens / ureg.meter, ureg.siemens / ureg.Unit(distance_unit) ],
        "Young": [ ureg.kilogram / ureg.meter / ureg.second,  ureg.kilogram / ureg.Unit(distance_unit) / ureg.second ],
        "Length": [ ureg.millimeter, ureg.Unit(distance_unit) ],
        "Area": [ ureg.millimeter*ureg.millimeter, ureg.Unit(distance_unit)*ureg.Unit(distance_unit) ],
        "mu0": [ ureg.henry / ureg.meter, ureg.henry / ureg.Unit(distance_unit) ],
        "h": [ ureg.watt / ureg.meter**2 / ureg.kelvin,  ureg.watt / ureg.Unit(distance_unit)**2 / ureg.kelvin],
        "Flow": [ ureg.liter/ureg.second, ureg.Unit(distance_unit)*ureg.Unit(distance_unit)*ureg.Unit(distance_unit)/ureg.second],
        "Current": [ureg.ampere, ureg.ampere],
        "Power": [ureg.watt, ureg.watt],
        "Temperature": [ureg.degK, ureg.degK]
    }

    return units

    
def convert_data(units: dict, quantity: Union[float, List[float]], qtype: str, debug: bool=False):
    """
    Returns quantity unit consistant with length unit
    """

    data = None
    if isinstance(quantity, float):
        data = Quantity(quantity, units[qtype][0]).to(units[qtype][1]).magnitude
        if debug: print(qtype, quantity, "data=", data)
    elif isinstance(quantity, list):
        data = Quantity(quantity, units[qtype][0]).to(units[qtype][1]).magnitude.tolist()
    else:
        raise Exception(f"convert_data/quantity: unsupported type {type(quantity)} for {qtype}")

    return data

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Change units according to specify length unit")
    parser.add_argument("--datafile", help="input data file (ex. HL-34-data.json)", default=None)
    parser.add_argument("--wd", help="set a working directory", type=str, default="")
    parser.add_argument("--magnet", help="Magnet name from magnetdb (ex. HL-34)", default=None)
    parser.add_argument("--length_unit", help="Length unit", type=str,
                    choices=['meter','millimeter'], default='meter')
    parser.add_argument("--debug", help="activate debug", action='store_true')
    args = parser.parse_args()

    if args.debug:
        print(args)

    distance_unit = args.length_unit

    # load appenv
    MyEnv = appenv()
    if args.debug: print(MyEnv.template_path())

    # loadconfig
    AppCfg = loadconfig()

    # Get current dir
    cwd = os.getcwd()
    if args.wd:
        os.chdir(args.wd)

    # load jsondata (aka geometry+materials)
    # Get Object
    if args.datafile != None:
        confdata = load_object(MyEnv, args.datafile, args.debug)
        jsonfile = args.datafile.replace(".json","")

    if args.magnet != None:
        confdata = load_object_from_db(MyEnv, "magnet", args.magnet, args.debug)
        jsonfile = args.magnet

    units = load_units(distance_unit)

    print("init:", confdata)

    from .file_utils import MyOpen, findfile, search_paths
    
    # select a default distance unit
    yamlfile = confdata["geom"]
    with MyOpen(yamlfile, 'r', paths=search_paths(MyEnv, "geom")) as cfgdata:
        cad = yaml.load(cfgdata, Loader = yaml.FullLoader)
        if isinstance(cad, Insert):
            gdata = python_magnetgeo.get_main_characteristics(cad, MyEnv)
            (NHelices, NRings, NChannels, Nsections, R1, R2, Z1, Z2, Zmin, Zmax, Dh, Sh) = gdata

            for mtype in ["Helix", "Ring", "Lead"]:
                for i in range(len(confdata[mtype])):            
                    for prop in ["ThermalConductivity", "Young", "VolumicMass", "ElectricalConductivity"]:
                        confdata[mtype][i]["material"][prop] = convert_data(units, confdata[mtype][i]["material"][prop], prop)
            print("converted:", confdata)

            # mm -> distance_unit
            for data in [R1, R2, Z1, Z2, Zmin, Zmax, Dh]:
                _convert = convert_data(units, R1, "Length")
            Sh_convert = convert_data(units, Sh, "Area")

            # Ssections_convert = convert_data(units, distance_unit, Ssections, "Area")

            # MagnetPermeability of vacuum : H/m --> H/distance_unit
            # mu0_convert = convert_data(distance_unit, mu0, "mu0")

            # Convection coefficients : W/m2/K --> W/distance_unit**2/K
            # h_convert = convert_data(distance_unit, h, "h")

    pass


if __name__ == "__main__":
    main()
