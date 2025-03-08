import streamlit as st
from state import *
from render_inputs import *

st.title("Physical Condtions")  # Change the title for each page
st.write("This page is under construction.")

case_dir = get_selected_case_path()

if case_dir is None:
    st.warning("Please select a case directory first.")
elif not case_dir.exists(): #Better safe than sorry
    st.warning("Case does not exist. Please try Case Selection again.")
else:
    with st.form("Physical Properties"):
        gDictSolid = get_file("gSolid").as_dict()
        gDictGroundwater = get_file("gGroundwater").as_dict()
        hrefDict = get_file("poroHydraulicProperties")

        if get_solver_type() in ["Mechanical","Coupled"]:

            st.write("Gravity Mechanics")
            current_g = tuple(gDictSolid["value"])
            gDictSolid["value"] = list(render_input_element("g",current_g,key_prefix="solid"))

        if get_solver_type() in ["Groundwater","Coupled"]:

            st.write("Gravity Groundwater")
            current_g = tuple(gDictGroundwater["value"])
            gDictGroundwater["value"] = list(render_input_element("g",current_g,key_prefix="groundwater"))
            current_href = hrefDict["href"].value
            hrefDict["href"].value = render_input_element("Reference Watertable",current_href)

        if st.form_submit_button("Save Physical Properties"):
            with (
                get_file("gSolid") as gSolid,
                get_file("gGroundwater") as gGroundwater,
                get_file("poroHydraulicProperties") as hRef
            ):
                gSolid.update(gDictSolid)
                gGroundwater.update(gDictGroundwater)
                hRef.update(hrefDict)
                st.success("Updated Physical Properties")
