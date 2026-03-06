"""Dashboard / Home page — portfolio summary."""

import pandas as pd
import streamlit as st

from ot_frontend import api_client
from ot_frontend.components import health_badge


def render():
    st.header("Dashboard")

    try:
        summary = api_client.get_dashboard_summary()
    except Exception as e:
        st.error(f"Could not connect to API: {e}")
        st.info("Make sure the API server is running on port 8000.")
        return

    # Top-level metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Contracts", summary["total_contracts"])
    with col2:
        st.metric("Obligations", summary["total_obligations"])
    with col3:
        st.metric("Overdue", summary["overdue_count"], delta=None)
    with col4:
        st.metric("Due (7 days)", summary["upcoming_7_days"])
    with col5:
        avg = summary.get("avg_health_score")
        st.metric("Avg Health", f"{avg:.0f}" if avg else "—")

    st.divider()

    # Charts
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("Obligations by Status")
        status_data = summary.get("status_breakdown", {})
        if status_data:
            df = pd.DataFrame(
                [{"Status": k.replace("_", " ").title(), "Count": v} for k, v in status_data.items()]
            )
            st.bar_chart(df.set_index("Status"))
        else:
            st.info("No obligations yet.")

    with col_right:
        st.subheader("Obligations by Type")
        type_data = summary.get("type_breakdown", {})
        if type_data:
            df = pd.DataFrame(
                [{"Type": k.replace("_", " ").title(), "Count": v} for k, v in type_data.items()]
            )
            st.bar_chart(df.set_index("Type"))
        else:
            st.info("No obligations yet.")

    st.divider()

    # Contract health scores table
    st.subheader("Contract Health Scores")
    try:
        health_data = api_client.get_health_scores()
        if health_data:
            rows = []
            for c in health_data:
                rows.append({
                    "Contract": c["title"],
                    "Counterparty": c["counterparty"],
                    "Type": c["contract_type"].upper(),
                    "Health": health_badge(c.get("health_score")),
                    "Obligations": c.get("obligation_count", 0),
                    "Overdue": c.get("overdue_count", 0),
                })
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        else:
            st.info("No contracts loaded. Load sample data from Settings to get started.")
    except Exception:
        st.warning("Could not load health scores.")
