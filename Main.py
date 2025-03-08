import streamlit as st
from state import *

st.set_page_config(
    page_title="Simulation Workflow",
    page_icon="🚀",  # Optional: Add a nice icon
    layout="wide",   # Use the full width of the page (optional, but often better)
)

initialize_state()  # Call the initialization function


pages = [
    st.Page("thePages/1_Case_Selection.py", title="Case Selection", icon=":material/folder:", default=True),
    st.Page("thePages/2_Mesh.py", title="Mesh", icon=":material/grid_4x4:"),
    st.Page("thePages/3_Solver_Settings.py", title="Solver", icon=":material/settings:"),
    st.Page("thePages/4_Materials.py", title="Materials", icon=":material/science:"),
    st.Page("thePages/5_Physical_Conditions.py", title="Physical Conditions", icon=":material/thermostat:"),
    st.Page("thePages/6_Boundary_Conditions.py", title="Boundary Conditions", icon=":material/border_all:"),
    st.Page("thePages/7_Initial_Conditions.py", title="Initial Conditions", icon=":material/looks_one:"),
    st.Page("thePages/8_Run_Simulation.py", title="Run", icon=":material/directions_run:"),
    st.Page("thePages/9_Post_Processing.py", title="Post Process", icon=":material/search:"),
    st.Page("thePages/10_Debug.py", title="Debug", icon=":material/question_mark:")
]

nav = st.navigation(
    {
        "Navigation": pages,
    }
)




#nav.title = "Navigation"
nav.run()


st.sidebar.divider()
case_details = st.sidebar.container(border = True)
case_details.header("Case Details:")
with case_details:
    col1, col2 = st.columns(2,gap="small")
    if get_selected_case_name() is not None:
        col1.write("Name:")
        col2.write(get_selected_case_name())
        if has_mesh():
            col1.write("Mesh:")
            col2.write("loaded")
            if get_solver_type() is not None:
                col1.write("Solver:")
                col2.write(get_solver_type())
                if get_solver_type() in ["Groundwater", "Coupled"] and get_case_data()["Solver"]["unsaturated"]:
                    col2.write("unsaturated")
                else:
                    col2.write("saturated")
            else:
                st.write("No solver selected!")
        else:
            st.write("Case has no mesh!")
    else:
        st.write("No Case selected!")
