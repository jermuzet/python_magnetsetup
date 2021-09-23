#!/usr/bin/env python3
# encoding: UTF-8

"""Enable to define mesh hypothesis (aka params) for MeshGems surfacic and volumic meshes"""

import math
import json
import yaml
import deserialize

# Load Modules for geometrical Objects
import Insert
import Helix
import Ring
import InnerCurrentLead
import OuterCurrentLead

class MeshData(yaml.YAMLObject):
    """
    Name:
    Object: geometry (either Insert, Helix, Ring, Lead)

    AlgoSurf
    AlgoVol

    Mesh hypothesys in Salome sens are stored by groups: Helices, Rings, Leads, Air, ...
    Each group consist of a list of:
       SurfName, SurfHypoth, SurfColor
       where SurfHypoth: PhysicalMesh, GeometricMesh, PhySyze, MinSize, ChordalError, others
    for AlgoSurface Hypoths.
    SurfName are taken from Object cfg file (Objects means either Helix, Ring or CurrentLead)

    Same for AlgoVol:
       VolName, VolHypoths, VolColor

    Opts: 
       MakeGroupsOfDomains, 
       KeepFiles, 
       RemoveLogOnSuccess, 
       MaximumMemory,

    VolHypoths: 
       OptimizationLevel, 
       SetToUseBoundaryRecoveryVersion, 
       Gradation, 
       AnglePrec, 
       Anisotropic, 
       AnistropicRatio, 
       others

    ATTENTION:
       SurfHypoth have to be the same for Interfaces:
           Helix: V0,V1 / Ring: V1, V0

       The order of definition is also important?

    def Default(...): define Defaults Hypothesys
    def Load(...): load Hypothesys
    def Dump(...): save Hypothesys
    """

    yaml_tag = 'MeshData'

    def __init__(self, name, geometry, algosurf="BLSURF", algovol="GHS3D"):
        """constructor"""
        self.name = name
        self.geometry = geometry
        self.algosurf = algosurf
        self.algovol = algovol

        # depending of geometry type
        self.surfhypoths = []
        self.volhypoths = []

        # main options
        self.MakeGroupsOfDomains = 0
        self.KeepFiles = 0
        self.RemoveLogOnSuccess = 1
        self.SetToUseBoundaryRecoveryVersion=0
        
        self.OptimizationLevel = 4
        self.Gradation = 1.05
        self.AnglePrec = 4

        self.Anisotropic = True
        self.AnisotropicRatio = 0

        self.Quadratic = False

        # specific treatment for memory to work around Memory bug on Stokes
        import psutil
        mem = psutil.virtual_memory()
        self.MaximumMemory = int(0.7*mem.total/1024./1024.)
        THRESOLD = 450559
        if int(0.7*mem.total/1024./1024.) > THRESOLD:
            self.MaximumMemory = THRESOLD

    def __repr__(self):
        """representation"""
        return "%s(name=%r, geometry=%r, algosurf=%r, algovol=%r, surfhypoths=%r volhypoths=%r, MakeGroupsOfDomains=%r, KeepFiles=%r, RemoveLogOnSuccess=%r, OptimizationLevel=%r, SetToUseBoundaryRecoveryVersion=%r, Gradation=%r, AnglePrec=%r, Anisotropic=%r, AnisotropicRatio=%r, Quadratic=%r)" % \
               (self.__class__.__name__,
                self.name,
                self.geometry,
                self.algosurf,
                self.algovol,
                self.surfhypoths,
                self.volhypoths,
                self.MakeGroupsOfDomains,
                self.KeepFiles,
                self.RemoveLogOnSuccess,
                self.MaximumMemory,
                self.OptimizationLevel,
                self.SetToUseBoundaryRecoveryVersion,
                self.Gradation,
                self.AnglePrec,
                self.Anisotropic,
                self.AnisotropicRatio,
                self.Quadratic)

    def algo3d(self, algovol):
        print ("set vol mesh algo - not implemented yet")

    def algo2d(self, algosurf):
        print ("set surfacic mesh algo - not implemented yet")

    def debug(self):
        """setup options for debugging meshing"""
        print ("activate debug for mesh algo")
        self.KeepFiles = 1 # toKeep
        self.RemoveLogOnSuccess = 0 # toNotRemove

    def SetBoundaryRecovery(self):
        """Force SetToUseBoundaryRecoveryVersion mode"""
        print ("Activate SetToUseBoundaryRecoveryVersion option - will force OptimizationLevel downgrade ")
        self.SetToUseBoundaryRecoveryVersion=1
        if self.OptimizationLevel == 4 :
            self.OptimizationLevel = 3
        
    def setQuadratic(self):
        """set Quadratic to True"""
        self.quadratic=True

    def setAnisotropic(self, ratio=0):
        """set Anisotropic to True"""
        self.Anisotropic = True
        self.AnisotropicRatio = ratio
        
    def helix_default(self, H, addname=False, mode="Fine"):
        """
        Define default mesh params for Helix

        mode: Fine Coarse
        """
        # print "helix_default: H=", H, "mode=", mode
        if mode != "Fine" and mode != "Coarse":
            raise Exception("Unknow MeshType %s for Helix %s"%(mode, H.name))

        name = ""
        if addname:
            name = H.name

        # Retreive main characteristics
        r_int = H.r[0]
        r_ext = H.r[1]
        z_inf = H.z[0]
        z_sup = H.z[1]
        cutwidth = H.cutwidth
        micro_channel_length = 1.5

        physsize = (r_ext - r_int)/3.
        minsize = (r_ext - r_int) / 10.
        maxsize = (r_ext - r_int) * 10
        chordalerror = r_int * (1-math.cos(2*math.pi/20.)) # equivalent of 40 nodes

        # Params for current inputs
        inputs = [name+"_V", [2, 1, physsize, minsize, maxsize, chordalerror]]
        boundary = [name+"_R", [2, 1, physsize, minsize, maxsize, chordalerror]]
        interface = [name+"_Interface", [2, 1, physsize/3., minsize/10., maxsize/10., chordalerror/10.]]
        if mode == "Coarse":
            interface = [name+"_Interface", [2, 1, physsize, minsize/2., maxsize/2., chordalerror/2.]]

        coolingslits = [name+"_coolingslit", []]
        microchannel = [name+"_muchannel", []]
        icoolingslits = [name+"_icoolingslits", []]
        imicrochannel = [name+"_imuchannel", []]
        iboundary = [name+"_iR", [2, 1, physsize/3., minsize/10., maxsize/10., chordalerror/10.]]
        if mode == "Coarse":
            iboundary = [name+"_iR", [2, 1, physsize, minsize/2., maxsize/2., chordalerror/2.]]

        if H.m3d.with_channels:
            interface = [name+"_Interface", [2, 1, physsize/10., minsize/20., maxsize/20., chordalerror/20.]]
            icoolingslits = [name+"_icoolingslits", [2, 1, physsize/10., minsize/20., maxsize/20., chordalerror/20.]]
            imicrochannel = [name+"_imucrochannel", [2, 1, micro_channel_length/5., minsize/20., maxsize/20., chordalerror/20.]]
            iboundary = [name+"_iR", [2, 1, physsize/10., minsize/20., maxsize/20., chordalerror/20.]]
            coolingslits = [name+"_coolingslit", [2, 1, physsize/10., minsize/20., maxsize/20., chordalerror/20.]]
            microchannel = [name+"_muchannel", [2, 1, physsize/10., minsize/20., maxsize/20., chordalerror/20.]]

        others = [name+"_others", [2, 1, physsize, minsize, maxsize, chordalerror]]

        if H.m3d.with_channels:
            return [inputs, boundary, interface, iboundary, coolingslits, microchannel, icoolingslits, imicrochannel, others]
        else:
            return [inputs, boundary, interface, iboundary, others]
        #return [inputs, boundary, interface, coolingslits, microchannel, icoolingslits, imicrochannel, others]

    def ring_default(self, Ring, addname=False):
        """
        Define default mesh params for Ring
        """

        name = ""
        if addname:
            name = Ring.name

        # Retreive main characteristics
        n = Ring.n
        angle = Ring.angle * math.pi/180.

        radius = Ring.r
        z_inf = Ring.z[0]
        z_sup = Ring.z[1]

        physsize = (radius[3] - radius[0])/3.
        minsize = (radius[3] - radius[0]) / 10.
        maxsize = (radius[3] - radius[0]) * 10
        chordalerror = radius[0] * (1-math.cos(2*math.pi/20.)) # equivalent of 40 nodes

        # Params for Surfaces
        H1 = [name+"_H1", [2, 1, (radius[1]-radius[0])/3., (radius[1]-radius[0])/10., (radius[1]-radius[0])*10, radius[0] * (1-math.cos(2*math.pi/20.))]]
        H2 = [name+"_H2", [2, 1, (radius[3]-radius[2])/3., (radius[3]-radius[2])/10., (radius[3]-radius[2])*10, radius[2] * (1-math.cos(2*math.pi/20.))]]
        cooling = [name+"_cooling", [2, 1, physsize, minsize, maxsize, chordalerror]]
        boundary = [name+"_R", [2, 1, physsize, minsize, maxsize, chordalerror]]

        # hypoths = [H1, H2, cooling, boundary]
        # print "hypoths: ",len(hypoths), type(hypoths), hypoths
        return [H1, H2, cooling, boundary]

    def lead_default(self, Lead, addname=False):
        """
        Define default mesh params for Lead
        """

        name = ""
        if addname:
            name = Lead.name

        # Retreive main characteristics
        width = (Lead.r[1] - Lead.r[0])
        physsize = width
        minsize = width / 10.
        maxsize = width * 10.
        chordalerror = Lead.r[0] * (1-math.cos(2*math.pi/10.)) # equivalent of 20 nodes

        # Params for Surfaces
        inputs = [name+"_V", [2, 1, physsize, minsize, maxsize, chordalerror]]
        boundary = [name+"_R", [2, 1, physsize, minsize, maxsize, chordalerror]]
        cooledsurf = [name+"_cooledsurf", [2, 1, physsize, minsize, maxsize, chordalerror]]
        fixingholes = [name+"_fixingholes", [2, 1, physsize, minsize, maxsize, chordalerror]]
        others = [name+"_others", [2, 1, physsize, minsize, maxsize, chordalerror]]

        return [inputs, boundary, cooledsurf, fixingholes, others]

    def air_default(self, H0, Hn, addname=False):
        """
        Define default mesh params for Air
        """

        # print "Define default mesh params for Air"
        name = "Air"

        # Retreive main characteristics
        width = (10 * Hn.r[1]) / 5
        physsize = width/3.
        minsize = width / 100.
        maxsize = width * 10.
        chordalerror = 2 * (10 * Hn.r[1]) * (1-math.cos(2*math.pi/10.)) # equivalent of 20 nodes

        # Params for inner bore part
        inner = [name+"_inner", [2, 1, (H0.r[1] - H0.r[0])/3., (H0.r[1] - H0.r[0])/10., (H0.r[1] - H0.r[0])*10., H0.r[0] * (1-math.cos(2*math.pi/20.))]]

        # Params for current inputs / outputs (except for inner bore part)
        inputs = [name+"_infV", [2, 1, physsize, minsize, maxsize, chordalerror]]

        # Params for InfR1
        infty = [name+"_infty", [2, 1, physsize, minsize, maxsize, chordalerror]]

        # Params for BiotShell
        Biotshell = [name+"_Biotshell", [2, 1, H0.r[1]/50., H0.r[1]/500., H0.r[1]/10., 2 * (10 * H0.r[0]) * (1-math.cos(2*math.pi/10.))]]

        return [inner, inputs, infty, Biotshell]

    def default(self, Object, H_MeshType="Fine", Air=False):
        """
        Define default mesh params
        """

        print ("creating default meshdata")

        # print "Object=", Object
        # print "Air=", Air

        # print "type=%s"%type(Object)

        # inspect type of geometry
        if isinstance(Object, Insert.Insert):
            print ("Creating MeshData for Insert %s" % self.geometry)
            theInsert = Object
            for H_cfg in Object.Helices:
                print ("MeshData for H:", H_cfg, "H_MeshType=", H_MeshType)
                H = None
                with open(H_cfg+".yaml", 'r') as f:
                    H = yaml.load(f, Loader=yaml.FullLoader)
                self.surfhypoths.append(self.helix_default(H, True, H_MeshType))
            # print "Rings:", Object.Rings
            if Object.Rings:
                for R_cfg in Object.Rings:
                    print ("MeshData for R:", R_cfg)
                    R = None
                    with open(R_cfg+".yaml", 'r') as f:
                        R = yaml.load(f, Loader=yaml.FullLoader)
                    self.surfhypoths.append(self.ring_default(R, True))
            # print "Leads:", Object.CurrentLeads
            if Object.CurrentLeads:
                for Lead in Object.CurrentLeads:
                    print ("MeshData for Lead:", Lead)
                    L = None
                    with open(Lead+".yaml", 'r') as f:
                        L = yaml.load(f, Loader=yaml.FullLoader)
                    self.surfhypoths.append(self.lead_default(L, True))

            if Air:
                print ("MeshData for Air")
                Hn = None
                with open(theInsert.Helices[-1]+".yaml", 'r') as f:
                    Hn = yaml.load(f, Loader=yaml.FullLoader)
                H0 = None
                with open(theInsert.Helices[0]+".yaml", 'r') as f:
                    H0 = yaml.load(f, Loader=yaml.FullLoader)
                self.surfhypoths.append(self.air_default(H0, Hn, True))
                # print "Creating MeshData for Air... done"

        elif isinstance(Object, Helix.Helix):
            print ("Creating MeshData for Helix %s"%self.geometry)
            self.surfhypoths = self.helix_default(Object)

        elif isinstance(Object, Ring.Ring):
            print ("Creating MeshData for Ring %s"%self.geometry)
            self.surfhypoths = self.ring_default(Object)

        elif isinstance(Object, (InnerCurrentLead.InnerCurrentLead, OuterCurrentLead.OuterCurrentLead)):
            print ("Creating MeshData for CurrentLead %s"%self.geometry)
            self.surfhypoths = self.lead_default(Object)

        # print "---------------------------------------------------------"
        # print "surfhypoths: ", len(self.surfhypoths), self.surfhypoths
        # print "---------------------------------------------------------"

    def load(self, Air=False):
        """
        Load Mesh params from yaml file
        """

        data = None
        filename = self.name
        if Air:
            filename += '_Air'
        filename += '_meshdata.yaml'
        print ("load mesh hypothesis from %s" % filename)
        with open(filename, 'r') as istream:
            data = yaml.load(stream=istream, Loader=yaml.FullLoader)

        self.name = data.name
        self.geometry = data.geometry
        self.algosurf = data.algosurf
        self.algovol = data.algovol

        # depending of geometry type
        self.surfhypoths = data.surfhypoths
        self.volhypoths = data.volhypoths

        # main otpions
        self.MakeGroupsOfDomains = data.MakeGroupsOfDomains
        self.KeepFiles = data.KeepFiles
        self.RemoveLogOnSuccess = data.RemoveLogOnSuccess
        self.MaximumMemory = data.MaximumMemory
        self.OptimizationLevel = data.OptimizationLevel
        self.SetToUseBoundaryRecoveryVersion = data.SetToUseBoundaryRecoveryVersion
        self.Gradation = data.Gradation
        self.AnglePrec = data.AnglePrec
        self.Anisotropic = data.Anisotropic
        self.AnisotropicRatio = data.AnisotropicRatio
        self.Quadratic = data.Quadratic

    def dump(self, Air=False):
        """
        Dump Mesh params to yaml file
        """

        filename = self.name
        if Air:
            filename += '_Air'
        filename += '_meshdata.yaml'
        print ("dump mesh hypothesys to %s" % filename)
        try:
            ostream = open(filename, 'w')
            yaml.dump(self, stream=ostream)
        except:
            print ("Failed to dump MeshData")

    def to_json(self):
        """
        Convert to json format
        """
        return json.dumps(self, default=deserialize.serialize_instance,
                          sort_keys=True, indent=4)

    def from_json(self, string):
        """
        Load from json format
        """
        return json.loads(string, object_hook=deserialize.unserialize_object)

    def write_to_json(self):
        """
        Dump Mesh params to json file
        """

        ostream = open(self.name + '_meshdata.json', 'w')
        jsondata = self.to_json()
        ostream.write(str(jsondata))
        ostream.close()

    def read_from_json(self):
        """
        Load Mesh params from json file
        """

        istream = open(self.name + '_meshdata.json', 'r')
        jsondata = self.from_json(istream.read())
        # print type(jsondata)
        istream.close()

def MeshData_constructor(loader, node):
    values = loader.construct_mapping(node)
    name = values["name"]
    geometry = values["geometry"]
    algosurf = values["algosurf"]
    algovol = values["algovol"]
    surfhypoths = values["surfhypoths"]
    volhypoths = values["volhypoths"]
    MakeGroupsOfDomains = values["MakeGroupsOfDomains"]
    KeepFiles = values["KeepFiles"]
    RemoveLogOnSuccess = values["RemoveLogOnSuccess"]
    MaximumMemory = values["MaximumMemory"]
    OptimizationLevel = values["OptimizationLevel"]
    if "SetToUseBoundaryRecoveryVersion" in values:
        SetToUseBoundaryRecoveryVersion = values["SetToUseBoundaryRecoveryVersion"]
    else:
        SetToUseBoundaryRecoveryVersion = 0
    Gradation = values["Gradation"]
    if "AnglePrec" in values:
        AnglePrec = values["AnglePrec"]
    else:
        AnglePrec = 4
    Anisotropic = values["Anisotropic"]
    AnisotropicRatio = values["AnisotropicRatio"]
    Quadratic = values["Quadratic"]
    return MeshData(name, geometry)

yaml.add_constructor(u'!MeshData', MeshData_constructor)


#
# To operate from command line

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("name", help="name of the meshdata to be stored")
    parser.add_argument("--geometry", help="define the geometry to load (without extension)", type=str)
    parser.add_argument("--coarse", help="request a coarse mesh", type=bool)
    args = parser.parse_args()

    import getpass
    UserName = getpass.getuser()

    ObjectName = args.geometry
    MeshType = "Fine"
    if args.coarse:
        MeshType = "Coarse"

    Hypoths = MeshData(args.name, ObjectName)
    Hypoths.default(H_MeshType=MeshType)
    Hypoths.dump()
