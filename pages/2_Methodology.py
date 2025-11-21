# Methodology Page

import streamlit as st
import pandas as pd
from PyPDF2 import PdfReader

# Import helper functions
from helper_functions.utility import check_password
from logics.research_summary_handler import (
    summarize_paper_structured,
    parse_structured_summary,
    query_repository,
    search_open_access_papers,
)

# ----------------- Streamlit Configuration -----------------
st.set_page_config(
    layout="wide",
    page_title="🧠 Structured Research Repository",
)
st.title("🧠 Structured Research Repository & Paper Summarizer")

# ----------------- Authentication -----------------
if not check_password():
    st.stop()

# ----------------- Session State -----------------
if "repository" not in st.session_state:
    st.session_state.repository = {}  # filename -> {"structured": str, "parsed": dict}

# ----------------- Tabs Layout -----------------
tab1, tab2, tab3 = st.tabs([
    "📄 Upload & Summarize Paper",
    "🌐 Search Open-Access Papers",
    "📘 Methodology"
])

# ---------------------------------------------------------------------
# TAB 1 — Upload & Summarize PDF
# ---------------------------------------------------------------------
with tab1:
    st.subheader("📄 Upload a Research Paper for Structured Summarization")

    uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"])

    if uploaded_file:
        pdf_reader = PdfReader(uploaded_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() or ""

        if text.strip():
            with st.spinner("🧠 Summarizing paper using AI..."):
                structured_summary = summarize_paper_structured(
                    text, uploaded_file.name
                )

            parsed_summary = parse_structured_summary(structured_summary)

            st.session_state.repository[uploaded_file.name] = {
                "structured": structured_summary,
                "parsed": parsed_summary,
            }

            st.markdown("### ✅ Structured Summary")
            st.markdown(structured_summary)

            st.markdown("### 📊 Summary Table View")
            df = pd.DataFrame([parsed_summary])
            st.dataframe(df, use_container_width=True)
        else:
            st.warning("⚠️ No readable text found in the uploaded PDF.")

    if st.session_state.repository:
        st.markdown("---")
        st.subheader("💬 Ask Questions About Uploaded Papers")
        query = st.text_input("Ask a question:")

        if query:
            with st.spinner("🤖 Analyzing repository..."):
                answer = query_repository(query, st.session_state.repository)

            st.markdown("### 🧩 Repository Answer")
            st.markdown(answer)

# ---------------------------------------------------------------------
# TAB 2 — Search and Summarize Open-Access Papers
# ---------------------------------------------------------------------
with tab2:
    st.subheader("🌐 Search for Open-Access Research Papers")

    user_prompt = st.text_input(
        "Enter a research topic (e.g., 'AI in radiology'):",
        placeholder="Type your research topic..."
    )

    if st.button("Search Papers"):
        if not user_prompt:
            st.warning("⚠️ Please enter a topic before searching.")
        else:
            with st.spinner("🔎 Searching open-access repositories..."):
                try:
                    summary, insights_df, references = search_open_access_papers(
                        user_prompt
                    )
                except Exception as e:
                    st.error(f"⚠️ Error while searching papers: {e}")
                    st.stop()

            # Display Results
            st.markdown("### 🧾 Combined Summary")
            st.markdown(summary)

            if not insights_df.empty:
                st.markdown("### 📚 Retrieved Papers")

                # Make paper links clickable
                insights_df["Link"] = insights_df["Link"].apply(
                    lambda url: f"[View Paper]({url})"
                )

                st.dataframe(
                    insights_df[["Title", "Authors", "Published", "Link"]],
                    use_container_width=True,
                )

                with st.expander("📖 Reference Links"):
                    for i, ref in enumerate(references, 1):
                        st.markdown(f"{i}. [Paper Link]({ref})")
            else:
                st.info("No open-access papers found. Try a different query.")

