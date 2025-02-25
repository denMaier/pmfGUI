import streamlit as st
import os
from dataclasses import dataclass
from typing import Dict, List
from pathlib import Path
from foamlib import FoamCase
from models.mechanical_law import MechanicalLaw, Parameter, MECHANICAL_LAWS
import re
from state import get_selected_case, get_case_data, get_case, get_path

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

def entry_mechanical(foamCase: FoamCase):
    """Handle the Materials stage of the workflow"""
                  
    cell_zones = get_case_data()["Mesh"]["cellZones"]
    
    if cell_zones:
        st.success(f"Found {len(cell_zones)} cell zones")
        
        tabs = st.tabs(cell_zones)
        
        for tab, zone_name in zip(tabs, cell_zones):
            with tab:
                
                zone_data = get_case_data()["Mesh"]["cellZones"][zone_name]
                
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
        
        if st.button("Generate Material Properties"):
            content = generate_material_properties(get_case_data()["Mesh"]["cellZones"])
            st.text("Preview of materialProperties:")
            st.code(content)
            if st.button("Save Material Properties"):
                foamCase = get_case()
                mechanicalProperties = foamCase.file(get_path("Materials","mechanicalProperties"))
                mechanicalProperties["mechanical"] = content
                st.success(f"Saved materialProperties to {Path(mechanicalProperties)}")
