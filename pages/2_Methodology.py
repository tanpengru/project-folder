import streamlit as st

# ----------------- Streamlit App Configuration -----------------
st.set_page_config(
    layout="centered",
    page_title="NRF AI Assistant Methodology",
    page_icon="🧭"
)

# ----------------- Page Title -----------------
st.title("🧭 Methodology")

# ----------------- Intro Section -----------------
st.markdown("""
## Methodology: How the NRF Knowledge AI Assistant Works

This page explains the **end-to-end workflow** of the
**NRF Parliamentary Questions AI Assistant**.

The application combines:

- Historical **Parliamentary Questions (PQs) and NRF answers**
- Uploaded **NRF documents**
- Semantic search using text embeddings
- An AI chatbot grounded in retrieved repository evidence

The chatbot follows a **Retrieval-Augmented Generation (RAG)** approach:
it first retrieves relevant information from the NRF repository and then
uses that evidence to generate an answer.
""")


# ============================================================
# 🏛️ PARLIAMENTARY QUESTIONS
# ============================================================

with st.expander("🏛️ Add & Manage Parliamentary Questions"):

    st.markdown("""
### **Workflow**

1. **User Adds a Parliamentary Question**

   The user enters information such as:

   - Date
   - Parliamentary sitting / session
   - MP name
   - Constituency
   - Parliamentary Question
   - NRF answer
   - Topic
   - Keywords
   - Source / reference

2. **Unique PQ ID Is Created**

   Each Parliamentary Question is assigned a unique `pq_id`.

   This allows all searchable text associated with the same PQ to be
   traced back to one original Parliamentary Question.

3. **PQ Is Saved to the Repository**

   The metadata and answer are stored in the Parliamentary Question
   repository.

4. **Semantic Search Index Is Rebuilt**

   The PQ content is converted into searchable text and incorporated
   into the semantic search index.

5. **PQ Becomes Available to the AI Chatbot**

   Relevant PQs can subsequently be retrieved as evidence when a user
   asks a question.
""")


# ============================================================
# 📚 NRF DOCUMENTS
# ============================================================

with st.expander("📚 Upload & Process NRF Documents"):

    st.markdown("""
### **Supported File Types**

The NRF document repository supports:

- PDF
- Word (`.docx`)
- Excel (`.xlsx` / `.xls`)
- Text (`.txt`)

### **Workflow**

1. **User Uploads an NRF Document**

   The user may also enter:

   - Document title
   - Document type
   - Description
   - Keywords
   - Source / reference

2. **Unique Document ID Is Created**

   Each uploaded file is assigned one unique `document_id`.

   The `document_id` identifies the **original uploaded document** and
   remains separate from the individual search chunks created later.

3. **Text Is Extracted**

   Depending on file type, the application extracts text using:

   - PDF text extraction
   - PyPDF2 fallback
   - OCR for scanned PDFs where required
   - Word paragraph, table and textbox extraction
   - Excel worksheet extraction
   - Plain-text reading

4. **Document Is Saved to the Repository**

   The uploaded file and its metadata are stored.

5. **Semantic Search Index Is Rebuilt**

   The extracted document text is prepared for semantic retrieval.
""")


