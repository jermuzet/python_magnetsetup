"""Console script for linking python_magnetsetup and python_magnettoos."""

from typing import List, Optional

import sys
import os
import json
import yaml
import math

import argparse
from .objects import load_object, load_object_from_db
from .config import appenv, loadconfig, loadtemplates

from python_magnetgeo import Insert, MSite, Bitter, Supra, SupraStructure
from python_magnetgeo import python_magnetgeo

from .file_utils import MyOpen, findfile, search_paths

import MagnetTools.MagnetTools as mt

def HMagnet(MyEnv, struct: Insert, data: dict, debug: bool=False):
    """
    create view of this insert as a Helices Magnet

    b=mt.BitterfMagnet(r2, r1, h, current_density, z_offset, fillingfactor, rho)
    """
    print("HMagnet:", data)

    # how to create Tubes??
    #Tube(const int n= len(struct.axi.turns), const MyDouble r1 = struct.r[0], const MyDouble r2 = struct.r[1], const MyDouble l = struct.axi.h??)

    Tubes = mt.VectorOfTubes()
    Helices = mt.VectorOfBitters()
    OHelices = mt.VectorOfBitters()

    index = 0
    for helix in data["Helix"]:
        material = helix["material"]
        geom = helix["geom"]
        with MyOpen(geom, 'r', paths=search_paths(MyEnv, "geom")) as cfgdata:
            cad = yaml.load(cfgdata, Loader = yaml.FullLoader)
        nturns = len(cad.axi.turns)
        print("nturns:", nturns)
        r1 = cad.r[0]
        r2 = cad.r[1]
        h = cad.axi.h
        Tube = mt.Tube(nturns, r1*1.e-3, r2*1.e-3, h*1.e-3)
        Tube.set_index(index)
        print("index:", index, Tube.get_index())
        print("cad.axi:", cad.axi)
        for (n, pitch) in zip(cad.axi.turns,cad.axi.pitch):
            Tube.set_pitch(pitch*1.e-3)
            Tube.set_nturn(n)

        Tubes.append( Tube )
        fillingfactor = 1
        tmp = BMagnet(cad, material, fillingfactor, debug)
        for item in tmp:
            Helices.append(item)
        index += Tube.get_n_elem()

    print("HMagnet:", struct.name, "Tubes:", len(Tubes), "Helices:", len(Helices))
    return (Tubes, Helices, OHelices)

def BMagnet(struct: Bitter, material: dict, fillingfactor: float=1, debug: bool=False):
    """
    create view of this insert as a Bitter Magnet

    b=mt.BitterfMagnet(r2, r1, h, current_density, z_offset, fillingfactor, rho)
    """
    
    BMagnets = mt.VectorOfBitters()
    
    rho = 1/ material["ElectricalConductivity"]
    f = fillingfactor # 1/struct.get_Nturns() # struct.getFillingFactor()
        
    r1 = struct.r[0]*1.e-3
    r2 = struct.r[1]*1.e-3
    z = -struct.axi.h*1.e-3

    for (n, pitch) in zip(struct.axi.turns, struct.axi.pitch):
        dz = n * pitch*1.e-3
        if f != 1:
            j = n / (r1 * math.log(r2/r1) * dz)
        else:
            j = 1 / (r1 * math.log(r2/r1) * dz)
        z_offset = z + dz/2.
        BMagnets.append( mt.BitterMagnet(r2, r1, dz, j, z_offset, f, rho) )
                
        z += dz

    print("BMagnet:", struct.name, len(BMagnets))
    return BMagnets

def UMagnet(struct: Supra, debug: bool=False):
    """
    create view of this insert as a Uniform Magnet

    b=mt.UnifMagnet(r2, r1, h, current_density, z_offset, fillingfactor, rho)
    """

    rho = 0
    f = struct.getFillingFactor()
    nturns = 0
    S = 0
    for dp in struct.dblepancakes:
        nturns += 2 * dp.pancake.n
        j = nturns / struct.getArea()*1.e-6
    
    print("UMagnets:", struct.name, 1)
    return mt.UnifMagnet(struct.r1*1.e-3, struct.r0*1.e-3, struct.h*1.e-3, j, struct.z0, f, rho)


def UMagnets(struct: SupraStructure.HTSinsert, detail: str ="dblepancake", debug: bool=False):
    """
    create view of this insert as a stack of Uniform Magnets

    detail: control the view model
    dblepancake: each double pancake is a U Magnet
    pancake: each pancake is a U Magnet
    tape: each tape is a U Magnet
    """
    rho = 0
    UMagnets = mt.VectorOfUnifs()

    for dp in struct.dblepancakes:
        h = dp.getH()
        zm = dp.getZ0()
        zi = zm - h/2.
        if detail == "dblepancake":
            f = dp.getFillingFactor()
            S = dp.getArea()
            j = 2 * dp.pancake.n / S
            UMagnets.append( mt.UnifMagnet(struct.r1, struct.r0, h, j, zm, f, rho) )

        elif detail == "pancake":
            h_p = dp.pancake.getH()
            f = dp.pancake.getFillingFactor()
            S = dp.pancake.getArea()
            j = dp.pancake.n / S
            UMagnets.append( mt.UnifMagnet(struct.r1, struct.r0, h_p, j, zi+h_p/2., f, rho))
            zi = (zm + h/2.) - h_p
            UMagnets.append( mt.UnifMagnet(struct.r1, struct.r0, h_p, j, zi+h_p/2., f, rho))

        elif detail == "tape":
            h_p = dp.pancake.getH()
            f = dp.pancake.tape.getFillingFactor()
            S = dp.pancake.tape.getArea()
            j =  1 / S / f
            ntapes = dp.pancake.n
            h_t = dp.pancake.tape.h
            w = dp.pancake.tape.w
            r = dp.pancake.getR()
            for l in range(ntapes):
                ri = r[l]
                ro = ri + w
                UMagnets.append( mt.UnifMagnet(ro, ri, h_t, j, zi+h_t/2., f, rho))

            zi = (zm + h/2.) - h_p
            for l in range(ntapes):
                ri = r[l]
                ro = ri + w
                UMagnets.append( mt.UnifMagnet(ro, ri, h_t, j, zi+h_t/2., f, rho))

    print("UMagnets:", struct.name, len(UMagnets))
    return UMagnets


def magnet_setup(MyEnv, confdata: str, debug: bool=False):
    """
    Creating MagnetTools data struct for setup for magnet
    """
    print("magnet_setup", "debug=", debug)
    
    yamlfile = confdata["geom"]
    if debug:
        print("magnet_setup:", yamlfile)

    Tubes = mt.VectorOfTubes()
    Helices = mt.VectorOfBitters()
    OHelices = mt.VectorOfBitters()
    UMagnets = mt.VectorOfUnifs()
    BMagnets = mt.VectorOfBitters()
    Shims = mt.VectorOfShims()
    
    if "Helix" in confdata:
        print("Load an insert")
        # Download or Load yaml file from data repository??
        cad = None
        # with open(yamlfile, 'r') as cfgdata:
        with MyOpen(yamlfile, 'r', paths=search_paths(MyEnv, "geom")) as cfgdata:
            cad = yaml.load(cfgdata, Loader = yaml.FullLoader)
        # if isinstance(cad, Insert):
        tmp = HMagnet(MyEnv, cad, confdata, debug)
        for item in tmp[0]:
            Tubes.append(item)
        for item in tmp[1]:
            Helices.append(item)
        for item in tmp[2]:
            OHelices.append(item)

    for mtype in ["Bitter", "Supra"]:
        if mtype in confdata:
            print("load a %s insert" % mtype)

            # loop on mtype
            for obj in confdata[mtype]:
                print("obj:", obj)
                cad = None
                with MyOpen(obj['geom'], 'r', paths=search_paths(MyEnv, "geom")) as cfgdata:
                    cad = yaml.load(cfgdata, Loader = yaml.FullLoader)
    
                if isinstance(cad, Bitter.Bitter):
                    fillingfactor = 1/cad.axi.get_Nturns()
                    tmp = BMagnet(cad, obj["material"], fillingfactor, debug)
                    for item in tmp:
                        BMagnets.append(item)
                elif isinstance(cad, Supra):
                    # get SupraStructure.HTSinsert from cad
                    if cad.detail == None:
                        tmp = UMagnet(cad, debug)
                        UMagnets.append(tmp)
                    else:
                        sstruct = SupraStructure()
                        fstruct = findfile(cad.struct, paths=search_paths(MyEnv, "geom"))
                        sstruct.loadCfg(fstruct)
                        tmp = UMagnets(sstruct, cad.detail, debug)
                        for item in tmp:
                            UMagnets.append(item)
                else:
                    raise Exception(f"setup: unexpected cad type {str(type(cad))}")

    # Bstacks = mt.VectorOfStacks()
    print("Helices:", len(Tubes))
    if len(BMagnets) != 0:
        Bstacks = mt.create_Bstack(BMagnets)
        print("Bstacks:", len(Bstacks))
    if len(UMagnets) != 0:
        Ustacks = mt.create_Ustack(UMagnets)
        print("UStacks:", len(Ustacks))
    # print("\n")
    
    return (Tubes,Helices,OHelices,BMagnets,UMagnets,Shims)


def msite_setup(MyEnv, confdata: str, debug: bool=False, session=None):
    """
    Creating MagnetTools data struct for setup for msite
    """
    print("msite_setup:", "debug=", debug)
    print("msite_setup:", "confdata=", confdata)
    print("miste_setup: confdata[magnets]=", confdata["magnets"])
    
    Tubes = mt.VectorOfTubes()
    Helices = mt.VectorOfBitters()
    OHelices = mt.VectorOfBitters()
    UMagnets = mt.VectorOfUnifs()
    BMagnets = mt.VectorOfBitters()
    Shims = mt.VectorOfShims()

    for magnet in confdata["magnets"]:
        print("magnet:", magnet, "type(magnet)=", type(magnet), "debug=", debug)
        try:
            mconfdata = load_object(MyEnv, magnet + "-data.json", magnet, debug)
        except:
            print("setup: failed to load %s, look into magnetdb" % (magnet + "-data.json") )
            try:
                mconfdata = load_object_from_db(MyEnv, "magnet", magnet, debug, session)
            except:
                raise Exception(f"setup: failed to load {magnet} from magnetdb")
                    
        if debug:
            print("mconfdata[geom]:", mconfdata["geom"])
        tmp = magnet_setup(MyEnv, mconfdata, debug)
        
        # pack magnets
        for item in tmp[0]:
            Tubes.append(item)
        for item in tmp[1]:
            Helices.append(item)
        for item in tmp[2]:
            OHelices.append(item)
        for item in tmp[3]:
            BMagnets.append(item)
        for item in tmp[4]:
            UMagnets.append(item)
        for item in tmp[5]:
            Shims.append(item)

    # Bstacks = mt.VectorOfStacks()
    print("\nHelices:", len(Tubes))
    if len(BMagnets) != 0:
        Bstacks = mt.create_Bstack(BMagnets)
        print("\nBstacks:", len(Bstacks))
    if len(UMagnets) != 0:
        Ustacks = mt.create_Ustack(UMagnets)
        print("\nUStacks:", len(Ustacks))
    print("\n")
    
    return (Tubes,Helices,OHelices,BMagnets,UMagnets,Shims)
    

def setup(MyEnv, args, confdata, jsonfile, session=None):
    """
    """
    print("ana/main")
    default_pathes={
        "geom" : MyEnv.yaml_repo,
        "cad" : MyEnv.cad_repo,
        "mesh" : MyEnv.mesh_repo
    }

    # loadconfig
    AppCfg = loadconfig()

    # Get current dir
    cwd = os.getcwd()
    if args.wd:
        os.chdir(args.wd)

    if "geom" in confdata:
        print("Load a magnet %s " % jsonfile, "debug:", args.debug)
        return magnet_setup(MyEnv, confdata, args.debug or args.verbose)
    else:
        print("Load a msite %s" % confdata["name"], "debug:", args.debug)
        # print("confdata:", confdata)

        # why do I need that???
        # would be better to do that when creating a msite in db
        if not findfile(confdata["name"] + ".yaml", paths=search_paths(MyEnv, "geom")):
            with open(confdata["name"] + ".yaml", "x") as out:
                out.write("!<MSite>\n")
                yaml.dump(confdata, out)
        return msite_setup(MyEnv, confdata, args.debug or args.verbose, session)               

    return 1
     
def main():
    # Manage Options
    command_line = None
    parser = argparse.ArgumentParser(description="Create template json model files for Feelpp/HiFiMagnet simu")
    parser.add_argument("--datafile", help="input data file (ex. HL-34-data.json)", default=None)
    parser.add_argument("--wd", help="set a working directory", type=str, default="")
    parser.add_argument("--magnet", help="Magnet name from magnetdb (ex. HL-34)", default=None)
    parser.add_argument("--msite", help="MSite name from magnetdb (ex. HL-34)", default=None)

    parser.add_argument("--debug", help="activate debug", action='store_true')
    parser.add_argument("--verbose", help="activate verbose", action='store_true')
    args = parser.parse_args()

    if args.debug:
        print("Arguments: " + str(args._))
    
    # make datafile/[magnet|msite] exclusive one or the other
    if args.magnet != None and args.msite:
        raise Exception("cannot specify both magnet and msite")
    if args.datafile != None:
        if args.magnet != None or args.msite != None:
            raise Exception("cannot specify both datafile and magnet or msite")

    # load appenv
    MyEnv = appenv()
    if args.debug: print(MyEnv.template_path())

    # Get Object
    if args.datafile != None:
        confdata = load_object(MyEnv, args.datafile, args.debug)
        jsonfile = args.datafile.replace("-data.json","")

    if args.magnet != None:
        confdata = load_object_from_db(MyEnv, "magnet", args.magnet, args.debug)
        jsonfile = args.magnet
    
    if args.msite != None:
        confdata = load_object_from_db(MyEnv, "msite", args.msite, args.debug)
        jsonfile = args.msite


    setup(MyEnv, args, confdata, jsonfile)    
    return 0


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
