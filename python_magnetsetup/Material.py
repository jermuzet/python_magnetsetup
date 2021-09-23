#!/usr/bin/env python
# encoding: UTF-8

import math
import yaml
import json
from deserialize import *

# to deal with units
from pint import UnitRegistry

class Material(yaml.YAMLObject):
    """
    name :
    ref :

    Electrical_Props : 
    Thermal_Props :
    Elastic_Props :
    Magnetic_Props :

    Each section of Props consists of a set of [ [name, symbol, expression, unit],... ]
    where expression is either a constant or a string (for syntax see "feelpp" expressions) 
    """

    yaml_tag = 'Material'

    def __init__(self, name, ref=[], Electric=[], Thermal=[], Mechanic=[], Magnetic=[]):
        self.name = name
        self.ref = ref
        self.Electric = Electric
        self.Thermal = Thermal
        self.Mechanic = Mechanic
        self.Magnetic = Magnetic

    def __repr__(self):
        return "%s(name=%r, ref=%r, Electric=%r, Thermal=%r, Mechanic=%r, Magnetic=%r)" % \
            (self.__class__.__name__,
             self.name,
             self.ref,
             self.Electric,
             self.Thermal,
             self.Mechanic,
             self.Magnetic
            )

    def dump (self):
        try:
            ostream = open("Mat_" + self.name + '.yaml', 'w')
            yaml.dump(self, stream=ostream)
        except:
            print ("Failed to Material dump")
            
    def load (self):
        data = None
        try:
            istream = open("Mat_" + self.name + '.yaml', 'r')
            data = yaml.load(self, stream=istream)
        except:
            raise Exception("Failed to load Material data %s"%self.name)
            
        self.name = data.name
        self.ref = data.ref
        self.Electric = data.Electric
        self.Thermal = data.Thermal
        self.Mechanic = data.Mechanic
        self.Magnetic = data.Magnetic

    def to_json(self):
        return json.dumps(self, default=deserialize.serialize_instance, 
            sort_keys=True, indent=4)

    def from_json(self, string):
        return json.loads(string, object_hook=deserialize.unserialize_object)

    def read_from_json(self):
        istream = open("Mat_" + self.name + '.json', 'r')
        jsondata= self.from_json(istream.read())
        # print type(jsondata)
        istream.close()
        
    def write_to_json(self):
        """
        write from json file
        """
        ostream = open(self.name + '.json', 'w')
        jsondata = self.to_json()
        ostream.write(str(jsondata))
        ostream.close()


        
def Material_constructor(loader, node):
    values = loader.construct_mapping(node)
    name = values["name"]
    ref = values["ref"]
    Electric = values["Electric"]
    Thermal = values["Thermal"]
    Mechanic = values["Mechanic"]
    Magnetic = values["Magnetic"]
    return Material(name, ref, Electric, Thermal, Mechanic, Magnetic)

yaml.add_constructor(u'!Material', Material_constructor)


###########################################################################
#
#
###########################################################################

def convert_to_mm(prop):
    value = None
    val_function = False
    
    try:
        value = float(prop[2])
    except:
        val_Function = True
        value = 1
            
    val_property = value * ureg[prop[3]]
    val_unit = str(val_property.units)
        
    if "meter" in val_unit:
        # replace m by mm
        new_unit = val_unit.replace("meter", "millimeter")
        val_property.to(new_unit)
        print  ("%s : "%prop[0], val_property, " --> ", val_property.to(new_unit))
    else:
        print ("%s : "%prop[0], val_property)

    if val_function:
        return prop[2] + " * " + str(val_property.magnitude)
    else:
        return val_property.magnitude
        

#
# To operate from command line

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("name", help="name of the material to be stored")
    parser.add_argument("--ref", help="define reference doc for material", type=str)
    args = parser.parse_args()
 
    import getpass
    UserName = getpass.getuser()

    # Load default units
    ureg = UnitRegistry()
    
    # to get value: print(distance.magnitude)
    # to get unit: print(distance.units)

    # List Electrical properties
    conductivity = ["electrical_conductivity", "sigma", "52.5e+6", "1/(ohm*m)"]
    alpha = ["temperature_coefficient", "alpha", "3.6e-3", "1/K"]
    Electric= [conductivity, alpha]
    
    # List Thermal properties
    conductivity = ["thermal_conductivity", "k", "380", "K/m"]
    lorentz = ["lorentz", "L", "2.47e-8", "ohm"]
    rho = ["volumic_mass", "rho", "8.96e+3", "kg/(m*m*m)"]
    cp =  ["specific heat", "Cp", "380", "N*m/(kg*K)"]
    Thermal = [conductivity, lorentz, rho, cp]
    
    # list Mechanical properties
    young = ["young_modulus", "E", "1200.e+6", "N/(m*m)"]
    poisson = ["poisson", "nu", "0.33", "1"]
    dilatation = ["dilatation", "alpha", "3.6e-3", "1/K"]
    Re = ["yield_strength", "Re", "450.e+6", "N/(m*m)"]
    Rm = ["Rm", "Rm", "450.e+6", "N/(m*m)"]
    Re02 = ["Re02", "Re02", "450.e+6", "N/(m*m)"]

    # cf http://fr.wikipedia.org/wiki/Limite_d'%C3%A9lasticit%C3%A9
    # Re: yield strength
    # Re: .............. at 0.2% strain
    # Rm: 
    Mechanic = [young, poisson, dilatation, Re]
    
    # List Magnetic properties
    mu = ["magnetic_permeability", "mu", "4*pi*1.e-07", "m*kg/(s*s*A*A)"]
    Magnetic = [mu]

    ref = []
    if args.ref:
        ref.append(ref)
        
    Mat = Material(args.name, ref, Electric, Thermal, Mechanic, Magnetic)
    Mat.dump()
    Mat.write_to_json()

    
