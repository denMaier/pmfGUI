import streamlit as st
from typing import Dict
from pathlib import Path
from foamlib import FoamCase, FoamFile
from models.mechanical_law import  MECHANICAL_LAWS
from state import *

@st.fragment
def main_mechanical(foamCase: FoamCase):
    """Handle the Materials stage of the workflow"""

    cell_zones = get_cell_zones()

    mechanicalDict = {}
    mechanicalList = get_file("mechanicalProperties").get("mechanical",[])
    for cellZone in mechanicalList:
        cellZoneName, cellZoneDict = cellZone
        mechanicalDict[cellZoneName] = cellZoneDict

    coupled = (get_solver_type() == "Coupled")

    rhoEntry = {"rho": FoamFile.Dimensioned(name="rho",dimensions=[1, -3, 0, 0, 0, 0, 0,], value=2000), "Description": "Density (total with water weight)"}
    if coupled:
        rhoEntry["Description"] = "Density (Fully Saturated)"

    if not cell_zones:
        st.warning("No cellZones found, at least one has to be present!")

    else:
        with st.form("mechanical_form"):

            st.success(f"Found {len(cell_zones)} cell zones")

            tabs = st.tabs(cell_zones)

            for tab, zone_name in zip(tabs, cell_zones):
                with tab:
                    zone_toggles = {}
                    zone_data1 = mechanicalDict.get(zone_name,{})
                    zone_data2 = {}

                    current_value = bool(zone_data1.get("effectiveStressMechanicalLaw",coupled))

                    if coupled:
                        zone_toggles["drained"] = st.toggle("Drained",value=not current_value,key=f"drained_{zone_name}")
                    else:
                        zone_toggles["readPressureFromDisk"] = st.toggle("flowForce",value=current_value,key=f"flowForce_{zone_name}")

                    if coupled or zone_toggles["readPressureFromDisk"]:
                        zone_data1["type"] = "poroMechanicalLaw2"
                        zone_data1["buoyancy"] = st.toggle("buoyancy",value=zone_data1["buoyancy"],key=f"buoyancy_{zone_name}")
                        st.write("Note: You can disable buoyancy and use buoyant density instead")
                        if is_unsaturated():
                            zone_data1["type"] = "varSatPoroMechanicalLaw"
                            zone_data1["effectiveStressModel"] = st.segmented_control(
                                "Effektive Stress Definition",
                                options=["suctionCutOff","terzaghi","bishop","uniform"],
                                default="bishop",
                                key=f"effStress_{zone_name}"
                            )
                        if zone_toggles["readPressureFromDisk"]:
                             n = st.number_input(
                                    label="Hydr. Porosity",
                                    value= 0.3,
                                    help=f"Dimensions: [0 0 0 0 0 0 0]",
                                    key=f"{zone_name}_n"
                                )
                             zone_data1["n"] = FoamFile.Dimensioned(name="n",dimensions=[0,0,0,0,0,0,0],value=n)

                    rhoEntry["rho"].value = st.number_input(
                        label=rhoEntry["Description"],
                        value=rhoEntry["rho"].value,
                        help=f"Dimensions: {rhoEntry['rho'].dimensions}",
                        key=f"{zone_name}_rho"
                    )
                    zone_data1["rho"] = rhoEntry["rho"]

                    zone_data2["type"] = "linearElasticity"

                    law_type = st.selectbox(
                        "Mechanical Law",
                        options=list(MECHANICAL_LAWS.keys()),
                        key=f"law_{zone_name}",
                        index=list(MECHANICAL_LAWS.keys()).index(zone_data2["type"])
                    )
                    zone_data2["type"] = law_type

                    st.subheader("Parameters")
                    law = MECHANICAL_LAWS[law_type]

                    for toggle_name, toggle in law.toggles.items():
                            value = st.toggle(
                                f"{toggle_name} ({toggle.description})",
                                value=toggle.default_value,
                                key=f"{zone_name}_{toggle_name}"
                            )

                    for param_name, param in law.parameters.items():
                        if isinstance(param.Dimensioned.value,float):
                            value = st.number_input(
                                f"{param_name} ({param.description})",
                                value=param.Dimensioned.value,
                                help=f"Dimensions: {param.Dimensioned.dimensions}",
                                key=f"{zone_name}_{param_name}"
                            )
                            zone_data2[param_name] = value
                        else:
                            st.error(f"Parameter {param_name} in the mechanicalLaw is not a float, other types are not yet supported")

                    if coupled or zone_toggles["readPressureFromDisk"]:
                        zone_data1["effectiveStressMechanicalLaw"] = zone_data2
                    else:
                        zone_data1.append(zone_data2)

                    mechanicalDict[zone_name] = zone_data1


                if st.form_submit_button("Generate Material Properties"):
                    content = generate_material_properties(mechanicalDict)
                    with get_file('mechanicalProperties') as mechanicalProperties:
                        mechanicalProperties["mechanical"] = content
                        st.success(f"Saved materialProperties to {mechanicalProperties}")


def generate_material_properties(mechanicalDict: dict) -> list:
    """Generate materialProperties file content"""

    mechanicalList = []
    for zone_name, zone_data in mechanicalDict.items():
        mechanicalList.append(tuple([zone_name,zone_data]))

    return mechanicalList


# def generate_coupled_material_properties(zone_name: str, zone_data: dict, content: list) -> list:
#     """Generate coupled materialProperties file content"""

#         if is_unsaturated():
#             content.append(f'\t\ttype      varSatPoroMechanicalLaw;')
#                             (feffectiveStressModel
#         else:
#             content.append(f'\t\ttype      poroMechanicalLaw2;')

#         for param_name, param_value in zone_data["parameters"].items():
#             law = MECHANICAL_LAWS[zone_data["type"]]
#             param = law.parameters[param_name]
#             content.append(f"\t\t{param_name} {param.dimensions} {param_value};")

#         content.append("\t}")

#     content.append(")")
#     return "\n".join(content)
