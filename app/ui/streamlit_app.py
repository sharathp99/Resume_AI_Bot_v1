from __future__ import annotations

import streamlit as st
import pandas as pd
import requests

API_URL = st.secrets.get("api_url", "http://localhost:8000") if hasattr(st, "secrets") else "http://localhost:8000"

st.set_page_config(page_title="Resume Intelligence Platform", layout="wide")
st.title("Resume Intelligence Platform")
st.caption("Internal recruiter copilot with grounded retrieval, ranking, and evidence-backed answers.")


def api_get(path: str, **kwargs):
    response = requests.get(f"{API_URL}{path}", timeout=30, **kwargs)
    response.raise_for_status()
    return response.json()


def api_post_json(path: str, payload: dict):
    response = requests.post(f"{API_URL}{path}", json=payload, timeout=120)
    response.raise_for_status()
    return response.json()


def api_post_response(path: str, payload: dict):
    response = requests.post(f"{API_URL}{path}", json=payload, timeout=120)
    response.raise_for_status()
    return response


tab_home, tab_ingestion, tab_search, tab_detail, tab_compare, tab_chat, tab_export = st.tabs(
    ["Dashboard", "Resume Ingestion", "Candidate Search", "Candidate Detail", "Compare", "Chat", "Export"]
)

with tab_home:
    st.subheader("Overview")
    try:
        candidates = api_get("/api/candidates/")
        history = api_get("/api/search/history")
        df = pd.DataFrame(candidates)
        st.metric("Total candidates", len(df))
        if not df.empty:
            st.dataframe(df[["id", "role_bucket", "full_name", "current_title", "location"]])
        st.subheader("Recent Query History")
        if history:
            st.dataframe(pd.DataFrame(history))
        else:
            st.info("No recruiter query history yet.")
    except Exception as exc:
        st.warning(f"API unavailable: {exc}")

with tab_ingestion:
    st.subheader("Resume Ingestion")
    role_bucket = st.text_input("Role bucket", value="data_engineer", key="ingest_role")
    reindex = st.checkbox("Recreate vector collection before ingest", value=False)
    if st.button("Ingest resumes"):
        try:
            result = api_post_json("/api/ingestion/resumes", {"role_bucket": role_bucket, "reindex": reindex})
            st.success(f"Indexed {result['indexed_count']} files. Failed: {result['failed_count']}")
            st.dataframe(pd.DataFrame(result["files"]))
        except Exception as exc:
            st.error(str(exc))

with tab_search:
    st.subheader("Search candidates by JD")
    role_bucket = st.text_input("Role bucket", value="data_engineer", key="search_role")
    top_k = st.slider("Top K", min_value=1, max_value=20, value=5)
    jd_text = st.text_area("Job description", height=240)
    if st.button("Search top candidates"):
        try:
            result = api_post_json("/api/search/jd", {"role_bucket": role_bucket, "jd_text": jd_text, "top_k": top_k})
            for row in result["results"]:
                with st.container(border=True):
                    st.markdown(f"### {row['full_name'] or row['candidate_id']} — score {row['score']}")
                    st.write(f"Email: {row.get('email')} | Phone: {row.get('phone')} | Location: {row.get('location')}")
                    st.write(f"Top skills: {', '.join(row.get('top_skills', []))}")
                    st.write(f"Strengths: {', '.join(row.get('strengths', []))}")
                    st.write(f"Gaps: {', '.join(row.get('gaps', []))}")
                    st.write(row.get("explanation"))
                    st.code("\n\n".join(row.get("evidence_snippets", [])))
        except Exception as exc:
            st.error(str(exc))

with tab_detail:
    st.subheader("Candidate Detail")
    candidate_id = st.text_input("Candidate ID")
    if st.button("Load candidate"):
        try:
            candidate = api_get(f"/api/candidates/{candidate_id}")
            st.json(candidate)
        except Exception as exc:
            st.error(str(exc))

with tab_compare:
    st.subheader("Candidate Comparison")
    role_bucket = st.text_input("Role bucket", value="data_engineer", key="compare_role")
    comparison_ids = st.text_input("Candidate IDs (comma separated)")
    compare_jd = st.text_area("Comparison JD", key="compare_jd")
    if st.button("Compare candidates"):
        try:
            result = api_post_json(
                "/api/search/compare",
                {
                    "role_bucket": role_bucket,
                    "candidate_ids": [item.strip() for item in comparison_ids.split(",") if item.strip()],
                    "jd_text": compare_jd,
                },
            )
            st.write(result["comparison"]["recommendation"])
            st.dataframe(pd.DataFrame(result["comparison"]["candidates"]))
        except Exception as exc:
            st.error(str(exc))

with tab_chat:
    st.subheader("Recruiter Copilot Chat")
    chat_role = st.text_input("Role bucket", value="data_engineer", key="chat_role")
    chat_candidate_ids = st.text_input("Candidate IDs (optional)")
    chat_jd = st.text_area("JD context (optional)", key="chat_jd")
    chat_message = st.text_area("Ask the copilot", height=160)
    if st.button("Send chat request"):
        try:
            result = api_post_json(
                "/api/chat/",
                {
                    "role_bucket": chat_role or None,
                    "candidate_ids": [item.strip() for item in chat_candidate_ids.split(",") if item.strip()],
                    "jd_text": chat_jd or None,
                    "message": chat_message,
                },
            )
            st.write(result["answer"])
            if result.get("evidence"):
                st.dataframe(pd.DataFrame(result["evidence"]))
        except Exception as exc:
            st.error(str(exc))

with tab_export:
    st.subheader("Export shortlist")
    export_ids = st.text_input("Candidate IDs for export")
    export_format = st.selectbox("Format", options=["csv", "xlsx"])
    if st.button("Export shortlist"):
        try:
            payload = {
                "candidate_ids": [item.strip() for item in export_ids.split(",") if item.strip()],
                "format": export_format,
            }
            response = api_post_response("/api/exports/shortlist", payload)
            st.success("Export generated successfully.")
            st.download_button(
                label=f"Download {export_format.upper()}",
                data=response.content,
                file_name=f"shortlist_export.{export_format}",
                mime=response.headers.get("content-type", "application/octet-stream"),
            )
        except Exception as exc:
            st.error(str(exc))
