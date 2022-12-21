import json
import os
from typing import List, Optional

from decouple import Config, RepositoryEnv


class appenv():
    
    def __init__(self, envfile: str = "settings.env", debug: bool = False, url_api: str = None,
                 yaml_repo: str = None, cad_repo: str = None, mesh_repo: str = None, template_repo: str = None,
                 simage_repo: str = None, mrecord_repo: str = None, optim_repo: str = None):
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

            self.url_api = data.get('URL_API')
            self.compute_server = data.get('COMPUTE_SERVER')
            self.visu_server = data.get('VISU_SERVER')
            if 'TEMPLATE_REPO' in envdata:
                self.template_repo = data.get('TEMPLATE_REPO')
            if 'SIMAGE_REPO' in envdata:
                self.simage_repo = data.get('SIMAGE_REPO')
            if 'DATA_REPO' in envdata:
                self.yaml_repo = data.get('DATA_REPO') + "/geometries"
                self.cad_repo = data.get('DATA_REPO') + "/cad"
                self.mesh_repo = data.get('DATA_REPO') + "/meshes"
                self.mrecord_repo = data.get('DATA_REPO') + "/mrecords"
                self.optim_repo = data.get('DATA_REPO') + "/optims"
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
    with open(os.path.join(default_path, 'magnetsetup.json'), 'r') as appcfg:
        magnetsetup = json.load(appcfg)
    return magnetsetup

def loadtemplates(appenv: appenv, appcfg: dict, method_data: List[str], debug: bool=False):
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

    cfg_model = appcfg[method][time][geom][model]["cfg"]
    json_model = appcfg[method][time][geom][model]["model"]
    if not nonlinear:
        conductor_model = appcfg[method][time][geom][model]["conductor-linear"]
    else:
        if geom == "3D":
            json_model = appcfg[method][time][geom][model]["model-nonlinear"]
        conductor_model = appcfg[method][time][geom][model]["conductor-nonlinear"]
    insulator_model = appcfg[method][time][geom][model]["insulator"]
    
    fcfg = os.path.join(template_path, cfg_model)
    if debug:
        print(f"fcfg: {fcfg} type={type(fcfg)}")
    fmodel = os.path.join(template_path, json_model)
    fconductor = os.path.join(template_path, conductor_model)
    finsulator = os.path.join(template_path, insulator_model)
    if 'th' in model:
        heat_conductor = appcfg[method][time][geom][model]["models"]["heat-conductor"]
        heat_insulator = appcfg[method][time][geom][model]["models"]["heat-insulator"]

        cooling_model = appcfg[method][time][geom][model]["cooling"][cooling]
        flux_model = appcfg[method][time][geom][model]["cooling-post"][cooling]
        stats_T_model = appcfg[method][time][geom][model]["stats_T"]

        fheatconductor = os.path.join(template_path, heat_conductor)
        fheatinsulator = os.path.join(template_path, heat_insulator)
    
        fcooling = os.path.join(template_path, cooling_model)
        frobin = os.path.join(template_path, appcfg[method][time][geom][model]["cooling"]["robin"])
        fflux = os.path.join(template_path, flux_model)
        fstats_T = os.path.join(template_path, stats_T_model)

    if 'mag' in model or 'mqs' in model :
        magnetic_conductor = appcfg[method][time][geom][model]["models"]["magnetic-conductor"]
        magnetic_insulator = appcfg[method][time][geom][model]["models"]["magnetic-insulator"]

        fmagconductor = os.path.join(template_path, magnetic_conductor)
        fmaginsulator = os.path.join(template_path, magnetic_insulator)

        plot_model = appcfg[method][time][geom][model]["plots_B"]
        plots_B =  os.path.join(template_path, plot_model)

    if 'magel' in model :
        elastic_conductor = appcfg[method][time][geom][model]["models"]["elastic-conductor"]
        elastic_insulator = appcfg[method][time][geom][model]["models"]["elastic-insulator"]
        felasconductor = os.path.join(template_path, elastic_conductor)
        felasinsulator = os.path.join(template_path, elastic_insulator)
        stats_Stress_model = appcfg[method][time][geom][model]["stats_Stress"]

    if 'mqsel' in model :
        elastic1_conductor = appcfg[method][time][geom][model]["models"]["elastic1-conductor"]
        elastic1_insulator = appcfg[method][time][geom][model]["models"]["elastic1-insulator"]
        elastic2_conductor = appcfg[method][time][geom][model]["models"]["elastic2-conductor"]
        elastic2_insulator = appcfg[method][time][geom][model]["models"]["elastic2-insulator"]

        felas1conductor = os.path.join(template_path, elastic1_conductor)
        felas1insulator = os.path.join(template_path, elastic1_insulator)
        felas2conductor = os.path.join(template_path, elastic2_conductor)
        felas2insulator = os.path.join(template_path, elastic2_insulator)

        stats_Stress_model = appcfg[method][time][geom][model]["stats_Stress"]

    #if model != 'mag' and model != 'mag_hcurl' and model != 'mqs' and model != 'mqs_hcurl':
    stats_Power_model = appcfg[method][time][geom][model]["stats_Power"]
    stats_Current_model = appcfg[method][time][geom][model]["stats_Current"]

    fstats_Power = os.path.join(template_path, stats_Power_model)
    fstats_Current = os.path.join(template_path, stats_Current_model)

    material_generic_def = ["conductor", "insulator"]
    if time == "transient":
        material_generic_def.append("conduct-nosource") # only for transient with mqs

    dict = {
        "cfg": fcfg,
        "model": fmodel,
        "conductor": fconductor,
        "insulator": finsulator,
        "stats": [],
        "plots":[],
        "material_def" : material_generic_def
    }

    if 'th' in model:
        dict["heat-conductor"] = fheatconductor
        dict["heat-insulator"] = fheatinsulator
        dict["cooling"] = fcooling
        dict["robin"] = frobin
        dict["flux"] = fflux
        dict["stats"].append(fstats_T)

    if 'mag' in model or 'mqs' in model :
        dict["magnetic-conductor"] = fmagconductor
        dict["magnetic-insulator"] = fmaginsulator
        dict["plots"].append(plots_B)

    if 'magel' in model :
        dict["elastic-conductor"] = felasconductor
        dict["elastic-insulator"] = felasinsulator

    if 'mqsel' in model :
        dict["elastic1-conductor"] = felas1conductor
        dict["elastic1-insulator"] = felas1insulator
        dict["elastic2-conductor"] = felas2conductor
        dict["elastic2-insulator"] = felas2insulator
    
    #if model != 'mag' and model != 'mag_hcurl' and model != 'mqs' and model != 'mqs_hcurl':
    dict["stats"].append(fstats_Power)
    dict["stats"].append(fstats_Current)

    if check_templates(dict):
        pass

    return dict

def check_templates(templates: dict):
    """
    check if template file exist
    """
    print("\n\n=== Checking Templates ===")
    for key in templates:
        if isinstance(templates[key], str):
            print(key, templates[key])
            with open(templates[key], "r") as f: pass

        elif isinstance(templates[key], str):
            for s in templates[key]:
                print(key, s)
                with open(s, "r") as f: pass
    print("==========================\n\n")

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
        if Appcfg[key] and not key in ['mesh', 'post']:
            methods.append(key)

    return methods
