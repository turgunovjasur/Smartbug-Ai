# ui/pages/testcase_generator.py
"""
Test Case Generator UI v3.3 FINAL

BARCHA TALABLAR:
1. Task Overview - ko'p ma'lumot, yaxshi dizayn
2. Test Scenario - Dropdown'lar, default yopiq
3. Statistics - Yaxshilangan dizayn
4. TZ Tab - BARCHA task ma'lumotlari
5. Export - Yaxshi

Author: JASUR TURGUNOV
"""
import streamlit as st


def render_testcase_generator():
    """Test Case Generator sahifasi"""

    st.markdown("""
    <div class="main-header">
        <h1>🧪 Test Case Generator</h1>
        <p>TZ, Comments va PR asosida O'zbek tilida QA test case'lar</p>
        <p class="author">v3.3 FINAL by JASUR TURGUNOV</p>
    </div>
    """, unsafe_allow_html=True)

    st.info("""
    📋 **Jarayon:** 
    1. Task key kiriting → 2. TZ va Comments olinadi → 3. PR qidiriladi → 4. AI O'zbek tilida test case'lar yaratadi

    🆕 **YANGI:** Comment'lar to'liq tahlil qilinadi, TZ o'zgarishlari aniqlanadi, Test case'lar O'ZBEK TILIDA

    ⚙️ **Settings:** Sidebar'dan (PR hisobga olish, Test type'lar)
    """)

    # Input
    col1, col2 = st.columns([3, 1])
    with col1:
        task_key = st.text_input("🔑 Task Key", placeholder="DEV-1234").strip().upper()
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        btn = st.button("🧪 Generate", use_container_width=True, type="primary")

    if btn and task_key:
        include_pr = st.session_state.get('include_pr', True)
        test_types = st.session_state.get('test_types', ['positive', 'negative'])
        _run_generation(task_key, include_pr, test_types)
    elif btn:
        st.error("❌ Task key kiriting!")

    # History
    if 'testcase_history' in st.session_state and st.session_state.testcase_history:
        st.markdown("---")
        st.markdown("### 📜 So'nggi 5 ta generatsiya")
        for idx, item in enumerate(reversed(st.session_state.testcase_history[-5:])):
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                emoji = "✅" if item.get('success') else "❌"
                st.write(f"{emoji} {item['key']}")
            with col2:
                st.write(f"🕐 {item['time']}")
            with col3:
                if st.button("🔄", key=f"h_{idx}"):
                    _run_generation(item['key'], item.get('include_pr', True), item.get('test_types', ['positive']))


def _run_generation(task_key: str, include_pr: bool, test_types: list):
    """Test case generatsiya"""

    prog_cont = st.container()
    res_cont = st.container()

    with prog_cont:
        pbar = st.progress(0)
        ptext = st.empty()

    def upd_prog(msg, step):
        pbar.progress(step / 4)
        ptext.info(f"**[{step}/4]** {msg}")

    try:
        from services.testcase_generator_service import TestCaseGeneratorService
        from datetime import datetime

        svc = TestCaseGeneratorService()

        def cb(st, msg):
            if 'TZ olindi' in msg:
                upd_prog("✅ TZ va Comments olindi", 1)
            elif 'PR' in msg:
                upd_prog("✅ PR tekshirildi", 2)
            elif 'yaratmoqda' in msg:
                upd_prog("🤖 AI test case'lar yaratmoqda...", 3)
            elif 'yaratildi' in msg:
                upd_prog("✅ Tayyor!", 4)

        upd_prog("🔍 Boshlandi...", 0)

        result = svc.generate_test_cases(task_key, include_pr, test_types or ['positive'], cb)

        prog_cont.empty()

        with res_cont:
            _display_results(result, svc, include_pr, test_types)

        if 'testcase_history' not in st.session_state:
            st.session_state.testcase_history = []
        st.session_state.testcase_history.append({
            'key': task_key, 'time': datetime.now().strftime('%H:%M:%S'),
            'success': result.success, 'include_pr': include_pr, 'test_types': test_types
        })

    except Exception as e:
        prog_cont.empty()
        st.error(f"❌ Xatolik: {e}")
        with st.expander("🔧 Debug"):
            import traceback
            st.code(traceback.format_exc())


def _display_results(r, svc, inc_pr, types):
    """Natijalarni ko'rsatish"""

    if not r.success:
        st.error(r.error_message)
        if r.warnings:
            for w in r.warnings:
                st.warning(f"• {w}")
        return

    st.success(f"✅ {r.task_key} uchun {r.total_test_cases} ta test case yaratildi!")

    # Top metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📋 Test Cases", r.total_test_cases, help="Jami yaratilgan test case'lar")
    with col2:
        st.metric("🔗 PR", r.pr_count, help="Topilgan Pull Request'lar soni")
    with col3:
        st.metric("📂 Files", r.files_changed, help="O'zgargan fayllar soni")
    with col4:
        high = r.by_priority.get('High', 0)
        st.metric("⚠️ High Priority", high, help="Yuqori prioritetli test case'lar")

    st.markdown("---")

    # Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Task Overview",
        "🧪 Test Scenario",
        "📈 Statistics",
        "📋 Technical Specification",
        "📥 Export"
    ])

    with tab1:
        _render_overview(r, inc_pr, types)

    with tab2:
        _render_scenario(r)

    with tab3:
        _render_stats(r)

    with tab4:
        _render_tz(r)

    with tab5:
        _render_export(r, svc)


def _render_overview(r, inc_pr, types):
    """TALAB 1: Task Overview - ko'p ma'lumot, yaxshi dizayn"""
    st.markdown("### 📊 Task Overview")

    # Header card
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                padding: 1.5rem; border-radius: 12px; margin-bottom: 1rem;">
        <h2 style="color: white; margin: 0;">{r.task_key}</h2>
        <p style="color: #e0e0e0; margin: 0.5rem 0 0 0;">{r.task_summary}</p>
    </div>
    """, unsafe_allow_html=True)

    # Task Ma'lumotlari - 3 column card layout
    st.markdown("#### 📋 Task Ma'lumotlari")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div style="background: rgba(102, 126, 234, 0.1); padding: 1rem; border-radius: 8px; border-left: 4px solid #667eea;">
            <p style="color: #8b949e; font-size: 0.85rem; margin: 0;">Type</p>
            <p style="color: #e6edf3; font-size: 1.1rem; font-weight: 600; margin: 0.5rem 0 0 0;">{}</p>
        </div>
        """.format(r.task_full_details.get('type', 'N/A')), unsafe_allow_html=True)

    with col2:
        priority_color = {'High': '#f85149', 'Medium': '#d29922', 'Low': '#3fb950'}.get(
            r.task_full_details.get('priority', 'Medium'), '#8b949e'
        )
        st.markdown(f"""
        <div style="background: rgba(248, 81, 73, 0.1); padding: 1rem; border-radius: 8px; border-left: 4px solid {priority_color};">
            <p style="color: #8b949e; font-size: 0.85rem; margin: 0;">Priority</p>
            <p style="color: #e6edf3; font-size: 1.1rem; font-weight: 600; margin: 0.5rem 0 0 0;">{r.task_full_details.get('priority', 'N/A')}</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        status_color = {'Done': '#3fb950', 'In Progress': '#d29922', 'To Do': '#8b949e'}.get(
            r.task_full_details.get('status', 'Unknown'), '#8b949e'
        )
        st.markdown(f"""
        <div style="background: rgba(63, 185, 80, 0.1); padding: 1rem; border-radius: 8px; border-left: 4px solid {status_color};">
            <p style="color: #8b949e; font-size: 0.85rem; margin: 0;">Status</p>
            <p style="color: #e6edf3; font-size: 1.1rem; font-weight: 600; margin: 0.5rem 0 0 0;">{r.task_full_details.get('status', 'N/A')}</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("")

    # Detailed info - 2 columns
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**👤 Assignee:**")
        st.info(r.task_full_details.get('assignee', 'Unassigned'))

        st.markdown("**📅 Created:**")
        st.info(r.task_full_details.get('created', 'N/A'))

        st.markdown("**📊 Story Points:**")
        st.info(r.task_full_details.get('story_points', 'N/A'))

    with col2:
        st.markdown("**📝 Reporter:**")
        st.info(r.task_full_details.get('reporter', 'Unknown'))

        if r.task_full_details.get('labels'):
            st.markdown("**🏷️ Labels:**")
            st.info(', '.join(r.task_full_details['labels']))

        if r.task_full_details.get('components'):
            st.markdown("**🔧 Components:**")
            st.info(', '.join(r.task_full_details['components']))

    st.markdown("---")

    # Comment tahlili
    st.markdown("#### 💬 Comment Tahlili")
    if r.comment_changes_detected:
        st.warning(f"⚠️ **O'zgarishlar aniqlandi!**\n\n{r.comment_summary}")
        if r.comment_details:
            with st.expander("📝 Muhim comment'lar"):
                for cd in r.comment_details[:5]:
                    st.markdown(f"• {cd}")
    else:
        st.success(f"✅ {r.comment_summary}")

    st.markdown("---")

    # Kod o'zgarishlari
    st.markdown("#### 💻 Kod O'zgarishlari")
    if r.pr_count > 0:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("PR Count", r.pr_count)
        with col2:
            st.metric("Files Changed", r.files_changed)
        with col3:
            st.metric("Lines", f"+/-")
    else:
        st.info("ℹ️ PR topilmadi yoki hisobga olinmadi")

    st.markdown("---")

    # Settings
    st.markdown("#### ⚙️ Ishlatilgan Settings")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**PR hisobga olish:** {'✅ Ha' if inc_pr else '❌ Yo\'q'}")
    with col2:
        st.markdown(f"**Test Type'lar:** {', '.join(types) if types else 'Hammasi'}")


def _render_scenario(r):
    """TALAB 2: Test Scenario - Dropdown'lar, default yopiq"""
    st.markdown("### 🧪 Test Scenario")

    if not r.test_cases:
        st.warning("⚠️ Test case'lar yo'q")
        return

    st.info("""
    📝 **Test Scenario** - Test case'lar type bo'yicha guruhlangan.
    Har bir type va test case dropdown ko'rinishida (default yopiq).
    """)

    # Group by type
    by_type = {}
    for tc in r.test_cases:
        if tc.test_type not in by_type:
            by_type[tc.test_type] = []
        by_type[tc.test_type].append(tc)

    # Type order
    type_order = ['positive', 'negative', 'edge_case', 'integration']

    for ttype in type_order:
        if ttype not in by_type:
            continue

        tcs = by_type[ttype]

        # Type emoji
        type_emoji = {
            'positive': '✅',
            'negative': '❌',
            'edge_case': '⚠️',
            'integration': '🔗'
        }.get(ttype, '📝')

        # TYPE DROPDOWN - default yopiq
        with st.expander(f"{type_emoji} **{ttype.upper()}** ({len(tcs)} ta test case)", expanded=False):

            for idx, tc in enumerate(tcs, 1):
                # Priority emoji
                p_emoji = {'High': '🔴', 'Medium': '🟡', 'Low': '🟢'}.get(tc.priority, '⚪')

                # TEST CASE DROPDOWN - default yopiq
                with st.expander(f"{p_emoji} {tc.id}: {tc.title}", expanded=False):

                    # Header
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.markdown(f"**Type:** {tc.test_type}")
                    with col2:
                        st.markdown(f"**Priority:** {tc.priority}")
                    with col3:
                        st.markdown(f"**Severity:** {tc.severity}")

                    if tc.tags:
                        st.markdown(f"**Tags:** {', '.join(tc.tags)}")

                    st.markdown("---")

                    # Description
                    st.markdown("**📝 Tavsif:**")
                    st.markdown(f"> {tc.description}")

                    # Preconditions
                    if tc.preconditions:
                        st.markdown("**📌 Boshlang'ich shartlar:**")
                        st.markdown(f"> {tc.preconditions}")

                    # Steps
                    st.markdown("**🔢 Test Qadamlari:**")
                    for step in tc.steps:
                        st.markdown(f"- {step}")

                    # Expected
                    st.markdown("**✅ Kutilgan Natija:**")
                    st.success(tc.expected_result)


def _render_stats(r):
    """TALAB 3: Statistics - Yaxshilangan dizayn"""
    st.markdown("### 📈 Test Cases Statistics")

    # Hero metrics
    st.markdown("#### 📊 Umumiy Ko'rsatkichlar")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 1.5rem; border-radius: 12px; text-align: center;">
            <p style="color: #e0e0e0; font-size: 0.9rem; margin: 0;">Total Test Cases</p>
            <h2 style="color: white; margin: 0.5rem 0 0 0;">{}</h2>
        </div>
        """.format(r.total_test_cases), unsafe_allow_html=True)

    with col2:
        crit = sum(1 for tc in r.test_cases if tc.severity == 'Critical')
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); 
                    padding: 1.5rem; border-radius: 12px; text-align: center;">
            <p style="color: #e0e0e0; font-size: 0.9rem; margin: 0;">Critical Tests</p>
            <h2 style="color: white; margin: 0.5rem 0 0 0;">{crit}</h2>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        avg = sum(len(tc.steps) for tc in r.test_cases) / len(r.test_cases) if r.test_cases else 0
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); 
                    padding: 1.5rem; border-radius: 12px; text-align: center;">
            <p style="color: #e0e0e0; font-size: 0.9rem; margin: 0;">O'rtacha Qadamlar</p>
            <h2 style="color: white; margin: 0.5rem 0 0 0;">{avg:.1f}</h2>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        high = r.by_priority.get('High', 0)
        perc = (high / r.total_test_cases * 100) if r.total_test_cases > 0 else 0
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); 
                    padding: 1.5rem; border-radius: 12px; text-align: center;">
            <p style="color: #e0e0e0; font-size: 0.9rem; margin: 0;">High Priority %</p>
            <h2 style="color: white; margin: 0.5rem 0 0 0;">{perc:.1f}%</h2>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("")
    st.markdown("---")

    # Distributions
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 🎯 Test Type Taqsimoti")
        st.caption("Har xil test turlarining ulushi")

        for tt, cnt in sorted(r.by_type.items(), key=lambda x: x[1], reverse=True):
            p = (cnt / r.total_test_cases) * 100

            desc = {
                'positive': 'Asosiy funksionallik',
                'negative': 'Xato holatlar',
                'edge_case': 'Chegaraviy holatlar',
                'integration': 'Integratsiya'
            }.get(tt, tt)

            st.markdown(f"**{tt}** - {desc}")
            st.progress(p / 100)
            st.caption(f"{cnt} ta ({p:.1f}%)")
            st.markdown("")

    with col2:
        st.markdown("#### ⚡ Priority Taqsimoti")
        st.caption("Muhimlik darajasi bo'yicha")

        for prio in ['High', 'Medium', 'Low']:
            cnt = r.by_priority.get(prio, 0)
            if cnt > 0:
                p = (cnt / r.total_test_cases) * 100

                desc = {
                    'High': 'Yuqori - birinchi navbatda',
                    'Medium': 'O\'rtacha - standart tsikl',
                    'Low': 'Past - vaqt bo\'lsa'
                }.get(prio, prio)

                emoji = {'High': '🔴', 'Medium': '🟡', 'Low': '🟢'}.get(prio, '⚪')

                st.markdown(f"{emoji} **{prio}** - {desc}")
                st.progress(p / 100)
                st.caption(f"{cnt} ta ({p:.1f}%)")
                st.markdown("")

    st.markdown("---")

    # Coverage analysis
    st.markdown("#### 📊 Qoplam Tahlili")

    col1, col2, col3 = st.columns(3)

    with col1:
        pos = r.by_type.get('positive', 0)
        pos_p = (pos / r.total_test_cases * 100) if r.total_test_cases > 0 else 0
        st.metric("Positive Coverage", f"{pos_p:.1f}%", help="Asosiy funksionallik qoplanishi")

    with col2:
        neg = r.by_type.get('negative', 0)
        neg_p = (neg / r.total_test_cases * 100) if r.total_test_cases > 0 else 0
        st.metric("Negative Coverage", f"{neg_p:.1f}%", help="Xato holatlar qoplanishi")

    with col3:
        edge = r.by_type.get('edge_case', 0)
        edge_p = (edge / r.total_test_cases * 100) if r.total_test_cases > 0 else 0
        st.metric("Edge Cases", f"{edge_p:.1f}%", help="Chegaraviy holatlar")

    st.markdown("---")

    # Insights
    st.markdown("#### 💡 Tahlil va Tavsiyalar")

    insights = []

    if pos > r.total_test_cases * 0.5:
        insights.append("✅ Yaxshi positive test coverage - asosiy funksiyalar yaxshi qoplangan")
    else:
        insights.append("⚠️ Positive coverage kam - asosiy funksionallikni ko'proq test qiling")

    if neg > 0:
        insights.append("✅ Negative test case'lar mavjud - xato holatlar tekshiriladi")
    else:
        insights.append("⚠️ Negative test'lar yo'q - xato holatlarni qo'shing")

    if crit > 0:
        insights.append(f"✅ {crit} ta critical test mavjud - muhim funksiyalar qoplangan")
    else:
        insights.append("⚠️ Critical test'lar yo'q - eng muhim funksiyalarni belgilang")

    if high > r.total_test_cases * 0.3:
        insights.append("✅ High priority test'lar yetarli")
    else:
        insights.append("⚠️ High priority test'lar kam")

    for ins in insights:
        st.markdown(f"• {ins}")


def _render_tz(r):
    """TALAB 4: TZ Tab - BARCHA task ma'lumotlari"""
    st.markdown("### 📋 Task Technical Specification")

    st.markdown(f"""
    <div style="background: rgba(102, 126, 234, 0.15); padding: 1rem; border-radius: 8px; border-left: 4px solid #667eea;">
        <h3 style="margin: 0; color: #e6edf3;">{r.task_key}</h3>
        <p style="margin: 0.5rem 0 0 0; color: #8b949e;">{r.task_summary}</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("")

    # BARCHA ma'lumotlar - organized sections

    # Section 1: Asosiy ma'lumotlar
    with st.expander("📊 Asosiy Ma'lumotlar", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**Type:** {r.task_full_details.get('type', 'N/A')}")
            st.markdown(f"**Priority:** {r.task_full_details.get('priority', 'N/A')}")
            st.markdown(f"**Status:** {r.task_full_details.get('status', 'N/A')}")
            st.markdown(f"**Story Points:** {r.task_full_details.get('story_points', 'N/A')}")
        with col2:
            st.markdown(f"**Assignee:** {r.task_full_details.get('assignee', 'Unassigned')}")
            st.markdown(f"**Reporter:** {r.task_full_details.get('reporter', 'Unknown')}")
            st.markdown(f"**Created:** {r.task_full_details.get('created', 'N/A')}")
            st.markdown(f"**Resolved:** {r.task_full_details.get('resolved', 'N/A')}")

        if r.task_full_details.get('labels'):
            st.markdown(f"**Labels:** {', '.join(r.task_full_details['labels'])}")
        if r.task_full_details.get('components'):
            st.markdown(f"**Components:** {', '.join(r.task_full_details['components'])}")

    # Section 2: TZ Content
    with st.expander("📝 Texnik Topshiriq (TZ)", expanded=True):
        st.info("💡 Bu TZ AI tomonidan o'qilgan va test case yaratishda ishlatilgan")
        st.text_area("TZ Content", r.tz_content, height=400, disabled=True, label_visibility="collapsed")

    # Section 3: Comments
    comments = r.task_full_details.get('comments', [])
    with st.expander(f"💬 Comments ({len(comments)} ta)", expanded=True):
        if comments:
            st.info("💡 Comment'lar AI tomonidan tahlil qilingan va test case yaratishda hisobga olingan")

            for i, c in enumerate(comments, 1):
                st.markdown(f"**[Comment #{i}]** {c.get('author', 'Unknown')} - {c.get('created', '')}")
                st.markdown(f"> {c.get('body', '')}")
                st.markdown("---")
        else:
            st.info("ℹ️ Comment'lar yo'q")

    # Section 4: Comment Tahlili
    with st.expander("🔍 Comment Tahlili", expanded=True):
        st.markdown(r.comment_summary)
        if r.comment_changes_detected and r.comment_details:
            st.warning("⚠️ Muhim comment'lar:")
            for cd in r.comment_details:
                st.markdown(f"• {cd}")


def _render_export(r, svc):
    """TALAB 5: Export - Yaxshi"""
    st.markdown("### 📥 Export Test Cases")

    st.info("""
    Test case'larni turli formatlarda yuklab olishingiz mumkin:
    - **Markdown** - Documentation va Wiki uchun
    - **JSON** - Integration va import uchun
    """)

    col1, col2 = st.columns(2)

    # Markdown
    with col1:
        st.markdown("#### 📄 Markdown")
        try:
            md = svc.export_test_cases_to_markdown(r)
            st.download_button(
                "⬇️ Download Markdown",
                md,
                f"{r.task_key}_test_cases.md",
                "text/markdown",
                use_container_width=True
            )
            with st.expander("👁️ Preview"):
                st.code(md[:500] + "...", language="markdown")
        except Exception as e:
            st.error(f"Markdown error: {e}")

    # JSON
    with col2:
        st.markdown("#### 📊 JSON")
        try:
            import json
            jdata = {
                'task_key': r.task_key,
                'task_summary': r.task_summary,
                'total': r.total_test_cases,
                'stats': {'by_type': r.by_type, 'by_priority': r.by_priority},
                'test_cases': [
                    {
                        'id': tc.id, 'title': tc.title, 'description': tc.description,
                        'preconditions': tc.preconditions, 'steps': tc.steps,
                        'expected_result': tc.expected_result, 'test_type': tc.test_type,
                        'priority': tc.priority, 'severity': tc.severity, 'tags': tc.tags
                    }
                    for tc in r.test_cases
                ]
            }
            jstr = json.dumps(jdata, indent=2, ensure_ascii=False)
            st.download_button(
                "⬇️ Download JSON",
                jstr,
                f"{r.task_key}_test_cases.json",
                "application/json",
                use_container_width=True
            )
            with st.expander("👁️ Preview"):
                st.code(jstr[:500] + "...", language="json")
        except Exception as e:
            st.error(f"JSON error: {e}")

    st.markdown("---")
    st.caption(
        "💡 Export qilingan fayllarni TestRail, Zephyr, Xray yoki boshqa test management tool'larga import qilish mumkin")