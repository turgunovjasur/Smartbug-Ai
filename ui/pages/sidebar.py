# ui/pages/sidebar.py
import streamlit as st


def render_sidebar():
    """Sidebar rendering - Returns: (page_name, settings_dict)"""

    with st.sidebar:
        st.markdown("""
        <div style="text-align: center; padding: 1rem 0; margin-bottom: 1rem;">
            <h2 style="color: #e6edf3; font-weight: 700; margin: 0;">JIRA Analyzer</h2>
            <p style="color: #8b949e; font-size: 0.85rem; margin-top: 0.5rem;">AI-Powered Analysis Suite</p>
            <p style="color: #6e7681; font-size: 0.7rem; font-style: italic;">v3.3 FINAL by JASUR TURGUNOV</p>
        </div>
        """, unsafe_allow_html=True)

        st.divider()

        st.markdown("### Sahifa tanlang")
        page = st.radio(
            "Funksiyalar",
            options=["Bug Analyzer", "Sprint Statistics", "TZ-PR Checker", "Test Case Generator"],
            label_visibility="collapsed",
            key="page_selector"
        )

        st.divider()
        st.markdown("### Sozlamalar")
        settings = {}

        if page == "Bug Analyzer":
            settings['top_n'] = st.slider("Top tasklar soni", 1, 10, 5)
            settings['min_similarity'] = st.slider("Min o'xshashlik %", 50, 95, 75, 5) / 100

        elif page == "Sprint Statistics":
            settings['chart_theme'] = st.selectbox("Chart theme", ["Dark", "Light"], 0)

        elif page == "TZ-PR Checker":
            st.markdown("#### AI Tahlil Sozlamalari")
            use_limit = st.checkbox("Fayllar sonini cheklash", False)
            settings['max_files'] = st.slider("Max fayllar", 5, 100, 20) if use_limit else None
            settings['show_full_diff'] = st.checkbox("To'liq diff", True)

        elif page == "Test Case Generator":
            st.markdown("#### 🧪 Test Case Settings")
            settings['include_pr'] = st.checkbox("📎 GitHub PR hisobga olish", True)

            st.markdown("**🎯 Test Type'lar:**")
            col1, col2 = st.columns(2)
            with col1:
                pos = st.checkbox("✅ Positive", True)
            with col2:
                neg = st.checkbox("❌ Negative", True)

            test_types = []
            if pos:
                test_types.append('positive')
            if neg:
                test_types.append('negative')
            settings['test_types'] = test_types if test_types else ['positive']

            st.divider()
            st.info("""
            **Positive** - Asosiy funksionallik
            **Negative** - Xato holatlar

            **Til:** Test case'lar har doim **O'ZBEK TILIDA**
            """)

        st.divider()
        st.markdown("### Status")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("✅ JIRA: OK" if _check_jira() else "❌ JIRA: ERROR")
        with col2:
            st.markdown("✅ GitHub: OK" if _check_github() else "⚠️ GitHub: Optional")

        st.markdown("""
        <div style="background: rgba(88, 166, 255, 0.1); padding: 0.75rem; border-radius: 8px; margin-top: 1rem;">
            <p style="color: #8b949e; font-size: 0.75rem; margin: 0;">
                <strong style="color: #58a6ff;">AI:</strong> Gemini 2.5 Flash<br>
                <strong style="color: #58a6ff;">Version:</strong> 3.3 FINAL
            </p>
        </div>
        """, unsafe_allow_html=True)

    return page, settings


def _check_jira():
    try:
        from config.settings import settings
        return bool(settings.JIRA_EMAIL and settings.JIRA_API_TOKEN)
    except:
        return False


def _check_github():
    try:
        from config.settings import settings
        return bool(settings.GITHUB_TOKEN)
    except:
        return False