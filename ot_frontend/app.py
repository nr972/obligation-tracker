"""Contract Obligation Tracker — Streamlit Frontend."""

import streamlit as st
import streamlit.components.v1 as components

from ot_frontend import api_client

st.set_page_config(
    page_title="Contract Obligation Tracker",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Shutdown state machine ──────────────────────────────────────────────
# If the shutdown flag is set, replace the entire page with a static HTML
# message *before* Streamlit tries to talk to the (now-dead) backend.
# This prevents the "connection error" / reconnection toast from appearing.

if st.session_state.get("_shutdown_triggered"):
    _SHUTDOWN_HTML = """
    <html>
    <head><title>App Shut Down</title></head>
    <body style="
        margin:0; padding:0;
        display:flex; align-items:center; justify-content:center;
        height:100vh;
        background:#f8f9fa; font-family:system-ui,-apple-system,sans-serif;
    ">
    <div style="text-align:center; max-width:460px; padding:2rem;">
        <h1 style="font-size:1.6rem; margin-bottom:0.5rem;">
            App has been shut down
        </h1>
        <p style="color:#555; font-size:1rem;">
            The API and dashboard servers have stopped.
            You can close this browser tab.
        </p>
        <p style="color:#999; font-size:0.85rem; margin-top:2rem;">
            To restart, run <code>./start.sh</code> again.
        </p>
    </div>
    <script>
        // Suppress Streamlit's WebSocket reconnection UI by overwriting
        // the parent document before the framework notices the lost connection.
        try {
            window.parent.document.open();
            window.parent.document.write(document.documentElement.outerHTML);
            window.parent.document.close();
        } catch(e) { /* cross-origin or already replaced */ }
    </script>
    </body>
    </html>
    """
    components.html(_SHUTDOWN_HTML, height=600, scrolling=False)
    st.stop()

# ── Normal app ──────────────────────────────────────────────────────────

# Navigation
PAGES = {
    "Dashboard": "dashboard",
    "Contracts": "contracts",
    "Obligations": "obligations",
    "Calendar": "calendar_view",
    "Settings": "settings",
}

st.sidebar.title("Obligation Tracker")
page = st.sidebar.radio("Navigate", list(PAGES.keys()))

# Shutdown button at bottom of sidebar
st.sidebar.divider()
if st.sidebar.button("Shut Down App", type="secondary", use_container_width=True):
    try:
        api_client.request_shutdown()
    except Exception:
        pass  # connection may drop before response arrives
    st.session_state["_shutdown_triggered"] = True
    st.rerun()

# Import and render the selected page
if page == "Dashboard":
    from ot_frontend.pages.dashboard import render
elif page == "Contracts":
    from ot_frontend.pages.contracts import render
elif page == "Obligations":
    from ot_frontend.pages.obligations import render
elif page == "Calendar":
    from ot_frontend.pages.calendar_view import render
elif page == "Settings":
    from ot_frontend.pages.settings import render

render()
