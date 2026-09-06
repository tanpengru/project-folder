import streamlit as st

# region <--------- Streamlit App Configuration --------->
st.set_page_config(
    layout="centered",
    page_title="About the NRF AI Assistant",
    page_icon="🏛️"
)
# endregion <--------- Streamlit App Configuration --------->


# ============================================================
# PAGE TITLE
# ============================================================

st.title("🏛️ About the NRF Parliamentary Questions AI Assistant")

st.write(
    """
This application is designed to help users **store, search, retrieve and
synthesise information from NRF Parliamentary Questions and NRF-related
documents**.

It combines a structured knowledge repository, semantic search and a
Retrieval-Augmented Generation (RAG) chatbot to make it easier to retrieve
relevant information while maintaining traceability to the original sources.

Below is an overview of the project's **scope**, **objectives**, **data sources**
and **core features**.
"""
)


# ============================================================
# PROJECT SCOPE
# ============================================================

st.header("📌 Project Scope")

st.write(
    """
The goal of this project is to build an **NRF Knowledge AI Assistant** capable of:

- Storing and managing historical **Parliamentary Questions (PQs) and NRF answers**.
- Storing and processing **NRF-related documents**.
- Extracting searchable text from PDF, Word, Excel and text files.
- Using **semantic search** to identify relevant information across the repository.
- Providing an **AI chatbot** that searches both PQs and NRF documents before answering.
- Generating answers grounded in retrieved repository evidence.
- Providing **source citations** so users can trace AI-generated answers back to the
  relevant PQs and uploaded documents.

The application focuses on **knowledge management, retrieval, synthesis and
source transparency** rather than unrestricted general-purpose AI search.
"""
)


# ============================================================
# PROJECT OBJECTIVES
# ============================================================

st.header("🎯 Objectives")

st.write(
    """
1. **Centralise NRF knowledge** by maintaining Parliamentary Questions,
   NRF answers and relevant documents in one searchable repository.

2. **Improve information retrieval** by using semantic search instead of
   relying only on exact keyword matching.

3. **Accelerate knowledge synthesis** by allowing users to ask natural-language
   questions across the repository.

4. **Ground AI-generated answers in repository evidence** using a
   Retrieval-Augmented Generation (RAG) approach.

5. **Improve source traceability** by providing inline citations that link
   generated claims to the relevant Parliamentary Questions and NRF documents.

6. **Support institutional knowledge management** by making historical and
   uploaded information easier to retrieve and compare.

7. **Provide a simple interface** that can be used without requiring technical
   knowledge of embeddings, semantic search or large language models.
"""
)


# ============================================================
# DATA SOURCES
# ============================================================

st.header("🔍 Data Sources")

st.write(
    """
The application currently uses two primary knowledge sources:

### 🏛️ Parliamentary Questions

Historical Parliamentary Questions and NRF answers stored in the application's
PQ repository.

Each PQ may contain information such as:

- Date
- Parliamentary sitting / session
- MP name
- Constituency
- Parliamentary Question
- NRF answer
- Topic
- Keywords
- Source / reference

Each Parliamentary Question is assigned a unique `pq_id`.


### 📚 NRF Documents

NRF-related documents uploaded into the application's document repository.

Supported formats include:

- **PDF**
- **Word (`.docx`)**
- **Excel (`.xlsx` / `.xls`)**
- **Text (`.txt`)**

Each uploaded document is assigned a unique `document_id`.

The application does **not rely on external scholarly databases** such as
OpenAlex or ArXiv for chatbot answers. The AI chatbot is designed to answer
using evidence retrieved from the NRF repository.
"""
)


# ============================================================
# CORE FEATURES
# ============================================================

st.header("⚙️ Core Features")


# ============================================================
# FEATURE 1
# ============================================================

st.subheader("🏛️ 1. Parliamentary Questions Repository")

with st.expander("Expand — Parliamentary Questions"):

    st.write(
        """
The application provides a structured repository for historical
Parliamentary Questions and NRF answers.

Users can:

- Add new Parliamentary Questions.
- Record the corresponding NRF answer.
- Store information about the MP, date and parliamentary sitting.
- Add topics and keywords.
- Record the original source or reference.
- Browse existing PQs.
- Filter and search historical PQs.
- Delete outdated or incorrect records.

Each Parliamentary Question receives a unique `pq_id`, allowing the search
engine and chatbot to trace retrieved information back to the original PQ.
"""
    )


# ============================================================
# FEATURE 2
# ============================================================

st.subheader("📚 2. NRF Document Repository")

with st.expander("Expand — NRF Documents"):

    st.write(
        """
Users can upload NRF-related documents into a central knowledge repository.

Supported document types include:

- PDF
- Word
- Excel
- Text files

The application extracts text from these documents and prepares the content
for semantic search.

For each uploaded document, users can record:

- Document title
- Document type
- Description
- Keywords
- Source / reference

Each uploaded file receives one unique `document_id`.

This ID represents the **original uploaded document**, even when the document
is subsequently divided into multiple searchable passages.
"""
    )

