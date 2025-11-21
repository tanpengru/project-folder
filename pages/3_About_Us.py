import streamlit as st

# region <--------- Streamlit App Configuration --------->
st.set_page_config(
    layout="centered",
    page_title="My Streamlit App"
)
# endregion <--------- Streamlit App Configuration --------->

st.title("About this App")

st.write("This is a Research App can 1) Upload & Summarize Research Papers 2) Search Open Access Papers.")

with st.expander("Upload & Summarize Research Papers"):
    st.write("1. Browse and Upload Research Papers.")
    st.write("2. Question the research paper.")
with st.expander("Open Access Search"):
    st.write("1. Search open access database.")
    st.write("2. Click Submit.")