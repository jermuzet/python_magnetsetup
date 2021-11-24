from typing import List, Optional

def entry_cfg(template: str, rdata: dict, debug: bool = False):
    import chevron

    if debug:
        print("entry/loading %s" % str(template), type(template))
        print("entry/rdata:", rdata)
    with open(template, "r") as f:
        jsonfile = chevron.render(f, rdata)
    jsonfile = jsonfile.replace("\'", "\"")
    return jsonfile

def create_cfg(cfgfile:str, name: str, nonlinear: bool, jsonfile: str, template: str, method_data: List[str], debug: bool=False):
    """
    Create a cfg file
    """
    print("create_cfg %s from %s" % (cfgfile, template) )

    dim = 2
    if method_data[2] == "3D":
        dim = 3

    linear = ""
    if nonlinear:
        linear = "nonlinear"

    mesh = name + ".med" # "med", "gmsh", "hdf5" aka "json"

    data = {
        "dim": dim,
        "method": method_data[0],
        "model": method_data[3],
        "geom": method_data[2],
        "time": method_data[1],
        "linear": linear,
        "name": name,
        "jsonfile": jsonfile,
        "mesh": mesh,
        "scale": 0.001,
        "partition": 0
    }
    
    mdata = entry_cfg(template, data, debug)
    if debug:
        print("create_cfg/mdata=", mdata)

    with open(cfgfile, "x") as out:
        out.write(mdata)
    
    pass

