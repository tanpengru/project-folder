import streamlit as st

# region <--------- Streamlit App Configuration --------->
st.set_page_config(
    layout="centered",
    page_title="My Streamlit App"
)
# endregion <--------- Streamlit App Configuration --------->

st.title("About this App")

st.write("This is a Research App can 1) Upload & Summarize Research Papers 2) Search Open Access Papers.")

with st.expander("Upload & Aummarize Research Papers"):
    st.write("1. Browse and Upload Research Papers.")
    st.write("2. Question the research paper.")
    st.write("3. The app will generate a text completion based on your prompt.")
