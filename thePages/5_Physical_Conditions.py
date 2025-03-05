import streamlit as st
from state import *

st.title("Physical Condtions")  # Change the title for each page
st.write("This page is under construction.")

if case_dir is None:
    st.warning("Please select a case directory first.")
elif not case_dir.exists(): #Better safe than sorry
    st.warning("Case does not exist. Please try Case Selection again.")
else:
    with st.form("Physical Properties"):
        gDict = get_file("g").as_dict()
        hrefDict = get_file("g").as_dict()
        
        st.write("gravity")
        vector = st.columns(3)
        with vector[0]:
            gx = st.number_input("x")
        with vector[1]:
            gy = st.number_input("y")
        with vector[2]:
            gz = st.number_input("z")
         
        gDict["value"] = f"({gx} {gy} {gz})"   
        hrefDict["href"] = st.number_input("hRef")
        
        if st.form_submit_button("Save Physical Properties"):
            with (
                get_file("g") as g,
                get_file("g") as hRef            
            ):
                g.update(gDict)
                hRef.update(hrefDict)
                st.success("Updated Physical Properties") 