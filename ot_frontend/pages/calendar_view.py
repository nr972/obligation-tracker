"""Calendar page — visual month/week view of obligation deadlines."""

import streamlit as st
from streamlit_calendar import calendar

from ot_frontend import api_client
from ot_frontend.components import display_error


def render():
    st.header("Obligation Calendar")

    try:
        events = api_client.get_calendar_events()
    except Exception as e:
        display_error(f"Could not load calendar events: {e}")
        return

    if not events:
        st.info("No obligations with due dates found. Load sample data or add obligations to see the calendar.")
        return

    # Format events for streamlit-calendar
    cal_events = []
    for ev in events:
        cal_events.append({
            "title": ev["title"],
            "start": ev["start"],
            "end": ev["end"],
            "backgroundColor": ev["color"],
            "borderColor": ev["color"],
            "extendedProps": {
                "id": ev["id"],
                "contract": ev["contract_title"],
                "type": ev["obligation_type"],
                "status": ev["status"],
                "risk": ev["risk_level"],
            },
        })

    calendar_options = {
        "initialView": "dayGridMonth",
        "headerToolbar": {
            "left": "prev,next today",
            "center": "title",
            "right": "dayGridMonth,timeGridWeek,listWeek",
        },
        "navLinks": True,
        "editable": False,
        "selectable": False,
        "eventDisplay": "block",
        "height": 650,
    }

    state = calendar(events=cal_events, options=calendar_options, key="obligation_calendar")

    # Show clicked event details
    if state and state.get("eventClick"):
        event_data = state["eventClick"].get("event", {})
        props = event_data.get("extendedProps", {})
        st.divider()
        st.subheader("Obligation Details")
        st.write(f"**Title:** {event_data.get('title', 'N/A')}")
        st.write(f"**Contract:** {props.get('contract', 'N/A')}")
        st.write(f"**Type:** {props.get('type', 'N/A').replace('_', ' ').title()}")
        st.write(f"**Status:** {props.get('status', 'N/A').replace('_', ' ').title()}")
        st.write(f"**Risk Level:** {props.get('risk', 'N/A').title()}")
        st.write(f"**Due Date:** {event_data.get('start', 'N/A')}")

    # Legend
    st.divider()
    st.caption("**Legend:** 🔴 Critical | 🟠 High | 🔵 Medium | 🟢 Low | ⬛ Overdue")
