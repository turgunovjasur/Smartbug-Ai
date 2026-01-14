# ui/pages/tz_pr_checker.py
"""
TZ-PR Moslik Tekshirish - OPTIMIZED STATUS

Yangilik:
- Faqat oxirgi status
- Progress bar
- Takror yo'q

Author: JASUR TURGUNOV
Version: 3.1
"""
import streamlit as st


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

    # Info
    st.info("""
    📋 **Qanday ishlaydi:** JIRA task key → TZ olish → PR olish → AI tahlil
    """)

    # Input
    col1, col2 = st.columns([3, 1])

    with col1:
        task_key = st.text_input(
            "🔑 Task Key",
            placeholder="DEV-1234"
        ).strip().upper()

    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        analyze_button = st.button("🔍 Tekshirish", use_container_width=True, type="primary")

    if analyze_button:
        if not task_key:
            st.error("❌ Task key kiriting!")
            return
        _run_analysis(task_key)

    # History
    if 'tz_pr_history' in st.session_state and st.session_state.tz_pr_history:
        st.markdown("---")
        st.markdown("### 📜 So'nggi tekshiruvlar")
        for idx, item in enumerate(reversed(st.session_state.tz_pr_history[-5:])):
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                status_emoji = "✅" if item.get('success') else "❌"
                st.write(f"{status_emoji} {item['key']}")
            with col2:
                st.write(f"🕐 {item['time']}")
            with col3:
                if st.button("🔄", key=f"r_{item['key']}_{idx}"):
                    _run_analysis(item['key'])


def _run_analysis(task_key: str):
    """Tahlil - QISQA VA ANIQ STATUS"""

    # Settings
    max_files = st.session_state.get('max_files')
    show_full_diff = st.session_state.get('show_full_diff', True)

    if max_files:
        st.caption(f"⚙️ Max {max_files} fayl, Diff: {'To\'liq' if show_full_diff else 'Qisqa'}")

    # FAQAT 2 TA CONTAINER
    progress_container = st.container()
    result_container = st.container()

    # Progress state
    progress_state = {'step': 0, 'total': 4, 'message': '', 'warnings': []}

    with progress_container:
        progress_bar = st.progress(0)
        status_text = st.empty()

    def update_progress(msg, step):
        """Progress yangilash"""
        progress_state['step'] = step
        progress_state['message'] = msg
        progress_bar.progress(step / progress_state['total'])
        status_text.info(f"**[{step}/{progress_state['total']}]** {msg}")

    try:
        from services.tz_pr_service import TZPRService
        from datetime import datetime

        service = TZPRService()

        # Callback - FAQAT ASOSIY STATUSLAR
        def callback(stype, msg):
            # Step 1: JIRA
            if 'TZ olindi' in msg:
                update_progress("✅ TZ olindi", 1)

            # Step 2: GitHub
            elif 'fayl o\'zgarishi topildi' in msg:
                update_progress(f"✅ {msg}", 2)

            # Step 3: AI tahlil
            elif 'AI tahlil qilmoqda' in msg:
                update_progress("🤖 AI tahlil...", 3)
            elif 'yuborilmoqda' in msg:
                update_progress("⚡ AI'ga yuborilmoqda (60s)...", 3)

            # Step 4: Tayyor
            elif 'AI tahlil tugadi' in msg:
                update_progress("✅ Tahlil tugadi!", 4)

            # Warnings
            elif stype == 'warning':
                progress_state['warnings'].append(msg)

        # Boshlash
        update_progress("🔍 Tahlil boshlandi...", 0)

        # Run
        result = service.analyze_task(
            task_key=task_key,
            max_files=max_files,
            show_full_diff=show_full_diff,
            status_callback=callback
        )

        # Clear progress
        progress_container.empty()

        # Warnings
        if progress_state['warnings']:
            with st.expander("⚠️ Ogohlantirishlar", expanded=False):
                for w in progress_state['warnings']:
                    st.warning(w)

        # Results
        with result_container:
            _display_results(result, max_files, show_full_diff)

        # History
        if 'tz_pr_history' not in st.session_state:
            st.session_state.tz_pr_history = []
        st.session_state.tz_pr_history.append({
            'key': task_key,
            'time': datetime.now().strftime('%H:%M:%S'),
            'success': result.success
        })

    except Exception as e:
        progress_container.empty()
        st.error(f"❌ Xatolik: {str(e)}")
        with st.expander("🔧 Debug"):
            import traceback
            st.code(traceback.format_exc())


def _display_results(result, max_files, show_full_diff):
    """Natijalar"""

    if not result.success:
        st.error(result.error_message)
        if result.warnings:
            for w in result.warnings:
                st.warning(f"• {w}")
        if result.tz_content:
            with st.expander("📋 TZ"):
                st.text(result.tz_content)
        return

    # Success
    st.success(f"✅ {result.task_key} tahlili tayyor!")

    # Retry info
    if result.ai_retry_count > 0:
        st.info(f"🔄 Retry: {result.ai_retry_count}, Files: {result.files_analyzed}/{result.files_changed}")

    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("🔗 PR", result.pr_count)
    with col2:
        st.metric("📁 Files", result.files_changed)
    with col3:
        st.metric("➕", result.total_additions)
    with col4:
        st.metric("➖", result.total_deletions)

    st.markdown("---")

    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["🤖 AI", "📋 TZ", "💻 Kod", "📊 Statistics"])

    with tab1:
        st.markdown("### 🤖 Gemini AI Tahlili")
        st.markdown(result.ai_analysis)

    with tab2:
        st.markdown("### 📋 Task TZ")
        st.markdown(f"**Task:** {result.task_key}")
        st.markdown(f"**Summary:** {result.task_summary}")
        st.markdown("---")
        st.text(result.tz_content)

    with tab3:
        st.markdown("### 💻 Kod O'zgarishlari")

        if not result.pr_details:
            st.warning("PR yo'q")
            return

        for pr in result.pr_details:
            with st.expander(
                    f"🔗 PR #{pr['pr_number']}: {pr['title'][:50]}...",
                    expanded=False
            ):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.write(f"👤 {pr['author']}")
                with col2:
                    st.write(f"➕ {pr['additions']}")
                with col3:
                    st.write(f"➖ {pr['deletions']}")

                st.write(f"🔗 [GitHub]({pr['url']})")

                # Files
                files_to_show = pr['files']
                if max_files and len(pr['files']) > max_files:
                    files_to_show = pr['files'][:max_files]
                    st.caption(f"⚠️ {len(pr['files'])} dan {max_files} ta ko'rsatilmoqda")

                for f in files_to_show:
                    emoji = {'modified': '📝', 'added': '➕', 'removed': '➖'}.get(f['status'], '📄')

                    with st.expander(f"{emoji} {f['filename']} (+{f['additions']} -{f['deletions']})"):
                        if f.get('patch'):
                            patch = f['patch']
                            if not show_full_diff and len(patch) > 1000:
                                st.code(patch[:1000] + "\n\n...", language='diff')
                                st.caption("💡 To'liq diff uchun sidebar'da sozlang")
                            else:
                                st.code(patch, language='diff')

    with tab4:
        st.markdown("### 📊 Statistika")
        from services.tz_pr_service import TZPRService
        service = TZPRService()
        summary = service.get_pr_files_summary(result.pr_details)

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Fayl turlari:**")
            for ext, cnt in sorted(summary['by_extension'].items(), key=lambda x: x[1], reverse=True)[:5]:
                st.write(f"• `{ext}`: {cnt}")
        with col2:
            st.markdown("**O'zgarishlar:**")
            for status, cnt in summary['by_status'].items():
                st.write(f"• {status}: {cnt}")