#!/usr/bin/env python
# encoding: UTF-8

import math
import yaml
import json
from deserialize import *

class SimMaterial(yaml.YAMLObject):
    """
    name :
    filename :
    """

    yaml_tag = 'Material'

    def __init__(self, markers, physics=[], filename=""):
        self.markers = markers
        self.physics = physics
        self.filename = filename

    def __repr__(self):
        return "%s(markers=%r, physics=%r, filename=%r)" % \
            (self.__class__.__name__,
             self.markers,
             self.physics,
             self.filename
            )

    def dump (self, name):
        try:
            ostream = open("Mat_" + name + '.yaml', 'w')
            yaml.dump(self, stream=ostream)
        except:
            print ("Failed to SimMaterial dump")
            
    def load (self, name):
        data = None
        try:
            istream = open("Mat_" + name + '.yaml', 'r')
            data = yaml.load(self, stream=istream)
        except:
            raise Exception("Failed to load SimMaterial data %s"%self.name)
            
        self.markers = data.markers
        self.filename = data.filename

    def to_json(self, sort_keys=False):
        return json.dumps(self, default=deserialize.serialize_instance, 
            sort_keys=sort_keys, indent=4)

    def from_json(self, string):
        return json.loads(string, object_hook=deserialize.unserialize_object)

    def read_from_json(self, name):
        istream = open("Mat_" + name + '.json', 'r')
        jsondata= self.from_json(istream.read())
        # print type(jsondata)
        istream.close()
        
    def write_to_json(self, name):
        """
        write from json file
        """
        ostream = open("Mat_" + name + '.json', 'w')
        jsondata = self.to_json()
        ostream.write(str(jsondata))
        ostream.close()


        
def SimMaterial_constructor(loader, node):
    values = loader.construct_mapping(node)
    markers = values["markers"]
    physics = values["physics"]
    filename = values["filename"]
    return SimMaterial(markers, physics, filename)

yaml.add_constructor(u'!SimMaterial', SimMaterial_constructor)


###########################################################################
#
#
###########################################################################


#
# To operate from command line

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("name", help="name of the material to be stored")
    parser.add_argument("--markers", help="define list of markers for SimMaterial (eg H1_Cu/H2_Cu)", type=str)
    parser.add_argument("--physics", help="define list of physics for SimMaterial (eg heat/electric)", type=str)
    parser.add_argument("--filename", help="define properties filename for SimMaterial", type=str)
    args = parser.parse_args()
 
    import getpass
    UserName = getpass.getuser()

    # to get value: print(distance.magnitude)
    # to get unit: print(distance.units)


    filename = ""
    if args.filename:
        filename = args.filename

    physics = ""
    if args.physics:
        physics = args.physics.split("/")

    markers = ""
    if args.markers:
        markers = args.markers.split("/")
        
    Mat = SimMaterial(markers, physics, filename)
    Mat.dump(name)
    Mat.write_to_json(name)

    
