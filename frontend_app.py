"""
Streamlit Frontend for AI Code Reviewer
Interactive UI for GitHub PR analysis
"""

import os
import streamlit as st
import requests
import json
from typing import Optional

# Configuration
BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")
# Ensure HTTPS for internal domain
if "railway.internal" in BACKEND_URL and not BACKEND_URL.startswith("https://"):
    BACKEND_URL = f"https://{BACKEND_URL}"

# Page config
st.set_page_config(
    page_title="AI Code Reviewer",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main {
        padding: 2rem;
    }
    .stTextInput {
        margin-bottom: 1rem;
    }
    .analysis-box {
        background-color: #f0f2f6;
        color: #1a1a1a;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .issue-critical {
        background-color: #ffe0e0;
        color: #1a1a1a;
        padding: 1rem;
        border-left: 4px solid #d32f2f;
        border-radius: 0.25rem;
        margin: 0.5rem 0;
    }
    .issue-high {
        background-color: #fff3e0;
        color: #1a1a1a;
        padding: 1rem;
        border-left: 4px solid #f57c00;
        border-radius: 0.25rem;
        margin: 0.5rem 0;
    }
    .issue-medium {
        background-color: #fff9c4;
        color: #1a1a1a;
        padding: 1rem;
        border-left: 4px solid #fbc02d;
        border-radius: 0.25rem;
        margin: 0.5rem 0;
    }
    .issue-low {
        background-color: #e8f5e9;
        color: #1a1a1a;
        padding: 1rem;
        border-left: 4px solid #388e3c;
        border-radius: 0.25rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "reviews" not in st.session_state:
    st.session_state.reviews = {}
if "current_review" not in st.session_state:
    st.session_state.current_review = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "session_token" not in st.session_state:
    st.session_state.session_token = None
if "github_user" not in st.session_state:
    st.session_state.github_user = None
if "manual_token" not in st.session_state:
    st.session_state.manual_token = ""

# Pick up the session token GitHub OAuth callback appends to the URL after
# a successful login, then strip it from the address bar.
query_params = st.experimental_get_query_params()
if "session_token" in query_params:
    st.session_state.session_token = query_params["session_token"][0]
    st.experimental_set_query_params()
    st.rerun()


def call_backend(endpoint: str, method: str = "GET", data: dict = None, params: dict = None):
    """Call backend API"""
    try:
        url = f"{BACKEND_URL}{endpoint}"
        if method == "POST":
            response = requests.post(url, json=data, params=params, timeout=300, verify=False)
        else:
            response = requests.get(url, params=params, timeout=10, verify=False)

        if response.status_code >= 400:
            st.error(f"Error: {response.status_code} - {response.text}")
            return None

        return response.json()

    except requests.exceptions.Timeout:
        st.error("Request timed out. Analysis may be taking longer than expected.")
        return None
    except requests.exceptions.ConnectionError:
        st.error(f"Cannot connect to backend at {BACKEND_URL}. Make sure it's running.")
        return None
    except Exception as e:
        st.error(f"Error calling backend: {str(e)}")
        return None


def get_github_user():
    """Fetch the authenticated GitHub user for the current session, if any."""
    if not st.session_state.session_token:
        return None
    result = call_backend("/auth/me", params={"session_token": st.session_state.session_token})
    if result and result.get("authenticated"):
        return result["user"]
    return None


def github_disconnect():
    """Log out of GitHub and clear the local session token."""
    call_backend("/auth/logout", params={"session_token": st.session_state.session_token})
    st.session_state.session_token = None
    st.session_state.github_user = None


def display_analysis(analysis: str):
    """Display analysis with formatting"""
    st.markdown("### 📋 Code Review Analysis")

    lines = analysis.split("\n")

    for line in lines:
        if "CRITICAL" in line or "Critical" in line:
            st.markdown(f'<div class="issue-critical">{line}</div>', unsafe_allow_html=True)
        elif "HIGH" in line or "High" in line:
            st.markdown(f'<div class="issue-high">{line}</div>', unsafe_allow_html=True)
        elif "MEDIUM" in line or "Medium" in line:
            st.markdown(f'<div class="issue-medium">{line}</div>', unsafe_allow_html=True)
        elif "LOW" in line or "Low" in line:
            st.markdown(f'<div class="issue-low">{line}</div>', unsafe_allow_html=True)
        elif line.strip():
            st.write(line)


# Main UI
st.title("🤖 AI Code Reviewer")
st.markdown("Analyze GitHub PRs for bugs, security issues, and improvements")

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuration")

    backend_status = call_backend("/health")
    if backend_status:
        st.success(f"✅ Backend connected")
        st.caption(f"Using LLM: **{backend_status.get('llm_provider', 'unknown').upper()}**")
    else:
        st.error("❌ Backend not reachable")

    st.divider()

    st.subheader("🐙 GitHub")

    if st.session_state.session_token and st.session_state.github_user is None:
        st.session_state.github_user = get_github_user()
        if st.session_state.github_user is None:
            # Session token is stale/invalid - drop it.
            st.session_state.session_token = None

    if st.session_state.github_user:
        user = st.session_state.github_user
        st.success(f"✅ Connected as **{user.get('login')}**")
        if st.button("🔌 Disconnect", use_container_width=True):
            github_disconnect()
            st.rerun()
    else:
        st.caption("Connect your GitHub account to analyze private repos")
        st.markdown(
            f'<a href="{BACKEND_URL}/auth/github/login" target="_self">'
            f'<button style="width:100%;padding:0.5rem;border-radius:0.5rem;'
            f'border:1px solid #d0d0d0;cursor:pointer;">🐙 Connect GitHub</button></a>',
            unsafe_allow_html=True,
        )

        with st.expander("🔑 Or use a personal access token (local dev)"):
            st.session_state.manual_token = st.text_input(
                "GitHub Token",
                type="password",
                value=st.session_state.manual_token,
                help="Paste a GitHub personal access token. Useful for local "
                     "development when running OAuth isn't convenient (e.g. no "
                     "public callback URL). Never leaves your machine.",
            )

# Main content
tab1, tab2 = st.tabs(["📊 Analyze PR", "💬 Ask Questions"])

# Tab 1: Analyze PR
with tab1:
    st.subheader("Enter GitHub PR URL")

    with st.form("analyze_form"):
        pr_url = st.text_input(
            "PR URL",
            placeholder="https://github.com/owner/repo/pull/123",
            help="Paste a GitHub pull request URL"
        )
        analyze_button = st.form_submit_button("🔍 Analyze PR", use_container_width=True)

    if st.session_state.current_review:
        if st.button("🔄 Clear", use_container_width=True):
            st.session_state.current_review = None
            st.session_state.chat_history = []
            st.rerun()

    if analyze_button:
        if not pr_url:
            st.error("Please enter a PR URL")
        else:
            with st.spinner("🔍 Analyzing PR... This may take a minute..."):
                result = call_backend(
                    "/analyze",
                    method="POST",
                    data={
                        "pr_url": pr_url,
                        "session_token": st.session_state.session_token,
                        "access_token": st.session_state.manual_token or None
                    }
                )

                if result:
                    st.session_state.current_review = result
                    st.session_state.chat_history = []

                    st.success("✅ Analysis complete!")

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Files Changed", result["files_changed"])
                    with col2:
                        st.metric("Author", result["pr_author"])
                    with col3:
                        st.metric("Status", result["status"].upper())

                    st.divider()

                    display_analysis(result["analysis"])

    if st.session_state.current_review:
        st.divider()
        review = st.session_state.current_review
        st.markdown(f"### 📌 {review['pr_title']}")
        st.caption(f"PR: {review['pr_url']}")

# Tab 2: Ask Questions
with tab2:
    if not st.session_state.current_review:
        st.info("👈 Analyze a PR first in the 'Analyze PR' tab to ask questions")
    else:
        st.subheader(f"Questions about: {st.session_state.current_review['pr_title']}")

        for msg in st.session_state.chat_history:
            role = "user" if msg["role"] == "user" else "assistant"
            with st.chat_message(role):
                st.markdown(msg["content"])

        with st.form("follow_up_form", clear_on_submit=True):
            question = st.text_input(
                "Ask a follow-up question",
                placeholder="e.g., 'Is this a security vulnerability?'",
            )
            send_clicked = st.form_submit_button("Send")

        if send_clicked:
            if not question:
                st.error("Please ask a question")
            else:
                with st.spinner("Thinking..."):
                    result = call_backend(
                        "/follow-up",
                        method="POST",
                        data={
                            "review_id": st.session_state.current_review["review_id"],
                            "question": question
                        }
                    )

                    if result:
                        st.session_state.chat_history.append({
                            "role": "user",
                            "content": question
                        })
                        st.session_state.chat_history.append({
                            "role": "agent",
                            "content": result["answer"]
                        })

                        st.rerun()

# Footer
st.divider()
st.markdown("""
---
**AI Code Reviewer** | Powered by LangChain & Claude
- 🐙 Analyze public and private GitHub PRs
- 🔍 Detect bugs, security issues, and improvements
- 💡 Get AI-powered suggestions
""")

