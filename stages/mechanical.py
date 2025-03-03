import streamlit as st
from typing import Dict
from pathlib import Path
from foamlib import FoamCase
from models.mechanical_law import  MECHANICAL_LAWS
from state import *


def main_mechanical(foamCase: FoamCase):
    """Handle the Materials stage of the workflow"""

    cell_zones = get_case_data()["Mesh"]["cellZones"]

    if not cell_zones:
        st.warning("No cellZones found, at least one has to be present!")

    else:
        with st.form("mechanical_form"):

            st.success(f"Found {len(cell_zones)} cell zones")

            tabs = st.tabs(cell_zones)

            for tab, zone_name in zip(tabs, cell_zones):
                with tab:

                    zone_data = get_case_data()["Mesh"]["cellZones"][zone_name]

                    if zone_data["type"] not in list(MECHANICAL_LAWS.keys()):
                        zone_data["type"] = "linearElasticity"

                    law_type = st.selectbox(
                        "Mechanical Law",
                        options=list(MECHANICAL_LAWS.keys()),
                        key=f"law_{zone_name}",
                        index=list(MECHANICAL_LAWS.keys()).index(zone_data["type"])
                    )

                    if law_type != zone_data["type"]:
                        zone_data["type"] = law_type
                        zone_data["parameters"] = {}

                    st.subheader("Parameters")
                    law = MECHANICAL_LAWS[law_type]

                    for param_name, param in law.parameters.items():
                        current_value = zone_data["parameters"].get(param_name, param.default_value)
                        value = st.number_input(
                            f"{param_name} ({param.description})",
                            value=float(current_value),
                            help=f"Dimensions: {param.dimensions}",
                            key=f"{zone_name}_{param_name}"
                        )
                        zone_data["parameters"][param_name] = value

                if st.form_submit_button("Generate Material Properties"):
                    content = generate_material_properties(get_case_data()["Mesh"]["cellZones"])
                    mechanicalProperties = Path(get_case_data()["Files"]['mechanicalProperties'])
                    mechanicalProperties = content
                    st.success(f"Saved materialProperties to {mechanicalProperties}")



def generate_material_properties(cell_zones: Dict[str, Dict]) -> str:
    """Generate materialProperties file content"""
    content = ["("]

    for zone_name, zone_data in cell_zones.items():
        content.append(f"{zone_name}")
        content.append("\t{")
        content.append(f'\t\ttype      {zone_data["type"]};')

        for param_name, param_value in zone_data["parameters"].items():
            law = MECHANICAL_LAWS[zone_data["type"]]
            param = law.parameters[param_name]
            content.append(f"\t\t{param_name} {param.dimensions} {param_value};")

        content.append("\t}")

    content.append(")")
    return "\n".join(content)
