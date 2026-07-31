import streamlit as st


# ============================================================
# STREAMLIT PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Nifty 100 Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# MAIN APP
# ============================================================

st.title("📊 Nifty 100 Analytics Dashboard")

st.write(
    """
    Welcome to the Nifty 100 Financial Analytics Dashboard.

    Use the sidebar to navigate through the dashboard.
    """
)


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title(
    "📊 Nifty 100 Analytics"
)

st.sidebar.success(
    "Dashboard is running successfully!"
)

st.sidebar.markdown(
    """
    ### Available Screens

    - 🏠 Home
    - 🏢 Company Profile
    - 🔍 Financial Screener
    - 👥 Peer Comparison
    - 📈 Trend Analysis
    - 🏭 Sector Analysis
    - 💰 Capital Allocation
    - 📄 Annual Reports
    """
)


# ============================================================
# DASHBOARD STATUS
# ============================================================

st.divider()

st.subheader(
    "Dashboard Status"
)

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Database",
    "Connected"
)

col2.metric(
    "Dashboard Screens",
    "8"
)

col3.metric(
    "Data Source",
    "SQLite"
)

col4.metric(
    "Status",
    "Running"
)


# ============================================================
# INFORMATION
# ============================================================

st.info(
    """
    The dashboard foundation is ready.

    The individual dashboard pages will be implemented
    in the next steps.
    """
)