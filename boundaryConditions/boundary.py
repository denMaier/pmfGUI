from dataclasses import dataclass
from typing import Dict, List, Union, Any, Optional, Tuple, Set, Generic, TypeVar, Literal
import pandas as pd
import abc

# Type variable for value types (scalar, vector, etc.)
T = TypeVar('T')

# Define Function1 Types as a Literal for type safety (or Enum if preferred)
Function1Type = Literal["constant", "zero", "linearRamp", "table"]
FUNCTION1_TYPES = ["constant", "zero", "linearRamp", "table"] # For easy iteration in UI

FUNCTION1_COEFFS_SPEC = {
    "constant": {}, # Constant type has no specific coefficients beyond the 'value' itself
    "zero": {},     # Zero type also has no coefficients
    "linearRamp": {
        "start": {"type": "scalar", "description": "Start value"},
        "duration": {"type": "scalar", "description": "Duration of ramp"}
    },
    "table": {
        "value": {"type": "dataframe", "description": "Table Data"}, # DataFrame input for table function1
        "outOfBounds": {"type": "string", "description": "Out-of-bounds handling (optional)", "optional": True}, # Mark as optional
        "interpolationScheme": {"type": "string", "description": "Interpolation method (optional)", "optional": True} # Mark as optional
    }
}


class ParameterValue(Generic[T], abc.ABC):
    """Base class for parameter values with type information."""

    @abc.abstractmethod
    def get_value(self) -> T:
        """Get the value of this parameter."""
        pass

    @abc.abstractmethod
    def get_type_name(self) -> str:
        """Get the type name of this parameter."""
        pass


class ScalarValue(ParameterValue[Union[float, int, bool]]):
    """Represents a scalar numeric parameter value."""

    def __init__(self, value: Union[float, int, bool]):
        self.value = value

    def get_value(self) -> Union[float, int, bool]:
        return self.value

    def get_type_name(self) -> str:
        return "scalar"


class StringValue(ParameterValue[str]):
    """Represents a string parameter value."""

    def __init__(self, value: str):
        self.value = value

    def get_value(self) -> str:
        return self.value

    def get_type_name(self) -> str:
        return "string"


class VectorValue(ParameterValue[Tuple[float, float, float]]):
    """Represents a vector parameter value."""

    def __init__(self, value: Tuple[float, float, float]):
        self.value = value

    def get_value(self) -> Tuple[float, float, float]:
        return self.value

    def get_type_name(self) -> str:
        return "vector"


class DataFrameValue(ParameterValue[pd.DataFrame]):
    """Represents a tabular data parameter value."""

    def __init__(self, value: pd.DataFrame):
        self.value = value

    def get_value(self) -> pd.DataFrame:
        return self.value

    def get_type_name(self) -> str:
        return "dataframe"


class GroupValue(ParameterValue[Dict[str, 'Parameter']]): # Forward reference to Parameter
    """Represents a group of parameters as a parameter value."""

    def __init__(self, parameters: Dict[str, 'Parameter']): # Forward reference to Parameter
        self.parameters = parameters

    def get_value(self) -> Dict[str, 'Parameter']: # Forward reference to Parameter
        return self.parameters

    def get_type_name(self) -> str:
        return "group"


class Function1ParameterValue(ParameterValue[Dict[str, Any]]):
    """Represents a parameter that can be defined using OpenFOAM's Function1 types."""

    def __init__(self, function_type: Optional[Function1Type] = None, coefficients: Optional[Dict[str, Any]] = None):
        self.function_type = function_type
        self.coefficients = coefficients or {} # Store coefficients as a dictionary

    def get_value(self) -> Dict[str, Any]:
        """Returns a dictionary representing the Function1 definition."""
        if not self.function_type:
            return {} # Or raise an exception, depending on desired behavior if type is not set

        value = {"type": self.function_type}
        if self.coefficients:
            value["coeffs"] = self.coefficients # Use "coeffs" dictionary for coefficients
        return value

    def get_type_name(self) -> str:
        return "function1"

    def set_function_type(self, function_type: Function1Type):
        """Set the Function1 type."""
        self.function_type = function_type

    def set_coefficients(self, coefficients: Dict[str, Any]):
        """Set the coefficients for the Function1 type."""
        self.coefficients = coefficients


@dataclass
class Parameter:
    """Definition of a boundary condition parameter."""
    name: str
    value: ParameterValue
    dimensions: str = ""
    description: str = ""
    is_function1: bool = False  # Flag to indicate if this parameter uses Function1


class BoundaryCondition(abc.ABC):
    """Base class for all boundary conditions."""

    def __init__(self, name: str, parameters: List[Parameter]):
        self.name = name
        self.parameters = {param.name: param for param in parameters}

    @abc.abstractmethod
    def get_applicable_fields(self) -> Set[str]:
        """Get fields this boundary condition can be applied to."""
        pass

    def get_parameters(self) -> Dict[str, Parameter]:
        """Get all parameters for this boundary condition."""
        return self.parameters

    def is_applicable_for(self, field_name: str) -> bool:
        """Check if this boundary condition can be applied to the given field."""
        return field_name in self.get_applicable_fields()


class ScalarBoundaryCondition(BoundaryCondition):
    """Boundary condition applicable to scalar fields like p_rgh."""

    def __init__(self, name: str, parameters: List[Parameter], fields: Optional[Set[str]] = None):
        super().__init__(name, parameters)
        self._fields = fields or {"p_rgh"}

    def get_applicable_fields(self) -> Set[str]:
        return self._fields


class VectorBoundaryCondition(BoundaryCondition):
    """Boundary condition applicable to vector fields like D."""

    def __init__(self, name: str, parameters: List[Parameter], fields: Optional[Set[str]] = None):
        super().__init__(name, parameters)
        self._fields = fields or {"D"}

    def get_applicable_fields(self) -> Set[str]:
        return self._fields


class DualFieldBoundaryCondition(BoundaryCondition):
    """Boundary condition applicable to both scalar and vector fields."""

    def __init__(self, name: str,
                 scalar_parameters: List[Parameter],
                 vector_parameters: List[Parameter],
                 scalar_fields: Optional[Set[str]] = None,
                 vector_fields: Optional[Set[str]] = None):

        # Store field-specific parameters separately
        self.scalar_parameters = {param.name: param for param in scalar_parameters}
        self.vector_parameters = {param.name: param for param in vector_parameters}

        # Combine parameters for the base class
        all_parameters = scalar_parameters + vector_parameters
        super().__init__(name, all_parameters)

        # Set fields
        self._scalar_fields = scalar_fields or {"p_rgh"}
        self._vector_fields = vector_fields or {"D"}

    def get_applicable_fields(self) -> Set[str]:
        return self._scalar_fields | self._vector_fields

    def get_scalar_fields(self) -> Set[str]:
        return self._scalar_fields

    def get_vector_fields(self) -> Set[str]:
        return self._vector_fields

    def get_field_type(self, field_name: str) -> Optional[str]:
        """Get the type (scalar/vector) of a field, if applicable."""
        if field_name in self._scalar_fields:
            return "scalar"
        elif field_name in self._vector_fields:
            return "vector"
        return None

    def get_parameters_for_field(self, field_name: str) -> Dict[str, Parameter]:
        """Get parameters specific to a field type."""
        if field_name in self._scalar_fields:
            return self.scalar_parameters
        elif field_name in self._vector_fields:
            return self.vector_parameters
        return {}


class BoundaryConditionRegistry:
    """Registry for all boundary conditions."""

    def __init__(self):
        self.scalar_boundary_conditions: Dict[str, BoundaryCondition] = {}
        self.vector_boundary_conditions: Dict[str, BoundaryCondition] = {}
        self.dual_boundary_conditions: Dict[str, DualFieldBoundaryCondition] = {}

    def register_scalar_bc(self, boundary_condition: ScalarBoundaryCondition) -> None:
        """Register a scalar boundary condition."""
        self.scalar_boundary_conditions[boundary_condition.name] = boundary_condition

    def register_vector_bc(self, boundary_condition: VectorBoundaryCondition) -> None:
        """Register a vector boundary condition."""
        self.vector_boundary_conditions[boundary_condition.name] = boundary_condition

    def register_dual_bc(self, boundary_condition: DualFieldBoundaryCondition) -> None:
        """Register a dual-field boundary condition."""
        self.dual_boundary_conditions[boundary_condition.name] = boundary_condition

    def get_for_field(self, field_name: str) -> Dict[str, BoundaryCondition]:
        """Get all boundary conditions applicable to the given field."""
        result = {}

        # Check scalar BCs
        for name, bc in self.scalar_boundary_conditions.items():
            if bc.is_applicable_for(field_name):
                result[name] = bc

        # Check vector BCs
        for name, bc in self.vector_boundary_conditions.items():
            if bc.is_applicable_for(field_name):
                result[name] = bc

        # Check dual-field BCs
        for name, bc in self.dual_boundary_conditions.items():
            if bc.is_applicable_for(field_name):
                result[name] = bc

        return result

    def get_parameters(self, bc_name: str, field_name: str) -> Optional[Dict[str, Dict]]:
        """Get parameters for a specific boundary condition and field."""
        # Check in all registries
        bc = None

        if bc_name in self.scalar_boundary_conditions:
            bc = self.scalar_boundary_conditions[bc_name]
        elif bc_name in self.vector_boundary_conditions:
            bc = self.vector_boundary_conditions[bc_name]
        elif bc_name in self.dual_boundary_conditions:
            bc = self.dual_boundary_conditions[bc_name]

        if bc and bc.is_applicable_for(field_name):
            # Handle dual field boundary conditions specially
            if isinstance(bc, DualFieldBoundaryCondition):
                params = bc.get_parameters_for_field(field_name)
            else:
                params = bc.get_parameters()

            # Format parameter information
            result = {}
            for name, param in params.items():
                param_value = param.value
                value_data = {
                    "type": param_value.get_type_name(),
                    "dimensions": param.dimensions,
                    "description": param.description,
                    "is_function1": param.is_function1 # Pass the flag to UI
                }
                if param.is_function1:
                    # For function1 parameters, provide available types and coefficient spec
                    value_data["function1_types"] = FUNCTION1_TYPES # List of available types for dropdown
                    value_data["function1_coeffs_spec"] = FUNCTION1_COEFFS_SPEC # Spec for dynamic UI
                    result[name] = value_data
                elif isinstance(param_value, GroupValue):
                    # Handle GroupValue to recursively represent nested parameters
                    group_params = {}
                    for nested_name, nested_param in param_value.get_value().items():
                        group_params[nested_name] = self._format_parameter_details(nested_param)
                    value_data["value"] = group_params
                    result[name] = value_data
                else:
                    value_data["value"] = param_value.get_value()
                    result[name] = value_data
            return result

        return None

    def _format_parameter_details(self, parameter: Parameter) -> Dict:
        """Helper function to format parameter details, handling nested groups."""
        param_value = parameter.value
        value_data = {
            "type": param_value.get_type_name(),
            "dimensions": parameter.dimensions,
            "description": parameter.description,
            "is_function1": parameter.is_function1 # Propagate the flag
        }
        if parameter.is_function1:
            value_data["function1_types"] = FUNCTION1_TYPES
            value_data["function1_coeffs_spec"] = FUNCTION1_COEFFS_SPEC
        elif isinstance(param_value, GroupValue):
            group_params = {}
            for nested_name, nested_param in param_value.get_value().items():
                group_params[nested_name] = self._format_parameter_details(nested_param)
            value_data["value"] = group_params
        else:
            value_data["value"] = param_value.get_value()
        return value_data


# Initialize registry
registry = BoundaryConditionRegistry()

# Create sample DataFrames
scalarDataFrame = pd.DataFrame({
    't': [0.0],
    'value': [1.0]
})

vectorDataFrame = pd.DataFrame({
    't': [0.0],
    'value': [1.0]
})

sample_df = pd.DataFrame({'x': [1, 2, 3], 'y': [4, 5, 6]})


# Register scalar boundary conditions
# Create sample DataFrame (if needed, though not used in this fixedPotential example as per your snippet)
scalarDataFrame_fixedPotential_h0 = pd.DataFrame({
    't': [0.0],
    'value': [0.0]
})

# Register scalar boundary conditions
registry.register_scalar_bc(ScalarBoundaryCondition(
    name="fixedPotential",
    parameters=[
        Parameter(
            name="h0",
            value=Function1ParameterValue(),  # Use Function1ParameterValue for h0, allowing function1 selection in UI
            description="- Potential in [m] // function1:  https://doc.openfoam.com/2306/fundamentals/input-types/Function1/",
            is_function1=True  # Mark as function1 parameter
        ),
        Parameter(
            name="value",
            value=ScalarValue(0.0),  # Represent 'value' as a ScalarValue, initialized to 0
            description="- Initialwert der Druckabweichung [Pa] (wird ueberschrieben)"
        )
    ]
))

registry.register_scalar_bc(ScalarBoundaryCondition(
    name="fixedPoroFlux",
    parameters=[
        Parameter(
            name="flux",
            value=Function1ParameterValue(),  # Funktion 1 Parameter für 'flux'
            description="- Durchfluss normal zum Rand (Positiv=Zufluss;Negativ=Abfluss) // function1: https://doc.openfoam.com/2306/fundamentals/input-types/Function1/",
            is_function1=True
        ),
        Parameter(
            name="value",
            value=ScalarValue(0.0),  # Skalarer Wert für 'value'
            description="- Initialwert der Druckabweichung [Pa]"
        )
    ]
))


registry.register_scalar_bc(ScalarBoundaryCondition(
    name="seepageOutlet",
    parameters=[
        Parameter(
            name="outletValue",
            value=ScalarValue(0.0),  # Skalarer Wert für 'outletValue'
            description="- Druckhöhe über Grundwasserspiegel (normalerweise Atmosphärendruck (=0))"
        ),
        Parameter(
            name="h0",
            value=Function1ParameterValue(),  # Funktion 1 Parameter für 'h0'
            description="- Wasserspiegel des anstehenden Gewässers // function1: https://doc.openfoam.com/2306/fundamentals/input-types/Function1/",
            is_function1=True
        ),
        Parameter(
            name="value",
            value=ScalarValue(0.0),  # Skalarer Wert für 'value'
            description="- Initialwert der Druckabweichung [Pa] (wird hier *teilweise* überschrieben)"
        ),
        # Beispiel für ein optionales Parameter, falls Sie es in der UI darstellen möchten
        # Parameter(
        #     name="depuitApproximation",
        #     value=ScalarValue(False), # Oder StringValue("false"), je nachdem, wie Sie es darstellen möchten
        #     description="- Optional:  depuitApproximation   true;  //No-Flow above water table",
        # ),
    ]
))

registry.register_scalar_bc(ScalarBoundaryCondition(
    name="limitedHeadInfiltration",
    parameters=[
        Parameter(
            name="flux",
            value=Function1ParameterValue(),  # Funktion 1 Parameter für 'flux'
            description="- Durchfluss normal zum Rand (Positiv=Zufluss;Negativ=Abfluss) // function1: https://doc.openfoam.com/2306/fundamentals/input-types/Function1/",
            is_function1=True
        ),
        Parameter(
            name="pMax",
            value=ScalarValue(0.0),  # Skalarer Wert für 'pMax'
            description="- Maximal zulässige Druckhöhe auf Infiltrationsrand"
        ),
        Parameter(
            name="value",
            value=ScalarValue(0.0),  # Skalarer Wert für 'value'
            description="- Initialwert der Druckabweichung [Pa] (wird hier *teilweise* überschrieben)"
        )
    ]
))

# Register vector boundary conditions
registry.register_vector_bc(VectorBoundaryCondition(
    name="fixedDisplacement",
    parameters=[
        Parameter("displacementType", Function1ParameterValue(), description="Type of displacement function", is_function1=True), # Marked as function1
        Parameter("p_At", ScalarValue(1e5), dimensions="[ 1 -1 -2 0 0 0 0 ]", description="Atmospheric Pressure"),
        Parameter("p_e", ScalarValue(0.0), dimensions="[ 1 -1 -2 0 0 0 0 ]", description="Reference Pressure"),
        Parameter("S_e", ScalarValue(0.98), dimensions="[0 0 0 0 0 0 0]", description="Degree of Water-Saturation")
    ]
))


registry.register_vector_bc(VectorBoundaryCondition(
    name="fixedDisplacementZeroShear",
    parameters=[
        Parameter(
            name="value",
            value=VectorValue((0.0, 0.0, 0.0)),  # Vektorwert für 'value'
            description="- Vector der Verschiebung, rand-normale Komponenten werden ignoriert."
        )
    ]
))

registry.register_vector_bc(VectorBoundaryCondition(
    name="poroTraction",
    parameters=[
        Parameter(
            name="total",
            value=ScalarValue(True),  # Skalarer Wert (Boolean) für 'total'
            description="total true; //false = effective traction"
        ),
        Parameter(
            name="traction",
            value=Function1ParameterValue(),  # Funktion 1 Parameter für 'traction'
            description="- Spannung auf den Rand (Richtung ist vorgegeben) // function1:  https://doc.openfoam.com/2306/fundamentals/input-types/Function1/",
            is_function1=True
        ),
        Parameter(
            name="pressure",
            value=Function1ParameterValue(),  # Funktion 1 Parameter für 'pressure'
            description="- Druck auf den Rand (wirkt immer senkrecht auf Rand) (DRUCK HIER POSITIV) // function1:  https://doc.openfoam.com/2306/fundamentals/input-types/Function1/",
            is_function1=True
        ),
        Parameter(
            name="value",
            value=VectorValue((0.0, 0.0, 0.0)),  # Vektorwert für 'value'
            description="- Initial-Wert der Verschiebung am Rand"
        ),
        # Beispiel für ein optionales Parameter 'effectiveStressModel', falls Sie es in der UI darstellen möchten
        # Parameter(
        #     name="effectiveStressModel",
        #     value=StringValue("suctionCutOff"), # oder StringValue("terzaghi"), etc.
        #     description="effectiveStressModel suctionCutOff; // oder terzaghi, niemunis, bishop",
        # ),
    ]
))

# Register dual-field boundary conditions
registry.register_dual_bc(DualFieldBoundaryCondition(
    name="fixedValue",
    scalar_parameters=[
        Parameter("value", ScalarValue(1e-6), description="The fixed scalar value to set")
    ],
    vector_parameters=[
        Parameter("value", VectorValue((0.0, 0.0, 0.0)), description="The fixed vector value to set")
    ]
))


# Helper functions for using the registry
def get_boundary_conditions_for_field(field_name: str) -> Dict[str, str]:
    """
    Get all boundary conditions applicable to the given field with their types.
    Returns dictionary mapping BC name to type (scalar/vector/dual).
    """
    bcs = registry.get_for_field(field_name)
    result = {}

    for name, bc in bcs.items():
        if isinstance(bc, ScalarBoundaryCondition):
            result[name] = "scalar"
        elif isinstance(bc, VectorBoundaryCondition):
            result[name] = "vector"
        elif isinstance(bc, DualFieldBoundaryCondition):
            if field_name in bc.get_scalar_fields():
                result[name] = "scalar"
            elif field_name in bc.get_vector_fields():
                result[name] = "vector"
            else:
                result[name] = "unknown"

    return result


def get_parameter_details(bc_name: str, field_name: str) -> Optional[Dict]:
    """Get detailed parameter information for a boundary condition and field."""
    return registry.get_parameters(bc_name, field_name)


# Example of usage with Function1 parameters and conceptual Streamlit DataFrame input
if __name__ == '__main__':
    field_name = "p_rgh"
    bc_name = "fixedPotential"

    parameter_details = get_parameter_details(bc_name, field_name)

    if parameter_details:
        print(f"Parameter details for BC '{bc_name}' and field '{field_name}':")
        import json
        print(json.dumps(parameter_details, indent=4))

        # --- Conceptual Streamlit UI part ---
        streamlit_data = {} # To store user input from Streamlit

        for param_name, param_data in parameter_details.items():
            print(f"\n-- Processing parameter: {param_name} --")
            if param_data.get("is_function1"):
                print(f"  Function1 parameter. Available types: {param_data['function1_types']}")
                selected_function1_type = "table" # In Streamlit, this would be from a selectbox
                streamlit_data[param_name + "_type"] = selected_function1_type # Store selected type

                if selected_function1_type == "table":
                    print("  Table function1 selected. Prompting for DataFrame input...")
                    # In Streamlit, here you would use:
                    # table_df = st.dataframe(pd.DataFrame()) # Or st.file_uploader for CSV, etc.
                    # streamlit_data[param_name + "_table_data"] = table_df # Store the DataFrame
                    # For this example, we'll create a dummy DataFrame:
                    table_df = pd.DataFrame({'x': [10, 20], 'y': [30, 40]})
                    streamlit_data[param_name + "_table_data"] = table_df
                    print("  (DataFrame input captured - in Streamlit, this would be from UI)")


                elif selected_function1_type == "linearRamp":
                    print("  LinearRamp function1 selected. Prompting for coefficients...")
                    coeffs_spec = param_data["function1_coeffs_spec"]["linearRamp"]
                    coeffs_input = {}
                    for coeff_name, coeff_spec in coeffs_spec.items():
                        # In Streamlit, use st.number_input or similar based on coeff_spec["type"]
                        value = 1.0 # Dummy value for example
                        coeffs_input[coeff_name] = value
                        print(f"  (Coefficient '{coeff_name}' input captured - in Streamlit, this would be from UI)")
                    streamlit_data[param_name + "_coeffs"] = coeffs_input # Store coefficients

                else: # constant, zero - no extra coefficients in this example FUNCTION1_COEFFS_SPEC
                    print(f"  Function1 type '{selected_function1_type}' selected (no extra coefficients).")


            else: # Regular parameter
                print(f"  Regular parameter of type: {param_data['type']}")
                # In Streamlit, create input based on param_data["type"] (e.g., st.number_input for scalar)
                value = "some_value" # Dummy value
                streamlit_data[param_name] = value
                print(f"  (Value input captured - in Streamlit, this would be from UI)")

        print("\n-- Streamlit Data Captured (Conceptual): --")
        print(json.dumps(streamlit_data, indent=4))


    else:
        print(f"No parameters found for BC '{bc_name}' and field '{field_name}'.")
