import streamlit as st
from alpha_runtime import collect_missing_paths
from state import *
from render_inputs import *

st.title("Physical Conditions")

case_dir = get_selected_case_path()

if case_dir is None:
    st.warning("Please select a case directory first.")
elif not case_dir.exists(): #Better safe than sorry
    st.warning("Case does not exist. Please try Case Selection again.")
else:
    missing_paths = collect_missing_paths(case_dir, ["physicsProperties", "gSolid", "gGroundwater", "poroHydraulicProperties"])
    if missing_paths:
        st.error("This case is missing required physical-condition files:")
        st.code("\n".join(str(path) for path in missing_paths), language="text")
    else:
        st.caption(f"Save paths: {case_dir / 'constant/solid/g'}, {case_dir / 'constant/poroFluid/g'}")
        st.caption(f"Hydraulic reference path: {case_dir / 'constant/poroFluid/poroHydraulicProperties'}")
        with st.form("Physical Properties"):
            gDictSolid = get_file("gSolid").as_dict()
            gDictGroundwater = get_file("gGroundwater").as_dict()
            hrefDict = get_file("poroHydraulicProperties")

            if get_solver_type() in ["Mechanics","Coupled"]:

                st.write("Gravity Mechanics")
                current_g = tuple(gDictSolid["value"])
                gDictSolid["value"] = list(render_input_element("g",current_g,key_prefix="solid"))

            if get_solver_type() in ["Groundwater","Coupled"]:

                st.write("Gravity Groundwater")
                current_g = tuple(gDictGroundwater["value"])
                gDictGroundwater["value"] = list(render_input_element("g",current_g,key_prefix="groundwater"))
                current_href = hrefDict["href"].value
                hrefDict["href"].value = render_input_element("Reference Watertable",current_href)

            if st.form_submit_button("Save Physical Properties", type="primary"):
                with (
                    get_file("gSolid") as gSolid,
                    get_file("gGroundwater") as gGroundwater,
                    get_file("poroHydraulicProperties") as hRef
                ):
                    gSolid.update(gDictSolid)
                    gGroundwater.update(gDictGroundwater)
                    hRef.update(hrefDict)
                    save_state(case_dir)
                    st.success("Updated Physical Properties")
