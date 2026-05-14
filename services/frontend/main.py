import os

import httpx
import streamlit as st

API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(page_title="DocSense", page_icon="📄")
st.title("📄 DocSense")
st.caption("Multi-tenant Document Q&A Platform")

st.divider()

with st.sidebar:
    st.header("System Status")
    if st.button(label="Check API health", key="check_api_health"):
        try:
            r = httpx.get(f"{API_URL}/health", timeout=5)
            if r.status_code == 200:
                st.success("API online ✅")
            else:
                st.error(f"API returned {r.status_code} ❌")
        except httpx.RequestError:
            st.error("API unreachable ❌")

st.info("Phase 1 - skeleton only. Features coming soon.")
