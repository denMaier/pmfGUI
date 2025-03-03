import streamlit as st
from distutils import util
from pathlib import Path
from foamlib import FoamCase
from models.hydraulic_laws import  HYDRAULIC_LAWS
from state import *

def main_hydraulic(foamCase: FoamCase):
    """Handle the Materials stage of the workflow"""
    cell_zones = get_case_data()["Mesh"]["cellZones"]
    if not cell_zones:
        st.warning("No cellZones found, at least one has to be present!")
    else:
        with st.form("hydraulic_form"):
            st.success(f"Found {len(cell_zones)} cell zones")

            tabs = st.tabs(cell_zones)

            law_defaults = {"storageLaw": "storageCoeff"}

            if get_case_data()["Solver"]["unsaturated"]:
                law_defaults["SWCC"] = "saturated"

            for law_type in list(law_defaults.keys()):
                for tab, zone_name in zip(tabs, cell_zones):
                    with tab:

                        if zone_name not in get_case_data()["Files"]['poroHydraulicProperties']:
                            get_case_data()["Files"]['poroHydraulicProperties'][zone_name]={}

                        zone_data = get_case_data()["Files"]['poroHydraulicProperties'][zone_name]

                        if law_type not in zone_data:
                            zone_data[law_type]=law_defaults[law_type]

                        law = st.selectbox(
                            law_type,
                            options=list(HYDRAULIC_LAWS[law_type].keys()),
                            key=f"law_{law_type}_{zone_name}",
                            index=list(HYDRAULIC_LAWS[law_type].keys()).index(zone_data[law_type])
                        )

                        zone_data[law_type] = law

                        st.subheader("Parameters")
                        lawData = HYDRAULIC_LAWS[law_type][law] #Available parameters

                        if f"{law}Coeffs" not in zone_data:
                            zone_data[f"{law}Coeffs"] = {}

                        for param_name, param in lawData.parameters.items():
                            current_value = zone_data[f"{law}Coeffs"].get(param_name, param.default_value)
                            if isinstance(param.default_value, bool):
                                value = st.toggle(
                                    f"{param_name} ({param.description})",
                                    value=util.strtobool(str(current_value)),
                                    help=f"Dimensions: {param.dimensions}",
                                    key=f"{zone_name}_{param_name}"
                                )
                            if isinstance(param.default_value, float):
                                value = st.number_input(
                                    f"{param_name} ({param.description})",
                                    value=float(current_value),
                                    help=f"Dimensions: {param.dimensions}",
                                    key=f"{zone_name}_{param_name}"
                                )
                            elif isinstance(param.default_value, int):
                                value = st.number_input(
                                    f"{param_name} ({param.description})",
                                    value=int(current_value),
                                    help=f"Dimensions: {param.dimensions}",
                                    key=f"{zone_name}_{param_name}"
                                )
                            else:
                                value = st.text_input(
                                    f"{param_name} ({param.description})",
                                    value=str(current_value),
                                    help=f"Dimensions: {param.dimensions}",
                                    key=f"{zone_name}_{param_name}"
                                )

                            zone_data[f"{law}Coeffs"][param_name] = value


            if st.form_submit_button("Save Hydraulic Properties"):
                poroHydraulicProperties = Path(get_case_data()["Files"]['poroHydraulicProperties'])
                st.success(f"Saved materialProperties to {poroHydraulicProperties}")
