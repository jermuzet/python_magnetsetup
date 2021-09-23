#!/usr/bin/env python3
#-*- coding:utf-8 -*-

"""
Provides tools to un/serialize data from json
"""

import json

from MeshData import *
from NumModel import *

from Material import *
from SimMaterial import *

# From : http://chimera.labs.oreilly.com/books/1230000000393/ch06.html#_discussion_95
# Dictionary mapping names to known classes

classes = {
    'MeshData' : MeshData,
    'SimMaterial' : SimMaterial,
    'Material' : Material,
    'NumModel' : NumModel
}

def serialize_instance(obj):
    """
    serialize_instance of an obj
    """
    d = {'__classname__' : type(obj).__name__}
    d.update(vars(obj))
    return d

def unserialize_object(d):
    """
    unserialize_instance of an obj
    """
    clsname = d.pop('__classname__', None)
    if clsname:
        cls = classes[clsname]
        obj = cls.__new__(cls)   # Make instance without calling __init__
        for key, value in d.items():
            setattr(obj, key, value)
        return obj
    else:
        return d

