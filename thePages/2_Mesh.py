import streamlit as st
from state import get_selected_case_path, get_case_data, has_mesh
from stages.mesh.mesh import main3D, main2D, plot_foam_mesh
from plotting_helpers import add_visu_sidebar

st.title("Mesh")  # Change the title for each page

if get_selected_case_path() is None:
    st.warning("Please select a case directory first.")
elif not get_selected_case_path().exists(): #Better safe than sorry
    st.warning("Case does not exist. Please try Case Selection again.")
else:

    get_case_data()["Mesh"]["showMeshVis"] = st.toggle(
        "Show Current Mesh",
        value=get_case_data()["Mesh"]["showMeshVis"],
        key= "Show Current Mesh Toggle 3D"
    )
    if get_case_data()["Mesh"]["showMeshVis"]:
        add_visu_sidebar()

    col1, col2 = st.columns(2,gap="medium")

    with col1:
        threeD, twoD = st.tabs(["3D", "2D/1D"])

        with threeD:
            st.subheader("Load a mesh")
            main3D()

        with twoD:
                st.subheader("Load a mesh")
                main2D()

                st.subheader("CellZones")
                st.write("Coming soon")
                st.subheader("Refinements")
                st.write("Coming soon")
                with st.expander("Surface Refinements"):
                    st.write("Coming soon")
                with st.expander("Volume Refinements"):
                    st.write("Coming soon")

    with col2:
        if has_mesh():
            if get_case_data()["Mesh"]["showMeshVis"]:
                st.subheader("Current mesh")
                vis = st.session_state.vis

                # Use our new visualization function
                plot_foam_mesh(
                    get_selected_case_path(),
                    show_mesh=vis["show_mesh"],
                    bg_darkness=vis["bg_darkness"],
                    selected_palette=vis["selected_palette"],
                    style=vis["style"],
                    color_patches=vis["color_patches"],
                    show_boundaries=vis["show_boundaries"],
                    only_boundaries=vis["only_boundaries"],
                    opacity=vis["opacity"]
                )
