"""
Classes for representing OpenFOAM boundary conditions with an abstract Function1 base class
and registration pattern to easily add new implementations.
"""
from typing import Dict, List, Union, Optional, Any, Type, Callable
from dataclasses import dataclass, field
import numpy as np
import streamlit as st
import re
from abc import ABC, abstractmethod


class Function1Registry:
    """Registry for Function1 implementations."""
    _creators: Dict[str, Type['Function1']] = {}
    _parsers: Dict[str, Callable[[str], 'Function1']] = {}
    _display_names: Dict[str, str] = {}
    _type_detectors: Dict[str, Callable[[object], bool]] = {}

    @classmethod
    def register(cls, function_type: str, display_name: str, creator_class: Type['Function1'],
                 parser: Callable[[str], 'Function1'], type_detector: Callable[[object], bool]):
        """
        Register a Function1 implementation.

        Args:
            function_type: Unique identifier for this Function1 type
            display_name: Human-readable name for UI display
            creator_class: Class that implements the Function1 interface
            parser: Function that parses a foam string into this Function1 type
            type_detector: Function that detects if an object is of this type
        """
        cls._creators[function_type] = creator_class
        cls._parsers[function_type] = parser
        cls._display_names[function_type] = display_name
        cls._type_detectors[function_type] = type_detector

    @classmethod
    def get_creator(cls, function_type: str) -> Type['Function1']:
        """Get creator class for the given function type."""
        if function_type not in cls._creators:
            raise ValueError(f"Unknown Function1 type: {function_type}")
        return cls._creators[function_type]

    @classmethod
    def get_all_types(cls) -> List[str]:
        """Get all registered function types."""
        return list(cls._creators.keys())

    @classmethod
    def get_display_name(cls, function_type: str) -> str:
        """Get display name for the given function type."""
        return cls._display_names.get(function_type, function_type)

    @classmethod
    def get_type_options(cls) -> List[tuple]:
        """Get all function types with their display names."""
        return [(t, cls._display_names[t]) for t in cls._creators.keys()]

    @classmethod
    def detect_type(cls, obj: object) -> str:
        """Detect the function type of an object."""
        for function_type, detector in cls._type_detectors.items():
            if detector(obj):
                return function_type
        return "custom"  # Default fallback

    @classmethod
    def parse_foam(cls, foam_str: str) -> 'Function1':
        """Parse a Function1 from OpenFOAM syntax string."""
        # Try each parser in order
        for function_type, parser in cls._parsers.items():
            try:
                return parser(foam_str)
            except (ValueError, AttributeError):
                continue

        # If no parser succeeds, use custom
        return CustomFunction1(code=foam_str)


class Function1(ABC):
    """Abstract base class for all Function1 types."""

    @abstractmethod
    def to_foam(self) -> str:
        """Convert to OpenFOAM syntax string."""
        pass

    @abstractmethod
    def render_ui(self, label: str, key_prefix: str) -> 'Function1':
        """Render UI for this Function1 and return updated instance."""
        pass

    @property
    @abstractmethod
    def is_vector(self) -> bool:
        """Whether this function returns vector values."""
        pass

    @staticmethod
    def create(function_type: str, is_vector: bool = False, **kwargs) -> 'Function1':
        """Factory method to create the appropriate Function1 subclass."""
        if function_type == "generic":
            return GenericFunction1(is_vector=is_vector)

        try:
            creator_class = Function1Registry.get_creator(function_type)
            # Add is_vector to kwargs if the implementation needs it
            if hasattr(creator_class, "is_vector"):
                kwargs["is_vector"] = is_vector
            return creator_class(**kwargs)
        except (ValueError, TypeError) as e:
            print(f"Error creating Function1 of type {function_type}: {e}")
            # Default to custom if creation fails
            code = kwargs.get("code", "// Custom Function1")
            return CustomFunction1(code=code)

    @staticmethod
    def from_foam(foam_str: str) -> 'Function1':
        """Parse a Function1 from OpenFOAM syntax string."""
        return Function1Registry.parse_foam(foam_str)

    def select_function_type(self, label: str, key_prefix: str) -> 'Function1':
        """Render a selector for Function1 type and return the selected type."""
        function1_options = Function1Registry.get_type_options()

        # Determine current function type
        current_type = Function1Registry.detect_type(self)

        # Display selector for Function1 type
        selected_type = st.selectbox(
            f"{label} Type",
            options=[t[0] for t in function1_options],
            format_func=lambda x: next((t[1] for t in function1_options if t[0] == x), x),
            index=[t[0] for t in function1_options].index(current_type) if current_type in [t[0] for t in function1_options] else 0,
            key=f"{key_prefix}_f1_type"
        )

        # If type hasn't changed, return self
        if (current_type == selected_type) and not isinstance(self, GenericFunction1):
            return self

        # Create a new instance with default values
        return Function1.create(selected_type, is_vector=self.is_vector)


class GenericFunction1(Function1):
    """
    A Function1 that doesn't commit to a specific implementation until render_ui is called.
    Acts as a placeholder that will be replaced with a concrete Function1 implementation.
    """

    def __init__(self, is_vector: bool = False):
        """
        Initialize with vector flag.

        Args:
            is_vector: Whether this function will return vector values
        """
        self._is_vector = is_vector
        # Default to uniform with appropriate value type
        self._impl = UniformFunction1(
            value=[0, 0, 0] if is_vector else 0.0,
            is_vector=is_vector
        )

    @property
    def is_vector(self) -> bool:
        return self._is_vector

    def to_foam(self) -> str:
        """
        Delegate to the concrete implementation.

        Returns:
            OpenFOAM syntax string
        """
        return self._impl.to_foam()

    def render_ui(self, label: str, key_prefix: str) -> 'Function1':
        """
        Render UI and allow user to select Function1 type.

        Args:
            label: Label for the UI
            key_prefix: Unique prefix for UI components

        Returns:
            The selected Function1 implementation
        """
        # This will allow the user to select the Function1 type and return the appropriate concrete instance
        return self._impl.select_function_type(label, key_prefix)


class Function1Factory:
    """Factory class that creates appropriate Function1 instances on demand."""

    @staticmethod
    def create_generic(is_vector: bool = False) -> Function1:
        """
        Create a generic Function1 that will prompt for type selection when render_ui is called.

        Args:
            is_vector: Whether this function will return vector values

        Returns:
            A GenericFunction1 instance that delegates to specific implementations
        """
        return GenericFunction1(is_vector=is_vector)


@dataclass
class UniformFunction1(Function1):
    """Uniform (constant) value Function1."""
    value: Union[float, List[float]] = 0.0
    is_vector: bool = False

    def to_foam(self) -> str:
        if self.is_vector:
            if isinstance(self.value, (list, np.ndarray)) and len(self.value) >= 3:
                return f"uniform ({self.value[0]} {self.value[1]} {self.value[2]})"
            else:
                return "uniform (0 0 0)"
        else:
            return f"uniform {self.value}"

    def render_ui(self, label: str, key_prefix: str) -> Function1:
        """Render UI for this Function1 and return updated instance."""
        # First, allow selection of different Function1 type
        new_fn = self.select_function_type(label, key_prefix)
        if new_fn is not self:
            return new_fn

        # Render uniform-specific UI
        if self.is_vector:
            # For vector fields, provide 3 inputs
            if isinstance(self.value, (list, np.ndarray)) and len(self.value) >= 3:
                default_vals = self.value[:3]
            else:
                default_vals = [0, 0, 0]

            cols = st.columns(3)
            with cols[0]:
                x = st.number_input("X", value=float(default_vals[0]), key=f"{key_prefix}_x")
            with cols[1]:
                y = st.number_input("Y", value=float(default_vals[1]), key=f"{key_prefix}_y")
            with cols[2]:
                z = st.number_input("Z", value=float(default_vals[2]), key=f"{key_prefix}_z")

            return UniformFunction1(value=[x, y, z], is_vector=True)
        else:
            # For scalar fields, provide a single input
            value = st.number_input(label, value=float(self.value), key=f"{key_prefix}_value")
            return UniformFunction1(value=value, is_vector=False)


@dataclass
class TableFileFunction1(Function1):
    """Table file Function1 for time series data."""
    file_path: str = "PATH/TO/FILE"
    out_of_bounds: str = "clamp"  # error, warn, clamp, repeat
    interpolation_scheme: str = "linear"

    @property
    def is_vector(self) -> bool:
        # TableFile can be either vector or scalar,
        # but we don't track that internally
        return False

    def to_foam(self) -> str:
        return f"""tableFile;
tableFileCoeffs
{{
    file "{self.file_path}";
    outOfBounds {self.out_of_bounds};
    interpolationScheme {self.interpolation_scheme};
}}"""

    def render_ui(self, label: str, key_prefix: str) -> Function1:
        """Render UI for this Function1 and return updated instance."""
        # First, allow selection of different Function1 type
        new_fn = self.select_function_type(label, key_prefix)
        if new_fn is not self:
            return new_fn

        # Render tableFile-specific UI
        st.info("Time series from an OpenFOAM format file")

        file_path = st.text_input(
            "File Path",
            value=self.file_path,
            key=f"{key_prefix}_file_path"
        )

        out_of_bounds = st.selectbox(
            "Out of Bounds Behavior",
            options=["clamp", "error", "warn", "repeat"],
            index=["clamp", "error", "warn", "repeat"].index(self.out_of_bounds),
            key=f"{key_prefix}_out_of_bounds"
        )

        interpolation_scheme = st.text_input(
            "Interpolation Scheme",
            value=self.interpolation_scheme,
            key=f"{key_prefix}_interp"
        )

        return TableFileFunction1(
            file_path=file_path,
            out_of_bounds=out_of_bounds,
            interpolation_scheme=interpolation_scheme
        )


@dataclass
class RampFunction1(Function1):
    """Ramp Function1 for gradual increase over time."""
    ramp_type: str = "linearRamp"  # linearRamp, halfCosineRamp, etc.
    start: float = 0.0
    duration: float = 10.0

    @property
    def is_vector(self) -> bool:
        # Ramp functions are typically scalar
        return False

    def to_foam(self) -> str:
        return f"""{self.ramp_type};
{self.ramp_type}Coeffs
{{
    start {self.start};
    duration {self.duration};
}}"""

    def render_ui(self, label: str, key_prefix: str) -> Function1:
        """Render UI for this Function1 and return updated instance."""
        # First, allow selection of different Function1 type
        new_fn = self.select_function_type(label, key_prefix)
        if new_fn is not self:
            return new_fn

        # Render ramp-specific UI
        st.info("Ramp function (gradual increase)")

        ramp_types = ["linearRamp", "halfCosineRamp", "quadraticRamp",
                      "quarterCosineRamp", "quarterSineRamp", "stepFunction"]

        ramp_type = st.selectbox(
            "Ramp Type",
            options=ramp_types,
            index=ramp_types.index(self.ramp_type) if self.ramp_type in ramp_types else 0,
            key=f"{key_prefix}_ramp_type"
        )

        start = st.number_input(
            "Start Time",
            value=self.start,
            key=f"{key_prefix}_start"
        )

        duration = st.number_input(
            "Duration",
            value=self.duration,
            key=f"{key_prefix}_duration"
        )

        return RampFunction1(
            ramp_type=ramp_type,
            start=start,
            duration=duration
        )


@dataclass
class CSVFileFunction1(Function1):
    """CSV file Function1 for time series data."""
    file_path: str = "PATH/TO/FILE.csv"
    header_lines: int = 4
    is_vector: bool = False

    def to_foam(self) -> str:
        component_cols = "(1 2 3)" if self.is_vector else "1"
        return f"""csvFile;
csvFileCoeffs
{{
    nHeaderLine {self.header_lines};
    refColumn 0;
    componentColumns {component_cols};
    separator ",";
    mergeSeparators no;
    file "{self.file_path}";
    outOfBounds clamp;
    interpolationScheme linear;
}}"""

    def render_ui(self, label: str, key_prefix: str) -> Function1:
        """Render UI for this Function1 and return updated instance."""
        # First, allow selection of different Function1 type
        new_fn = self.select_function_type(label, key_prefix)
        if new_fn is not self:
            return new_fn

        # Render csvFile-specific UI
        st.info("Time series from a CSV file")

        file_path = st.text_input(
            "CSV File Path",
            value=self.file_path,
            key=f"{key_prefix}_csv_path"
        )

        header_lines = st.number_input(
            "Header Lines",
            value=self.header_lines,
            min_value=0,
            key=f"{key_prefix}_header_lines"
        )

        return CSVFileFunction1(
            file_path=file_path,
            header_lines=header_lines,
            is_vector=self.is_vector
        )


@dataclass
class CosineFunction1(Function1):
    """Cosine wave Function1."""
    frequency: float = 10.0
    amplitude: float = 1.0
    scale: float = 1.0
    level: float = 0.0

    @property
    def is_vector(self) -> bool:
        # Cosine functions are typically scalar
        return False

    def to_foam(self) -> str:
        return f"""cosine;
cosineCoeffs
{{
    frequency {self.frequency};
    amplitude {self.amplitude};
    scale {self.scale};
    level {self.level};
}}"""

    def render_ui(self, label: str, key_prefix: str) -> Function1:
        """Render UI for this Function1 and return updated instance."""
        # First, allow selection of different Function1 type
        new_fn = self.select_function_type(label, key_prefix)
        if new_fn is not self:
            return new_fn

        # Render cosine-specific UI
        st.info("Cosine wave function")

        frequency = st.number_input(
            "Frequency [1/s]",
            value=self.frequency,
            key=f"{key_prefix}_frequency"
        )

        amplitude = st.number_input(
            "Amplitude",
            value=self.amplitude,
            key=f"{key_prefix}_amplitude"
        )

        scale = st.number_input(
            "Scale Factor",
            value=self.scale,
            key=f"{key_prefix}_scale"
        )

        level = st.number_input(
            "Offset Level",
            value=self.level,
            key=f"{key_prefix}_level"
        )

        return CosineFunction1(
            frequency=frequency,
            amplitude=amplitude,
            scale=scale,
            level=level
        )


@dataclass
class CustomFunction1(Function1):
    """Custom Function1 for direct code entry."""
    code: str = "// Custom Function1"
    _is_vector: bool = False

    @property
    def is_vector(self) -> bool:
        return self._is_vector

    def to_foam(self) -> str:
        return self.code

    def render_ui(self, label: str, key_prefix: str) -> Function1:
        """Render UI for this Function1 and return updated instance."""
        # First, allow selection of different Function1 type
        new_fn = self.select_function_type(label, key_prefix)
        if new_fn is not self:
            return new_fn

        # Render custom-specific UI
        st.info("Custom Function1 configuration")

        code = st.text_area(
            label,
            value=self.code,
            key=f"{key_prefix}_custom",
            height=150
        )

        is_vector = st.checkbox(
            "Is Vector Value",
            value=self._is_vector,
            key=f"{key_prefix}_is_vector"
        )

        return CustomFunction1(code=code, _is_vector=is_vector)


# Register the built-in Function1 implementations
# UniformFunction1
Function1Registry.register(
    function_type="uniform",
    display_name="Uniform (constant) value",
    creator_class=UniformFunction1,
    parser=UniformFunction1.from_foam,
    type_detector=lambda obj: isinstance(obj, UniformFunction1)
)

# TableFileFunction1
Function1Registry.register(
    function_type="tableFile",
    display_name="Table file (time series)",
    creator_class=TableFileFunction1,
    parser=lambda foam_str: TableFileFunction1.from_foam(foam_str) if "tableFile" in foam_str else None,
    type_detector=lambda obj: isinstance(obj, TableFileFunction1)
)

# RampFunction1
Function1Registry.register(
    function_type="ramp",
    display_name="Ramp (gradual increase)",
    creator_class=RampFunction1,
    parser=lambda foam_str: RampFunction1.from_foam(foam_str) if any(ramp in foam_str for ramp in ["linearRamp", "halfCosineRamp", "quadraticRamp"]) else None,
    type_detector=lambda obj: isinstance(obj, RampFunction1)
)

# CSVFileFunction1
Function1Registry.register(
    function_type="csvFile",
    display_name="CSV file (time series)",
    creator_class=CSVFileFunction1,
    parser=lambda foam_str: CSVFileFunction1.from_foam(foam_str) if "csvFile" in foam_str else None,
    type_detector=lambda obj: isinstance(obj, CSVFileFunction1)
)

# CosineFunction1
Function1Registry.register(
    function_type="cosine",
    display_name="Cosine wave",
    creator_class=CosineFunction1,
    parser=lambda foam_str: CosineFunction1.from_foam(foam_str) if "cosine" in foam_str else None,
    type_detector=lambda obj: isinstance(obj, CosineFunction1)
)

# CustomFunction1
Function1Registry.register(
    function_type="custom",
    display_name="Custom configuration",
    creator_class=CustomFunction1,
    parser=lambda foam_str: CustomFunction1(code=foam_str),
    type_detector=lambda obj: isinstance(obj, CustomFunction1)
)
