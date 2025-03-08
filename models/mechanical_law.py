from dataclasses import dataclass
from typing import List
from foamlib import FoamFile

@dataclass
class Parameter:
    Dimensioned: FoamFile.Dimensioned
    description: str = ""

@dataclass
class Toggles:
    name: str
    default_value: bool
    description: str = ""

class MechanicalLaw:
    def __init__(self, name: str, parameters: List[Parameter],toggles: List[Toggles] = []):
        self.name = name
        self.toggles = {toggle.name: toggle for toggle in toggles}
        self.parameters = {param.Dimensioned.name: param for param in parameters}


# Define available mechanical laws and their parameters
MECHANICAL_LAWS = {
    "linearElasticity": MechanicalLaw(
        "linearElasticity",
        [
            Parameter(FoamFile.Dimensioned(name="E", dimensions=[1, -1, -2, 0, 0, 0, 0], value=2.1e11), "Young's modulus"),
            Parameter(FoamFile.Dimensioned(name="nu", dimensions=[0, 0, 0, 0, 0, 0, 0], value=0.3), "Poisson's ratio"),
            Parameter(FoamFile.Dimensioned(name="rho", dimensions=[1, -3, 0, 0, 0, 0, 0], value=7850), "Density")
        ]
    ),
    "linearElasticMohrCoulombPlastic": MechanicalLaw(
        "linearElasticMohrCoulombPlastic",
        [
            Parameter(FoamFile.Dimensioned(name="E", dimensions=[1, -1, -2, 0, 0, 0, 0], value=2e7), "Young's modulus"),
            Parameter(FoamFile.Dimensioned(name="nu", dimensions=[0, 0, 0, 0, 0, 0, 0], value=0.3), "Poisson's ratio"),
            Parameter(FoamFile.Dimensioned(name="frictionAngle", dimensions=[0, 0, 0, 0, 0, 0, 0], value=30), "Friction Angle"),
            Parameter(FoamFile.Dimensioned(name="dilationAngle", dimensions=[0, 0, 0, 0, 0, 0, 0], value=0), "Dilation Angle"),
            Parameter(FoamFile.Dimensioned(name="cohesion", dimensions=[1, -1, -2, 0, 0, 0, 0], value=1e5), "Cohesion"),
        ]
    ),
    "manzariDafalias": MechanicalLaw(
        "manzariDafalias",
        [
            Parameter(FoamFile.Dimensioned(name="e0", dimensions=[0, 0, 0, 0, 0, 0, 0], value=0.85), "Initial void ratio"),
            Parameter(FoamFile.Dimensioned(name="e_cref", dimensions=[0, 0, 0, 0, 0, 0, 0], value=0.80), "Reference void ratio"),
            Parameter(FoamFile.Dimensioned(name="K0", dimensions=[1, -1, -2, 0, 0, 0, 0], value=3.14e7), "Initial bulk modulus"),
            Parameter(FoamFile.Dimensioned(name="G0", dimensions=[1, -1, -2, 0, 0, 0, 0], value=3.14e7), "Initial shear modulus"),
            Parameter(FoamFile.Dimensioned(name="Pref", dimensions=[1, -1, -2, 0, 0, 0, 0], value=1.6e5), "Reference pressure"),
            Parameter(FoamFile.Dimensioned(name="a", dimensions=[0, 0, 0, 0, 0, 0, 0], value=0.6), "Exponent for K and G"),
            Parameter(FoamFile.Dimensioned(name="Mc", dimensions=[0, 0, 0, 0, 0, 0, 0], value=1.14), "Mc (critical state parameter)"),
            Parameter(FoamFile.Dimensioned(name="Me", dimensions=[0, 0, 0, 0, 0, 0, 0], value=1.14), "Me (critical state parameter)"),
            Parameter(FoamFile.Dimensioned(name="lambda", dimensions=[0, 0, 0, 0, 0, 0, 0], value=0.025), "Lambda (critical state parameter)"),
            Parameter(FoamFile.Dimensioned(name="A0", dimensions=[0, 0, 0, 0, 0, 0, 0], value=0.6), "A0 (dilatancy parameter)"),
            Parameter(FoamFile.Dimensioned(name="Cf", dimensions=[0, 0, 0, 0, 0, 0, 0], value=100), "Cf (fabric-dilatancy parameter)"),
            Parameter(FoamFile.Dimensioned(name="Fmax", dimensions=[0, 0, 0, 0, 0, 0, 0], value=100), "Fmax (fabric-dilatancy parameter)"),
            Parameter(FoamFile.Dimensioned(name="h0", dimensions=[0, 0, 0, 0, 0, 0, 0], value=800), "h0 (hardening parameter)"),
            Parameter(FoamFile.Dimensioned(name="m0", dimensions=[0, 0, 0, 0, 0, 0, 0], value=0.05), "m0 (hardening parameter)"),
            Parameter(FoamFile.Dimensioned(name="cm", dimensions=[0, 0, 0, 0, 0, 0, 0], value=0.0), "cm (hardening parameter)"),
            Parameter(FoamFile.Dimensioned(name="k_cb", dimensions=[0, 0, 0, 0, 0, 0, 0], value=3.975), "k_cb (bounding surface parameter)"),
            Parameter(FoamFile.Dimensioned(name="k_eb", dimensions=[0, 0, 0, 0, 0, 0, 0], value=2.0), "k_eb (bounding surface parameter)"),
            Parameter(FoamFile.Dimensioned(name="k_cd", dimensions=[0, 0, 0, 0, 0, 0, 0], value=4.2), "k_cd (bounding surface parameter)"),
        ]
    )
}
