"""Settings page — mode indicator, demo data management."""

import streamlit as st

from ot_frontend import api_client
from ot_frontend.components import display_error, display_success


def render():
    st.header("Settings")

    # Mode indicator
    try:
        mode = api_client.get_mode()
        health = api_client.get_health()
    except Exception as e:
        display_error(f"Could not connect to API: {e}")
        st.info("Make sure the API server is running on port 8000.")
        return

    st.subheader("System Status")
    col1, col2, col3 = st.columns(3)
    with col1:
        ai_status = "Enabled" if mode.get("ai_enabled") else "Not configured"
        st.metric("AI Extraction", ai_status)
    with col2:
        st.metric("API Version", health.get("version", "unknown"))
    with col3:
        st.metric("API Status", health.get("status", "unknown").title())

    if not mode.get("ai_enabled"):
        st.info(
            "AI extraction is not available. Set the `ANTHROPIC_API_KEY` environment variable to enable it. "
            "You can still use demo data and manual obligation entry."
        )

    st.divider()

    # Demo data management
    st.subheader("Sample Data")
    st.write("Load synthetic sample contracts and obligations to explore the dashboard.")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Load Sample Data", use_container_width=True):
            with st.spinner("Loading sample data..."):
                try:
                    result = api_client.load_demo_data()
                    display_success(f"Loaded {result['loaded']} sample obligations across 8 contracts.")
                except Exception as e:
                    display_error(f"Failed to load sample data: {e}")

    with col2:
        if st.button("Clear Sample Data", use_container_width=True, type="secondary"):
            try:
                result = api_client.reset_demo_data()
                display_success(f"Cleared {result['cleared']} sample contracts and their obligations.")
            except Exception as e:
                display_error(f"Failed to clear sample data: {e}")

    st.divider()

    # About
    st.subheader("About")
    st.write("**Contract Obligation Tracker & Compliance Dashboard**")
    st.write("Extract and track contract obligations, deadlines, SLAs, and deliverables.")
    st.write("Part of the Legal Quant portfolio — open-source tools for in-house legal teams.")
    st.write("MIT License | Copyright (c) 2026 Noam Raz and Pleasant Secret Labs")
