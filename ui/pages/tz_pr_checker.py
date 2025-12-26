# ui/pages/tz_pr_checker.py
"""
TZ-PR Moslik Tekshirish Sahifasi

Bu sahifa:
1. Task key kiritish
2. JIRA dan TZ olish
3. GitHub dan PR kod olish
4. AI tahlil ko'rsatish
"""
import streamlit as st


def render_loading_animation_simple(text, subtext=""):
    """Oddiy loading animation"""
    st.markdown(f"""
    <div style="
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 2rem;
        background: rgba(88, 166, 255, 0.05);
        border-radius: 12px;
        border: 1px solid #30363d;
    ">
        <div style="
            width: 50px;
            height: 50px;
            border: 3px solid #30363d;
            border-top: 3px solid #58a6ff;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        "></div>
        <p style="color: #e6edf3; margin-top: 1rem; font-weight: 500;">{text}</p>
        <p style="color: #8b949e; font-size: 0.85rem;">{subtext}</p>
    </div>
    <style>
        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
    </style>
    """, unsafe_allow_html=True)


def render_tz_pr_checker():
    """TZ-PR Moslik Checker sahifasi"""

    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🔍 TZ-PR Moslik Tekshirish</h1>
        <p>Task TZ va GitHub kod o'zgarishlarini solishtiring</p>
        <p class="author">Developed by JASUR TURGUNOV</p>
    </div>
    """, unsafe_allow_html=True)

    # Info box
    st.info("""
    📋 **Qanday ishlaydi:**
    1. JIRA task key kiriting (masalan: DEV-1234)
    2. Tizim JIRA dan TZ (description) oladi
    3. GitHub dan PR kod o'zgarishlarini oladi
    4. Gemini AI ikkalasini solishtiradi va moslikni baholaydi
    """)

    # GitHub token tekshirish
    try:
        from config.settings import settings
        if not settings.GITHUB_TOKEN:
            st.warning("""
            ⚠️ **GitHub Token topilmadi!**

            TZ-PR Checker ishlashi uchun GitHub token kerak.

            `.env` faylga qo'shing:
            ```
            GITHUB_TOKEN=ghp_your_token_here
            ```
            """)
    except:
        pass

    # Input section
    col1, col2 = st.columns([3, 1])

    with col1:
        task_key = st.text_input(
            "📝 Task Key kiriting",
            placeholder="DEV-1234",
            help="JIRA task key (masalan: DEV-1234, DEV-5678)"
        ).strip().upper()

    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        analyze_button = st.button("🔍 Tekshirish", use_container_width=True, type="primary")

    # Validation
    if analyze_button:
        if not task_key:
            st.error("❌ Iltimos, task key kiriting!")
            return

        if not task_key.startswith(('DEV-', 'PROD-', 'TEST-', 'BUG-')):
            st.warning("⚠️ Task key formati noto'g'ri bo'lishi mumkin. Davom etilmoqda...")

        # Analysis
        _run_analysis(task_key)

    # Recent searches (session state)
    if 'tz_pr_history' in st.session_state and st.session_state.tz_pr_history:
        st.markdown("---")
        st.markdown("### 📜 So'nggi tekshiruvlar")

        for idx, item in enumerate(reversed(st.session_state.tz_pr_history[-5:])):
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                status_emoji = "✅" if item.get('success', False) else "❌"
                st.write(f"{status_emoji} {item['key']}")
            with col2:
                st.write(f"🕐 {item['time']}")
            with col3:
                if st.button("🔄", key=f"reload_{item['key']}_{idx}"):
                    _run_analysis(item['key'])


def _run_analysis(task_key: str):
    """Tahlilni ishga tushirish"""

    # Loading placeholder
    loading_placeholder = st.empty()
    result_placeholder = st.empty()

    # Step 1: Loading
    with loading_placeholder.container():
        render_loading_animation_simple(
            "🔄 Ma'lumotlar yuklanmoqda...",
            f"Task: {task_key}"
        )

    try:
        # Import service
        from services.tz_pr_service import TZPRService

        # Initialize
        service = TZPRService()

        # Run analysis
        result = service.analyze_task(task_key)

        # Clear loading
        loading_placeholder.empty()

        # Show results
        with result_placeholder.container():
            _display_results(result)

        # Save to history
        if 'tz_pr_history' not in st.session_state:
            st.session_state.tz_pr_history = []

        from datetime import datetime
        st.session_state.tz_pr_history.append({
            'key': task_key,
            'time': datetime.now().strftime('%H:%M:%S'),
            'success': result.success
        })

    except Exception as e:
        loading_placeholder.empty()
        st.error(f"❌ Xatolik yuz berdi: {str(e)}")

        with st.expander("🔧 Debug ma'lumotlar"):
            import traceback
            st.code(traceback.format_exc())


def _display_results(result):
    """Natijalarni ko'rsatish"""

    if not result.success:
        st.error(result.error_message)

        if result.tz_content:
            with st.expander("📋 TZ mazmuni (mavjud)"):
                st.text(result.tz_content)
        return

    # Success - show results
    st.success(f"✅ {result.task_key} tahlili tayyor!")

    # Metrics row
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("🔗 PR Count", result.pr_count)

    with col2:
        st.metric("📁 Files Changed", result.files_changed)

    with col3:
        st.metric("➕ Additions", result.total_additions)

    with col4:
        st.metric("➖ Deletions", result.total_deletions)

    st.markdown("---")

    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "🤖 AI Tahlil",
        "📋 TZ Mazmuni",
        "💻 Kod O'zgarishlari",
        "📊 Statistika"
    ])

    # Tab 1: AI Analysis
    with tab1:
        st.markdown("### 🤖 Gemini AI Tahlili")
        st.markdown(result.ai_analysis)

    # Tab 2: TZ Content
    with tab2:
        st.markdown("### 📋 Task TZ (Technical Zadanie)")
        st.markdown(f"**Task:** {result.task_key}")
        st.markdown(f"**Summary:** {result.task_summary}")
        st.markdown("---")
        st.text(result.tz_content)

    # Tab 3: Code Changes
    with tab3:
        st.markdown("### 💻 Kod O'zgarishlari")

        if not result.pr_details:
            st.warning("PR ma'lumotlari yo'q")
            return

        for pr in result.pr_details:
            with st.expander(
                    f"🔗 PR #{pr['pr_number']}: {pr['title']} "
                    f"({'✅ Merged' if pr['merged'] else '⏳ ' + pr['state']})",
                    expanded=True
            ):
                # PR info
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.write(f"👤 **Author:** {pr['author']}")
                with col2:
                    st.write(f"➕ **Additions:** {pr['additions']}")
                with col3:
                    st.write(f"➖ **Deletions:** {pr['deletions']}")

                st.write(f"🔗 [GitHub da ochish]({pr['url']})")

                # Files
                st.markdown("#### 📁 O'zgargan fayllar:")

                for f in pr['files']:
                    status_emoji = {
                        'modified': '📝',
                        'added': '➕',
                        'removed': '➖',
                        'renamed': '📋'
                    }.get(f['status'], '📄')

                    with st.expander(f"{status_emoji} {f['filename']} (+{f['additions']} -{f['deletions']})"):
                        if f.get('patch'):
                            st.code(f['patch'], language='diff')
                        else:
                            st.write("*Diff mavjud emas*")

    # Tab 4: Statistics
    with tab4:
        st.markdown("### 📊 Statistika")

        # File types
        from services.tz_pr_service import TZPRService
        service = TZPRService()
        summary = service.get_pr_files_summary(result.pr_details)

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### 📁 Fayl turlari")
            for ext, count in sorted(summary['by_extension'].items(), key=lambda x: x[1], reverse=True):
                st.write(f"• `{ext}`: {count} ta")

        with col2:
            st.markdown("#### 📊 O'zgarish turlari")
            for status, count in summary['by_status'].items():
                emoji = {'modified': '📝', 'added': '➕', 'removed': '➖'}.get(status, '📄')
                st.write(f"• {emoji} {status}: {count} ta")

        if summary['large_files']:
            st.markdown("#### ⚠️ Katta o'zgarishlar (100+ qator)")
            for f in summary['large_files']:
                st.write(f"• `{f['filename']}`: {f['changes']} o'zgarish")