import os

import httpx
import streamlit as st

API_URL = os.getenv("API_URL", "http://localhost:8000")

# --- hardcoded for dev; comes from auth in production ---
TENANT_ID = "f7880935-2fb3-4096-877b-49b7b7b5b5e0"
USER_ID = "a5845bd5-a405-4652-840a-0b22577f00c3"
HEADERS = {"x-tenant-id": TENANT_ID, "x-user-id": USER_ID}

st.set_page_config(page_title="DocSense", page_icon="📄")
st.title("📄 DocSense")
st.caption("Multi-tenant Document Q&A Platform")

with st.sidebar:
    st.header("System Status")
    if st.button("Check API health"):
        try:
            r = httpx.get(f"{API_URL}/health", timeout=5)
            if r.status_code == 200:
                st.success("API online ✅")
            else:
                st.error(f"API returned {r.status_code} ❌")
        except httpx.RequestError:
            st.error("API unreachable ❌")

st.divider()

# ── Upload section ──────────────────────────────────────────
st.header("Upload a document")
uploaded = st.file_uploader("Choose a .txt or .pdf file", type=["txt", "pdf"])
if uploaded and st.button("Upload & process"):
    with st.spinner("Uploading and chunking..."):
        r = httpx.post(
            f"{API_URL}/documents/upload",
            headers=HEADERS,
            files={"file": (uploaded.name, uploaded.getvalue(), uploaded.type)},
            timeout=60,
        )
    if r.status_code == 201:
        data = r.json()
        st.success(f"✅ {data['filename']} — {data['chunks']} chunks — status: {data['status']}")
    else:
        st.error(f"Upload failed: {r.text}")

st.divider()

# ── Search section ──────────────────────────────────────────
st.header("Ask a question")
query = st.text_input("Your question", placeholder="What is...")
top_k = st.slider("Chunks to retrieve", min_value=1, max_value=10, value=5)

if st.button("Search", disabled=not query):
    with st.spinner("Searching and generating answer..."):
        r = httpx.post(
            f"{API_URL}/search/",
            headers=HEADERS,
            json={"query": query, "top_k": top_k},
            timeout=30,
        )
    if r.status_code == 200:
        data = r.json()
        st.subheader("Answer")
        st.write(data["answer"])
        st.subheader("Sources")
        for src in data["sources"]:
            st.caption(f"📄 {src['filename']} · chunk {src['chunk_index']} · score {src['score']:.3f}")
    else:
        st.error(f"Search failed: {r.text}")

st.divider()

# -- Evaluation section --------------------------------------
st.header("Evaluation")
if st.button("Run evaluation"):
    with st.spinner("Running eval on golden set (~30s)..."):
        r = httpx.post(
            f"{API_URL}/evaluation/run",
            headers=HEADERS,
            params={"top_k": 5},
            timeout=120,
        )
    if r.status_code == 200:
        report = r.json()
        summary = report["summary"]

        st.subheader("Summary")
        col1, col2, col3 = st.columns(3)
        col1.metric("Faithfulness", f"{summary['avg_faithfulness']:.3f}")
        col2.metric("Answer Similarity", f"{summary['avg_answer_similarity']:.3f}")
        col3.metric("Context Precision", f"{summary['avg_context_precision']:.3f}")

        st.subheader("Per-question results")

        for result in report["results"]:
            with st.expander(f"{result['id']} - {result['question']}"):
                st.write(f"**Generated:** {result['generated_answer']}")
                st.write(f"**Gound truth:** {result['ground_truth']}")
                m = result["metrics"]
                st.caption(
                    f"Faithfulness: {m['faithfulness']} · "
                    f"Similarity: {m['answer_similarity']} · "
                    f"Precision: {m['context_precision']}"
                )

    else:
        st.error(f"Eval failed: {r.text}")
