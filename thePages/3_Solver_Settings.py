import streamlit as st
from alpha_runtime import collect_missing_paths
from stages.solver_settings import main
from state import *

st.title("Solver")

case_dir = get_selected_case_path()

if case_dir is None:
    st.warning("Please select a case directory first.")
elif not case_dir.exists(): #Better safe than sorry
    st.warning("Case does not exist. Please try Case Selection again.")
else:
    missing_paths = collect_missing_paths(
        case_dir,
        ["physicsProperties", "fvSolution", "fvSchemes", "solidProperties", "poroFluidProperties", "poroCouplingProperties"],
    )
    if missing_paths:
        st.error("This case is missing required solver files:")
        st.code("\n".join(str(path) for path in missing_paths), language="text")
    else:
        st.caption(f"Case path: {case_dir}")
        st.caption(f"Save paths: {case_dir / 'system/fvSolution'}, {case_dir / 'system/fvSchemes'}")
        st.caption(
            f"Model paths: {case_dir / 'constant/solid/solidProperties'}, "
            f"{case_dir / 'constant/poroFluid/poroFluidProperties'}, "
            f"{case_dir / 'constant/poroCouplingProperties'}"
        )
        main()
