from dataclasses import dataclass
from typing import Dict, List

@dataclass
class Parameter:
    name: str
    dimensions: str
    default_value: float
    description: str = ""

class MechanicalLaw:
    def __init__(self, name: str, parameters: List[Parameter]):
        self.name = name
        self.parameters = {param.name: param for param in parameters}

# Define available mechanical laws and their parameters
MECHANICAL_LAWS = {
    "linearElasticity": MechanicalLaw(
        "linearElasticity",
        [
            Parameter("E", "[1 -1 -2 0 0 0 0]", 2.1e11, "Young's modulus"),
            Parameter("nu", "[0 0 0 0 0 0 0]", 0.3, "Poisson's ratio"),
            Parameter("rho", "[1 -3 0 0 0 0 0]", 7850, "Density")
        ]
    ),
    "linearElasticMohrCoulombPlastic": MechanicalLaw(
        "linearElasticMohrCoulombPlastic",
        [
            Parameter("rho", "[1 -3 0 0 0 0 0]", 0, "Density"),
            Parameter("E", "[1 -1 -2 0 0 0 0]", 2e7, "Young's modulus"),
            Parameter("nu", "[0 0 0 0 0 0 0]", 0.3, "Poisson's ratio"),
            Parameter("frictionAngle", "[0 0 0 0 0 0 0]", 30, "Friction Angle"),
            Parameter("dilationAngle", "[0 0 0 0 0 0 0]", 0, "Dilation Angle"),
            Parameter("cohesion", "[1 -1 -2 0 0 0 0]", 1e5, "Cohesion"),
        ]
    ),
    "manzariDafalias": MechanicalLaw(
        "manzariDafalias",
        [
            Parameter("rho", "[1 3 0 0 0 0 0]", 1000, "Density"),  #Note: "WERT" is kept as a string, as per input.
            Parameter("e0", "[0 0 0 0 0 0 0]", 0.85, "Initial void ratio"),
            Parameter("e_cref", "[0 0 0 0 0 0 0]", 0.80, "Reference void ratio"),
            Parameter("K0", "[1 -1 -2 0 0 0 0]", 3.14e7, "Initial bulk modulus"),
            Parameter("G0", "[1 -1 -2 0 0 0 0]", 3.14e7, "Initial shear modulus"),
            Parameter("Pref", "[1 -1 -2 0 0 0 0]", 1.6e5, "Reference pressure"),
            Parameter("a", "[0 0 0 0 0 0 0]", 0.6, "Exponent for K and G"),
            Parameter("Mc", "[0 0 0 0 0 0 0]", 1.14, "Mc (critical state parameter)"),
            Parameter("Me", "[0 0 0 0 0 0 0]", 1.14, "Me (critical state parameter)"),
            Parameter("lambda", "[0 0 0 0 0 0 0]", 0.025, "Lambda (critical state parameter)"),
            Parameter("A0", "[0 0 0 0 0 0 0]", 0.6, "A0 (dilatancy parameter)"),
            Parameter("Cf", "[0 0 0 0 0 0 0]", 100, "Cf (fabric-dilatancy parameter)"),
            Parameter("Fmax", "[0 0 0 0 0 0 0]", 100, "Fmax (fabric-dilatancy parameter)"),
            Parameter("h0", "[0 0 0 0 0 0 0]", 800, "h0 (hardening parameter)"),
            Parameter("m0", "[0 0 0 0 0 0 0]", 0.05, "m0 (hardening parameter)"),
            Parameter("cm", "[0 0 0 0 0 0 0]", 0.0, "cm (hardening parameter)"),
            Parameter("k_cb", "[0 0 0 0 0 0 0]", 3.975, "k_cb (bounding surface parameter)"),
            Parameter("k_eb", "[0 0 0 0 0 0 0]", 2.0, "k_eb (bounding surface parameter)"),
            Parameter("k_cd", "[0 0 0 0 0 0 0]", 4.2, "k_cd (bounding surface parameter)"),
        ]
    )
}