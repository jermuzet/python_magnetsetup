import pandas as pd
import math

import warnings
from pint import UnitRegistry, Unit, Quantity
# Ignore warning for pint
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    Quantity([])

# Pint configuration
ureg = UnitRegistry()
ureg.default_system = 'SI'
ureg.autoconvert_offset_to_baseunit = True

def update_U(params: dict, marker: str, target: float, val: float):
    return float(params[marker]['U']) * target/val
    pass

def getCurrent(df: pd.DataFrame, marker: str):
    return df[f"Statistics_Intensity_{marker}_integrate"].iloc[-1]

def setCurrent(marker: str, params: dict, objectif):
    return float(params[marker]['N']) * objectif

def getPower(df: pd.DataFrame, marker: str):
    return df[f"Statistics_Power_{marker}_integrate"].iloc[-1]

def setPower():
    pass

def getFlux(df: pd.DataFrame, marker: str):
    return df[f"Statistics_Flux_{marker}_integrate"].iloc[-1]

# For Heat exchange

def setFlux():
    pass

def vpump(objectif: float) -> float:
    Vpmax = 2840 # rpm
    Imax = 28000 # A
    
    Vpump = Vpmax
    if objectif <= Imax:
        Vpump = 1000+(Vpmax-1000)*(objectif/Imax)**2

    return Vpump

def flow(objectif: float) -> float: 
    """
    compute flow in m^3/s
    """
    Vpmax = 2840 # rpm
    
    units = [ ureg.liter/ureg.second, ureg.meter*ureg.meter*ureg.meter/ureg.second]
    Fmax = Quantity(140, units[0]).to(units[1]).magnitude
    
    return Fmax * vpump(objectif)/Vpmax

def pressure(objectif: float) -> float:
    """
    compute pressure in bar ???
    """
    Vpmax = 2840 # rpm
    Pmax=22 # bar
    Pmin=4 # bar

    return (Pmin + (Pmax-Pmin) * (vpump(objectif)/Vpmax)**2)

def umean(objectif: float, section: float) -> float:
    """
    compute umean in m/s ???
    """
    print("flow:", flow(objectif), section)
    return flow(objectif)/section

def rho(Tw: float, P: float) -> float:
    """
    compute water volumic mass in ???
    """
    return 1.e+3

def Cp(Tw: float, P: float) -> float:
    """
    compute water specific heat in ???
    """
    return 2840

def montgomery(Tw: float, Umean: float, Dh: float) -> float:
    """
    compute heat exchange coefficient in ??

    Tw: K
    Umean: m/s
    Dh: meter
    """
    
    return 1426*(1+1.5e-2*(Tw-273))*math.exp(math.log(Umean)*0.8)/math.exp(math.log(Dh)*0.2)

def setDT(objectif: float, Power: float, Tw: float, P: float) -> float:
    # compute dT as Power / rho *Cp * Flow(I)
    return Power/ (rho(Tw, P) * Cp(Tw, P) * flow(objectif))

def getDT():
    pass

def setHeatCoeff(Dh: float, Umean: float, Tw: float):
    # compute h as Montgomery()
    # P = pressure(objectif)
    # dTw = setDT(objectif, Power, Tw, P) 
    return montgomery(Tw, Umean, Dh)

def getHeatCoeff():
    pass


