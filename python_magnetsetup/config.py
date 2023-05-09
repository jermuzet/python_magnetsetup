import json
import os
from typing import List, Optional

from decouple import Config, RepositoryEnv


class appenv:
    def __init__(
        self,
        envfile: str = "settings.env",
        debug: bool = False,
        url_api: str = None,
        yaml_repo: str = None,
        cad_repo: str = None,
        mesh_repo: str = None,
        template_repo: str = None,
        simage_repo: str = None,
        mrecord_repo: str = None,
        optim_repo: str = None,
    ):
        self.url_api: str = url_api
        self.yaml_repo: Optional[str] = yaml_repo
        self.cad_repo: Optional[str] = cad_repo
        self.mesh_repo: Optional[str] = mesh_repo
        self.template_repo: Optional[str] = template_repo
        self.simage_repo: Optional[str] = simage_repo
        self.mrecord_repo: Optional[str] = mrecord_repo
        self.optim_repo: Optional[str] = optim_repo

        if envfile is not None:
            envdata = RepositoryEnv(envfile)
            data = Config(envdata)
            if debug:
                print("appenv:", RepositoryEnv("settings.env").data)

            self.url_api = data.get("URL_API")
            self.compute_server = data.get("COMPUTE_SERVER")
            self.visu_server = data.get("VISU_SERVER")
            if "TEMPLATE_REPO" in envdata:
                self.template_repo = data.get("TEMPLATE_REPO")
            if "SIMAGE_REPO" in envdata:
                self.simage_repo = data.get("SIMAGE_REPO")
            if "DATA_REPO" in envdata:
                self.yaml_repo = data.get("DATA_REPO") + "/geometries"
                self.cad_repo = data.get("DATA_REPO") + "/cad"
                self.mesh_repo = data.get("DATA_REPO") + "/meshes"
                self.mrecord_repo = data.get("DATA_REPO") + "/mrecords"
                self.optim_repo = data.get("DATA_REPO") + "/optims"
        if debug:
            print(f"DATA: {self.yaml_repo}")

    def template_path(self, debug: bool = False):
        """
        returns template_repo
        """
        if not self.template_repo:
            default_path = os.path.dirname(os.path.abspath(__file__))
            repo = os.path.join(default_path, "templates")
        else:
            repo = self.template_repo

        if debug:
            print("appenv/template_path:", repo)
        return repo

    def simage_path(self, debug: bool = False):
        """
        returns simage_repo
        """
        if not self.simage_repo:
            repo = os.path.join("/home/singularity")
        else:
            repo = self.simage_repo

        if debug:
            print("appenv/simage_path:", repo)
        return repo


def loadconfig():
    """
    Load app config (aka magnetsetup.json)
    """

    default_path = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(default_path, "magnetsetup.json"), "r") as appcfg:
        magnetsetup = json.load(appcfg)
    return magnetsetup


def loadtemplates(
    appenv: appenv, appcfg: dict, method_data: List[str], debug: bool = False
):
    """
    Load templates into a dict

    method_data:
    method
    time
    geom
    model
    cooling

    """

    [method, time, geom, model, cooling, units_def, nonlinear] = method_data
    print(f"time: {time}")
    print(f"nonlinear: {nonlinear} type={type(nonlinear)}")
    template_path = os.path.join(appenv.template_path(), method, geom, model)

    modelcfg = appcfg[method][time][geom][model]
    cfg_model = modelcfg["cfg"]
    json_model = modelcfg["model"]
    if not nonlinear:
        conductor_model = modelcfg["conductor-linear"]
    else:
        if geom == "3D":
            json_model = modelcfg["model-nonlinear"]
        conductor_model = modelcfg["conductor-nonlinear"]
    insulator_model = modelcfg["insulator"]

    fcfg = os.path.join(template_path, cfg_model)
    if debug:
        print(f"fcfg: {fcfg} type={type(fcfg)}")

    fmodel = os.path.join(template_path, json_model)
    fconductor = os.path.join(template_path, conductor_model)
    finsulator = os.path.join(template_path, insulator_model)

    if geom == "Axi":
        pyfeelU = modelcfg["create_U"]
        fpyfeelU = os.path.join(template_path, pyfeelU)

    material_generic_def = ["conductor", "insulator"]
    if time == "transient":
        material_generic_def.append("conduct-nosource")  # only for transient with mqs

    dict = {
        "physic": modelcfg["physic"],
        "cfg": fcfg,
        "model": fmodel,
        "conductor": fconductor,
        "insulator": finsulator,
        "stats": {},
        "plots": {},
        "material_def": material_generic_def,
    }

    if geom == "Axi":
        dict["create_U"] = fpyfeelU

    if "stats" in modelcfg:
        _cfg = modelcfg["stats"]
        for field in _cfg:
            # print(f'stats[{field}]: {_cfg} (type={type(_cfg)})')
            dict["stats"][field] = _cfg[field]
            dict["stats"][field]["template"] = os.path.join(
                template_path, _cfg[field]["template"]
            )
        if debug:
            print(f"dict[stats]={dict['stats']}")

    if "plots" in modelcfg:
        _cfg = modelcfg["plots"]
        for field in _cfg:
            dict["plots"][field] = os.path.join(template_path, _cfg[field])
        if debug:
            print(f"dict[plots]={dict['plots']}")

    for kdata in modelcfg["models"]:
        dict[kdata] = os.path.join(template_path, modelcfg["models"][kdata])

    if "th" in model:
        cooling_model = modelcfg["cooling"][cooling]
        flux_model = modelcfg["cooling-post"][cooling]

        fcooling = os.path.join(template_path, cooling_model)
        fflux = os.path.join(template_path, flux_model)

        dict["cooling"] = fcooling
        dict["flux"] = fflux

    if check_templates(dict):
        pass

    return dict


def check_templates(templates: dict):
    """
    check if template file exist
    """
    print(f"=== Templates keys ===\n {templates.keys()}")
    print("=== Checking Templates ===")
    for key in templates:
        if isinstance(templates[key], str):
            print(f"{key}: {templates[key]}")
            with open(templates[key], "r") as f:
                pass

        elif isinstance(templates[key], str):
            for s in templates[key]:
                print(f"{key}: {s}")
                with open(s, "r") as f:
                    pass
    print("==========================")

    return True


def supported_models(Appcfg, method: str, geom: str, time: str) -> List:
    """
    get supported models by method as a dict
    """

    models = []
    # print(f'supported_models[{method}]: {Appcfg[method]}')
    if Appcfg[method][time]:
        if geom in Appcfg[method][time]:
            for key in Appcfg[method][time][geom]:
                models.append(key)

    return models


def supported_methods(Appcfg) -> List:
    """
    get supported methods as a dict
    """

    methods = []
    for key in Appcfg:
        if Appcfg[key] and not key in ["mesh", "post"]:
            methods.append(key)

    return methods
