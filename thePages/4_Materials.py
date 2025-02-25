import streamlit as st
from stages.mechanical import entry_mechanical
#from stages.hydraulic import entry_hydraulic
from state import get_selected_case, has_mesh, get_case, get_path, get_solver_type
from pathlib import Path

st.title("Materials")



case_dir = get_selected_case()

if case_dir is None:
    st.warning("Please select a case directory first.")
elif not has_mesh():
    st.warning("Please create a mesh first.")
else:
    foamCase = get_case()
    solver = get_solver_type()
    
    st.write(f"Selected Case Directory: {case_dir}")
    st.write(f"Selected Solver: {solver}")
    
    if solver in ["Mechanics","Coupled"]:    
        with st.expander("Mechanics"):
            col1, col2 = st.columns(2)
            
            with col1:
                entry_mechanical(foamCase)
            with (
                col2,
                foamCase.file(get_path("Materials","mechanicalProperties")) as mechanicalProperties
            ):
                st.header("Current mechanicalProperties")
                with Path(mechanicalProperties).open() as f:
                    st.code(f.read(),language="cpp")
    if solver in ["Groundwater","Coupled"]:
        with st.expander("Hydraulics"):
            col1, col2 = st.columns(2)
            st.write("Under construction")
            #entry_hydraulic()  
