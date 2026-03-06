"""Obligations page — filterable table, status management, manual entry."""

import pandas as pd
import streamlit as st

from ot_frontend import api_client
from ot_frontend.components import display_error, display_success

STATUSES = ["pending", "in_progress", "completed", "overdue", "waived", "escalated"]
OBLIGATION_TYPES = [
    "payment", "delivery", "reporting", "compliance", "notification",
    "renewal", "sla", "confidentiality", "data_protection", "other",
]
RISK_LEVELS = ["critical", "high", "medium", "low"]
RESPONSIBLE_PARTIES = [("us", "Us"), ("counterparty", "Counterparty"), ("both", "Both")]
DEADLINE_TYPES = [("fixed", "Fixed"), ("recurring", "Recurring"), ("ongoing", "Ongoing"), ("event_triggered", "Event Triggered")]


def render():
    st.header("Obligations")

    if st.button("Add Obligation"):
        st.session_state["show_add_obligation"] = True

    if st.session_state.get("show_add_obligation"):
        _render_add_form()

    st.divider()

    # Sidebar filters
    with st.sidebar:
        st.subheader("Filter Obligations")
        status_filter = st.selectbox("Status", ["All"] + [s.replace("_", " ").title() for s in STATUSES])
        type_filter = st.selectbox("Obligation Type", ["All"] + [t.replace("_", " ").title() for t in OBLIGATION_TYPES])
        risk_filter = st.selectbox("Risk Level", ["All"] + [r.title() for r in RISK_LEVELS])
        overdue_only = st.checkbox("Overdue only")

    params = {}
    if status_filter != "All":
        params["status"] = status_filter.lower().replace(" ", "_")
    if type_filter != "All":
        params["obligation_type"] = type_filter.lower().replace(" ", "_")
    if risk_filter != "All":
        params["risk_level"] = risk_filter.lower()
    if overdue_only:
        params["overdue_only"] = True

    try:
        obligations = api_client.list_obligations(**params)
    except Exception as e:
        display_error(f"Could not load obligations: {e}")
        return

    if not obligations:
        st.info("No obligations found matching your filters.")
        return

    # Build table data
    rows = []
    for ob in obligations:
        rows.append({
            "ID": ob["id"],
            "Title": ob["title"],
            "Contract": ob.get("contract_title", ""),
            "Type": ob["obligation_type"].replace("_", " ").title(),
            "Party": ob["responsible_party"].title(),
            "Due Date": ob.get("next_due_date") or ob.get("deadline_date") or "—",
            "Risk": ob["risk_level"].title(),
            "Status": ob["status"].replace("_", " ").title(),
            "Source": ob["extraction_source"].title(),
        })

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)

    # Obligation detail / status change
    st.subheader("Manage Obligation")
    ob_options = {f"{ob['title']} (ID: {ob['id']})": ob["id"] for ob in obligations}
    selected = st.selectbox("Select obligation", ["—"] + list(ob_options.keys()))

    if selected != "—":
        ob_id = ob_options[selected]
        try:
            detail = api_client.get_obligation(ob_id)
        except Exception:
            display_error("Could not load obligation details.")
            return

        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Description:** {detail.get('description') or 'None'}")
            st.write(f"**Penalty:** {detail.get('penalty') or 'None'}")
            st.write(f"**Source Section:** {detail.get('source_section') or 'N/A'}")
        with col2:
            st.write(f"**Deadline Type:** {detail['deadline_type'].replace('_', ' ').title()}")
            st.write(f"**Recurrence:** {detail.get('recurrence_pattern') or 'N/A'}")
            st.write(f"**Notes:** {detail.get('notes') or 'None'}")

        # Status change
        current_idx = STATUSES.index(detail["status"]) if detail["status"] in STATUSES else 0
        new_status = st.selectbox(
            "Change status",
            [s.replace("_", " ").title() for s in STATUSES],
            index=current_idx,
            key=f"status_{ob_id}",
        )
        notes = st.text_input("Status change notes", key=f"notes_{ob_id}")

        if st.button("Update Status", key=f"update_{ob_id}"):
            new_status_val = new_status.lower().replace(" ", "_")
            if new_status_val != detail["status"]:
                try:
                    api_client.change_obligation_status(ob_id, new_status_val, notes or None)
                    display_success(f"Status updated to {new_status}.")
                    st.rerun()
                except Exception as e:
                    display_error(f"Status update failed: {e}")

        # Status history
        if detail.get("status_history"):
            st.write("**Status History:**")
            for h in detail["status_history"]:
                note_text = f" — {h['notes']}" if h.get("notes") else ""
                st.write(f"- {h['old_status']} → {h['new_status']} at {h['changed_at']}{note_text}")

        if st.button("Delete Obligation", key=f"del_ob_{ob_id}", type="secondary"):
            api_client.delete_obligation(ob_id)
            st.rerun()


def _render_add_form():
    st.subheader("Add Obligation")

    try:
        contracts = api_client.list_contracts()
    except Exception:
        display_error("Could not load contracts.")
        return

    if not contracts:
        st.warning("Create a contract first before adding obligations.")
        return

    contract_options = {f"{c['title']} ({c['counterparty']})": c["id"] for c in contracts}

    with st.form("add_obligation"):
        contract_sel = st.selectbox("Contract", list(contract_options.keys()))
        title = st.text_input("Obligation title")
        description = st.text_area("Description (optional)")
        ob_type = st.selectbox("Type", [t.replace("_", " ").title() for t in OBLIGATION_TYPES])
        party = st.selectbox("Responsible party", [p[1] for p in RESPONSIBLE_PARTIES])
        deadline = st.selectbox("Deadline type", [d[1] for d in DEADLINE_TYPES])
        deadline_date = st.date_input("Deadline date (if applicable)", value=None)
        risk = st.selectbox("Risk level", [r.title() for r in RISK_LEVELS], index=2)
        penalty = st.text_input("Penalty for breach (optional)")
        notes = st.text_area("Notes (optional)")

        submitted = st.form_submit_button("Create Obligation")

        if submitted:
            if not title:
                display_error("Title is required.")
            else:
                data = {
                    "contract_id": contract_options[contract_sel],
                    "title": title,
                    "obligation_type": ob_type.lower().replace(" ", "_"),
                    "responsible_party": next((p[0] for p in RESPONSIBLE_PARTIES if p[1] == party), "us"),
                    "deadline_type": next((d[0] for d in DEADLINE_TYPES if d[1] == deadline), "fixed"),
                    "risk_level": risk.lower(),
                }
                if description:
                    data["description"] = description
                if deadline_date:
                    data["deadline_date"] = str(deadline_date)
                if penalty:
                    data["penalty"] = penalty
                if notes:
                    data["notes"] = notes

                try:
                    result = api_client.create_obligation(data)
                    display_success(f"Obligation '{result['title']}' created.")
                    st.session_state.pop("show_add_obligation", None)
                    st.rerun()
                except Exception as e:
                    display_error(f"Creation failed: {e}")
