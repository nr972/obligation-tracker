"""Reusable UI components for the Streamlit frontend."""

import streamlit as st


def health_badge(score: float | None) -> str:
    """Return a colored health score string."""
    if score is None:
        return "—"
    if score >= 80:
        return f"🟢 {score:.0f}"
    elif score >= 50:
        return f"🟡 {score:.0f}"
    else:
        return f"🔴 {score:.0f}"


def status_color(status: str) -> str:
    """Return a color for obligation status."""
    colors = {
        "pending": "blue",
        "in_progress": "orange",
        "completed": "green",
        "overdue": "red",
        "waived": "gray",
        "escalated": "violet",
    }
    return colors.get(status, "gray")


def risk_color(risk: str) -> str:
    """Return a color for risk level."""
    colors = {
        "critical": "red",
        "high": "orange",
        "medium": "blue",
        "low": "green",
    }
    return colors.get(risk, "gray")


def status_pill(status: str) -> str:
    """Return status as a styled label."""
    return f":{status_color(status)}[{status.replace('_', ' ').title()}]"


def risk_pill(risk: str) -> str:
    """Return risk level as a styled label."""
    return f":{risk_color(risk)}[{risk.title()}]"


def metric_card(label: str, value, delta=None):
    """Display a metric in the dashboard."""
    st.metric(label=label, value=value, delta=delta)


def display_error(message: str):
    """Show an error message."""
    st.error(message)


def display_success(message: str):
    """Show a success message."""
    st.success(message)
