from typing import List, Optional

import sys
import os
import json
import yaml

from .config import appenv

def query_db(appenv: appenv, mtype: str, name: str, debug: bool = False):
    """
    Get object from magnetdb
    """

    import requests
    import requests.exceptions
    
    r = requests.get(url= appenv.url_api + '/' + mtype + '/mdata/' + name )
    if debug: print("request:", r)
    if (r.status_code == requests.codes.ok):
        if debug: print("request:", r.text)
        mdata = json.loads(r.text)
        if debug:
            print("query_db/mdata:", mdata)
        # confdata = ast.literal_eval(r.text)
        return mdata
    else:
        print("failed to retreive %s from db" % name)
        list_mtype_db(appenv, mtype)
        print("available requested mtype in db are: ", list_mtype_db(appenv, mtype))
        sys.exit(1)

def list_mtype_db(appenv: appenv, mtype: str, debug: bool = False):
    """
    List object of mtype stored in magnetdb
    """

    import requests
    import requests.exceptions
    
    names = []
    if mtype in ["Helix", "Bitter", "Supra"]:
        mtype = "mpart"
    r = requests.get(url= appenv.url_api + '/' + mtype + 's/' )
    if debug:
        print("url=%s", appenv.url_api)
        print("request(url=%s):" % (appenv.url_api + '/' + mtype + 's/'), r)
    if (r.status_code == requests.codes.ok):
        data = json.loads(r.text)
        # data = ast.literal_eval(r.text)
        if debug:
            print("list_mtype_db:", data)
        return [ d["name"] for d in data ]
    pass

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

def load_object_from_db(appenv: appenv, mtype: str, name: str, debug: bool = False):
    """
    Load object props from db
    """

    if not mtype in ["msite", "magnet", "Helix", "Bitter", "Supra", "material"]:
        raise("query_bd: %s not supported" % mtype)
    
    return query_db(appenv, mtype, name, debug)
