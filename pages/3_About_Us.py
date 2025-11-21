import streamlit as st

# region <--------- Streamlit App Configuration --------->
st.set_page_config(
    layout="centered",
    page_title="About This Research App"
)
# endregion <--------- Streamlit App Configuration --------->

# ------------------ PAGE TITLE ------------------
st.title("📘 About This AI-Research Assistant")

st.write(
    """
This application is designed to help researchers, students, and knowledge workers 
**analyze, summarize, and retrieve insights from academic literature** with speed and structure.

Below is an overview of the project's **scope**, **objectives**, **data sources**, and **core features**.
"""
)

# ------------------ PROJECT SCOPE ------------------
st.header("📌 Project Scope")
st.write(
    """
The goal of this project is to build an **intelligent research assistant** capable of:

- Handling **uploaded academic papers** (PDFs, text-based documents).
- Generating **structured summaries** using LLMs.
- Allowing users to **query the content** of any uploaded paper.
- Searching **open-access scholarly databases** for relevant literature.
- Providing combined summaries and citations for retrieved papers.

This app focuses on **automation, retrieval, and structured interpretation** of research papers.
"""
)

# ------------------ PROJECT OBJECTIVES ------------------
st.header("🎯 Objectives")
st.write(
    """
1. **Accelerate research review** by summarizing long academic papers into structured key sections.
2. **Improve literature search** using open-access sources and automated extraction.
3. **Enable question-answering** directly over the content of uploaded research papers.
4. **Support decision-making** by providing clean, formatted, reference-ready summaries.
5. **Provide a simple and efficient interface** for both technical and non-technical users.
"""
)

# ------------------ DATA SOURCES ------------------
st.header("🔍 Data Sources")
st.write(
    """
This application currently integrates the following open scholarly data sources:

- **OpenAlex** – for open-access metadata, abstracts, authorship, and citation information.
- **ArXiv RSS API** – for retrieving preprints and abstracts in specific fields.
- **Uploaded PDF documents** – processed locally via PyPDF2 and summarized using an LLM.

Additional sources may be added in future versions (e.g., PubMed, Semantic Scholar).
"""
)

# ------------------ FEATURES ------------------
st.header("⚙️ Core Features")

st.subheader("📄 1. Upload & Summarize Research Papers")
with st.expander("Expand — Upload & Summarize"):
    st.write(
        """
- Upload PDF research papers.
- Automatically extract content (first 12,000 characters for processing efficiency).
- Generate **structured summaries**, including:
  - Research problem & motivation  
  - Methodology  
  - Key findings  
  - Limitations  
  - Future directions  
- Ask follow-up questions about the uploaded paper.
"""
    )

st.subheader("🌐 2. Search Open-Access Papers")
with st.expander("Expand — Open Access Search"):
    st.write(
        """
- Search scholarly databases using keywords or topics.
- Retrieve:
  - Article titles  
  - Abstracts  
  - Authors  
  - Open-access availability  
  - Links & identifiers  
- Automatically generate **combined summaries** with citations.
"""
    )

st.subheader("🧠 3. AI-Driven Research Insights")
with st.expander("Expand — AI Insights"):
    st.write(
        """
- Query the LLM for:
  - Explanations  
  - Comparisons between papers  
  - Research gaps  
  - Hypothesis generation  
- Receive structured, academically suitable responses.
"""
    )
