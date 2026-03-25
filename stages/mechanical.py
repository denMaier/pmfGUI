import streamlit as st
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

    rho_description = "Density (Fully Saturated)" if coupled else "Density (total with water weight)"

    if not cell_zones:
        st.warning("No cellZones found, at least one has to be present!")

    else:
        with st.form("mechanical_form"):

            st.success(f"Found {len(cell_zones)} cell zones")

            zone_names = list(cell_zones.keys())
            tabs = st.tabs(zone_names)

            for tab, zone_name in zip(tabs, zone_names):
                with tab:
                    zone_toggles = {}
                    zone_data1 = mechanicalDict.get(zone_name, {}).copy()
                    existing_law = zone_data1.get("effectiveStressMechanicalLaw", zone_data1)
                    zone_data2 = existing_law.copy() if isinstance(existing_law, dict) else {}

                    current_value = bool(zone_data1.get("effectiveStressMechanicalLaw",coupled))

                    if coupled:
                        zone_toggles["drained"] = st.toggle("Drained",value=not current_value,key=f"drained_{zone_name}")
                    else:
                        zone_toggles["readPressureFromDisk"] = st.toggle("flowForce",value=current_value,key=f"flowForce_{zone_name}")

                    if coupled or zone_toggles["readPressureFromDisk"]:
                        zone_data1["type"] = "poroMechanicalLaw2"
                        zone_data1["buoyancy"] = st.toggle(
                            "buoyancy",
                            value=bool(zone_data1.get("buoyancy", True)),
                            key=f"buoyancy_{zone_name}"
                        )
                        st.write("Note: You can disable buoyancy and use buoyant density instead")
                        if is_unsaturated():
                            zone_data1["type"] = "varSatPoroMechanicalLaw"
                            stress_model_options = ["suctionCutOff","terzaghi","bishop","uniform"]
                            current_stress_model = zone_data1.get("effectiveStressModel", "bishop")
                            zone_data1["effectiveStressModel"] = st.segmented_control(
                                "Effektive Stress Definition",
                                options=stress_model_options,
                                default=current_stress_model if current_stress_model in stress_model_options else "bishop",
                                key=f"effStress_{zone_name}"
                            )
                        if zone_toggles["readPressureFromDisk"]:
                             current_n = zone_data1.get("n")
                             current_n_value = getattr(current_n, "value", 0.3)
                             n = st.number_input(
                                    label="Hydr. Porosity",
                                    value=current_n_value,
                                    help=f"Dimensions: [0 0 0 0 0 0 0]",
                                    key=f"{zone_name}_n"
                                )
                             zone_data1["n"] = FoamFile.Dimensioned(name="n",dimensions=[0,0,0,0,0,0,0],value=n)

                    current_rho = zone_data1.get("rho")
                    rho_value = getattr(current_rho, "value", 2000)
                    rho_dimensioned = FoamFile.Dimensioned(
                        name="rho",
                        dimensions=[1, -3, 0, 0, 0, 0, 0],
                        value=st.number_input(
                        label=rho_description,
                        value=rho_value,
                        help=f"Dimensions: {[1, -3, 0, 0, 0, 0, 0]}",
                        key=f"{zone_name}_rho"
                        )
                    )
                    zone_data1["rho"] = rho_dimensioned

                    default_law_type = zone_data2.get("type", "linearElasticity")
                    if default_law_type not in MECHANICAL_LAWS:
                        default_law_type = "linearElasticity"

                    law_type = st.selectbox(
                        "Mechanical Law",
                        options=list(MECHANICAL_LAWS.keys()),
                        key=f"law_{zone_name}",
                        index=list(MECHANICAL_LAWS.keys()).index(default_law_type)
                    )
                    zone_data2["type"] = law_type

                    st.subheader("Parameters")
                    law = MECHANICAL_LAWS[law_type]

                    for toggle_name, toggle in law.toggles.items():
                            zone_data2[toggle_name] = st.toggle(
                                f"{toggle_name} ({toggle.description})",
                                value=bool(zone_data2.get(toggle_name, toggle.default_value)),
                                key=f"{zone_name}_{toggle_name}"
                            )

                    for param_name, param in law.parameters.items():
                        if isinstance(param.Dimensioned.value,float):
                            current_param = zone_data2.get(param_name, param.Dimensioned.value)
                            current_param_value = getattr(current_param, "value", current_param)
                            value = st.number_input(
                                f"{param_name} ({param.description})",
                                value=float(current_param_value),
                                help=f"Dimensions: {param.Dimensioned.dimensions}",
                                key=f"{zone_name}_{param_name}"
                            )
                            zone_data2[param_name] = value
                        else:
                            st.error(f"Parameter {param_name} in the mechanicalLaw is not a float, other types are not yet supported")

                    if coupled or zone_toggles["readPressureFromDisk"]:
                        zone_data1["effectiveStressMechanicalLaw"] = zone_data2
                    else:
                        # In uncoupled mode the constitutive law lives directly on the zone.
                        zone_data1.pop("effectiveStressMechanicalLaw", None)
                        zone_data1.pop("effectiveStressModel", None)
                        zone_data1.pop("buoyancy", None)
                        zone_data1.pop("n", None)
                        zone_data1.update(zone_data2)

                    mechanicalDict[zone_name] = zone_data1


                if st.form_submit_button("Generate Material Properties"):
                    content = generate_material_properties(mechanicalDict)
                    with get_file('mechanicalProperties') as mechanicalProperties:
                        mechanicalProperties["mechanical"] = content
                        save_state(get_selected_case_path())
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
