"""Console script for linking python_magnetsetup and python_magnettoos."""

from typing import List, Optional

import sys
import os
import json
import yaml

import argparse
from .objects import load_object, load_object_from_db
from .config import appenv, loadconfig, loadtemplates
from .objects import load_object, load_object_from_db

from python_magnetgeo import Insert, MSite, Bitter, Supra, SupraStructure
from python_magnetgeo import python_magnetgeo

import MagnetTools.MagnetTools as mt

def HMagnet(struct: Insert, data: dict, debug: bool=False):
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

    for helix in data["Helix"]:
        material = helix["material"]
        geom = helix["geom"]
        with open(geom, 'r') as cfgdata:
            cad = yaml.load(cfgdata, Loader = yaml.FullLoader)
        nturns = len(cad.axi.turns)
        print("nturns:", nturns)
        r1 = cad.r[0]
        r2 = cad.r[1]
        h = cad.axi.h
        Tubes.append( mt.Tube(nturns, r1, r2, h) )
        tmp = BMagnet(cad, material, debug)
        for item in tmp:
            Helices.append(item)

    print("HMagnet:", struct.name, "Tubes:", len(Tubes), "Helices:", len(Helices))
    
    return (Tubes, Helices, OHelices)

def BMagnet(struct: Bitter, material: dict, debug: bool=False):
    """
    create view of this insert as a Bitter Magnet

    b=mt.BitterfMagnet(r2, r1, h, current_density, z_offset, fillingfactor, rho)
    """
    
    BMagnets = mt.VectorOfBitters()
    
    rho = 1/ material["ElectricalConductivity"]
    f = 1 # 1/struct.get_Nturns() # struct.getFillingFactor()
        
    r1 = struct.r[0]
    r2 = struct.r[1]
    z = -struct.axi.h

    for (n, pitch) in zip(struct.axi.turns, struct.axi.pitch):
        dz = n * pitch
        j = n / ( (r2-r1) * dz )
        z_offset = z + dz/2.
        BMagnets.append( mt.BitterMagnet(r2, r1, dz/2., j, z_offset, f, rho) )
                
        z += dz

    print("BMagnet:", struct.name, len(BMagnets))
    return BMagnets

def UMagnet(struct: SupraStructure.HTSinsert, debug: bool=False):
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
        j = nturns / struct.getArea()
    
    print("UMagnets:", struct.name, 1)
    return mt.UnifMagnet(struct.r1, struct.r0, struct.h, j, struct.z0, f, rho)


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


def magnet_setup(confdata: str, debug: bool=False):
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
        with open(yamlfile, 'r') as cfgdata:
            cad = yaml.load(cfgdata, Loader = yaml.FullLoader)
        # if isinstance(cad, Insert):
        tmp = HMagnet(cad, confdata, debug)
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
                with open(obj['geom'], 'r') as cfgdata:
                    cad = yaml.load(cfgdata, Loader = yaml.FullLoader)
    
                if isinstance(cad, Bitter.Bitter):
                    tmp = BMagnet(cad, obj["material"], debug)
                    for item in tmp:
                        BMagnets.append(item)
                elif isinstance(cad, Supra):
                    tmp = UMagnet(cad, obj["material"], debug)
                    for item in tmp:
                        UMagnets.append(item)
                else:
                    print("setup: unexpected cad type %s" % str(type(cad)))
                    sys.exit(1)

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


def msite_setup(MyEnv, confdata: str, debug: bool=False):
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
                mconfdata = load_object_from_db(MyEnv, "magnet", magnet, debug)
            except:
                print("setup: failed to load %s from magnetdb" % magnet)
                sys.exit(1)
                    
        if debug:
            print("mconfdata[geom]:", mconfdata["geom"])
        (Tubes,Helices,OHelices,BMagnets,UMagnets,Shims) = magnet_setup(mconfdata, debug)
        
        # pack magnets
    
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
    

def setup(MyEnv, args, confdata, jsonfile):
    """
    """
    print("ana/main")
    
    # loadconfig
    AppCfg = loadconfig()

    # Get current dir
    cwd = os.getcwd()
    if args.wd:
        os.chdir(args.wd)

    if "geom" in confdata:
        print("Load a magnet %s " % jsonfile, "debug:", args.debug)
        magnet_setup(confdata, args.debug or args.verbose)
    else:
        print("Load a msite %s" % confdata["name"], "debug:", args.debug)
        # print("confdata:", confdata)

        # why do I need that???
        with open(confdata["name"] + ".yaml", "x") as out:
                out.write("!<MSite>\n")
                yaml.dump(confdata, out)
        msite_setup(MyEnv, confdata, args.debug or args.verbose)               
                    
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
        print("cannot specify both magnet and msite")
        sys.exit(1)
    if args.datafile != None:
        if args.magnet != None or args.msite != None:
            print("cannot specify both datafile and magnet or msite")
            sys.exit(1)

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
