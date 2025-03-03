from panel.io.server import get_server
import streamlit as st
from foamlib import FoamCase, FoamFile
from pathlib import Path
from state import *
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
    "None": "Mechanics" # Default
}

poroFluidModelTypes = {
    "saturated": "poroFluid",
    "unsaturated":"varSatPoroFluid"
}

def get_solver_state_from_case(case_dir: str):
    case_data = get_case_data()
    solver_type = case_data["Files"]["physicsProperties"]["type"]
    set_solver_type(solver_type_map[solver_type])
    if get_solver_type() in ["Groundwater","Coupled"]:
        if Path(case_data["Files"]["poroFluidProperties"]).exists():
            if case_data["Files"]["poroFluidProperties"] == "varSatPoroFluid":
                case_data['Solver']["unsaturated"] = True

def show_settings(file: FoamFile):
    with Path(file).open() as f:
        st.code(f.open(),language="cpp")

def main():
    case_data = get_case_data()
    with case_data["Files"]["physicsProperties"] as physicsProperties:
        if get_solver_type() is None:
            selected_solver = st.selectbox("Select Solver:", list(solver_options.keys()))  # Use keys() for clarity
        else:
            selected_solver = st.selectbox("Select Solver:", list(solver_options.keys()),
                                        index=list(solver_options.keys()).index(get_solver_type()))
        if st.button("Select Solver"):
            physicsProperties.type = solver_options.selected_solver.type
            set_solver_type(selected_solver)
            st.rerun()
    if get_solver_type() is not None:
        st.subheader("Selected: " + get_solver_type())
        set_solver_type_settings()

@st.fragment
def set_solver_type_settings():
    case_data = get_case_data()
    selected_solver = get_solver_type()
    with (
        case_data["Files"]['fvSchemes'] as fvSchemes,
        case_data["Files"]['fvSolution'] as fvSolution,
        case_data["Files"]['poroCouplingProperties'] as poroCouplingProperties,
        case_data["Files"]["poroFluidProperties"] as poroFluidProperties,
        case_data["Files"]['solidProperties'] as solidProperties,
        st.form("Solver Settings")
    ):

        tabNames = ["Linear Solvers","Schemes"] + solver_options[selected_solver]["tabs"]
        tabs = st.tabs(tabNames)

        with (
            tabs[0] #fvSolution
        ):
            st.subheader("Relaxation")
            for field in solver_options[selected_solver]["fields"]:
                fvSolution["relaxationFactors"][field] = st.slider(
                    field,min_value=0.0,
                    max_value=1.2,
                    step=0.01,
                    value=fvSolution["relaxationFactors"].as_dict()[field]
                    )
        with (
            tabs[1] # fvSchemes
        ):
            st.subheader("Time")
            if selected_solver in ["Groundwater","Coupled"]:
                ddt_options = ["steadyState", "Euler", "CrankNicolson 0.9", "backward"]
                fvSchemes["ddtSchemes"]["default"] = st.selectbox("default", ddt_options, index=ddt_options.index(fvSchemes["ddtSchemes"]["default"]))
            if selected_solver in ["Mechanics,Coupled"]:
                if st.toggle("Dynamic Calculation"):
                    st.write("At the moment no dynamic calculations in the GUI, please edit end run the case manually.")

        if selected_solver in ["Mechanics","Coupled"]:
            with (
                tabs[tabNames.index("Mechanics")]
            ):
                solid_dict = solidProperties["linearGeometryTotalDisplacementCoeffs"]
                for key, value in solid_dict.items():
                    new_value = render_input_element(key,value)
                    solidProperties["linearGeometryTotalDisplacementCoeffs"][key] = new_value

        if selected_solver in ["Groundwater","Coupled"]:
            with (
                tabs[tabNames.index("Hydraulics")]
            ):
                fluidmodel = st.selectbox("Model",list(poroFluidModelTypes.keys()),index=list(poroFluidModelTypes.values()).index(poroFluidProperties["poroFluidModel"]))
                fluidmodel = poroFluidModelTypes[fluidmodel]
                poroFluidProperties["poroFluidModel"] = fluidmodel
                coeffsDict = poroFluidProperties[f"{fluidmodel}Coeffs"]
                poroFluidProperties[f"{fluidmodel}Coeffs"]["iterations"] = st.number_input("iterations",0, value=coeffsDict["iterations"], step=1)
                algo_options = ["standard","Casulli","LScheme","Celia"]
                if fluidmodel=="varSatPoroFluid":
                    poroFluidProperties[fluidmodel+"Coeffs"]["solutionAlgorithm"] = st.selectbox(
                        "Algorithm",
                        algo_options,
                        index=algo_options.index(coeffsDict["solutionAlgorithm"])
                        )
                st.write("Convergence Criteria")
                convergence = makeConvergence(coeffsDict["convergence"].as_dict())
                poroFluidProperties[f"{fluidmodel}Coeffs"]["convergence"] = {}
                for key, value in convergence.items():
                    new_value = str(value[0])+" "+str(value[1])
                    poroFluidProperties[f"{fluidmodel}Coeffs"]["convergence"][key] = new_value

        if selected_solver == "Coupled":
            with (
                tabs[tabNames.index("Coupling")]
            ):
                poroSolidInterface = "poroSolid" if poroFluidProperties["poroFluidModel"] == "poroFluid" else "varSatPoroSolid"
                poroCouplingProperties["poroSolidInterface"] = poroSolidInterface
                coeffsDict = poroCouplingProperties[f"{poroSolidInterface}Coeffs"]
                poroCouplingProperties[f"{poroSolidInterface}Coeffs"]["iterations"] = st.number_input("iterations",0, value=coeffsDict["iterations"], step=1)
                st.write("Convergence Criteria")
                convergence = makeConvergence(coeffsDict["convergence"].as_dict())
                for key, value in convergence.items():
                    new_value = str(value[0])+" "+str(value[1])
                    poroCouplingProperties[f"{poroSolidInterface}Coeffs"]["convergence"][key] = new_value

        if st.form_submit_button("Save Solver Settings"):
                st.success("Solver settings saved.")


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
