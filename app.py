# app.py
"""
JIRA Bug Analyzer - Main Application v3.1

4 ta asosiy funksiya:
1. Bug Analyzer - Bug root cause analysis
2. Sprint Statistics - Sprint statistikasi
3. TZ-PR Checker - TZ va kod mosligi
4. Test Case Generator - Test case lar generatsiya

Author: JASUR TURGUNOV
Version: 3.1.0
"""
import streamlit as st

# ==================== PAGE CONFIG ====================
st.set_page_config(
    page_title="JIRA Bug Analyzer",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': """
        # JIRA Bug Analyzer v3.1

        AI-powered bug analysis system.

        **Features:**
        - Bug Root Cause Analysis
        - Sprint Statistics
        - TZ-PR Compliance Check
        - Test Case Generator

        **Author:** JASUR TURGUNOV
        """
    }
)

# ==================== STYLES ====================
from ui.styles import CUSTOM_CSS

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ==================== MAIN APP ====================
def main():
    """Main application entry point"""

    # Sidebar - page selection & settings
    from ui.pages.sidebar import render_sidebar
    page, settings = render_sidebar()

    # Save settings to session state
    for key, value in settings.items():
        st.session_state[key] = value

    # ==================== PAGE ROUTING ====================

    if page == "Bug Analyzer":
        # Bug Analyzer sahifasi
        from ui.pages.bug_analyzer import render_bug_analyzer
        render_bug_analyzer()

    elif page == "Sprint Statistics":
        # Statistics sahifasi
        from ui.pages.statistics import render_statistics
        render_statistics()

    elif page == "TZ-PR Checker":
        # TZ-PR Checker sahifasi
        from ui.pages.tz_pr_checker import render_tz_pr_checker
        render_tz_pr_checker()

    elif page == "Test Case Generator":
        # Test Case Generator sahifasi
        from ui.pages.testcase_generator import render_testcase_generator
        render_testcase_generator()

    else:
        # Fallback
        st.error(f"Noma'lum sahifa: {page}")


# ==================== ERROR HANDLER ====================
def handle_error(error: Exception):
    """Global error handler"""
    st.error(f"Xatolik yuz berdi: {str(error)}")

    with st.expander("Debug ma'lumotlar"):
        import traceback
        st.code(traceback.format_exc())

    st.info("""
    **Mumkin sabablar:**
    - JIRA/GitHub credentials noto'g'ri
    - Network xatolik
    - API rate limit

    **Yechim:** .env faylini tekshiring
    """)


# ==================== ENTRY POINT ====================
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        handle_error(e)