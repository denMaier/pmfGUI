import streamlit as st
from state import get_selected_case, get_selected_case_name
from stages.mesh import entry
from plot_with_paraview import plot_foam_mesh

st.title("Mesh")  # Change the title for each page
st.write("This page is under construction.")

if get_selected_case() is None:
    st.warning("Please select a case directory first.")
else:
    col1, col2 = st.columns(2)
    with col1:
        entry()
    with col2:
        #plot_mesh()
        if st.button("Plot mesh"):
            st.write(get_selected_case()+f"/{get_selected_case_name()}.foam")
            plot_foam_mesh(get_selected_case()+f"/{get_selected_case_name()}.foam")