import requests
import feedparser
import pandas as pd
from textwrap import shorten
from helper_functions.llm import get_completion


# ---------------------------------------------------------------------
# 🔹 PART 1: Structured Summarization for Uploaded Papers
# ---------------------------------------------------------------------
def summarize_paper_structured(text, filename):
    """Summarize a paper into structured components."""
    if len(text) > 12000:
        text = text[:12000]

    prompt = f"""
    You are an expert academic summarizer. 
    Read the following research paper titled "{filename}" and extract the key information.

    Respond ONLY in **structured Markdown format** with these sections:

    ### 1. Research Questions / Objectives
    - What the study aimed to investigate.

    ### 2. Methodology
    - How the study was conducted (design, data, participants, analysis).

    ### 3. Key Findings / Implications
    - Main results, insights, and implications.

    Research Paper Text:
    {text}
    """

    return get_completion(prompt, model="gpt-4o-mini", temperature=0.3, max_tokens=1024).strip()


def query_repository(question, repo_data):
    """Query the repository using structured summaries."""
    if not repo_data:
        return "⚠️ Repository is empty. Please upload and summarize papers first."

    combined_text = "\n\n---\n\n".join([
        f"{fn}:\n{data['structured']}" for fn, data in repo_data.items()
    ])

    prompt = f"""
    You are a research assistant.
    Use the following structured research summaries to answer the user's question.

    Summaries:
    {combined_text}

    Question: {question}

    Provide a concise, accurate answer referencing research findings when relevant.
    """

    return get_completion(prompt, model="gpt-4o-mini", temperature=0.4, max_tokens=1024).strip()


def parse_structured_summary(summary_md):
    """Convert markdown sections into a dictionary for table display."""
    sections = {"Research Questions": "", "Methodology": "", "Findings": ""}
    lines = summary_md.splitlines()
    current_key = None

    for line in lines:
        line_lower = line.lower()
        if "research question" in line_lower or "objective" in line_lower:
            current_key = "Research Questions"
        elif "methodology" in line_lower:
            current_key = "Methodology"
        elif "finding" in line_lower or "implication" in line_lower:
            current_key = "Findings"
        elif current_key:
            sections[current_key] += line + " "
    return {k: v.strip() for k, v in sections.items()}


# ---------------------------------------------------------------------
# 🔹 PART 2: Open-Access Research Paper Search & Summarization
# ---------------------------------------------------------------------
def search_open_access_papers(query, max_results=10):
    """
    Searches for open-access research papers using the arXiv API.
    Returns: (combined_summary, insights_df, references)
    """
    base_url = "http://export.arxiv.org/api/query"
    params = {
        "search_query": f"all:{query}",
        "start": 0,
        "max_results": max_results,
    }

    response = requests.get(base_url, params=params, timeout=10)
    if response.status_code != 200:
        return f"❌ Error fetching papers: {response.status_code}", pd.DataFrame(), []

    feed = feedparser.parse(response.text)
    if not feed.entries:
        return f"No open-access papers found for '{query}'.", pd.DataFrame(), []

    papers = []
    for entry in feed.entries:
        papers.append({
            "Title": entry.title,
            "Authors": ", ".join([a.name for a in entry.authors]),
            "Summary": shorten(entry.summary.replace("\n", " "), width=300),
            "Published": entry.published,
            "Link": entry.link
        })

    df = pd.DataFrame(papers)
    references = [p["Link"] for p in papers]
    combined_summary = summarize_papers(papers, query)

    return combined_summary, df, references


def summarize_papers(papers, query):
    """Generate a readable summary from the list of open-access papers."""
    if not papers:
        return f"No papers found for '{query}'."

    summary_parts = [f"### Overview\nFound {len(papers)} open-access papers for **'{query}'**:\n"]
    for i, p in enumerate(papers, 1):
        summary_parts.append(
            f"**{i}. {p['Title']}** — {p['Authors']}\n\n"
            f"📄 {p['Summary']}\n\n"
            f"🗓️ Published: {p['Published']}\n"
            f"🔗 [Read more]({p['Link']})\n"
        )

    return "\n".join(summary_parts)
