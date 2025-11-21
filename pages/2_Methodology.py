import streamlit as st

# region <--------- Streamlit App Configuration --------->
st.set_page_config(
    layout="centered",
    page_title="My Streamlit App"
)
# endregion <--------- Streamlit App Configuration --------->

st.title("Methodology")

st.write("Methodology: How the Application Works

This page explains the end-to-end workflow for each use case inside the Structured Research Repository & Paper Summarizer application. It covers the core logic, data flow, and how the system processes and responds to user input across the two main features:
1. Upload & Summarize PDF Papers
2. Search Open-Access Research Papers)

with st.expander("Upload & Summarize Research Papers"):
    st.write("This workflow handles user-uploaded PDF files, extracts their content, sends them for AI-based processing, stores the results, and enables question-answering.")
    st.write("Step-by-Step Process Flow:" \
    "1. User Uploads PDF" \
    "2. PDF Text Extraction" \
    "3. AI-Powered Structured Summarization" \
    "4. Parsing the Summary" \
    "5. Save into the Repository" \
    "6. Diplay to the user" \
    "7. Ask Questions About Uploaded Papers")
with st.expander("Search Open-Access Research Papers"):
    st.write("This workflow retrieves relevant research papers from online academic sources and generates a combined summary.")
    st.write("Step-by-Step Process Flow:" \
    "1. User Enters a Research Topic" \
    "2. User triggers a search." \
    "3. Fetching Papers from Open-Access Sources" \
    "4. AI-Powered Combined Summary" \
    "5. Display the results" \
    "6. Error Handling")