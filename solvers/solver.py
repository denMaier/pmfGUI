from dataclasses import dataclass
from typing import Dict, List

@dataclass
class Parameter:
    name: str
    dimensions: str
    default_value: float
    description: str = ""

class solverType:
    def __init__(self, name: str, coupled: bool, parameters: List[Parameter]):
        self.name = name
        self.coupled = coupled
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
    )
}