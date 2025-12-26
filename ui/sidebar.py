# ui/sidebar.py
"""
Sidebar - Sahifa tanlash va sozlamalar

3 ta asosiy funksiya:
1. 🛠 Bug Analyzer - Bug root cause analysis
2. 📊 Sprint Statistics - Sprint statistikasi
3. 🔍 TZ-PR Checker - TZ va kod mosligi
"""
import streamlit as st


def render_sidebar():
    """
    Sidebar rendering

    Returns:
        (page_name, settings_dict)
    """

    with st.sidebar:
        # Logo / Header
        st.markdown("""
        <div style="text-align: center; padding: 1rem 0; margin-bottom: 1rem;">
            <h2 style="color: #e6edf3; font-weight: 700; margin: 0;">
                🔬 JIRA Analyzer
            </h2>
            <p style="color: #8b949e; font-size: 0.85rem; margin-top: 0.5rem;">
                AI-Powered Analysis Suite
            </p>
            <p style="color: #6e7681; font-size: 0.7rem; font-style: italic;">
                v2.0 by JASUR TURGUNOV
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.divider()

        # ==================== PAGE SELECTION ====================
        st.markdown("### 📑 Sahifa tanlang")

        # Radio buttons for page selection
        page = st.radio(
            "Funksiyalar",
            options=[
                "🛠 Bug Analyzer",
                "📊 Sprint Statistics",
                "🔍 TZ-PR Checker"
            ],
            label_visibility="collapsed",
            key="page_selector"
        )

        # Map to simple names
        page_map = {
            "🛠 Bug Analyzer": "Bug Analyzer",
            "📊 Sprint Statistics": "Sprint Statistics",
            "🔍 TZ-PR Checker": "TZ-PR Checker"
        }
        selected_page = page_map.get(page, "Bug Analyzer")

        st.divider()

        # ==================== SETTINGS ====================
        st.markdown("### ⚙️ Sozlamalar")

        settings = {}

        # Page-specific settings
        if selected_page == "Bug Analyzer":
            settings['top_n'] = st.slider(
                "🎯 Top tasklar soni",
                min_value=1,
                max_value=10,
                value=5,
                help="Qidiruv natijasida ko'rsatiladigan eng o'xshash tasklar soni"
            )

            settings['min_similarity'] = st.slider(
                "📊 Min o'xshashlik %",
                min_value=50,
                max_value=95,
                value=70,
                step=5,
                help="Minimal o'xshashlik foizi (threshold)"
            ) / 100

        elif selected_page == "Sprint Statistics":
            settings['chart_theme'] = st.selectbox(
                "🎨 Chart theme",
                options=["Dark", "Light"],
                index=0
            )

        elif selected_page == "TZ-PR Checker":
            settings['show_full_diff'] = st.checkbox(
                "📝 To'liq diff ko'rsatish",
                value=False,
                help="Har bir fayl uchun to'liq diff ko'rsatish"
            )

            settings['max_files'] = st.slider(
                "📁 Max files ko'rsatish",
                min_value=5,
                max_value=50,
                value=20,
                help="Ko'rsatiladigan maksimal fayllar soni"
            )

        st.divider()

        # ==================== STATUS INFO ====================
        st.markdown("### 📡 Status")
        _render_connection_status()

        st.divider()

        # ==================== HELP INFO ====================
        with st.expander("ℹ️ Yordam"):
            if selected_page == "Bug Analyzer":
                st.markdown("""
                **Bug Analyzer** - Production buglarning 
                root cause'ini topadi.

                1. Bug description kiriting
                2. O'xshash tasklar topiladi
                3. AI tahlil qiladi
                """)

            elif selected_page == "Sprint Statistics":
                st.markdown("""
                **Sprint Statistics** - Sprint 
                ma'lumotlarini tahlil qiladi.

                - Developer performance
                - Bug statistika
                - Timeline analysis
                """)

            elif selected_page == "TZ-PR Checker":
                st.markdown("""
                **TZ-PR Checker** - Task TZ va 
                GitHub kod mosligini tekshiradi.

                1. Task key kiriting (DEV-1234)
                2. TZ va kod olinadi
                3. AI moslikni tahlil qiladi

                ⚠️ GitHub token kerak!
                """)

        # ==================== TECH INFO ====================
        st.markdown("""
        <div style="
            background: rgba(88, 166, 255, 0.1); 
            padding: 0.75rem; 
            border-radius: 8px; 
            border: 1px solid #30363d;
            margin-top: 1rem;
        ">
            <p style="color: #8b949e; font-size: 0.75rem; margin: 0;">
                <strong style="color: #58a6ff;">Model:</strong> multilingual-e5-large<br>
                <strong style="color: #58a6ff;">AI:</strong> Gemini 2.5 Flash<br>
                <strong style="color: #58a6ff;">DB:</strong> ChromaDB
            </p>
        </div>
        """, unsafe_allow_html=True)

    return selected_page, settings


def _render_connection_status():
    """Connection status indicators"""
    col1, col2 = st.columns(2)

    with col1:
        jira_ok = _check_jira_connection()
        if jira_ok:
            st.markdown("🟢 JIRA")
        else:
            st.markdown("🔴 JIRA")

    with col2:
        github_ok = _check_github_connection()
        if github_ok:
            st.markdown("🟢 GitHub")
        else:
            st.markdown("🟡 GitHub")


def _check_jira_connection() -> bool:
    """JIRA connection check"""
    try:
        from config.settings import settings
        return bool(settings.JIRA_EMAIL and settings.JIRA_API_TOKEN)
    except:
        return False


def _check_github_connection() -> bool:
    """GitHub connection check"""
    try:
        from config.settings import settings
        return bool(settings.GITHUB_TOKEN)
    except:
        return False