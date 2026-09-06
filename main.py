# ============================================================
# main.py — NRF Parliamentary Questions AI Assistant
#
# Functions:
# 1. Store and manage past NRF Parliamentary Questions & Answers
# 2. Upload and manage NRF-related PDF, DOCX, Excel and TXT documents
# 3. AI chatbot grounded in:
#    - Parliamentary Questions / NRF answers
#    - Uploaded NRF documents
#
# Search engine:
# helper_functions/PQAI.py
#
# AI:
# OpenAI Responses API
# ============================================================

import os
import re
import zipfile
import hashlib
import json
import importlib
import logging
from datetime import datetime

import streamlit as st
import pandas as pd

import pdfplumber
from PyPDF2 import PdfReader
from docx import Document
from lxml import etree
from pdf2image import convert_from_path
import pytesseract

from openai import OpenAI


# ============================================================
# 🔐 AUTH
# ============================================================

from helper_functions.utility import check_password


# ============================================================
# 🧠 NRF PQ AI SEARCH ENGINE
# ============================================================

try:
    from helper_functions import PQAI
except ImportError:
    PQAI = importlib.import_module("helper_functions.PQAI")


logger = logging.getLogger(__name__)


# ============================================================
# ⚙️ STREAMLIT CONFIG
# ============================================================

st.set_page_config(
    layout="wide",
    page_title="NRF Parliamentary Questions AI Assistant",
    page_icon="🏛️"
)

st.title("🏛️ NRF Parliamentary Questions AI Assistant")

if not check_password():
    st.stop()


# ============================================================
# 📁 GLOBAL CONSTANTS
# ============================================================

PQ_FOLDER = "nrf_pq_repo"
DOCUMENT_FOLDER = "nrf_documents"

PQ_METADATA_FILE = "nrf_pq_metadata.csv"
DOCUMENT_METADATA_FILE = "nrf_documents_metadata.csv"

os.makedirs(PQ_FOLDER, exist_ok=True)
os.makedirs(DOCUMENT_FOLDER, exist_ok=True)


# ============================================================
# 📊 METADATA SCHEMAS
# ============================================================

PQ_COLUMNS = [
    "pq_id",
    "date",
    "sitting",
    "mp_name",
    "constituency",
    "question",
    "answer",
    "topic",
    "keywords",
    "source",
    "uploaded_at",
]


DOCUMENT_COLUMNS = [
    "document_id",
    "filename",
    "filepath",
    "document_title",
    "document_type",
    "description",
    "keywords",
    "source",
    "uploaded_at",
]


# ============================================================
# 📚 GENERIC DATA HELPERS
# ============================================================

def load_csv(path, columns):
    """Load CSV while ensuring all expected columns exist."""

    if os.path.exists(path):
        try:
            df = pd.read_csv(
                path,
                dtype=str,
                keep_default_na=False
            )
        except Exception as exc:
            logger.exception(
                "Failed to load CSV %s: %s",
                path,
                exc
            )
            df = pd.DataFrame(columns=columns)
    else:
        df = pd.DataFrame(columns=columns)

    for col in columns:
        if col not in df.columns:
            df[col] = ""

    return df[columns]


def save_csv(df, path):
    """Save dataframe to CSV."""

    df.to_csv(
        path,
        index=False,
        encoding="utf-8-sig"
    )


def generate_id(prefix):
    """Generate short unique ID."""

    timestamp = datetime.now().isoformat()
    raw = f"{prefix}_{timestamp}"

    return hashlib.md5(
        raw.encode("utf-8")
    ).hexdigest()[:12]


def ensure_unique_path(folder, filename):
    """Prevent uploaded files from overwriting existing files."""

    base, ext = os.path.splitext(filename)

    path = os.path.join(
        folder,
        filename
    )

    counter = 1

    while os.path.exists(path):
        path = os.path.join(
            folder,
            f"{base} ({counter}){ext}"
        )
        counter += 1

    return path


# ============================================================
# 📄 DOCX TEXTBOX EXTRACTION
# ============================================================

def extract_textboxes_from_docx(filepath):

    text_chunks = []

    ns = {
        "w":
            "http://schemas.openxmlformats.org/"
            "wordprocessingml/2006/main",

        "wps":
            "http://schemas.microsoft.com/office/word/2010/"
            "wordprocessingShape",

        "v":
            "urn:schemas-microsoft-com:vml",
    }

    try:
        with zipfile.ZipFile(
            filepath,
            "r"
        ) as docx:

            for name in docx.namelist():

                if not name.startswith("word/"):
                    continue

                if not name.endswith(".xml"):
                    continue

                try:
                    xml_data = docx.read(name)
                    root = etree.fromstring(xml_data)
                except Exception:
                    continue

                for node in root.findall(
                    ".//w:txbxContent",
                    ns
                ):
                    text_chunks.extend(
                        node.itertext()
                    )

                for node in root.findall(
                    ".//wps:txbx",
                    ns
                ):
                    text_chunks.extend(
                        node.itertext()
                    )

                for node in root.findall(
                    ".//v:textbox",
                    ns
                ):
                    text_chunks.extend(
                        node.itertext()
                    )

    except Exception as exc:
        logger.exception(
            "Failed to extract DOCX textboxes from %s: %s",
            filepath,
            exc
        )

    return "\n".join(
        t.strip()
        for t in text_chunks
        if t.strip()
    )


# ============================================================
# 📕 PDF EXTRACTION
# ============================================================

def extract_text_from_pdf(filepath):

    parts = []

    try:
        with pdfplumber.open(filepath) as pdf:
            for page in pdf.pages:
                text = page.extract_text()

                if text and text.strip():
                    parts.append(text)

    except Exception as exc:
        logger.warning(
            "pdfplumber failed for %s: %s",
            filepath,
            exc
        )

    try:
        reader = PdfReader(filepath)

        text = "\n".join(
            page.extract_text() or ""
            for page in reader.pages
        )

        if text.strip() and not parts:
            parts.append(text)

    except Exception as exc:
        logger.warning(
            "PyPDF2 failed for %s: %s",
            filepath,
            exc
        )

    try:
        if not parts:

            images = convert_from_path(
                filepath,
                dpi=200
            )

            ocr_parts = []

            for image in images:
                text = pytesseract.image_to_string(
                    image
                )

                if text.strip():
                    ocr_parts.append(text)

            if ocr_parts:
                parts.append(
                    "\n".join(ocr_parts)
                )

    except Exception as exc:
        logger.warning(
            "OCR fallback failed for %s: %s",
            filepath,
            exc
        )

    return "\n\n".join(parts)


# ============================================================
# 📘 DOCX EXTRACTION
# ============================================================

def extract_text_from_docx(filepath):

    parts = []

    try:
        doc = Document(filepath)

        for paragraph in doc.paragraphs:
            text = paragraph.text.strip()

            if text:
                parts.append(text)

        for table in doc.tables:
            for row in table.rows:

                cells = []

                for cell in row.cells:
                    text = cell.text.strip()

                    if text:
                        cells.append(text)

                if cells:
                    parts.append(
                        " | ".join(cells)
                    )

    except Exception as exc:
        logger.warning(
            "DOCX extraction failed for %s: %s",
            filepath,
            exc
        )

    try:
        textbox_text = extract_textboxes_from_docx(
            filepath
        )

        if textbox_text.strip():
            parts.append(textbox_text)

    except Exception as exc:
        logger.warning(
            "DOCX textbox extraction failed for %s: %s",
            filepath,
            exc
        )

    return "\n".join(parts)


# ============================================================
# 📊 EXCEL EXTRACTION
# ============================================================

def extract_text_from_excel(filepath):

    parts = []

    try:
        excel_file = pd.ExcelFile(filepath)

        for sheet_name in excel_file.sheet_names:

            try:
                df = pd.read_excel(
                    filepath,
                    sheet_name=sheet_name,
                    dtype=str
                )

                df = df.fillna("")

                parts.append(
                    f"\n=== SHEET: {sheet_name} ==="
                )

                parts.append(
                    " | ".join(
                        str(col)
                        for col in df.columns
                    )
                )

                for _, row in df.iterrows():

                    values = [
                        str(value).strip()
                        for value in row.tolist()
                        if str(value).strip()
                    ]

                    if values:
                        parts.append(
                            " | ".join(values)
                        )

            except Exception as exc:
                logger.warning(
                    "Failed to read Excel sheet %s in %s: %s",
                    sheet_name,
                    filepath,
                    exc
                )

    except Exception as exc:
        logger.warning(
            "Excel extraction failed for %s: %s",
            filepath,
            exc
        )

    return "\n".join(parts)


# ============================================================
# 📄 GENERAL FILE EXTRACTION
# ============================================================

def extract_raw_text(filepath):

    if not filepath:
        return ""

    if not os.path.exists(filepath):
        return ""

    extension = os.path.splitext(
        filepath
    )[1].lower()

    if extension == ".pdf":
        return extract_text_from_pdf(filepath)

    elif extension == ".docx":
        return extract_text_from_docx(filepath)

    elif extension in [
        ".xlsx",
        ".xls"
    ]:
        return extract_text_from_excel(filepath)

    elif extension == ".txt":

        try:
            with open(
                filepath,
                "r",
                encoding="utf-8",
                errors="ignore"
            ) as f:
                return f.read()

        except Exception as exc:
            logger.warning(
                "TXT extraction failed for %s: %s",
                filepath,
                exc
            )

            return ""

    return ""


# ============================================================
# 🔄 SAFE SEARCH INDEX REBUILD
# ============================================================

def rebuild_search_index_safe(
    pq_dataframe,
    document_dataframe
):
    """
    Rebuild semantic search index safely.

    Returns:
        (success, rebuilt_index)
    """

    try:

        rebuilt = PQAI.rebuild_search_index(
            pq_dataframe,
            document_dataframe
        )

        if isinstance(rebuilt, pd.DataFrame):
            return True, rebuilt

        if (
            isinstance(rebuilt, tuple)
            and len(rebuilt) >= 1
            and isinstance(rebuilt[0], pd.DataFrame)
        ):
            return True, rebuilt[0]

        logger.warning(
            "PQAI.rebuild_search_index returned "
            "unexpected type: %s",
            type(rebuilt).__name__
        )

        return False, pd.DataFrame()

    except Exception as exc:

        logger.exception(
            "Search index rebuild failed: %s",
            exc
        )

        return False, pd.DataFrame()


# ============================================================
# 🤖 OPENAI CLIENT
# ============================================================

def get_openai_api_key():
    """
    Load OpenAI API key from Streamlit Secrets first,
    then environment variables.
    """

    try:
        if "OPENAI_API_KEY" in st.secrets:
            return st.secrets["OPENAI_API_KEY"]
    except Exception:
        pass

    return os.getenv(
        "OPENAI_API_KEY",
        ""
    )


def get_openai_model():
    """
    Allow the model to be configured in Streamlit Secrets.
    """

    try:
        if "OPENAI_MODEL" in st.secrets:
            return st.secrets["OPENAI_MODEL"]
    except Exception:
        pass

    return os.getenv(
        "OPENAI_MODEL",
        "gpt-5-mini"
    )


def get_openai_client():

    api_key = get_openai_api_key()

    if not api_key:
        return None

    return OpenAI(
        api_key=api_key
    )


# ============================================================
# 🤖 CHATBOT SEARCH HELPERS
# ============================================================

def retrieve_chatbot_sources(
    query,
    pq_top_k=5,
    document_top_k=5,
    min_similarity=0.20
):
    """
    Search PQs and NRF documents separately.

    This deliberately avoids one source category crowding
    out the other when searching the combined repository.
    """

    try:
        pq_results = (
            PQAI.search_parliamentary_questions(
                query=query,
                top_k=pq_top_k,
                min_similarity=min_similarity
            )
        )

    except Exception as exc:

        logger.exception(
            "PQ retrieval failed: %s",
            exc
        )

        pq_results = pd.DataFrame()

    try:
        document_results = (
            PQAI.search_nrf_documents(
                query=query,
                top_k=document_top_k,
                min_similarity=min_similarity
            )
        )

    except Exception as exc:

        logger.exception(
            "Document retrieval failed: %s",
            exc
        )

        document_results = pd.DataFrame()

    sources = []

    # --------------------------------------------------------
    # PQ sources
    # --------------------------------------------------------

    if not pq_results.empty:

        for i, (_, row) in enumerate(
            pq_results.iterrows(),
            start=1
        ):

            sources.append(
                {
                    "label":
                        f"PQ{i}",

                    "source_type":
                        "Parliamentary Question",

                    "title":
                        str(
                            row.get(
                                "title",
                                "Parliamentary Question"
                            )
                        ),

                    "text":
                        str(
                            row.get(
                                "text",
                                ""
                            )
                        ),

                    "similarity":
                        float(
                            row.get(
                                "similarity",
                                0
                            )
                        ),

                    "metadata":
                        row.get(
                            "metadata",
                            ""
                        ),
                }
            )

    # --------------------------------------------------------
    # Document sources
    # --------------------------------------------------------

    if not document_results.empty:

        for i, (_, row) in enumerate(
            document_results.iterrows(),
            start=1
        ):

            sources.append(
                {
                    "label":
                        f"DOC{i}",

                    "source_type":
                        "NRF Document",

                    "title":
                        str(
                            row.get(
                                "title",
                                "NRF Document"
                            )
                        ),

                    "text":
                        str(
                            row.get(
                                "text",
                                ""
                            )
                        ),

                    "similarity":
                        float(
                            row.get(
                                "similarity",
                                0
                            )
                        ),

                    "metadata":
                        row.get(
                            "metadata",
                            ""
                        ),
                }
            )

    return sources


# ============================================================
# 🤖 SOURCE CONTEXT BUILDER
# ============================================================

def build_chatbot_context(
    sources
):
    """
    Build a source-labelled evidence block for the AI.
    """

    context_parts = []

    for source in sources:

        label = source.get(
            "label",
            ""
        )

        source_type = source.get(
            "source_type",
            ""
        )

        title = source.get(
            "title",
            ""
        )

        text = source.get(
            "text",
            ""
        )

        metadata = source.get(
            "metadata",
            ""
        )

        similarity = source.get(
            "similarity",
            0
        )

        if isinstance(
            metadata,
            str
        ):

            try:
                metadata = json.loads(metadata)
            except Exception:
                metadata = {}

        if not isinstance(
            metadata,
            dict
        ):
            metadata = {}

        context_parts.append(
            f"""
SOURCE [{label}]
Source type: {source_type}
Title: {title}
Retrieval relevance: {similarity:.1%}
Metadata: {json.dumps(metadata, ensure_ascii=False)}

Relevant passage:
{text}
""".strip()
        )

    return "\n\n---\n\n".join(
        context_parts
    )


# ============================================================
# 🤖 CHAT HISTORY BUILDER
# ============================================================

def build_recent_chat_history(
    messages,
    max_messages=8
):
    """
    Provide a limited amount of conversational history
    to the model while preventing the prompt from growing
    indefinitely.
    """

    if not messages:
        return ""

    recent_messages = messages[
        -max_messages:
    ]

    parts = []

    for message in recent_messages:

        role = message.get(
            "role",
            ""
        )

        content = message.get(
            "content",
            ""
        )

        if role == "user":
            speaker = "User"

        elif role == "assistant":
            speaker = "NRF AI Assistant"

        else:
            continue

        parts.append(
            f"{speaker}:\n{content}"
        )

    return "\n\n".join(parts)


# ============================================================
# 🤖 GENERATE GROUNDED AI RESPONSE
# ============================================================

def generate_chatbot_answer(
    query,
    sources,
    chat_history
):
    """
    Generate an answer grounded only in retrieved NRF sources.
    """

    client = get_openai_client()

    if client is None:
        raise RuntimeError(
            "OPENAI_API_KEY has not been configured."
        )

    if not sources:
        return (
            "I could not find sufficiently relevant information "
            "in the Parliamentary Questions or uploaded NRF "
            "documents to answer this question reliably."
        )

    context = build_chatbot_context(
        sources
    )

    recent_history = build_recent_chat_history(
        chat_history
    )

    instructions = """
You are the NRF Knowledge AI Assistant.

Your task is to answer questions using ONLY the evidence supplied
from the NRF knowledge repository.

The repository contains:
1. Historical Parliamentary Questions and NRF answers.
2. NRF-related uploaded documents.

IMPORTANT RULES:

- Ground all factual claims in the supplied sources.
- Do not invent NRF positions, policies, programmes, statistics,
  dates, commitments or explanations.
- If the evidence is insufficient, say that the repository does
  not contain enough information to answer confidently.
- Where useful, distinguish between what NRF said in a
  Parliamentary Question and what appears in an NRF document.
- Cite supporting evidence inline using the exact source labels,
  for example [PQ1], [PQ2], [DOC1].
- Never invent source labels.
- Multiple sources may be cited together, for example
  [PQ1][DOC2].
- Prefer synthesis over copying source text.
- Answer directly and clearly.
- Use concise headings or bullets only when they improve clarity.
- Do not mention semantic similarity scores.
- Do not claim to have searched sources that were not supplied.
"""

    prompt = f"""
CURRENT USER QUESTION

{query}


RECENT CONVERSATION

{recent_history or "No previous conversation."}


RETRIEVED NRF EVIDENCE

{context}


Answer the current user question using the retrieved NRF evidence.
Use inline citations such as [PQ1] and [DOC1].
"""

    model = get_openai_model()

    response = client.responses.create(
        model=model,
        instructions=instructions,
        input=prompt
    )

    answer = getattr(
        response,
        "output_text",
        ""
    )

    if not answer:
        raise RuntimeError(
            "The AI model returned an empty response."
        )

    return answer.strip()


# ============================================================
# 📚 LOAD REPOSITORIES
# ============================================================

pq_df = load_csv(
    PQ_METADATA_FILE,
    PQ_COLUMNS
)

document_df = load_csv(
    DOCUMENT_METADATA_FILE,
    DOCUMENT_COLUMNS
)


# ============================================================
# 🧭 MAIN NAVIGATION
# ============================================================

tab_chat, tab_pq, tab_documents, tab_admin = st.tabs(
    [
        "🤖 NRF AI Chatbot",
        "🏛️ Parliamentary Questions",
        "📚 NRF Documents",
        "⚙️ Repository Management",
    ]
)


# ============================================================
# 🤖 TAB 1 — NRF AI CHATBOT
# ============================================================

with tab_chat:

    st.header(
        "🤖 NRF Knowledge AI Chatbot"
    )

    st.markdown(
        """
        Ask questions about NRF using the knowledge stored in
        this repository.

        The chatbot searches both:

        - **Historical Parliamentary Questions and NRF answers**
        - **Uploaded NRF documents**

        before generating its response.
        """
    )

    # --------------------------------------------------------
    # API status
    # --------------------------------------------------------

    api_key = get_openai_api_key()

    if not api_key:

        st.warning(
            """
            OpenAI API access has not been configured.

            Add `OPENAI_API_KEY` to Streamlit Secrets to enable
            AI-generated answers.
            """
        )

    # --------------------------------------------------------
    # Search-index health
    # --------------------------------------------------------

    try:

        search_index = (
            PQAI.load_search_index()
        )

    except Exception:

        search_index = pd.DataFrame()

    if search_index.empty:

        st.info(
            """
            The semantic search index is currently empty.

            Add Parliamentary Questions or NRF documents, then
            go to **Repository Management → Rebuild Semantic
            Search Index**.
            """
        )

    # --------------------------------------------------------
    # Chat state
    # --------------------------------------------------------

    if "nrf_chat_messages" not in st.session_state:

        st.session_state[
            "nrf_chat_messages"
        ] = []

    if "nrf_chat_sources" not in st.session_state:

        st.session_state[
            "nrf_chat_sources"
        ] = {}

    # --------------------------------------------------------
    # Chat controls
    # --------------------------------------------------------

    control_col1, control_col2 = st.columns(
        [5, 1]
    )

    with control_col2:

        if st.button(
            "🗑️ Clear chat",
            use_container_width=True
        ):

            st.session_state[
                "nrf_chat_messages"
            ] = []

            st.session_state[
                "nrf_chat_sources"
            ] = {}

            st.rerun()

    # --------------------------------------------------------
    # Welcome message
    # --------------------------------------------------------

    if not st.session_state[
        "nrf_chat_messages"
    ]:

        with st.chat_message(
            "assistant"
        ):

            st.markdown(
                """
                Hello. I can answer questions using the NRF
                repository.

                For example:

                - What has NRF said about AI research?
                - What Parliamentary Questions have been asked
                  about R&D funding?
                - What do our uploaded documents say about
                  research manpower?
                - Compare NRF's Parliamentary responses with
                  the relevant strategy documents.
                """
            )

    # --------------------------------------------------------
    # Existing chat
    # --------------------------------------------------------

    for message_index, message in enumerate(
        st.session_state[
            "nrf_chat_messages"
        ]
    ):

        role = message.get(
            "role",
            "assistant"
        )

        content = message.get(
            "content",
            ""
        )

        with st.chat_message(role):

            st.markdown(content)

            if role == "assistant":

                sources = (
                    st.session_state[
                        "nrf_chat_sources"
                    ]
                    .get(
                        str(message_index),
                        []
                    )
                )

                if sources:

                    with st.expander(
                        f"📚 Sources used ({len(sources)})"
                    ):

                        for source in sources:

                            label = source.get(
                                "label",
                                ""
                            )

                            source_type = (
                                source.get(
                                    "source_type",
                                    ""
                                )
                            )

                            title = source.get(
                                "title",
                                ""
                            )

                            text = source.get(
                                "text",
                                ""
                            )

                            similarity = source.get(
                                "similarity",
                                0
                            )

                            if (
                                source_type
                                == "Parliamentary Question"
                            ):
                                icon = "🏛️"

                            else:
                                icon = "📄"

                            st.markdown(
                                f"### {icon} [{label}] {title}"
                            )

                            st.caption(
                                f"Retrieval relevance: "
                                f"{similarity:.1%}"
                            )

                            st.write(text)

                            st.markdown("---")

    # --------------------------------------------------------
    # User input
    # --------------------------------------------------------

    user_question = st.chat_input(
        "Ask a question about NRF..."
    )

    if user_question:

        # ----------------------------------------------------
        # Save user message
        # ----------------------------------------------------

        st.session_state[
            "nrf_chat_messages"
        ].append(
            {
                "role":
                    "user",

                "content":
                    user_question
            }
        )

        with st.chat_message(
            "user"
        ):

            st.markdown(
                user_question
            )

        # ----------------------------------------------------
        # Retrieve evidence
        # ----------------------------------------------------

        with st.chat_message(
            "assistant"
        ):

            with st.spinner(
                "Searching Parliamentary Questions and "
                "NRF documents..."
            ):

                sources = (
                    retrieve_chatbot_sources(
                        query=user_question,
                        pq_top_k=5,
                        document_top_k=5,
                        min_similarity=0.20
                    )
                )

            # ------------------------------------------------
            # Generate response
            # ------------------------------------------------

            if not sources:

                answer = (
                    "I could not find sufficiently relevant "
                    "information in the Parliamentary Questions "
                    "or uploaded NRF documents to answer this "
                    "question reliably."
                )

            elif not api_key:

                answer = (
                    "I found relevant repository sources, but "
                    "the OpenAI API key has not been configured, "
                    "so I cannot generate the AI response yet."
                )

            else:

                try:

                    with st.spinner(
                        "Preparing NRF-grounded answer..."
                    ):

                        answer = (
                            generate_chatbot_answer(
                                query=user_question,
                                sources=sources,
                                chat_history=(
                                    st.session_state[
                                        "nrf_chat_messages"
                                    ]
                                )
                            )
                        )

                except Exception as exc:

                    logger.exception(
                        "AI chatbot generation failed: %s",
                        exc
                    )

                    answer = (
                        "I found relevant NRF repository "
                        "information, but the AI response "
                        "could not be generated.\n\n"
                        f"Error: `{exc}`"
                    )

            st.markdown(answer)

            # ------------------------------------------------
            # Display sources immediately
            # ------------------------------------------------

            if sources:

                with st.expander(
                    f"📚 Sources used ({len(sources)})"
                ):

                    for source in sources:

                        label = source.get(
                            "label",
                            ""
                        )

                        source_type = source.get(
                            "source_type",
                            ""
                        )

                        title = source.get(
                            "title",
                            ""
                        )

                        text = source.get(
                            "text",
                            ""
                        )

                        similarity = source.get(
                            "similarity",
                            0
                        )

                        if (
                            source_type
                            == "Parliamentary Question"
                        ):
                            icon = "🏛️"

                        else:
                            icon = "📄"

                        st.markdown(
                            f"### {icon} [{label}] {title}"
                        )

                        st.caption(
                            f"Retrieval relevance: "
                            f"{similarity:.1%}"
                        )

                        st.write(text)

                        st.markdown("---")

        # ----------------------------------------------------
        # Save assistant message and source mapping
        # ----------------------------------------------------

        assistant_index = len(
            st.session_state[
                "nrf_chat_messages"
            ]
        )

        st.session_state[
            "nrf_chat_messages"
        ].append(
            {
                "role":
                    "assistant",

                "content":
                    answer
            }
        )

        st.session_state[
            "nrf_chat_sources"
        ][
            str(assistant_index)
        ] = sources


# ============================================================
# 🏛️ TAB 2 — PARLIAMENTARY QUESTIONS
# ============================================================

with tab_pq:

    st.header(
        "🏛️ Parliamentary Questions & Answers"
    )

    st.markdown(
        "Add, browse and manage historical NRF "
        "Parliamentary Questions."
    )

    # ========================================================
    # ADD PQ
    # ========================================================

    with st.expander(
        "➕ Add Parliamentary Question",
        expanded=False
    ):

        with st.form(
            "add_pq_form"
        ):

            col1, col2 = st.columns(2)

            with col1:

                pq_date = st.date_input(
                    "Date"
                )

                mp_name = st.text_input(
                    "MP Name"
                )

                constituency = st.text_input(
                    "Constituency"
                )

            with col2:

                sitting = st.text_input(
                    "Parliamentary Sitting / Session"
                )

                topic = st.text_input(
                    "Topic",
                    placeholder=(
                        "e.g. AI, R&D funding, "
                        "research manpower"
                    )
                )

                keywords = st.text_input(
                    "Keywords",
                    placeholder=(
                        "AI, R&D, research funding"
                    )
                )

            question = st.text_area(
                "Parliamentary Question",
                height=180
            )

            answer = st.text_area(
                "NRF Answer",
                height=250
            )

            source = st.text_input(
                "Source / Reference",
                placeholder=(
                    "e.g. Parliamentary Sitting, "
                    "Hansard reference"
                )
            )

            submitted = st.form_submit_button(
                "💾 Save Parliamentary Question",
                type="primary"
            )

            if submitted:

                if (
                    not question.strip()
                    or not answer.strip()
                ):

                    st.error(
                        "Both the Parliamentary Question "
                        "and NRF Answer are required."
                    )

                else:

                    duplicate = pq_df[
                        (
                            pq_df["date"].astype(str)
                            == str(pq_date)
                        )
                        &
                        (
                            pq_df["mp_name"]
                            .astype(str)
                            .str.lower()
                            == mp_name.strip().lower()
                        )
                        &
                        (
                            pq_df["question"]
                            .astype(str)
                            .str.strip()
                            == question.strip()
                        )
                    ]

                    if not duplicate.empty:

                        st.warning(
                            "This Parliamentary Question "
                            "already appears to exist in "
                            "the repository."
                        )

                    else:

                        new_pq = {

                            "pq_id":
                                generate_id("PQ"),

                            "date":
                                str(pq_date),

                            "sitting":
                                sitting.strip(),

                            "mp_name":
                                mp_name.strip(),

                            "constituency":
                                constituency.strip(),

                            "question":
                                question.strip(),

                            "answer":
                                answer.strip(),

                            "topic":
                                topic.strip(),

                            "keywords":
                                keywords.strip(),

                            "source":
                                source.strip(),

                            "uploaded_at":
                                datetime.now().isoformat()
                        }

                        pq_df = pd.concat(
                            [
                                pq_df,
                                pd.DataFrame(
                                    [new_pq]
                                )
                            ],
                            ignore_index=True
                        )

                        save_csv(
                            pq_df,
                            PQ_METADATA_FILE
                        )

                        with st.spinner(
                            "Updating semantic search index..."
                        ):

                            index_ok, _ = (
                                rebuild_search_index_safe(
                                    pq_df,
                                    document_df
                                )
                            )

                        if index_ok:

                            st.success(
                                "Parliamentary Question saved "
                                "and added to semantic search."
                            )

                        else:

                            st.warning(
                                "Parliamentary Question was saved, "
                                "but the semantic search index "
                                "could not be rebuilt."
                            )

                        st.rerun()

    # ========================================================
    # PQ SEARCH / FILTER
    # ========================================================

    st.markdown("---")

    if pq_df.empty:

        st.info(
            "No Parliamentary Questions have been added yet."
        )

    else:

        col1, col2 = st.columns(2)

        with col1:

            pq_keyword_search = st.text_input(
                "Filter Parliamentary Questions",
                placeholder=(
                    "Search MP, topic, question or answer..."
                )
            )

        with col2:

            topic_options = [
                "All Topics"
            ] + sorted(
                [
                    x
                    for x in pq_df["topic"]
                    .dropna()
                    .astype(str)
                    .unique()
                    if x.strip()
                ]
            )

            selected_topic = st.selectbox(
                "Topic",
                topic_options
            )

        filtered_pq = pq_df.copy()

        if pq_keyword_search.strip():

            q = pq_keyword_search.lower()

            mask = filtered_pq.apply(
                lambda row:
                    q in " ".join(
                        [
                            str(
                                row.get(
                                    "mp_name",
                                    ""
                                )
                            ),
                            str(
                                row.get(
                                    "question",
                                    ""
                                )
                            ),
                            str(
                                row.get(
                                    "answer",
                                    ""
                                )
                            ),
                            str(
                                row.get(
                                    "topic",
                                    ""
                                )
                            ),
                            str(
                                row.get(
                                    "keywords",
                                    ""
                                )
                            )
                        ]
                    ).lower(),
                axis=1
            )

            filtered_pq = filtered_pq[
                mask
            ]

        if selected_topic != "All Topics":

            filtered_pq = filtered_pq[
                filtered_pq["topic"]
                == selected_topic
            ]

        filtered_pq = filtered_pq.sort_values(
            "date",
            ascending=False
        )

        st.markdown(
            f"**{len(filtered_pq)} "
            f"Parliamentary Questions found**"
        )

        for _, row in filtered_pq.iterrows():

            title = (
                f"{row['date']} — "
                f"{row['mp_name'] or 'Unknown MP'}"
            )

            with st.expander(
                f"🏛️ {title}"
            ):

                st.markdown(
                    f"**Topic:** "
                    f"{row['topic'] or 'Not specified'}"
                )

                if row["sitting"]:

                    st.caption(
                        f"Sitting: {row['sitting']}"
                    )

                if row["constituency"]:

                    st.caption(
                        f"Constituency: "
                        f"{row['constituency']}"
                    )

                st.markdown(
                    "### Parliamentary Question"
                )

                st.write(
                    row["question"]
                )

                st.markdown(
                    "### NRF Answer"
                )

                st.write(
                    row["answer"]
                )

                if row["keywords"]:

                    st.caption(
                        f"Keywords: {row['keywords']}"
                    )

                if row["source"]:

                    st.caption(
                        f"Source: {row['source']}"
                    )

                st.markdown("---")

                if st.button(
                    "🗑️ Delete",
                    key=f"delete_pq_{row['pq_id']}"
                ):

                    pq_df = pq_df[
                        pq_df["pq_id"]
                        != row["pq_id"]
                    ]

                    save_csv(
                        pq_df,
                        PQ_METADATA_FILE
                    )

                    with st.spinner(
                        "Updating search index..."
                    ):

                        index_ok, _ = (
                            rebuild_search_index_safe(
                                pq_df,
                                document_df
                            )
                        )

                    if index_ok:

                        st.success(
                            "Parliamentary Question deleted."
                        )

                    else:

                        st.warning(
                            "Parliamentary Question deleted, "
                            "but the search index rebuild failed."
                        )

                    st.rerun()


# ============================================================
# 📚 TAB 3 — NRF DOCUMENTS
# ============================================================

with tab_documents:

    st.header(
        "📚 NRF Document Repository"
    )

    st.write(
        """
        Upload NRF-related PDF, Word, Excel and text documents.
        Uploaded documents are extracted, chunked and added
        to the semantic search index.
        """
    )

    uploaded_files = st.file_uploader(
        "Upload NRF Documents",
        type=[
            "pdf",
            "docx",
            "xlsx",
            "xls",
            "txt"
        ],
        accept_multiple_files=True,
        key="nrf_documents"
    )

    if uploaded_files:

        for uploaded_file in uploaded_files:

            st.markdown(
                f"### `{uploaded_file.name}`"
            )

            col1, col2 = st.columns(2)

            with col1:

                document_title = st.text_input(
                    "Document title",
                    value=os.path.splitext(
                        uploaded_file.name
                    )[0],
                    key=f"title_{uploaded_file.name}"
                )

                document_type = st.selectbox(
                    "Document type",
                    [
                        "Annual Report",
                        "Strategy / Policy",
                        "Research / R&D",
                        "Programme / Funding",
                        "Statistics / Dataset",
                        "Speech",
                        "Press Release",
                        "Parliamentary Material",
                        "Other"
                    ],
                    key=f"type_{uploaded_file.name}"
                )

            with col2:

                document_keywords = st.text_input(
                    "Keywords",
                    key=f"keywords_{uploaded_file.name}"
                )

                document_source = st.text_input(
                    "Source / Reference",
                    key=f"source_{uploaded_file.name}"
                )

            description = st.text_area(
                "Description",
                key=f"description_{uploaded_file.name}"
            )

            if st.button(
                f"📥 Add `{uploaded_file.name}` to Repository",
                key=f"add_doc_{uploaded_file.name}",
                type="primary"
            ):

                existing = document_df[
                    document_df["filename"]
                    .astype(str)
                    .str.lower()
                    == uploaded_file.name.lower()
                ]

                if not existing.empty:

                    st.warning(
                        f"`{uploaded_file.name}` is already "
                        "in the repository."
                    )

                    continue

                save_path = ensure_unique_path(
                    DOCUMENT_FOLDER,
                    uploaded_file.name
                )

                try:

                    with open(
                        save_path,
                        "wb"
                    ) as f:

                        f.write(
                            uploaded_file.getbuffer()
                        )

                except Exception as exc:

                    logger.exception(
                        "Could not save uploaded file %s: %s",
                        uploaded_file.name,
                        exc
                    )

                    st.error(
                        f"Could not save "
                        f"`{uploaded_file.name}`: {exc}"
                    )

                    continue

                with st.spinner(
                    "Extracting document contents..."
                ):

                    extracted_text = extract_raw_text(
                        save_path
                    )

                if not extracted_text.strip():

                    st.error(
                        "No text could be extracted from "
                        "this document."
                    )

                    try:
                        os.remove(save_path)
                    except OSError:
                        pass

                    continue

                document_id = generate_id(
                    "DOC"
                )

                new_document = {

                    "document_id":
                        document_id,

                    "filename":
                        uploaded_file.name,

                    "filepath":
                        save_path,

                    "document_title":
                        document_title.strip(),

                    "document_type":
                        document_type,

                    "description":
                        description.strip(),

                    "keywords":
                        document_keywords.strip(),

                    "source":
                        document_source.strip(),

                    "uploaded_at":
                        datetime.now().isoformat()
                }

                document_df = pd.concat(
                    [
                        document_df,
                        pd.DataFrame(
                            [new_document]
                        )
                    ],
                    ignore_index=True
                )

                save_csv(
                    document_df,
                    DOCUMENT_METADATA_FILE
                )

                with st.spinner(
                    "Adding document to semantic search index..."
                ):

                    index_ok, _ = (
                        rebuild_search_index_safe(
                            pq_df,
                            document_df
                        )
                    )

                if index_ok:

                    st.success(
                        f"`{uploaded_file.name}` successfully "
                        f"added to the NRF repository "
                        f"and search index."
                    )

                else:

                    st.warning(
                        f"`{uploaded_file.name}` was added "
                        f"to the repository, but the search "
                        f"index rebuild failed."
                    )

    st.markdown("---")

    st.subheader(
        "📂 Uploaded NRF Documents"
    )

    document_df = load_csv(
        DOCUMENT_METADATA_FILE,
        DOCUMENT_COLUMNS
    )

    if document_df.empty:

        st.info(
            "No NRF documents have been uploaded."
        )

    else:

        document_df = document_df.sort_values(
            "uploaded_at",
            ascending=False
        )

        st.markdown(
            f"**{len(document_df)} "
            f"documents in repository**"
        )

        for _, row in document_df.iterrows():

            document_title_display = (
                row["document_title"]
                or row["filename"]
                or "Untitled Document"
            )

            with st.expander(
                f"📄 {document_title_display}"
            ):

                st.caption(
                    f"Filename: {row['filename']}"
                )

                st.caption(
                    f"Type: {row['document_type']}"
                )

                if row["description"]:

                    st.write(
                        row["description"]
                    )

                if row["keywords"]:

                    st.caption(
                        f"Keywords: {row['keywords']}"
                    )

                if row["source"]:

                    st.caption(
                        f"Source: {row['source']}"
                    )

                col1, col2 = st.columns(2)

                with col1:

                    filepath = row[
                        "filepath"
                    ]

                    if (
                        isinstance(filepath, str)
                        and os.path.exists(filepath)
                    ):

                        try:

                            with open(
                                filepath,
                                "rb"
                            ) as f:

                                file_bytes = f.read()

                            st.download_button(
                                "⬇️ Download",
                                data=file_bytes,
                                file_name=row[
                                    "filename"
                                ],
                                key=(
                                    f"download_"
                                    f"{row['document_id']}"
                                )
                            )

                        except Exception as exc:

                            logger.warning(
                                "Could not open repository "
                                "document %s: %s",
                                filepath,
                                exc
                            )

                            st.caption(
                                "⚠️ Stored file could not "
                                "be opened."
                            )

                    else:

                        st.caption(
                            "⚠️ Stored file is missing."
                        )

                with col2:

                    if st.button(
                        "🗑️ Delete",
                        key=(
                            f"delete_doc_"
                            f"{row['document_id']}"
                        )
                    ):

                        filepath = row[
                            "filepath"
                        ]

                        if (
                            isinstance(filepath, str)
                            and os.path.exists(filepath)
                        ):

                            try:
                                os.remove(filepath)

                            except Exception as exc:

                                logger.warning(
                                    "Could not delete file "
                                    "%s: %s",
                                    filepath,
                                    exc
                                )

                        document_df = document_df[
                            document_df[
                                "document_id"
                            ]
                            != row["document_id"]
                        ]

                        save_csv(
                            document_df,
                            DOCUMENT_METADATA_FILE
                        )

                        with st.spinner(
                            "Updating search index..."
                        ):

                            index_ok, _ = (
                                rebuild_search_index_safe(
                                    pq_df,
                                    document_df
                                )
                            )

                        if index_ok:

                            st.success(
                                "Document deleted."
                            )

                        else:

                            st.warning(
                                "Document deleted, but the "
                                "search index rebuild failed."
                            )

                        st.rerun()


# ============================================================
# ⚙️ TAB 4 — REPOSITORY MANAGEMENT
# ============================================================

with tab_admin:

    st.header(
        "⚙️ Repository Management"
    )

    pq_df = load_csv(
        PQ_METADATA_FILE,
        PQ_COLUMNS
    )

    document_df = load_csv(
        DOCUMENT_METADATA_FILE,
        DOCUMENT_COLUMNS
    )

    try:
        search_index = PQAI.load_search_index()

    except Exception as exc:

        logger.warning(
            "Could not load search index: %s",
            exc
        )

        search_index = pd.DataFrame()

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "Parliamentary Questions",
            len(pq_df)
        )

    with col2:

        st.metric(
            "NRF Documents",
            len(document_df)
        )

    with col3:

        st.metric(
            "Searchable Chunks",
            len(search_index)
        )

    st.markdown("---")

    st.subheader(
        "🔄 Search Index"
    )

    st.write(
        """
        Rebuild the semantic search index after adding or
        modifying repository files outside the application.
        """
    )

    if st.button(
        "🔄 Rebuild Semantic Search Index",
        type="primary"
    ):

        with st.spinner(
            "Rebuilding NRF semantic search index..."
        ):

            index_ok, rebuilt = (
                rebuild_search_index_safe(
                    pq_df,
                    document_df
                )
            )

        if index_ok:

            st.success(
                f"Search index rebuilt successfully. "
                f"{len(rebuilt)} searchable chunks created."
            )

        else:

            st.error(
                "Search index rebuild failed. "
                "Check the application logs for the "
                "underlying PQAI error."
            )

    st.markdown("---")

    st.subheader(
        "🩺 Search Index Health"
    )

    embeddings = None

    try:
        embeddings = PQAI.load_embeddings()

    except Exception as exc:

        logger.warning(
            "Could not load embeddings: %s",
            exc
        )

    index_count = len(search_index)

    if embeddings is None:
        embedding_count = 0

    else:
        try:
            embedding_count = len(embeddings)
        except TypeError:
            embedding_count = 0

    health_col1, health_col2 = st.columns(2)

    with health_col1:

        st.metric(
            "Indexed passages",
            index_count
        )

    with health_col2:

        st.metric(
            "Embedding vectors",
            embedding_count
        )

    if (
        index_count == embedding_count
        and index_count > 0
    ):

        st.success(
            "Search index and embeddings are synchronized."
        )

    elif (
        index_count == 0
        and embedding_count == 0
    ):

        st.info(
            "The search index is currently empty."
        )

    else:

        st.warning(
            "The search index and embeddings are not "
            "synchronized. Rebuild the semantic search index."
        )

    st.markdown("---")

    st.subheader(
        "📊 Repository Data"
    )

    st.write(
        "Parliamentary Questions"
    )

    if not pq_df.empty:

        st.dataframe(
            pq_df,
            use_container_width=True,
            hide_index=True
        )

    else:

        st.caption(
            "No Parliamentary Questions in repository."
        )

    st.write(
        "NRF Documents"
    )

    if not document_df.empty:

        st.dataframe(
            document_df,
            use_container_width=True,
            hide_index=True
        )

    else:

        st.caption(
            "No NRF documents in repository."
        )