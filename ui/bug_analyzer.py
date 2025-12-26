# ui/bug_analyzer.py - V2 (Emoji fixed)
import streamlit as st
from ui.components import load_models, render_header, render_loading_animation, render_results_info


def search_similar_bugs(bug_description, embedding_helper, vectordb_helper, top_n=3, min_similarity=0.70):
    """Bug uchun o'xshash tasklar qidirish"""

    # Bug ni embed qilish
    bug_embedding = embedding_helper.encode_query(bug_description)

    # O'xshash tasklar qidirish
    results = vectordb_helper.search(
        query_embedding=bug_embedding,
        n_results=20,
        filters={
            "$and": [
                {"status": "Closed"},
                {"type": {"$ne": "AnalysisTask"}}
            ]
        }
    )

    # Natijalarni formatlash
    all_tasks = []
    filtered_tasks = []

    for i in range(len(results['ids'][0])):
        distance = results['distances'][0][i]
        similarity = 1 - distance

        task = {
            'key': results['ids'][0][i],
            'text': results['documents'][0][i],
            'similarity': similarity,
            'metadata': results['metadatas'][0][i]
        }

        all_tasks.append(task)

        if similarity >= min_similarity:
            filtered_tasks.append(task)

    top_tasks = filtered_tasks[:top_n]

    return top_tasks, len(filtered_tasks), len(all_tasks)


def analyze_with_gemini(bug_description, top_tasks, gemini_helper):
    """Gemini AI bilan tahlil qilish"""

    prompt = f"""
**VAZIFA:** Production da BUG topildi. Quyidagi {len(top_tasks)} ta task bu BUG ga sabab bo'lgan bo'lishi mumkin. 
Chuqur tahlil qilib, qaysi task(lar) muammoga olib kelgan va nima qilish kerakligini ayt.

**PRODUCTION BUG:**
{bug_description}

**TOP {len(top_tasks)} POTENSIAL SABAB TASKLAR:**
"""

    for i, task in enumerate(top_tasks, 1):
        meta = task['metadata']
        prompt += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{i}. **{task['key']}** (O'xshashlik: {task['similarity']:.1%})
────────────────────────────────────────────────────────────────────────────────
Sprint: {meta.get('sprint_id', 'Unknown')}
Type: {meta.get('type', 'Unknown')}
Status: {meta.get('status', 'Unknown')}
Assignee: {meta.get('assignee', 'Unknown')}
Reporter: {meta.get('reporter', 'Unknown')}
Priority: {meta.get('priority', 'Unknown')}
Story Points: {meta.get('story_points', 'N/A')}
Created: {meta.get('created_date', 'Unknown')}
Resolved: {meta.get('resolved_date', 'Unknown')}
Return from Test: {meta.get('return_count', '0')} marta
Labels: {meta.get('labels', 'None')}
Components: {meta.get('components', 'None')}

**TASK BATAFSIL MA'LUMOT:**
{task['text']}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"""

    prompt += """

**CHUQUR TAHLIL QILISH KERAK:**

1. **Root Cause Identification**
   - Qaysi ANIQ task(lar) bu BUG ga BEVOSITA sabab bo'lgan?
   - Nima uchun bu task muammoga olib kelgan? (Texnik jihatdan)

2. **Developer va Process Analysis**
   - Kim qilgan va ularning past task larida shunday xato bormi?
   - Return from Test count yuqori bo'lsa, nimaga?

3. **Preventive Actions**
   - Kelajakda shunday xatolar qanday oldini olish mumkin?
   - Qanday test case lar qo'shish kerak?

**JAVOB FORMATI (Uzbek tilida, batafsil va konkret):**

🎯 **ASOSIY SABAB:**
[Qaysi task(lar), nima uchun, kim qilgan, qanday xato qilingan - KONKRET]

🔍 **TEXNIK TAHLIL:**
[Muammoning texnik tahlili - kod darajasida, integration muammosi, logic error va h.k.]

📊 **TIMELINE VA PROCESS TAHLIL:**
[Task lifecycle, return reasons, sprint phase, test coverage gaps]

👤 **DEVELOPER VA TEAM INSIGHTS:**
[Developer performance, past bugs, workload, training needs]

✅ **YECHIM VA FIX:**
[Qanday tuzatish kerak - KONKRET kod yoki config o'zgarishlar]

🛡️ **PREVENTIVE MEASURES:**
[Kelajakda oldini olish uchun - code review checklist, test automation, documentation]

💡 **TAVSIYALAR:**
[Management, team, va process level tavsiyalar]

---
**MUHIM:** Javob maksimal KONKRET va ACTIONABLE bo'lsin. Generic javob emas, aniq task key, developer, sana va texnik details bilan.
"""

    analysis = gemini_helper.analyze(prompt)
    return analysis


def render_bug_analyzer():
    """Bug Analyzer sahifasi"""

    # Header - EMOJI FIXED VERSION
    st.markdown("""
    <div class="main-header">
        <h1>🐛 Bug Root Cause Analyzer</h1>
        <p>AI yordamida bugning asosiy sababini toping</p>
        <p class="author">Developed by JASUR TURGUNOV</p>
    </div>
    """, unsafe_allow_html=True)

    # Bug input
    col1, col2 = st.columns([3, 1])

    with col1:
        bug_description = st.text_area(
            "📝 Bug tavsifini kiriting",
            height=200,
            placeholder="Summary: ...\n\nDescription: ...\n\nAssignee: ...\nReporter: ...",
            help="Bug haqida batafsil ma'lumot kiriting - summary, description, server va boshqalar"
        )

    with col2:
        st.markdown("<br>", unsafe_allow_html=True)

        # Quick stats from VectorDB
        try:
            _, vectordb_helper, _ = load_models()
            stats = vectordb_helper.get_stats()

            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{stats['total_issues']}</div>
                <div class="metric-label">Jami Issue</div>
            </div>
            """, unsafe_allow_html=True)
        except:
            pass

        st.markdown("<br>", unsafe_allow_html=True)

        analyze_button = st.button("🔍 Tahlil qilish", use_container_width=True)

    # Analysis
    if analyze_button and bug_description.strip():

        # Loading animation
        loading_placeholder = st.empty()

        with loading_placeholder.container():
            render_loading_animation(
                "🔧 Modellar yuklanmoqda...",
                "Iltimos kuting..."
            )

        # Load models
        embedding_helper, vectordb_helper, gemini_helper = load_models()

        # Get settings
        top_n = st.session_state.get('top_n', 5)
        min_similarity = st.session_state.get('min_similarity', 0.75)

        # Update loading
        with loading_placeholder.container():
            render_loading_animation(
                "🔎 O'xshash tasklar qidirilmoqda...",
                "Semantic search ishlamoqda..."
            )

        # Search
        top_tasks, filtered_count, total_found = search_similar_bugs(
            bug_description,
            embedding_helper,
            vectordb_helper,
            top_n=top_n,
            min_similarity=min_similarity
        )

        # Clear loading
        loading_placeholder.empty()

        if not top_tasks:
            st.warning(f"⚠️ {min_similarity:.0%} o'xshashlikda task topilmadi.")

            if total_found > 0:
                st.info(f"""
                📊 **Qidiruv natijasi:**
                - Jami topilgan tasklar: {total_found} ta
                - {min_similarity:.0%} threshold ga to'g'ri kelgan: 0 ta

                💡 **Tavsiya:** Min o'xshashlik foizini pasaytiring yoki boshqa bug tavsifini kiriting.
                """)
            return

        # Show results info
        render_results_info(top_n, len(top_tasks), filtered_count, min_similarity)

        # Display results
        st.markdown("---")
        st.markdown(f"### 📋 Top {len(top_tasks)} Potensial Sabab Tasklar")

        for i, task in enumerate(top_tasks, 1):
            similarity = task['similarity']

            with st.expander(f"**{task['key']}** — {similarity:.1%} o'xshashlik", expanded=(i == 1)):
                col1, col2, col3, col4 = st.columns(4)

                meta = task['metadata']

                with col1:
                    st.markdown(f"**Sprint:** {meta.get('sprint_id', 'Unknown')}")
                    st.markdown(f"**Type:** {meta.get('type', 'Unknown')}")

                with col2:
                    st.markdown(f"**Assignee:** {meta.get('assignee', 'Unknown')}")
                    st.markdown(f"**Priority:** {meta.get('priority', 'Unknown')}")

                with col3:
                    st.markdown(f"**Story Points:** {meta.get('story_points', 'N/A')}")
                    st.markdown(f"**Return Count:** {meta.get('return_count', '0')}")

                with col4:
                    st.markdown(f"**Created:** {meta.get('created_date', 'Unknown')}")
                    st.markdown(f"**Resolved:** {meta.get('resolved_date', 'Unknown')}")

                st.markdown("---")
                st.markdown("**📖 Task ma'lumotlari:**")
                st.text(task['text'][:1000] + "..." if len(task['text']) > 1000 else task['text'])

        # AI Analysis
        st.markdown("---")
        st.markdown("""
        <div class="ai-analysis">
            <div class="ai-analysis-header">
                <span style="font-size: 1.5rem;">🤖</span>
                <h3>Gemini AI Tahlili</h3>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # AI Loading
        ai_loading_placeholder = st.empty()

        with ai_loading_placeholder.container():
            render_loading_animation(
                "⚡ Gemini AI tahlil qilmoqda...",
                "Bu 15-35 sekund olishi mumkin"
            )

        analysis = analyze_with_gemini(bug_description, top_tasks, gemini_helper)

        # Clear AI loading
        ai_loading_placeholder.empty()

        st.markdown(analysis)

        # Summary
        st.markdown("---")
        st.markdown("### 📊 Quick Summary")

        col1, col2, col3 = st.columns(3)

        with col1:
            avg_similarity = sum(t['similarity'] for t in top_tasks) / len(top_tasks)
            st.metric("O'rtacha O'xshashlik", f"{avg_similarity:.1%}")

        with col2:
            devs = set(t['metadata'].get('assignee', 'Unknown') for t in top_tasks if
                       t['metadata'].get('assignee') != 'Unassigned')
            st.metric("Involved Developers", len(devs))

        with col3:
            st.metric("Topilgan Tasklar", len(top_tasks))

        # Developers list
        if devs:
            st.markdown("**👥 Involved Developers:**")
            for dev in devs:
                st.markdown(f"• {dev}")

    elif analyze_button:
        st.warning("⚠️ Iltimos, bug tavsifini kiriting!")