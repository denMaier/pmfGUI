from pathlib import Path


PATHS = {
    "cellZones": "constant/polyMesh/cellZones",
    "boundary": "constant/polyMesh/boundary",
    "physicsProperties": "constant/physicsProperties",
    "solidProperties": "constant/solid/solidProperties",
    "poroFluidProperties": "constant/poroFluid/poroFluidProperties",
    "poroCouplingProperties": "constant/poroCouplingProperties",
    "mechanicalProperties": "constant/solid/mechanicalProperties",
    "poroHydraulicProperties": "constant/poroFluid/poroHydraulicProperties",
    "dotFoam": None,
    "blockMeshDict": None,
    "controlDict": "system/controlDict",
    "fvSolution": "system/fvSolution",
    "fvSchemes": "system/fvSchemes",
    "meshDict": "system/meshDict",
    "edgeDict": "system/edgeDict",
    "gSolid": "constant/solid/g",
    "gGroundwater": "constant/poroFluid/g",
}

SOLVER_OPTIONS = {
    "Mechanics": {
        "type": "solid",
        "tabs": ["Mechanics"],
        "fields": ["D"],
    },
    "Groundwater": {
        "type": "poroFluid",
        "tabs": ["Hydraulics"],
        "fields": ["p_rgh"],
    },
    "Coupled": {
        "type": "poroSolid",
        "tabs": ["Coupling", "Mechanics", "Hydraulics"],
        "fields": ["D", "p_rgh"],
    },
}

SOLVER_TYPE_MAP = {
    "solid": "Mechanics",
    "poroFluid": "Groundwater",
    "poroSolid": "Coupled",
    "None": "Mechanics",
}

POROFLUIDMODEL_TYPES = {
    "saturated": "poroFluid",
    "unsaturated": "varSatPoroFluid",
}

FIELD_REGIONS = {
    "p_rgh": "poroFluid",
    "S": "poroFluid",
    "k": "poroFluid",
    "n": "poroFluid",
    "D": "solid",
    "epsilon": "solid",
    "sigma": "solid",
    "sigmaEff": "solid",
}

FIELD_DEFAULT_VALUE = {
    "p_rgh": "uniform 0",
    "S": "uniform 0",
    "k": "uniform 1e-4",
    "n": "uniform 0.5",
    "D": "uniform (0 0 0)",
    "epsilon": "uniform (0 0 0 0 0 0)",
    "sigma": "uniform (0 0 0 0 0 0)",
    "sigmaEff": "uniform (0 0 0 0 0 0)",
}

BC_TYPES = {
    "p_rgh": [
        "fixedValue",
        "zeroGradient",
        "fixedPotential",
        "fixedPoroFlux",
        "seepageOutlet",
        "empty",
        "symmetry",
        "cyclic",
        "fixedGradient",
        "mixed",
        "directionMixed",
        "fixedFluxPressure",
        "noSlip",
        "slip",
    ],
    "D": [],
}


def case_path(case_dir: Path | str, key: str) -> Path:
    relative_path = PATHS[key]
    if relative_path is None:
        raise ValueError(f"Optional path '{key}' is not configured")
    return Path(case_dir) / relative_path
