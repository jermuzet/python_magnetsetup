from typing import List, Optional

import sys
import os
import json
import yaml

from .config import appenv

# def query_db(appenv: appenv, mtype: str, name: str, debug: bool = False):
#     """
#     Get object from magnetdb
#     """
 
#     from python_magnetapi.utils import get_list, get_object
#     headers = {"Authorization": os.getenv("MAGNETDB_API_KEY")}
#     web = appenv.url_api

#     ids = get_list(
#                 f"{web}", headers=headers, mtype=mtype, debug=debug
#             )
#     if name in ids:
#         response = get_object(
#                     f"{web}",
#                     headers=headers,
#                     mtype=mtype,
#                     id=ids[name],
#                     debug=debug,
#                 )
#         if debug: print("response:", response)
#         mdata = {json.dumps(response)}
#         return mdata
#     else:
#         available_objs = [id['name'] for id in ids]
#         raise Exception(f"failed to retreive {name} from db: available requested mtype in db are: {available_objs}")

# def list_mtype_db(appenv: appenv, mtype: str, debug: bool = False):
#     """
#     List object of mtype stored in magnetdb
#     """

#     from python_magnetapi.utils import get_list
#     headers = {"Authorization": os.getenv("MAGNETDB_API_KEY")}
#     web = appenv.url_api
    
#     if mtype.lower() in ["helix", "bitter", "supra"]:
#         mtype = "part"
    
#     ids = get_list(
#                 f"{web}", headers=headers, mtype=mtype, debug=debug
#             )
#     return [ id["name"] for id in ids ]

def load_object(appenv: appenv, datafile: str, debug: bool = False):
    """
    Load object props
    """

    if appenv.yaml_repo:
        print("Look for %s in %s" % (datafile, appenv.yaml_repo))
    else:
        print("Look for %s in workingdir %s" % (datafile, os.getcwd()))

    with open(datafile, 'r') as cfgdata:
            confdata = json.load(cfgdata)
    return confdata


# def load_object_from_db(appenv: appenv, mtype: str, name: str, debug: bool = False, session = None):
#     """
#     Load object props from db
#     """
#     if not mtype.lower() in ["msite", "magnet", "helix", "bitter", "supra", "material"]:
#         raise("query_bd: %s not supported" % mtype)

#     if session:

#         from python_magnetapi.utils import get_list
#         headers = {"Authorization": os.getenv("MAGNETDB_API_KEY")}
#         web = appenv.url_api

#         mdata = None
#         if mtype.lower() == "magnet":
#             mdata = get_magnet_data(session, name)
#             r = requests.get(url=f'{appenv.url_api}/{mtype}s/{id}/mdata')
#         if mtype.lower() == "msite":
#             mdata = get_msite_data(session, name)

#         print ("load_object_from_db: use direct call to db")
#         return mdata
    
#     print ("load_object_from_db: use request")
#     return query_db(appenv, mtype, name, debug)

