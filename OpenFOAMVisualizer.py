import os
import numpy as np
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
from pathlib import Path
import pandas as pd
import pyvista as pv
from foamlib import FoamCase
from typing import List, Dict, Tuple, Optional, Union, Any


class OpenFOAMVisualizer:
    """
    Backend for visualizing OpenFOAM postprocessing data.
    Uses PyVista's OpenFOAM reader and foamlib for file handling.
    Provides functionality for reading and plotting line samples, slices, and point samples.
    """

    # Dictionary of available color palettes
    COLOR_PALETTES = {
        # Custom color palettes
        "deep": mcolors.LinearSegmentedColormap.from_list("deep", ["#4C72B0", "#55A868", "#C44E52", "#8172B2", "#CCB974", "#64B5CD"]),
        "muted": mcolors.LinearSegmentedColormap.from_list("muted", ["#4878CF", "#6ACC65", "#D65F5F", "#956CB4", "#D3C36C", "#8CB4CD"]),
        "pastel": mcolors.LinearSegmentedColormap.from_list("pastel", ["#A1C9F4", "#B0E57C", "#F28C82", "#D3A4DE", "#FCE29A", "#94D0F5"]),
        "bright": mcolors.LinearSegmentedColormap.from_list("bright", ["#0079FA", "#36BC1C", "#EB4034", "#A64DCD", "#FFC71C", "#00C2C7"]),
        "dark": mcolors.LinearSegmentedColormap.from_list("dark", ["#001C7F", "#013220", "#8B0909", "#592887", "#A63700", "#3C1098"]),
        "colorblind": mcolors.LinearSegmentedColormap.from_list("colorblind", ["#0072B2", "#009E73", "#D55E00", "#CC79A7", "#F0E442", "#56B4E9"])
    }

    def __init__(self, case_path: Union[str, Path], region: Optional[str] = None):
        """
        Initialize the OpenFOAM visualization backend.

        Parameters:
            case_path: Path to the OpenFOAM case directory
        """
        self.case_path = Path(case_path)
        if not self.case_path.exists():
            raise FileNotFoundError(f"Case directory not found: {self.case_path}")

        # Initialize instance variables
        self.foam_case = None
        self.foam_file = None
        self.time_dirs = []
        self.latest_time = None

        # Region handling
        self.has_regions = bool(region)
        self.region = region

        # File modification timestamps for cache invalidation
        self.cache_timestamps = {}

        # Data caches
        self._data_cache = {}

        # Initialize everything
        self.refresh()

    def refresh(self):
        """
        Refresh all case data, clearing any cached information.
        Call this method when the case has been modified.
        """
        # Clear caches
        self._data_cache = {}
        self.cache_timestamps = {}

        # Reinitialize foamlib case
        self.foam_case = FoamCase(self.case_path)

        # Update or create the .foam file for PyVista
        self.foam_file = Path(self.case_path) / f"{self.case_path.name}.foam"
        if not self.foam_file.exists():
            # Create the .foam file if it doesn't exist (just an empty file for PyVista to recognize)
            self.foam_file.touch()

        # Refresh time directories and latest time
        self.time_dirs = self._get_time_dirs()
        self.latest_time = self._get_latest_time()

        return self

    def has_case_changed(self, path: Optional[Union[str, Path]] = None, check_subdirs: bool = True) -> bool:
        """
        Check if the case has been modified since last read.

        Parameters:
            path: Path to check (default is case root directory)
            check_subdirs: Whether to also check subdirectories

        Returns:
            True if the case has been modified, False otherwise
        """
        if path is None:
            path = self.case_path
        else:
            path = Path(path)

        # Get current timestamp
        try:
            current_timestamp = os.path.getmtime(path)
        except FileNotFoundError:
            return False

        # Compare with cached timestamp
        if str(path) in self.cache_timestamps:
            if current_timestamp > self.cache_timestamps[str(path)]:
                # Update timestamp and return True
                self.cache_timestamps[str(path)] = current_timestamp
                return True
        else:
            # Add timestamp to cache
            self.cache_timestamps[str(path)] = current_timestamp

        # Check subdirectories if requested
        if check_subdirs and path.is_dir():
            for subpath in path.iterdir():
                if subpath.is_dir():
                    if self.has_case_changed(subpath, check_subdirs=True):
                        return True

        return False

    def _get_time_dirs(self) -> List[str]:
        """Get all time directories in the case, sorted numerically."""
        # Use foamlib to get time directories
        time_dirs = []
        for item in self.case_path.iterdir():
            if item.is_dir() and self._is_time_dir(item.name):
                # Add the original directory name (not converted to float)
                time_dirs.append(item.name)
        time_dirs.sort(key=lambda x: float(x) if x != 'constant' else -1)
        return sorted(time_dirs)

    def _get_latest_time(self) -> str:
        """Get the latest time directory."""
        if not self.time_dirs:
            raise ValueError("No time directories found in the case")
        return self.time_dirs[-1]

    def _is_time_dir(self, dirname: str) -> bool:
        """Check if the directory name is a valid time directory (numeric or 'constant')."""
        if dirname == 'constant':
            return False
        try:
            float(dirname)
            return True
        except ValueError:
            return False

    def _has_regions(self, block_names: List[str]) -> bool:
        """Check if the case has regions."""
        if block_names and 'internalMesh' not in block_names:
            self.has_regions = True
        return self.has_regions

    def get_region_path(self, time_dir: str) -> Path:
        """
        Get the path for a specific time directory, considering the region if set.

        Parameters:
            time_dir: Time directory name

        Returns:
            Path to the time directory for the specific region
        """
        if self.region and time_dir == 'constant':
            # For constant directory, regions are stored in constant/{region}
            return self.case_path / time_dir / self.region
        elif self.region:
            # For time directories, regions might be in {time}/{region}
            region_path = self.case_path / time_dir / self.region
            if region_path.exists():
                return region_path

        # Default (no region or region directory doesn't exist)
        return self.case_path / time_dir

    def read_line_sample(self, sample_name: str, time: Optional[str] = None, force_reload: bool = False) -> pd.DataFrame:
        """
        Read a line sample from postProcessing directory.

        Parameters:
            sample_name: Name of the line sample
            time: Time to read (default is latest time)
            force_reload: Force reloading data from disk even if cached

        Returns:
            DataFrame containing the line sample data
        """
        if time is None:
            time = self.latest_time

        # Check cache first (unless force_reload is True)
        cache_key = f"line_sample_{sample_name}_{time}"
        if not force_reload and cache_key in self._data_cache:
            return self._data_cache[cache_key]

        # Find the matching time directory
        pp_dir = self.case_path / "postProcessing" / sample_name
        if not pp_dir.exists():
            raise FileNotFoundError(f"Sample directory not found: {pp_dir}")

        # Find the closest time directory
        time_dirs = [d.name for d in pp_dir.iterdir() if self._is_time_dir(d.name)]
        if not time_dirs:
            raise FileNotFoundError(f"No time directories found in {pp_dir}")
        float_time_dirs = [float(d) for d in time_dirs]

        closest_time = min(float_time_dirs, key=lambda x: abs(x - float(time)))
        closest_time_index = float_time_dirs.index(closest_time)

        # Check if the directory has been modified since last read
        time_dir = pp_dir / time_dirs[closest_time_index]
        if not force_reload and not self.has_case_changed(time_dir):
            if cache_key in self._data_cache:
                return self._data_cache[cache_key]

        # Read the data file
        data_files = list(time_dir.glob("*.xy"))
        if not data_files:
            raise FileNotFoundError(f"No .xy files found in {time_dir}")

        # Read all data files in the directory
        dataframes = []
        for data_file in data_files:
            # Extract field name from filename
            field_name = data_file.stem.split('_')[-1]

            # Read the data
            df = pd.read_csv(data_file, delim_whitespace=True, comment='#', header=None)

            # Determine if this is positional data (assuming first file contains coordinates)
            if len(dataframes) == 0:
                # First file - assume first 3 columns are x, y, z
                if df.shape[1] >= 3:
                    df.columns = ['x', 'y', 'z'] + [f'{field_name}_{i}' for i in range(df.shape[1]-3)]
                else:
                    df.columns = [f'pos_{i}' for i in range(df.shape[1]-1)] + [field_name]

                base_df = df
                dataframes.append(df)
            else:
                # For subsequent files, just add the field columns to the base dataframe
                if df.shape[1] > 3:  # Has positional data and field data
                    field_cols = df.iloc[:, 3:].values
                    for i in range(field_cols.shape[1]):
                        col_name = f'{field_name}_{i}' if field_cols.shape[1] > 1 else field_name
                        base_df[col_name] = field_cols[:, i]
                else:  # Only field data
                    field_cols = df.iloc[:, -1].values
                    base_df[field_name] = field_cols

        result = base_df if dataframes else pd.DataFrame()

        # Cache the result
        self._data_cache[cache_key] = result

        return result

    def plot_line_sample(self, sample_name: str, field_name: Optional[str] = None,
                         time: Optional[float] = None, ax=None, force_reload: bool = False, **kwargs):
        """
        Plot a line sample from OpenFOAM case.

        Parameters:
            sample_name: Name of the line sample
            field_name: Name of the field to plot (if None, attempts to plot all fields)
            time: Time to plot (default is latest time)
            ax: Matplotlib axis to plot on (creates new if None)
            force_reload: Force reloading data from disk even if cached
            **kwargs: Additional arguments passed to matplotlib plot

        Returns:
            Matplotlib axis object
        """
        data = self.read_line_sample(sample_name, time, force_reload)

        # Create a new axis if not provided
        if ax is None:
            fig, ax = plt.subplots(figsize=(10, 6))

        # Calculate distance along the line
        if 'x' in data.columns and 'y' in data.columns:
            distance = np.zeros(len(data))
            for i in range(1, len(data)):
                if 'z' in data.columns:
                    dx = data['x'][i] - data['x'][i-1]
                    dy = data['y'][i] - data['y'][i-1]
                    dz = data['z'][i] - data['z'][i-1]
                    distance[i] = distance[i-1] + np.sqrt(dx**2 + dy**2 + dz**2)
                else:
                    dx = data['x'][i] - data['x'][i-1]
                    dy = data['y'][i] - data['y'][i-1]
                    distance[i] = distance[i-1] + np.sqrt(dx**2 + dy**2)
        else:
            # Use index as distance if no coordinate columns
            distance = data.index

        # Filter to only data columns (not coordinate columns)
        data_columns = [col for col in data.columns if col not in ['x', 'y', 'z']]

        # Plot specified field or attempt to plot all fields
        if field_name:
            matching_columns = [col for col in data_columns if field_name in col]
            if matching_columns:
                for col in matching_columns:
                    ax.plot(distance, data[col], label=col, **kwargs)
            else:
                raise ValueError(f"Field '{field_name}' not found in data columns: {data_columns}")
        else:
            # Plot all data columns
            for col in data_columns:
                ax.plot(distance, data[col], label=col, **kwargs)

        ax.set_xlabel('Distance [m]')
        ax.set_ylabel('Value')
        ax.set_title(f'Line Sample: {sample_name} (Time: {time if time is not None else self.latest_time}s)')
        ax.legend()
        ax.grid(True)

        return ax

    def read_slice(self, slice_name: str, time: Optional[float] = None, force_reload: bool = False) -> pv.DataSet:
        """
        Read a slice from postProcessing directory using PyVista.

        Parameters:
            slice_name: Name of the slice
            time: Time to read (default is latest time)
            force_reload: Force reloading data from disk even if cached

        Returns:
            PyVista dataset containing the slice data
        """
        if time is None:
            time = self.latest_time

        # Check cache first (unless force_reload is True)
        cache_key = f"slice_{slice_name}_{time}"
        if not force_reload and cache_key in self._data_cache:
            return self._data_cache[cache_key]

        # Find the slice directory
        pp_dir = self.case_path / "postProcessing" / slice_name
        if not pp_dir.exists():
            raise FileNotFoundError(f"Slice directory not found: {pp_dir}")

        # Find the closest time directory
        time_dirs = [float(d.name) for d in pp_dir.iterdir() if self._is_time_dir(d.name)]
        if not time_dirs:
            raise FileNotFoundError(f"No time directories found in {pp_dir}")

        closest_time = min(time_dirs, key=lambda x: abs(x - time))
        time_dir = pp_dir / str(closest_time)

        # Check if the directory has been modified since last read
        if not force_reload and not self.has_case_changed(time_dir):
            if cache_key in self._data_cache:
                return self._data_cache[cache_key]

        # Check for VTK files
        vtk_files = list(time_dir.glob("*.vtk"))
        if not vtk_files:
            vtk_files = list(time_dir.glob("*.vtp"))

        if not vtk_files:
            raise FileNotFoundError(f"No VTK files found in {time_dir}")

        # Use PyVista to read the VTK file
        mesh = pv.read(vtk_files[0])
        mesh.time_value = closest_time  # Attach time value as metadata

        # Cache the result
        self._data_cache[cache_key] = mesh

        return mesh

    def plot_slice(self, slice_name: str, field_name: Optional[str] = None,
                   vector_field: Optional[str] = None, time: Optional[float] = None,
                   plotter=None, force_reload: bool = False, **kwargs):
        """
        Plot a slice from OpenFOAM case.

        Parameters:
            slice_name: Name of the slice
            field_name: Name of the scalar field to plot (if None, uses first available)
            vector_field: Name of the vector field to plot as arrows
            time: Time to plot (default is latest time)
            plotter: PyVista plotter to use (creates new if None)
            force_reload: Force reloading data from disk even if cached
            **kwargs: Additional arguments passed to PyVista

        Returns:
            PyVista plotter object
        """
        mesh = self.read_slice(slice_name, time, force_reload)

        # Create a new plotter if not provided
        if plotter is None:
            plotter = pv.Plotter()

        # Plot scalar field if specified
        if field_name:
            if field_name in mesh.array_names:
                plotter.add_mesh(mesh, scalars=field_name, **kwargs)
            else:
                raise ValueError(f"Field '{field_name}' not found in slice data. Available fields: {mesh.array_names}")
        elif mesh.array_names:
            # Use the first available array
            field_name = mesh.array_names[0]
            plotter.add_mesh(mesh, scalars=field_name, **kwargs)

        # Add vector field as arrows if specified
        if vector_field:
            if vector_field in mesh.array_names:
                vector_data = mesh[vector_field]
                if len(vector_data.shape) > 1 and vector_data.shape[1] == 3:
                    # Get a subset of points for arrows (too many makes visualization cluttered)
                    n_points = len(mesh.points)
                    skip = max(1, n_points // 100)  # Aim for around 100 arrows

                    arrow_mesh = mesh.extract_subset(np.arange(0, n_points, skip))
                    arrows = arrow_mesh.glyph(
                        orient=vector_field,
                        scale=vector_field,
                        factor=0.05,  # Adjust scale factor as needed
                        geom=pv.Arrow()
                    )
                    plotter.add_mesh(arrows, color='black', **kwargs)
                else:
                    print(f"Warning: Vector field '{vector_field}' does not have 3 components")
            else:
                raise ValueError(f"Vector field '{vector_field}' not found in slice data. Available fields: {mesh.array_names}")

        # Set a sensible camera position
        plotter.view_xy()

        # Add title
        plotter.add_text(f'Slice: {slice_name} (Time: {mesh.time_value}s)', position='upper_edge')

        return plotter

    def read_point_sample(self, sample_name: str, force_reload: bool = False) -> pd.DataFrame:
        """
        Read a point sample from postProcessing directory.

        Parameters:
            sample_name: Name of the point sample
            force_reload: Force reloading data from disk even if cached

        Returns:
            DataFrame containing the point sample data over time
        """
        # Check cache first (unless force_reload is True)
        cache_key = f"point_sample_{sample_name}"
        pp_dir = self.case_path / "postProcessing" / sample_name

        if not force_reload:
            # Check if the directory has been modified
            if not self.has_case_changed(pp_dir):
                if cache_key in self._data_cache:
                    return self._data_cache[cache_key]

        if not pp_dir.exists():
            raise FileNotFoundError(f"Point sample directory not found: {pp_dir}")

        # Look for data files
        data_files = list(pp_dir.glob("*.dat"))
        if not data_files:
            raise FileNotFoundError(f"No .dat files found in {pp_dir}")

        # Read the data file
        data_file = data_files[0]

        # Read header to determine columns
        with open(data_file, 'r') as f:
            header_line = None
            for line in f:
                if line.startswith('#'):
                    header_line = line.strip('# \n')
                else:
                    break

        # Read the data
        data = pd.read_csv(data_file, delim_whitespace=True, comment='#', header=None)

        # Assign column names if available
        if header_line:
            columns = header_line.split()
            if len(columns) == data.shape[1]:
                data.columns = columns
        else:
            # Default column names
            data.columns = ['time'] + [f'field_{i}' for i in range(data.shape[1]-1)]

        # Cache the result
        self._data_cache[cache_key] = data

        return data

    def plot_point_sample(self, sample_name: str, field_names: Optional[List[str]] = None,
                          ax=None, force_reload: bool = False, **kwargs):
        """
        Plot a point sample over time from OpenFOAM case.

        Parameters:
            sample_name: Name of the point sample
            field_names: List of field names to plot (if None, attempts to plot all fields)
            ax: Matplotlib axis to plot on (creates new if None)
            force_reload: Force reloading data from disk even if cached
            **kwargs: Additional arguments passed to matplotlib plot

        Returns:
            Matplotlib axis object
        """
        data = self.read_point_sample(sample_name, force_reload)

        # Create a new axis if not provided
        if ax is None:
            fig, ax = plt.subplots(figsize=(10, 6))

        # Assume first column is time
        time_col = data.columns[0]

        # Plot specified fields or all fields
        if field_names:
            for field in field_names:
                matching_columns = [col for col in data.columns if field in col and col != time_col]
                for col in matching_columns:
                    ax.plot(data[time_col], data[col], label=col, **kwargs)
                if not matching_columns:
                    print(f"Warning: Field '{field}' not found in data columns: {data.columns.tolist()}")
        else:
            # Plot all columns except time
            for col in data.columns[1:]:
                ax.plot(data[time_col], data[col], label=col, **kwargs)

        ax.set_xlabel('Time [s]')
        ax.set_ylabel('Value')
        ax.set_title(f'Point Sample: {sample_name}')
        ax.legend()
        ax.grid(True)

        return ax

    def read_full_case(self, time: Optional[str] = None, force_reload: bool = False) -> pv.MultiBlock:
        """
        Read the full OpenFOAM case using PyVista's OpenFOAMReader.

        Parameters:
            time: Time to read (default is latest time)
            force_reload: Force reloading data from disk even if cached

        Returns:
            PyVista MultiBlock dataset
        """
        if time is None or time == 'constant':
            time = self.latest_time

        # Check cache first (unless force_reload is True)
        cache_key = f"full_case_{time}"
        if self.region:
            cache_key += f"_{self.region}"

        if not force_reload:
            # Check if the case has been modified
            if not self.has_case_changed(self.case_path / "constant") and \
            (time == 'constant' or not self.has_case_changed(self.case_path / time)):
                if cache_key in self._data_cache:
                    return self._data_cache[cache_key]

        # Use PyVista's OpenFOAMReader
        reader = pv.OpenFOAMReader(str(self.foam_file))

        # Find the matching time
        time_values = reader.time_values
        if not time_values:
            raise ValueError("No time steps found in the OpenFOAM case")

        # Try to find exact string match in reader's time_names if available
        if hasattr(reader, 'time_names') and time in reader.time_names:
            time_idx = reader.time_names.index(time)
        else:
            # Fall back to numeric comparison
            try:
                time_val = float(time)
                time_idx = min(range(len(time_values)), key=lambda i: abs(time_values[i] - time_val))
            except ValueError:
                # If conversion fails, use the latest time
                time_idx = len(time_values) - 1

        reader.set_active_time_value(time_values[time_idx])

        # Get data with all fields
        reader.all_patches = True

        reader.add_dimensions = True

        # Read all data
        data = reader.read()

        # Cache the result
        self._data_cache[cache_key] = data

        if self.region:
            data = data[self.region]
        elif 'defaultRegion' in data.keys():
            data = data['defaultRegion']

        return data

    def visualize_mesh(self, time: Optional[str] = None, plotter=None,
                       show_edges: bool = True, color: Optional[str] = None,
                       style: str = 'surface', color_patches: bool = False,
                       show_boundaries: bool = True, only_boundaries: bool = False,
                       opacity: float = 1.0, edge_color: str = 'black',
                       boundary_palette: str = 'deep', force_reload: bool = False, **kwargs):
        """
        Visualize only the mesh geometry from the OpenFOAM case.

        Parameters:
            time: Time to visualize (default is latest time)
            plotter: PyVista plotter to use (creates new if None)
            show_edges: Whether to show mesh edges
            color: Color for the mesh (if None and color_patches is False, uses a default color)
            style: Visualization style ('surface', 'wireframe', or 'points')
            color_patches: Whether to color each patch differently
            show_boundaries: Whether to show boundary patches
            only_boundaries: Whether to show only boundary patches (not internal mesh)
            opacity: Opacity of the mesh (0.0-1.0)
            edge_color: Color of mesh edges when show_edges is True
            boundary_palette: Color palette to use when color_patches is True
            force_reload: Force reloading data from disk even if cached
            **kwargs: Additional arguments passed to PyVista

        Returns:
            PyVista plotter object
        """
        data = self.read_full_case(time, force_reload)

        # Create a new plotter if not provided
        if plotter is None:
            plotter = pv.Plotter()

        # Get all blocks from the case
        blocks = []
        patch_names = []

        # Filter and collect blocks based on options
        for i in range(data.n_blocks):
            block = data[i]
            block_name = data.keys()[i]

            if hasattr(block, 'n_points') and block.n_points > 0:
                # Check if this is an internal mesh or boundary patch
                is_internal = "internalMesh" in block_name.lower()

                # Skip internal mesh if only_boundaries is True
                if only_boundaries and is_internal:
                    continue
                # Skip boundary patches if show_boundaries is False
                if not show_boundaries and not is_internal:
                    continue

                blocks.append(block)
                patch_names.append(block_name)

        if not blocks:
            raise ValueError("No valid blocks found in the case data to visualize")

        # Generate colors for patches if requested
        if color_patches:
            if boundary_palette in self.COLOR_PALETTES:
                cmap = self.COLOR_PALETTES[boundary_palette]
            else:
                cmap = plt.cm.plasma  # Default fallback

            colors = [cmap(i / max(1, len(blocks) - 1)) for i in range(len(blocks))]

        # Add the meshes to the plotter
        for i, (block, patch_name) in enumerate(zip(blocks, patch_names)):
            # Determine style parameters
            if style == 'wireframe':
                show_edges = True
                block_style = 'wireframe'
            elif style == 'points':
                show_edges = False
                block_style = 'points'
            else:  # 'surface' is default
                block_style = 'surface'

            # Determine color
            if color_patches:
                block_color = colors[i]
            else:
                block_color = color if color else 'lightgray'

            # Add mesh to plotter
            plotter.add_mesh(
                block,
                style=block_style,
                color=block_color,
                show_edges=show_edges,
                edge_color=edge_color,
                opacity=opacity,
                label=patch_name,
                **kwargs
            )

        # Add legend if coloring patches
        if color_patches:
            plotter.add_legend()

        # Add time and region information to title
        title = f'Time: {time if time is not None else self.latest_time}'
        if self.region:
            title += f', Region: {self.region}'
        plotter.add_text(title, position='upper_edge')

        return plotter

    def visualize_3d(self, field_name: Optional[str] = None, time: Optional[float] = None,
                    clip_plane: bool = False, slice_origin: Optional[List[float]] = None,
                    slice_normal: Optional[List[float]] = None, plotter=None,
                    show_edges: bool = False, edge_color: str = 'black',
                    color_palette: str = 'plasma', opacity: float = 1.0,
                    force_reload: bool = False, **kwargs):
        """
        Create a 3D visualization of the OpenFOAM case.

        Parameters:
            field_name: Name of the field to visualize
            time: Time to visualize (default is latest time)
            clip_plane: Whether to add a clip plane
            slice_origin: Origin point for slicing plane [x,y,z]
            slice_normal: Normal vector for slicing plane [nx,ny,nz]
            plotter: PyVista plotter to use (creates new if None)
            show_edges: Whether to show mesh edges
            edge_color: Color of mesh edges when show_edges is True
            color_palette: Color palette to use for the scalar field
            opacity: Opacity of the mesh (0.0-1.0)
            force_reload: Force reloading data from disk even if cached
            **kwargs: Additional arguments passed to PyVista

        Returns:
            PyVista plotter object
        """
        data = self.read_full_case(time, force_reload)

        # Create a new plotter if not provided
        if plotter is None:
            plotter = pv.Plotter()

        # Get the patches from the case
        patches = []
        field_names = []

        # Extract all blocks that have data
        for i in range(data.n_blocks):
            block = data[i]
            if hasattr(block, 'n_points') and block.n_points > 0:
                patches.append(block)
                if not field_names and hasattr(block, 'array_names'):
                    field_names = block.array_names

        if not patches:
            raise ValueError("No valid patches found in the case data")

        # Process field name
        if field_name is None and field_names:
            field_name = field_names[0]

        if field_name and field_name not in field_names:
            raise ValueError(f"Field '{field_name}' not found. Available fields: {field_names}")

        # Apply slice if requested
        if slice_origin and slice_normal:
            sliced_patches = []
            for patch in patches:
                try:
                    sliced = patch.slice(normal=slice_normal, origin=slice_origin)
                    if sliced.n_points > 0:
                        sliced_patches.append(sliced)
                except:
                    # Skip patches that can't be sliced
                    pass

            if sliced_patches:
                patches = sliced_patches
            else:
                print("Warning: No valid slices created - using original patches")

        # Apply clip if requested
        if clip_plane:
            if not slice_origin or not slice_normal:
                # Default to XY plane at z=0 if not specified
                slice_origin = [0, 0, 0]
                slice_normal = [0, 0, 1]

            clipped_patches = []
            for patch in patches:
                try:
                    clipped = patch.clip(normal=slice_normal, origin=slice_origin)
                    if clipped.n_points > 0:
                        clipped_patches.append(clipped)
                except:
                    # Skip patches that can't be clipped
                    pass

            if clipped_patches:
                patches = clipped_patches
            else:
                print("Warning: No valid clips created - using original patches")

# Set up color map
        cmap = kwargs.pop('cmap', color_palette)
        if cmap in self.COLOR_PALETTES:
            cmap = self.COLOR_PALETTES[cmap]

        # Add all patches to plotter
        for patch in patches:
            if field_name and field_name in patch.array_names:
                plotter.add_mesh(
                    patch,
                    scalars=field_name,
                    show_edges=show_edges,
                    edge_color=edge_color,
                    opacity=opacity,
                    cmap=cmap,
                    **kwargs
                )
            else:
                plotter.add_mesh(
                    patch,
                    show_edges=show_edges,
                    edge_color=edge_color,
                    opacity=opacity,
                    **kwargs
                )

        # Add time information to title
        current_time = data._get_attrs().get('time', time if time is not None else self.latest_time)
        plotter.add_text(f'Time: {current_time}s', position='upper_edge')

        return plotter


# Convenience functions for easy access
def plot_openfoam_line_sample(case_path: Union[str, Path], sample_name: str,
                             field_name: Optional[str] = None, time: Optional[float] = None,
                             ax=None, force_reload: bool = False, **kwargs):
    """
    Convenience function to plot a line sample from OpenFOAM case.

    Parameters:
        case_path: Path to the OpenFOAM case directory
        sample_name: Name of the line sample
        field_name: Name of the field to plot (if None, attempts to plot all fields)
        time: Time to plot (default is latest time)
        ax: Matplotlib axis to plot on (creates new if None)
        force_reload: Force reloading data from disk even if cached
        **kwargs: Additional arguments passed to matplotlib plot

    Returns:
        Matplotlib axis object
    """
    visualizer = OpenFOAMVisualizer(case_path)
    return visualizer.plot_line_sample(sample_name, field_name, time, ax, force_reload, **kwargs)

def plot_openfoam_slice(case_path: Union[str, Path], slice_name: str,
                       field_name: Optional[str] = None, vector_field: Optional[str] = None,
                       time: Optional[float] = None, plotter=None, force_reload: bool = False, **kwargs):
    """
    Convenience function to plot a slice from OpenFOAM case.

    Parameters:
        case_path: Path to the OpenFOAM case directory
        slice_name: Name of the slice
        field_name: Name of the scalar field to plot (if None, uses first available)
        vector_field: Name of the vector field to plot as arrows
        time: Time to plot (default is latest time)
        plotter: PyVista plotter to use (creates new if None)
        force_reload: Force reloading data from disk even if cached
        **kwargs: Additional arguments passed to PyVista

    Returns:
        PyVista plotter object
    """
    visualizer = OpenFOAMVisualizer(case_path)
    return visualizer.plot_slice(slice_name, field_name, vector_field, time, plotter, force_reload, **kwargs)

def plot_openfoam_point_sample(case_path: Union[str, Path], sample_name: str,
                              field_names: Optional[List[str]] = None, ax=None,
                              force_reload: bool = False, **kwargs):
    """
    Convenience function to plot a point sample over time from OpenFOAM case.

    Parameters:
        case_path: Path to the OpenFOAM case directory
        sample_name: Name of the point sample
        field_names: List of field names to plot (if None, attempts to plot all fields)
        ax: Matplotlib axis to plot on (creates new if None)
        force_reload: Force reloading data from disk even if cached
        **kwargs: Additional arguments passed to matplotlib plot

    Returns:
        Matplotlib axis object
    """
    visualizer = OpenFOAMVisualizer(case_path)
    return visualizer.plot_point_sample(sample_name, field_names, ax, force_reload, **kwargs)

def visualize_openfoam_mesh(case_path: Union[str, Path], time: Optional[float] = None,
                          show_edges: bool = True, color: Optional[str] = None,
                          style: str = 'surface', color_patches: bool = False,
                          show_boundaries: bool = True, only_boundaries: bool = False,
                          opacity: float = 1.0, edge_color: str = 'black',
                          boundary_palette: str = 'plasma', force_reload: bool = False,
                          plotter=None, **kwargs):
    """
    Convenience function to visualize the mesh geometry from an OpenFOAM case.

    Parameters:
        case_path: Path to the OpenFOAM case directory
        time: Time to visualize (default is latest time)
        show_edges: Whether to show mesh edges
        color: Color for the mesh (if None and color_patches is False, uses a default color)
        style: Visualization style ('surface', 'wireframe', or 'points')
        color_patches: Whether to color each patch differently
        show_boundaries: Whether to show boundary patches
        only_boundaries: Whether to show only boundary patches (not internal mesh)
        opacity: Opacity of the mesh (0.0-1.0)
        edge_color: Color of mesh edges when show_edges is True
        boundary_palette: Color palette to use when color_patches is True
        force_reload: Force reloading data from disk even if cached
        plotter: PyVista plotter to use (creates new if None)
        **kwargs: Additional arguments passed to PyVista

    Returns:
        PyVista plotter object
    """
    visualizer = OpenFOAMVisualizer(case_path)
    return visualizer.visualize_mesh(
        time=time,
        plotter=plotter,
        show_edges=show_edges,
        color=color,
        style=style,
        color_patches=color_patches,
        show_boundaries=show_boundaries,
        only_boundaries=only_boundaries,
        opacity=opacity,
        edge_color=edge_color,
        boundary_palette=boundary_palette,
        force_reload=force_reload,
        **kwargs
    )

def visualize_openfoam_3d(case_path: Union[str, Path], field_name: Optional[str] = None,
                         time: Optional[float] = None, clip_plane: bool = False,
                         slice_origin: Optional[List[float]] = None,
                         slice_normal: Optional[List[float]] = None,
                         show_edges: bool = False, edge_color: str = 'black',
                         color_palette: str = 'plasma', opacity: float = 1.0,
                         force_reload: bool = False, plotter=None, **kwargs):
    """
    Convenience function to create a 3D visualization of an OpenFOAM case.

    Parameters:
        case_path: Path to the OpenFOAM case directory
        field_name: Name of the field to visualize
        time: Time to visualize (default is latest time)
        clip_plane: Whether to add a clip plane
        slice_origin: Origin point for slicing plane [x,y,z]
        slice_normal: Normal vector for slicing plane [nx,ny,nz]
        show_edges: Whether to show mesh edges
        edge_color: Color of mesh edges when show_edges is True
        color_palette: Color palette to use for the scalar field
        opacity: Opacity of the mesh (0.0-1.0)
        force_reload: Force reloading data from disk even if cached
        plotter: PyVista plotter to use (creates new if None)
        **kwargs: Additional arguments passed to PyVista

    Returns:
        PyVista plotter object
    """
    visualizer = OpenFOAMVisualizer(case_path)
    return visualizer.visualize_3d(
        field_name=field_name,
        time=time,
        clip_plane=clip_plane,
        slice_origin=slice_origin,
        slice_normal=slice_normal,
        plotter=plotter,
        show_edges=show_edges,
        edge_color=edge_color,
        color_palette=color_palette,
        opacity=opacity,
        force_reload=force_reload,
        **kwargs
    )

def refresh_openfoam_case(case_path: Union[str, Path]) -> OpenFOAMVisualizer:
    """
    Refresh an OpenFOAM case by clearing caches and rereading data.

    Parameters:
        case_path: Path to the OpenFOAM case directory

    Returns:
        Updated OpenFOAMVisualizer instance
    """
    visualizer = OpenFOAMVisualizer(case_path)
    return visualizer.refresh()
