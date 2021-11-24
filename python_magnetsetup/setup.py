"""
Create template json model files for Feelpp/HiFiMagnet simu
From a yaml definition file of an insert

Inputs:
* method : method of solve, with feelpp cfpdes, getdp...
* time: stationnary or transient case
* geom: geometry of solve, 3D or Axi
* model: physic solved, thermic, thermomagnetism, thermomagnetism-elastic
* phytype: if the materials are linear or non-linear
* cooling: what type of cooling, mean or grad

Output: 
* tmp.json

App setup is stored in a json file that defines
the mustache template to be used.

Default path:
magnetsetup.json
mustache templates
"""

# TODO check for unit consistency
# depending on Length base unit

from typing import List, Optional

import sys
import os
import json
import yaml

from python_magnetgeo import Insert
from python_magnetgeo import python_magnetgeo

from .config import appenv, loadconfig, loadtemplates
from .objects import load_object, load_object_from_db
from .utils import Merge
from .cfg import create_cfg
from .jsonmodel import create_json, create_params, create_bcs, create_materials
    
def main():
    """
    """
    print("setup/main")
    import argparse

    # Manage Options
    command_line = None
    parser = argparse.ArgumentParser(description="Create template json model files for Feelpp/HiFiMagnet simu")
    parser.add_argument("--datafile", help="input data file (ex. HL-34-data.json)", default=None)
    parser.add_argument("--wd", help="set a working directory", type=str, default="")
    parser.add_argument("--magnet", help="Magnet name from magnetdb (ex. HL-34)", default=None)

    parser.add_argument("--method", help="choose method (default is cfpdes", type=str,
                    choices=['cfpdes', 'CG', 'HDG', 'CRB'], default='cfpdes')
    parser.add_argument("--time", help="choose time type", type=str,
                    choices=['static', 'transient'], default='static')
    parser.add_argument("--geom", help="choose geom type", type=str,
                    choices=['Axi', '3D'], default='Axi')
    parser.add_argument("--model", help="choose model type", type=str,
                    choices=['thelec', 'mag', 'thmag', 'thmagel'], default='thmagel')
    parser.add_argument("--nonlinear", help="force non-linear", action='store_true')
    parser.add_argument("--cooling", help="choose cooling type", type=str,
                    choices=['mean', 'grad', 'meanH', 'gradH'], default='mean')
    parser.add_argument("--scale", help="scale of geometry", type=float, default=1e-3)

    parser.add_argument("--debug", help="activate debug", action='store_true')
    parser.add_argument("--verbose", help="activate verbose", action='store_true')
    args = parser.parse_args()

    if args.debug:
        print(args)
    
    # TODO make datafile/magnet exclusive one or the other
    
    # load appenv
    MyEnv = appenv()
    if args.debug: print(MyEnv.template_path())

    # loadconfig
    AppCfg = loadconfig()

    # Get current dir
    cwd = os.getcwd()
    if args.wd:
        os.chdir(args.wd)
    
    # load appropriate templates
    method_data = [args.method, args.time, args.geom, args.model, args.cooling]
    templates = loadtemplates(MyEnv, AppCfg, method_data, (not args.nonlinear) )

    # Get Object
    if args.datafile != None:
        confdata = load_object(MyEnv, args.datafile, args.debug)
        jsonfile = args.datafile.replace(".json","")

    if args.magnet != None:
        confdata = load_object_from_db(MyEnv, "magnet", args.magnet, args.debug)
        jsonfile = args.magnet
    
    # load geom: yamlfile = confdata["geom"]
    part_thermic = []
    part_electric = []
    index_electric = []
    index_Helices = []
    index_Insulators = []
    
    boundary_meca = []
    boundary_maxwell = []
    boundary_electric = []

    yamlfile = confdata["geom"]
    with open(yamlfile, 'r') as cfgdata:
        cad = yaml.load(cfgdata, Loader = yaml.FullLoader)
        if isinstance(cad, Insert):
            gdata = python_magnetgeo.get_main_characteristics(cad)
            (NHelices, NRings, NChannels, Nsections, R1, R2, Z1, Z2, Zmin, Zmax, Dh, Sh) = gdata

            print("Insert: %s" % cad.name, "NHelices=%d NRings=%d NChannels=%d" % (NHelices, NRings, NChannels))

            for i in range(NHelices):
                part_electric.append("H{}".format(i+1))
                if args.geom == "Axi":
                    for j in range(Nsections[i]+2):
                        part_thermic.append("H{}_Cu{}".format(i+1,j))
                    for j in range(Nsections[i]):
                        index_electric.append( [str(i+1),str(j+1)] )
                    index_Helices.append(["0:{}".format(Nsections[i]+2)])
                
                else:
                    with open(cad.Helices[i]+".yaml", "r") as f:
                        hhelix = yaml.load(cad.Helices[i]+".yaml", Loader = yaml.FullLoader)
                        (insulator_name, insulator_number) = hhelix.insulators()
                        index_Insulators.append((insulator_name, insulator_number))

            for i in range(NRings):
                part_thermic.append("R{}".format(i+1))
                part_electric.append("R{}".format(i+1))

            # Add currentLeads
            if  args.geom == "3D" and len(cad.CurrentLeads):
                part_thermic.append("iL1")
                part_thermic.append("oL2")
                part_electric.append("iL1")
                part_electric.append("oL2")
                boundary_electric.append(["Inner1_LV0", "iL1", "0"])
                boundary_electric.append(["OuterL2_LV0", "oL2", "V0:V0"])
                
                boundary_meca.append("Inner1_LV0")
                boundary_meca.append("OuterL2_LV0")

                boundary_maxwell.append("InfV00")
                boundary_maxwell.append("InfV01")

            else:
                boundary_electric.append(["H1_V0", "H1", "0"])
                boundary_electric.append(["H%d_V0" % NHelices, "H%d" % NHelices, "V0:V0"])
                
                boundary_meca.append("H1_HP")
                boundary_meca.append("H_HP")    
                
            boundary_maxwell.append("InfV1")
            boundary_maxwell.append("InfR1")

            
            for i in range(1,NRings+1):
                if i % 2 == 1 :
                    boundary_meca.append("R{}_BP".format(i))
                else :
                    boundary_meca.append("R{}_HP".format(i))

            # TODO : manage the scale
            for i in range(NChannels):
                 Zmin[i] *= args.scale
                 Zmax[i] *= args.scale
                 Dh[i] *= args.scale
                 Sh[i] *= args.scale
            
            if args.debug:
                print("part_electric:", part_electric)
                print("part_thermic:", part_thermic)

            # params section
            params_data = create_params(gdata, method_data, args.debug)

            # bcs section
            bcs_data = create_bcs(boundary_meca, 
                                  boundary_maxwell,
                                  boundary_electric,
                                  gdata, confdata, templates, method_data, args.debug) # merge all bcs dict

            # build dict from geom for templates
            # TODO fix initfile name (see create_cfg for the name of output / see directory entry)
            # eg: $home/feelppdb/$directory/cfppdes-heat.save

            main_data = {
                "part_thermic": part_thermic,
                "part_electric": part_electric,
                "index_electric": index_electric,
                "index_V0": boundary_electric,
                "temperature_initfile": "tini.h5",
                "V_initfile": "Vini.h5"
            }
            mdict = Merge( Merge(main_data, params_data), bcs_data)

            powerH_data = { "Power_H": [] }
            meanT_data = { "meanT_H": [] }
            if args.geom == "Axi":
                for i in range(NHelices) :
                    powerH_data["Power_H"].append( {"header": "Power_H{}".format(i+1), "name": "H{}_Cu%1%".format(i+1), "index": index_Helices[i]} )
                    meanT_data["meanT_H"].append( {"header": "MeanT_H{}".format(i+1), "name": "H{}_Cu%1%".format(i+1), "index": index_Helices[i]} )
            else:
                for i in range(NHelices) :
                    powerH_data["Power_H"].append( {"header": "Power_H{}".format(i+1), "name": "H{}".format(i+1)} )
                    meanT_data["meanT_H"].append( {"header": "MeanT_H{}".format(i+1), "name": "H{}".format(i+1)} )
                # TODO add Glue/Kaptons
                for i in range(NRings) :
                    powerH_data["Power_H"].append( {"header": "Power_R{}".format(i+1), "name": "R{}".format(i+1)} )
                    meanT_data["meanT_H"].append( {"header": "MeanT_R{}".format(i+1), "name": "R{}".format(i+1)} )

                if len(cad.CurrentLeads):
                    powerH_data["Power_H"].append( {"header": "Power_iL1", "name": "iL1"} )
                    powerH_data["Power_H"].append( {"header": "Power_oL2", "name": "oL2"} )
                    meanT_data["meanT_H"].append( {"header": "MeanT_iL1", "name": "iL1"} )
                    meanT_data["meanT_H"].append( {"header": "MeanT_oL2", "name": "oL2"} )

            mpost = { 
                "flux": {'index_h': "0:%s" % str(NChannels)},
                "meanT_H": meanT_data ,
                "power_H": powerH_data 
            }
            mmat = create_materials(gdata, index_Insulators, confdata, templates, method_data, args.debug)

            # create cfg
            if args.datafile: 
                jsonfile = args.datafile.replace("-data.json","")
            if args.magnet: 
                jsonfile = args.magnet
            jsonfile += "-" + args.method
            jsonfile += "-" + args.model
            if args.nonlinear:
                jsonfile += "-nonlinear"
            jsonfile += "-" + args.geom
            jsonfile += "-sim.json"
            cfgfile = jsonfile.replace(".json", ".cfg")

            name = yamlfile.replace(".yaml","")
            create_cfg(cfgfile, name, args.nonlinear, jsonfile, templates["cfg"], method_data, args.debug)
            
            # create json
            create_json(jsonfile, mdict, mmat, mpost, templates, method_data, args.debug)

            # copy some additional json file 
            material_generic_def = ["conductor", "insulator"]

            if args.time == "transient":
                material_generic_def.append("conductor-nosource") # only for transient with mqs

            if args.method == "cfpdes":
                if args.debug: print("cwd=", cwd)
                from shutil import copyfile
                for jsonfile in material_generic_def:
                    filename = AppCfg[args.method][args.time][args.geom][args.model]["filename"][jsonfile]
                    src = os.path.join(MyEnv.template_path(), args.method, args.geom, args.model, filename)
                    dst = os.path.join(jsonfile + "-" + args.method + "-" + args.model + "-" + args.geom + ".json")
                    if args.debug:
                        print(jsonfile, "filename=", filename, "src=%s" % src, "dst=%s" % dst)
                    copyfile(src, dst)
     
        else:
            raise Exception("expected Insert yaml file")

    # Print command to run
    print("\n\n=== Commands to run (ex pour cfpdes/Axi) ===")
    salome = "/home/singularity/hifimagnet-salome-9.7.0.sif"
    feelpp = "/home/singularity/feelpp-toolboxes-v0.109.0.sif"
    partitioner = 'feelpp_mesh_partitioner'
    exec = 'feelpp_toolbox_coefficientformpdes'
    pyfeel = 'cfpdes_insert_fixcurrent.py'
    if args.geom == "Axi" and args.method == "cfpdes" :
        xaofile = cad.name + "-Axi_withAir.xao"
        geocmd = "salome -w1 -t $HIFIMAGNET/HIFIMAGNET_Cmd.py args:%s,--axi,--air,2,2,--wd,$PWD" % (yamlfile)
        
        # if gmsh:
        meshcmd = "python3 -m python_magnetgeo.xao %s --wd $PWD mesh --group CoolingChannels --geo %s --lc=1" % (xaofile, yamlfile)
        meshfile = xaofile.replace(".xao", ".msh")

        # if MeshGems:
        #meshcmd = "salome -w1 -t $HIFIMAGNET/HIFIMAGNET_Cmd.py args:%s,--axi,--air,2,2,mesh,--group,CoolingChannels" % yamlfile
        #meshfile = xaofile.replace(".xao", ".med")
        
        h5file = xaofile.replace(".xao", "_p.json")
        partcmd = "feelpp_mesh_partition --ifile %s --ofile %s [--part NP] [--mesh.scale=0.001]" % (meshfile, h5file)
        feelcmd = "[mpirun -np NP] %s --config-file %s" % (exec, cfgfile)
        pyfeelcmd = "[mpirun -np NP] python %s" % pyfeel
    
        print("Guidelines for running a simu")
        print("export HIFIMAGNET=/opt/SALOME-9.7.0-UB20.04/INSTALL/HIFIMAGNET/bin/salome")
        print("workingdir:", args.wd)
        print("CAD:", "singularity exec %s %s" % (salome,geocmd) )
        # if gmsh
        print("Mesh:", meshcmd)
        # print("Mesh:", "singularity exec -B /opt/DISTENE:/opt/DISTENE:ro %s %s" % (salome,meshcmd))
        print("Partition:", "singularity exec %s %s" % (feelpp, partcmd) )
        print("Feel:", "singularity exec %s %s" % (feelpp, feelcmd) )
        print("pyfeel:", "singularity exec %s %s" % (feelpp, pyfeel))
    pass

if __name__ == "__main__":
    main()
