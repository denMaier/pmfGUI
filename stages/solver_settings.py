import streamlit as st
from foamlib import FoamCase
from foamlib import FoamFile
from pathlib import Path
#from solvers.solver import MechanicalLaw, Parameter, MECHANICAL_LAWS
from state import get_case, get_selected_case, set_solver_type, get_solver_type, get_case_data, get_path
from render_inputs import render_input_element
import os 
import pandas as pd

solver_options = {
    "Mechanics": {
        "type": "solid",
        "tabs": ["Mechanics"],
        "fields": ["D"]
    },
    "Groundwater": {
        "type": "poroFluid",
        "tabs": ["Hydraulics"],
        "fields": ["p_rgh"]
    },
    "Coupled": {
        "type": "poroSolid",
        "tabs": ["Coupling","Mechanics","Hydraulics"],
        "fields": ["D","p_rgh"]
    }
}

solver_type_map = {
    "solid": "Mechanics",
    "poroFluid": "Groundwater",
    "poroSolid": "Coupled",
    "": None
}

def show_settings(file: FoamFile):
    with Path(file).open() as f:
        st.code(f.open(),language="cpp")

def entry():
    foamcase = get_case()
    physicsProperties = get_case_data()["Solver"]["physicsProperties"]
    selected_solver = getSolver()
    if st.button("Select Solver"):
        set_solver_type(selected_solver)
        physicsProperties["type"] = solver_options[selected_solver]["type"] # Moved inside set_solver_type
        st.rerun()
    if get_solver_type() is not None:
        st.subheader("Selected: " + get_solver_type())
        set_solver_type_settings(foamcase, get_solver_type())

def getSolver():
    if get_solver_type() is None:
        selected_solver = st.selectbox("Select Solver:", list(solver_options.keys()))  # Use keys() for clarity
    else:
        selected_solver = st.selectbox("Select Solver:", list(solver_options.keys()),
                                    index=list(solver_options.keys()).index(get_solver_type()))
    return selected_solver
        
def get_solver_state_from_case():
    foamcase = get_case()
    get_case_data()["Solver"]["physicsProperties"] = foamcase.file(get_path("Solver","physicsProperties"))
    solver_type = get_case_data()["Solver"]["physicsProperties"]["type"]
    set_solver_type(solver_type_map[solver_type])
    
    if get_solver_type() in ["Mechanics","Coupled"]:
        if os.path.exists(get_path("Solver","solidProperties")):
            get_case_data()["Solver"]["solidProperties"] = foamcase.file(get_path("Solver","solidProperties"))
    if get_solver_type() in ["Groundwater","Coupled"]:
        if os.path.exists(get_path("Solver","poroFluidProperties")):
            get_case_data()["Solver"]["poroFluidProperties"] = foamcase.file(get_path("Solver","poroFluidProperties"))
    if get_solver_type() == "Coupled":
        if os.path.exists(get_path("Solver","poroCouplingProperties")):
            get_case_data()["Solver"]["poroCouplingProperties"] = foamcase.file(get_path("Solver","poroCouplingProperties"))

@st.fragment        
def set_solver_type_settings(foamcase: FoamCase, selected_solver: str):         
        
    with st.form("Solver Settings"):
        
        control_dict = foamcase.control_dict
        fv_schemes = foamcase.fv_schemes
        fv_solution = foamcase.fv_solution
            
        tabNames = ["Linear Solvers","Schemes"] + solver_options[selected_solver]["tabs"]
        tabs = st.tabs(tabNames)
        
        data = {}
        data["fv_solution"] = {}
        data["fv_solution"]["relaxationFactors"] = {}
        data["fv_schemes"] = {}
        data["fv_schemes"]["ddtSchemes"] = {}
        data["solidProperties"] = {}
        data["solidProperties"]["linearGeometryTotalDisplacementCoeffs"] = {}
        data["poroFluidProperties"] = {}
        data["poroCouplingProperties"] = {}
        
        with (
            tabs[0]
        ):
            st.subheader("Relaxation")
            for field in solver_options[selected_solver]["fields"]:
                data["fv_solution"]["relaxationFactors"][field] = st.slider(
                    field,min_value=0.0,
                    max_value=1.2,
                    step=0.01,
                    value=fv_solution["relaxationFactors"].as_dict()[field]
                    )
        with (
            tabs[1]
        ):
            st.subheader("Time")
            if selected_solver in ["Groundwater","Coupled"]:
                ddt_options = ["steadyState", "Euler", "CrankNicolson 0.9", "backward"]
                data["fv_schemes"]["ddtSchemes"]["default"] = st.selectbox("default", ddt_options)
            if selected_solver in ["Mechanics,Coupled"]:
                if st.checkbox("Dynamic Calculation"):
                    st.write("At the moment no dynamic calculations in the GUI, please edit end run the case manually.")

        if selected_solver in ["Mechanics","Coupled"]:
            get_case_data()["Solver"]["solidProperties"] = foamcase.file(get_path("Solver","solidProperties"))
            with (
                tabs[tabNames.index("Mechanics")],
                get_case_data()["Solver"]["solidProperties"] as solidProperties,
            ):
                solid_dict = solidProperties["linearGeometryTotalDisplacementCoeffs"].as_dict()
                for key, value in solid_dict.items():
                    new_value = render_input_element(key,value)
                    data["solidProperties"]["linearGeometryTotalDisplacementCoeffs"][key] = new_value
                
        if selected_solver in ["Groundwater","Coupled"]:
            get_case_data()["Solver"]["poroFluidProperties"] = foamcase.file(get_path("Solver","poroFluidProperties"))
            with (
                tabs[tabNames.index("Hydraulics")],
                get_case_data()["Solver"]["poroFluidProperties"] as poroFluidProperties,
            ):
                fluidmodel = st.selectbox("Model",["saturated","unsaturated"])
                fluidmodel = "poroFluid" if fluidmodel == "saturated" else "varSatPoroFluid"    
                data["poroFluidProperties"]["poroFluidModel"] = fluidmodel
                coeffsDict = poroFluidProperties[fluidmodel+"Coeffs"]
                data["poroFluidProperties"][fluidmodel+"Coeffs"] = {}
                data["poroFluidProperties"][fluidmodel+"Coeffs"]["iterations"] = st.number_input("iterations",0, value=coeffsDict["iterations"], step=1)
                algo_options = ["standard","Casulli","LScheme","Celia"]
                if fluidmodel=="varSatPoroFluid":
                    data["poroFluidProperties"]["poroFluidModel"][coeffsDict]["solutionAlgorithm"] = st.selectbox(
                        "Algorithm",
                        algo_options,
                        index=algo_options.index(coeffsDict["solutionAlgorithm"])
                        )
                st.write("Convergence Criteria")
                convergence = makeConvergence(coeffsDict["convergence"].as_dict())
                data["poroFluidProperties"][fluidmodel+"Coeffs"]["convergence"] = {}
                for key, value in convergence.items():
                    new_value = str(value[0])+" "+str(value[1])
                    data["poroFluidProperties"][fluidmodel+"Coeffs"]["convergence"][key] = new_value
        
        if selected_solver == "Coupled":
            get_case_data()["Solver"]["poroCouplingProperties"] = foamcase.file(get_path("Solver","poroCouplingProperties"))
            with (
                tabs[tabNames.index("Coupling")],
                get_case_data()["Solver"]["poroCouplingProperties"] as poroCouplingProperties,
            ):
                poroSolidInterface = "poroSolid" if data["poroFluidProperties"]["poroFluidModel"] == "poroFluid" else "varSatPoroSolid"    
                data["poroCouplingProperties"]["poroSolidInterface"] = poroSolidInterface
                coeffsDict = poroCouplingProperties[poroSolidInterface+"Coeffs"]
                data["poroCouplingProperties"][poroSolidInterface+"Coeffs"] = {}
                data["poroCouplingProperties"][poroSolidInterface+"Coeffs"]["iterations"] = st.number_input("iterations",0, value=coeffsDict["iterations"], step=1)
                st.write("Convergence Criteria")
                convergence = makeConvergence(coeffsDict["convergence"].as_dict())
                data["poroCouplingProperties"][poroSolidInterface+"Coeffs"]["convergence"] = {}
                for key, value in convergence.items():
                    new_value = str(value[0])+" "+str(value[1])
                    data["poroCouplingProperties"][poroSolidInterface+"Coeffs"]["convergence"][key] = new_value

                
        if st.form_submit_button("Save Solver Settings"):
            try:
                solver_data = get_case_data()["Solver"]

                foamcase.fv_solution.update(data["fv_solution"])
                foamcase.fv_schemes.update(data["fv_schemes"])
                if solver_data["solidProperties"] is not None:
                    solidProperties = solver_data["solidProperties"]
                    solidProperties.update(data["solidProperties"])
                if solver_data["poroFluidProperties"] is not None:
                    poroFluidProperties = solver_data["poroFluidProperties"]
                    poroFluidProperties.update(data["poroFluidProperties"])
                if solver_data["poroCouplingProperties"] is not None:
                    poroCouplingProperties = solver_data["poroCouplingProperties"]
                    poroCouplingProperties.update(data["poroCouplingProperties"])
                st.success("Solver settings saved.")
            except Exception as e:
                print(f"An unexpected error occurred: {e}")    


def makeConvergence(convergence: dict):
    # Initialize session state for the DataFrame
    df = pd.DataFrame.from_dict(convergence,orient='index',columns=["Type","Tolerance"])

    edited_df = st.data_editor(df,num_rows="dynamic",column_config={    # Configure columns for better UX
            "Label": st.column_config.TextColumn("Field", required=True),
            "Type": st.column_config.SelectboxColumn("Type", options=["RMS", "max"], required=True),
            "Tolerance": st.column_config.NumberColumn("Tolerance", min_value=0.0, format="%.3f", required=True) #For both types
        },
        column_order=["Label","Type","Tolerance"],
        use_container_width=True,
        #key="data_editor", #add a key!
    )

    edited_df.columns = [0,1]
    convergence = edited_df.to_dict(orient='index')

    return convergence
