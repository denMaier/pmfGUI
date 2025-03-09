from stages.boundary.boundary_conditions import BoundaryCondition
from stages.boundary.function1 import UniformFunction1

# Dictionary of boundary condition templates using GenericFunction1
BOUNDARY_CONDITION_TEMPLATES = {
    "U": {
        "fixedValue": BoundaryCondition(
            type="uniformFixedValue",
            entries={"value": UniformFunction1(value=[0, 0, 0], _is_vector=True, _selectable=True)},
            description=""
        ),
        "zeroGradient": BoundaryCondition(
            type="zeroGradient",
            description=""
        )
    },
    "D": {
        "fixedValue": BoundaryCondition(
            type="uniformFixedValue",
            entries={"value": UniformFunction1(value=[0, 0, 0], _is_vector=True, _selectable=True)},
            description=""
        ),
        "fixedDisplacement": BoundaryCondition(
            type="fixedDisplacement",
            entries={"value": UniformFunction1(value=[0, 0, 0], _is_vector=True, _selectable=False)},
            description=""
        ),
        "fixedDisplacementZeroShear": BoundaryCondition(
            type="fixedDisplacementZeroShear",
            entries={"value": UniformFunction1(value=[0, 0, 0], _is_vector=True, _selectable=False)},
            description="Fixed displacement with zero shear stress"
        ),
        "traction": BoundaryCondition(
            type="poroTraction",
            entries={
                "total": True,
                "traction": UniformFunction1(value=[0, 0, 0], _is_vector=True, _selectable=True),
                "pressure": UniformFunction1(value=0.0, _is_vector=False, _selectable=True),
                "value": UniformFunction1(value=[0, 0, 0], _is_vector=True, _selectable=False)
            },
            description="traction boundary for fully saturated conditions"
        ),
        "varSatTraction": BoundaryCondition(
            type="varSatPoroTraction",
            entries={
                "total": True,
                "effectiveStressModel": "suctionCutOff",
                "traction": UniformFunction1(value=[0, 0, 0], _is_vector=True, _selectable=True),
                "pressure": UniformFunction1(value=0.0, _is_vector=False, _selectable=True),
                "value": UniformFunction1(value=[0, 0, 0], _is_vector=True, _selectable=False)
            },
            description="Variable saturation traction boundary"
        )
    },
    "p": {
        "fixedValue": BoundaryCondition(
            type="uniformFixedValue",
            entries={"value": UniformFunction1(value=0.0, _is_vector=False, _selectable=True)},
            description=""
        ),
        "zeroGradient": BoundaryCondition(
            type="zeroGradient",
            description=""
        )
    },
    "p_rgh": {
        "fixedValue": BoundaryCondition(
            type="uniformFixedValue",
            entries={"value": UniformFunction1(value=0.0, _is_vector=False, _selectable=True)},
            description=""
        ),
        "fixedPotential": BoundaryCondition(
            type="fixedPotential",
            entries={
                "h0": UniformFunction1(value=0.0, _is_vector=False, _selectable=True),
                "value": UniformFunction1(value=0.0, _is_vector=False, _selectable=False)
            },
            description="Fixed hydraulic potential h[m]"
        ),
        "fixedFlux": BoundaryCondition(
            type="fixedPoroFlux",
            entries={
                "flux": UniformFunction1(value=0.0, _is_vector=False, _selectable=True),
                "value": UniformFunction1(value=0.0, _is_vector=False, _selectable=False)
            },
            description="Fixed volume flux q[m/s]"
        ),
        "seepageOutlet": BoundaryCondition(
            type="seepageOutlet",
            entries={
                "outletValue": UniformFunction1(value=0.0, _is_vector=False, _selectable=False),
                "h0": UniformFunction1(value=0.0, _is_vector=False, _selectable=True),
                "value": UniformFunction1(value=0.0, _is_vector=False, _selectable=False)
            },
            description="Variable pressure/flow depending on groundwater level"
        ),
        "limitedHeadInfiltration": BoundaryCondition(
            type="limitedHeadInfiltration",
            entries={
                "flux": UniformFunction1(value=0.0, _is_vector=False, _selectable=True),
                "pMax": UniformFunction1(value=0.0, _is_vector=False, _selectable=False),
                "value": UniformFunction1(value=0.0, _is_vector=False, _selectable=False)
            },
            description="Variable pressure/flow depending on pressure level"
        )
    }
}
