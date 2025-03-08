from panel.io.server import get_server
import streamlit as st
from foamlib import FoamCase, FoamFile
from pathlib import Path
from state import *
from render_inputs import render_input_element
import os
import pandas as pd



def show_settings(file: FoamFile):
    with Path(file).open() as f:
        st.code(f.open(),language="cpp")

def main():
    current_solver_type = get_solver_type()
    if current_solver_type is not None:

        current_solver_index = list(SOLVER_OPTIONS.keys()).index(current_solver_type)
        selected_solver = st.selectbox("Select Solver:", list(SOLVER_OPTIONS.keys()),
                                    index=current_solver_index)

        if st.button("Select Solver"):
            set_solver_type(selected_solver)
            save_state(Path(get_selected_case_path()))
            st.rerun()

        st.subheader(f"Selected: {get_solver_type()}")
        set_solver_type_settings()

@st.fragment
def set_solver_type_settings():
    case_data = get_case_data()
    selected_solver = get_solver_type()
    with (
        st.form("Solver Settings")
    ):

        fvSolutionDict = get_case().fv_solution.as_dict()
        fvSchemesDict = get_case().fv_schemes.as_dict()
        poroCouplingDict = get_file('poroCouplingProperties').as_dict()
        poroFluidDict = get_file("poroFluidProperties").as_dict()
        solidDict = get_file('solidProperties').as_dict()

        tabNames = ["Linear Solvers","Schemes"] + SOLVER_OPTIONS[selected_solver]["tabs"]
        tabs = st.tabs(tabNames)

        with (
            tabs[0] #fvSolutionDict
        ):
            st.subheader("Relaxation")
            for field in SOLVER_OPTIONS[selected_solver]["fields"]:
                fvSolutionDict["relaxationFactors"][field] = st.slider(
                    field,min_value=0.0,
                    max_value=1.2,
                    step=0.01,
                    value=fvSolutionDict["relaxationFactors"][field]
                    )
        with (
            tabs[1] # fvSchemesDict
        ):
            st.subheader("Time")
            if selected_solver in ["Groundwater","Coupled"]:
                ddt_options = ["steadyState", "Euler", "CrankNicolson 0.9", "backward"]
                fvSchemesDict["ddtSchemes"]["default"] = st.selectbox("default", ddt_options, index=ddt_options.index(fvSchemesDict["ddtSchemes"]["default"]))
            if selected_solver in ["Mechanics,Coupled"]:
                if st.toggle("Dynamic Calculation"):
                    st.write("At the moment no dynamic calculations in the GUI, please edit end run the case manually.")

        if selected_solver in ["Mechanics","Coupled"]:
            with (
                tabs[tabNames.index("Mechanics")]
            ):
                solid_dict = solidDict["linearGeometryTotalDisplacementCoeffs"]
                for key, value in solid_dict.items():
                    new_value = render_input_element(key,value)
                    solidDict["linearGeometryTotalDisplacementCoeffs"][key] = new_value

        if selected_solver in ["Groundwater","Coupled"]:
            with (
                tabs[tabNames.index("Hydraulics")]
            ):
                fluidModelFromDict = poroFluidDict["poroFluidModel"]
                fluidModelIndex = list(POROFLUIDMODEL_TYPES.values()).index(str(fluidModelFromDict))
                fluidmodel = st.selectbox("Model",list(POROFLUIDMODEL_TYPES.keys()),index=fluidModelIndex)
                fluidmodel = POROFLUIDMODEL_TYPES[fluidmodel]
                poroFluidDict["poroFluidModel"] = fluidmodel
                coeffsDict = poroFluidDict[f"{fluidmodel}Coeffs"]
                current_iterations = int(coeffsDict["iterations"])
                poroFluidDict[f"{fluidmodel}Coeffs"]["iterations"] = st.number_input(
                    "iterations",
                    value=current_iterations,
                    min_value=1,
                    step=1
                )
                if fluidmodel=="varSatPoroFluid":
                    algo_options = ["standard","Casulli","LScheme","Celia"]
                    algo_index = algo_options.index(coeffsDict["solutionAlgorithm"])
                    poroFluidDict[fluidmodel+"Coeffs"]["solutionAlgorithm"] = st.selectbox(
                        "Algorithm",
                        algo_options,
                        index=algo_index
                    )
                st.write("Convergence Criteria")
                convergence = makeConvergence(coeffsDict["convergence"])
                poroFluidDict[f"{fluidmodel}Coeffs"]["convergence"] = {}
                for key, value in convergence.items():
                    new_value = str(value[0])+" "+str(value[1])
                    poroFluidDict[f"{fluidmodel}Coeffs"]["convergence"][key] = new_value

        if selected_solver == "Coupled":
            with (
                tabs[tabNames.index("Coupling")]
            ):
                poroSolidInterface = "poroSolid" if poroFluidDict["poroFluidModel"] == "poroFluid" else "varSatPoroSolid"
                poroCouplingDict["poroSolidInterface"] = poroSolidInterface
                coeffsDict = poroCouplingDict[f"{poroSolidInterface}Coeffs"]
                current_iterations = int(coeffsDict["iterations"])
                poroCouplingDict[f"{poroSolidInterface}Coeffs"]["iterations"] = st.number_input(
                    "iterations",
                    value=current_iterations,
                    min_value=1,
                    step=1
                )
                st.write("Convergence Criteria")
                convergence = makeConvergence(coeffsDict["convergence"])
                for key, value in convergence.items():
                    new_value = str(value[0])+" "+str(value[1])
                    poroCouplingDict[f"{poroSolidInterface}Coeffs"]["convergence"][key] = new_value

        if st.form_submit_button("Save Solver Settings"):

            with(
                get_case().fv_schemes as fvSchemes,
                get_case().fv_schemes as fvSolution,
                get_file('poroCouplingProperties') as poroCouplingProperties,
                get_file("poroFluidProperties") as poroFluidProperties,
                get_file('solidProperties') as solidProperties
            ):
                fvSchemes.update(fvSchemesDict)
                fvSolution.update(fvSolutionDict)
                poroCouplingProperties.update(poroCouplingDict)
                poroFluidProperties.update(poroFluidDict)
                solidProperties.update(solidDict)

            save_state(get_selected_case_path())
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
