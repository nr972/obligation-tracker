"""Contracts page — list, upload, detail view."""

import streamlit as st

from ot_frontend import api_client
from ot_frontend.components import display_error, display_success, health_badge

CONTRACT_TYPES = [
    ("saas", "SaaS"),
    ("vendor", "Vendor"),
    ("dpa", "DPA"),
    ("consulting", "Consulting"),
    ("license", "License"),
    ("msa", "MSA"),
    ("contractor", "Contractor"),
    ("lease", "Lease"),
    ("other", "Other"),
]


def render():
    st.header("Contracts")

    # Action buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Upload Contract", use_container_width=True):
            st.session_state["show_upload"] = True
            st.session_state.pop("show_manual", None)
    with col2:
        if st.button("Add Manually", use_container_width=True):
            st.session_state["show_manual"] = True
            st.session_state.pop("show_upload", None)

    # Upload form
    if st.session_state.get("show_upload"):
        _render_upload_form()

    # Manual form
    if st.session_state.get("show_manual"):
        _render_manual_form()

    st.divider()

    # Filters
    with st.sidebar:
        st.subheader("Filter Contracts")
        search = st.text_input("Search")
        type_filter = st.selectbox("Type", ["All"] + [t[1] for t in CONTRACT_TYPES])
        status_filter = st.selectbox("Status", ["All", "Active", "Expired", "Terminated"])

    type_val = None
    if type_filter != "All":
        type_val = next((t[0] for t in CONTRACT_TYPES if t[1] == type_filter), None)
    status_val = status_filter.lower() if status_filter != "All" else None

    try:
        contracts = api_client.list_contracts(
            status=status_val,
            contract_type=type_val,
            search=search or None,
        )
    except Exception as e:
        display_error(f"Could not load contracts: {e}")
        return

    if not contracts:
        st.info("No contracts found. Upload a contract or load sample data from Settings.")
        return

    # Contract list
    for c in contracts:
        with st.expander(f"{c['title']} — {c['counterparty']} ({c['contract_type'].upper()})"):
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Health", health_badge(c.get("health_score")))
            with col2:
                st.metric("Obligations", c.get("obligation_count", 0))
            with col3:
                st.metric("Overdue", c.get("overdue_count", 0))
            with col4:
                st.metric("Status", c["status"].title())

            dates_col1, dates_col2 = st.columns(2)
            with dates_col1:
                st.write(f"**Effective:** {c.get('effective_date') or 'N/A'}")
            with dates_col2:
                st.write(f"**Expires:** {c.get('expiration_date') or 'N/A'}")

            if c.get("extraction_status") == "pending" and c.get("file_name"):
                mode = api_client.get_mode()
                if mode.get("ai_enabled"):
                    if st.button("Extract Obligations", key=f"extract_{c['id']}"):
                        with st.spinner("Extracting obligations..."):
                            try:
                                result = api_client.extract_obligations(c["id"])
                                display_success(f"Extracted {result['obligations_found']} obligations.")
                                st.rerun()
                            except Exception as e:
                                display_error(f"Extraction failed: {e}")
                else:
                    st.info("AI extraction requires ANTHROPIC_API_KEY. You can add obligations manually.")

            btn_col1, btn_col2 = st.columns(2)
            with btn_col1:
                if st.button("View Details", key=f"view_{c['id']}"):
                    st.session_state["selected_contract"] = c["id"]
                    st.rerun()
            with btn_col2:
                if st.button("Delete", key=f"del_{c['id']}", type="secondary"):
                    api_client.delete_contract(c["id"])
                    st.rerun()

    # Detail view
    if "selected_contract" in st.session_state:
        _render_contract_detail(st.session_state["selected_contract"])


def _render_upload_form():
    st.subheader("Upload Contract")
    with st.form("upload_form"):
        file = st.file_uploader("Contract file (PDF or DOCX)", type=["pdf", "docx"])
        title = st.text_input("Contract title")
        counterparty = st.text_input("Counterparty name")
        contract_type = st.selectbox("Contract type", [t[1] for t in CONTRACT_TYPES])
        submitted = st.form_submit_button("Upload")

        if submitted:
            if not file or not title or not counterparty:
                display_error("Please fill in all fields and select a file.")
            else:
                type_val = next((t[0] for t in CONTRACT_TYPES if t[1] == contract_type), "other")
                try:
                    result = api_client.upload_contract(file, title, counterparty, type_val)
                    display_success(f"Contract '{result['title']}' uploaded successfully.")
                    st.session_state.pop("show_upload", None)
                    st.rerun()
                except Exception as e:
                    display_error(f"Upload failed: {e}")


def _render_manual_form():
    st.subheader("Add Contract Manually")
    with st.form("manual_form"):
        title = st.text_input("Contract title")
        counterparty = st.text_input("Counterparty name")
        contract_type = st.selectbox("Contract type", [t[1] for t in CONTRACT_TYPES])
        effective = st.date_input("Effective date", value=None)
        expiration = st.date_input("Expiration date", value=None)
        submitted = st.form_submit_button("Create")

        if submitted:
            if not title or not counterparty:
                display_error("Title and counterparty are required.")
            else:
                type_val = next((t[0] for t in CONTRACT_TYPES if t[1] == contract_type), "other")
                data = {
                    "title": title,
                    "counterparty": counterparty,
                    "contract_type": type_val,
                }
                if effective:
                    data["effective_date"] = str(effective)
                if expiration:
                    data["expiration_date"] = str(expiration)
                try:
                    result = api_client.create_contract(data)
                    display_success(f"Contract '{result['title']}' created.")
                    st.session_state.pop("show_manual", None)
                    st.rerun()
                except Exception as e:
                    display_error(f"Creation failed: {e}")


def _render_contract_detail(contract_id: int):
    st.divider()
    try:
        detail = api_client.get_contract(contract_id)
    except Exception:
        display_error("Could not load contract details.")
        return

    st.subheader(f"Contract: {detail['title']}")
    st.write(f"**Counterparty:** {detail['counterparty']}")
    st.write(f"**Type:** {detail['contract_type'].upper()}")
    st.write(f"**Health Score:** {health_badge(detail.get('health_score'))}")

    if detail.get("obligations"):
        st.write(f"**Obligations ({len(detail['obligations'])}):**")
        for ob in detail["obligations"]:
            st.write(f"- **{ob['title']}** — {ob['status'].replace('_', ' ').title()} ({ob['risk_level'].title()})")

    if st.button("Close Details"):
        st.session_state.pop("selected_contract", None)
        st.rerun()
