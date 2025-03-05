from dataclasses import dataclass
from typing import List, Union

@dataclass(frozen=True)
class Parameter:
    name: str
    dimensions: str
    default_value: Union[float, int, bool, str]
    description: str = ""

class StorageLaw:
    def __init__(self, name: str, parameters: List[Parameter]):
        self.name = name
        self.parameters = {param.name: param for param in parameters}

class SaturationLaw:
    def __init__(self, name: str, parameters: List[Parameter]):
        self.name = name
        self.parameters = {param.name: param for param in parameters}

# Define available mechanical laws and their parameters
HYDRAULIC_LAWS = {
    "storageLaw": {
        "storageCoeff": StorageLaw(
            "storageCoeff",
            [
                Parameter("Ss", "[ -1 1 2 0 0 0 0 ]", 1e-6, "Hydraulic Storage Coefficient"),
            ]
        ),
        "KPrime": StorageLaw(
            "KPrime",
            [
                Parameter("pDependent", "", False, "Storage depends on pressure?"),
                Parameter("p_At", "[ 1 -1 -2 0 0 0 0 ]", 1e5, "Atmospheric Pressure"),
                Parameter("Kw", "[ 1 -1 -2 0 0 0 0 ]", 2.08e9, "Stiffness of Pure Water"),
                Parameter("Sw_0", "[0 0 0 0 0 0 0]", 0.98, "Degree of Water-Saturation")
            ]
        ),
        "montenegro": StorageLaw(
            "montenegro",
            [
                Parameter("p_At", "[ 1 -1 -2 0 0 0 0 ]", 1e5, "Atmospheric Pressure"),
                Parameter("p_e", "[ 1 -1 -2 0 0 0 0 ]", -0.0, "Reference Pressure"),
                Parameter("S_e", "[0 0 0 0 0 0 0]", 0.98, "Degree of Water-Saturation at Reference Pressure")
            ]
        )
    },
    # Define available mechanical laws and their parameters
    "SWCC": {
        "saturated": SaturationLaw(
            "saturated", []
        ),
        "vanGenuchten": SaturationLaw(
            "vanGenuchten",
            [
                Parameter("S_0", "[0 0 0 0 0 0 0]", 1.0, "Degree of PoreFluid-Saturation at Atmospheric Pressure"),
                Parameter("S_r", "[0 0 0 0 0 0 0]", 0.1, "Degree of minimal PoreFluid-Saturation"),
                Parameter("alpha", "[ -1 1 2 0 0 0 0 ]", 3.3e-4, "Van-Genuchten Fitting-Parameter"),
                Parameter("n", "[0 0 0 0 0 0 0]", 3.1, "Van-Genuchten Fitting-Parameter")
            ]
        ),
        "brooksCorey": SaturationLaw(
            "brooksCorey",
            [
                Parameter("S_0", "[0 0 0 0 0 0 0]", 1.0, "Degree of PoreFluid-Saturation at Atmospheric Pressure"),
                Parameter("S_r", "[0 0 0 0 0 0 0]", 0.1, "Degree of minimal PoreFluid-Saturation"),
                Parameter("p_e", "[ 1 -1 -2 0 0 0 0 ]", -4400, "Air-Entry Pressure"),
                Parameter("n", "[0 0 0 0 0 0 0]", 3.1, "Brooks and Corey Fitting-Parameter")
            ]
        ),
    }
}
