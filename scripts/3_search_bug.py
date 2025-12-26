# scripts/3_search_bug.py
import sys
import os
from tqdm import tqdm

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.embedding_helper import EmbeddingHelper
from utils.vectordb_helper import VectorDBHelper
from utils.gemini_helper import GeminiHelper
from dotenv import load_dotenv

load_dotenv()


def search_similar_bugs(bug_description):
    """Bug uchun o'xshash tasklar qidirish (SMART CHUNKING VERSION)"""

    print("=" * 80)
    print("🔍 BUG ROOT CAUSE ANALYSIS")
    print("🎯 SMART CHUNKING + MULTILINGUAL SUPPORT")
    print("=" * 80)
    print()

    # 1. Helpers
    print("📦 Modellar yuklanmoqda...")
    embedding_helper = EmbeddingHelper()
    vectordb_helper = VectorDBHelper()
    gemini_helper = GeminiHelper()
    print("✅ Tayyor!")
    print()

    # 2. Bug tavsifi
    print("🐛 BUG DESCRIPTION:")
    print("-" * 80)
    print(bug_description[:500])
    if len(bug_description) > 500:
        print("...")
    print("-" * 80)
    print()

    # 3. Bug ni embed qilish
    print("🔄 Bug embedding qilinmoqda...")
    bug_embedding = embedding_helper.encode_query(bug_description)
    print("✅ Bug embedding tayyor (1024 dimensions)")
    print()

    # 4. O'xshash tasklar qidirish
    print("🔍 Semantic search boshlandi...")

    top_k = int(os.getenv('TOP_K_RESULTS', 20))
    min_similarity = float(os.getenv('MIN_SIMILARITY', 0.70))

    # Search with filters
    results = vectordb_helper.search_with_chunks(
        query_embedding=bug_embedding,
        n_results=top_k,
        filters={
            "$and": [
                {"status": {"$in": ["CLOSED", "Closed", "Done", "Resolved"]}},
                {"type": {"$ne": "AnalysisTask"}}
            ]
        }
    )

    print(f"✅ Search completed: {len(results)} ta candidate topildi")
    print()

    # 5. Similarity threshold bo'yicha filtrlash
    final_top_n = int(os.getenv('FINAL_TOP_N', 5))

    filtered_results = [
        r for r in results
        if r['similarity'] >= min_similarity
    ]

    if not filtered_results:
        print(f"❌ {min_similarity:.0%} threshold da task topilmadi")
        if results:
            print(f"   Eng yuqori o'xshashlik: {max([r['similarity'] for r in results]):.1%}")
            print(f"   💡 Tavsiya: MIN_SIMILARITY ni kamaytirib ko'ring (.env faylda)")
        return None

    print(f"✅ Threshold filter: {len(filtered_results)} ta task (>={min_similarity:.0%})")
    print()

    # Top N ni olish
    top_tasks = filtered_results[:final_top_n]

    # 6. Top tasklar ni ko'rsatish
    print("=" * 80)
    print("📋 TOP O'XSHASH TASKLAR (POTENSIAL ROOT CAUSE)")
    print("=" * 80)
    print()

    for i, task in enumerate(top_tasks, 1):
        print(f"{i}. {task['key']}")
        print(f"   📊 Similarity Score: {task['similarity']:.1%}")
        print(f"   📏 Distance: {task['distance']:.4f}")

        # Chunk info
        if task.get('chunks'):
            print(f"   📦 Chunks: {len(task['chunks'])} ta")

            # Chunk types va weights
            chunk_info = []
            for chunk in task['chunks']:
                chunk_type = chunk.get('type', 'unknown')
                chunk_weight = chunk.get('weight', 0)
                chunk_info.append(f"{chunk_type}({chunk_weight})")

            print(f"   🔖 Chunk details: {', '.join(chunk_info)}")

        meta = task['metadata']
        print(f"   🏷️  Type: {meta.get('type', 'Unknown')}")
        print(f"   📍 Sprint: {meta.get('sprint_id', 'Unknown')}")
        print(f"   👤 Assignee: {meta.get('assignee', 'Unknown')}")
        print(f"   ⚡ Priority: {meta.get('priority', 'Unknown')}")
        print(f"   📊 Story Points: {meta.get('story_points', 'N/A')}")
        print(f"   🔄 Return Count: {meta.get('return_count', '0')}")

        if meta.get('has_pr') == 'yes':
            print(f"   🔗 PR Status: {meta.get('pr_status', 'Unknown')}")

        print()
        print(f"   📄 Content Preview:")
        preview_text = task['text'][:300].replace('\n', ' ')
        print(f"   {preview_text}...")
        print()

    # 7. GEMINI AI TAHLIL
    print("=" * 80)
    print("🤖 GEMINI AI TAHLILI")
    print("=" * 80)
    print()

    # Batafsil prompt
    prompt = f"""
**VAZIFA:** Production da BUG topildi. Quyidagi {len(top_tasks)} ta task bu BUG ga sabab bo'lgan bo'lishi mumkin. 
Bu tasklar semantic search + smart chunking orqali topildi.

**PRODUCTION BUG:**
{bug_description}

**TOP {len(top_tasks)} POTENSIAL SABAB TASKLAR:**
"""

    for i, task in enumerate(top_tasks, 1):
        meta = task['metadata']

        prompt += f"""
╔═══════════════════════════════════════════════════════════════════════════
{i}. **{task['key']}** (Similarity: {task['similarity']:.1%})
───────────────────────────────────────────────────────────────────────────
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
╚═══════════════════════════════════════════════════════════════════════════

"""

    prompt += """

**CHUQUR TAHLIL QILISH KERAK:**

1. **Root Cause Identification**
   - Qaysi ANIQ task(lar) bu BUG ga BEVOSITA sabab bo'lgan?
   - Nima uchun bu task muammoga olib kelgan? (Texnik jihatdan)

2. **Developer va Process Analysis**
   - Kim qilgan va ularning past task larida shunday xato bormi?
   - Return from Test count yuqori bo'lsa, nimaga?
   - Test jarayonida nima o'tkazib yuborilgan?

3. **Timeline Analysis**
   - Task qachon yaratilgan va qachon closed bo'lgan?
   - Sprint phase da qaysi bosqichda bug kiritilgan?

4. **Component va Priority**
   - Qaysi component zaif?
   - Priority to'g'ri belgilangan bo'lganmi?

5. **Preventive Actions**
   - Kelajakda shunday xatolar qanday oldini olish mumkin?
   - Code review da nimaga e'tibor berish kerak?
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

    print("⏳ Gemini AI tahlil qilmoqda...")
    print("   (Bu 15-30 sekund olishi mumkin)")
    print()

    with tqdm(total=1, desc="   🤖 AI Analysis", bar_format="{l_bar}{bar}| {elapsed}s") as pbar:
        analysis = gemini_helper.analyze(prompt)
        pbar.update(1)

    print()
    print(analysis)
    print()

    print("=" * 80)
    print("🎉 TAHLIL TUGADI")
    print("=" * 80)
    print()

    # Qo'shimcha summary
    print("📌 QUICK SUMMARY:")
    print(f"   🔍 Searched: {top_k} tasks")
    print(f"   ✅ Passed threshold (>={min_similarity:.0%}): {len(filtered_results)}")
    print(f"   🎯 Top results analyzed: {len(top_tasks)}")
    print()

    print("📊 SIMILARITY SCORES:")
    for task in top_tasks:
        print(f"   {task['key']}: {task['similarity']:.1%}")
    print()

    print("👥 INVOLVED DEVELOPERS:")
    devs = set()
    for task in top_tasks:
        assignee = task['metadata'].get('assignee', 'Unknown')
        if assignee not in ['Unassigned', 'Unknown', 'none']:
            devs.add(assignee)

    if devs:
        for dev in sorted(devs):
            print(f"   • {dev}")
    else:
        print("   No developers specified")
    print()

    print("🗂️ AFFECTED COMPONENTS:")
    comps = set()
    for task in top_tasks:
        components = task['metadata'].get('components', '')
        if components and components != 'none':
            for comp in components.split(','):
                comp = comp.strip()
                if comp:
                    comps.add(comp)

    if comps:
        for comp in sorted(comps):
            print(f"   • {comp}")
    else:
        print("   No components specified")
    print()

    return {
        'bug': bug_description,
        'top_tasks': top_tasks,
        'analysis': analysis,
        'involved_developers': list(devs),
        'affected_components': list(comps),
        'search_stats': {
            'total_searched': top_k,
            'passed_threshold': len(filtered_results),
            'top_results': len(top_tasks),
            'min_similarity': min_similarity
        }
    }


# MAIN - Interactive Mode
if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("🐛 BUG ROOT CAUSE ANALYZER")
    print("=" * 80)
    print()

    # Option 1: Use test bug
    print("Variantlar:")
    print("  1. Test bug ishlatish (default)")
    print("  2. O'z bug description kiritish")
    print()

    choice = input("Tanlang (1/2) [default: 1]: ").strip()

    if choice == "2":
        print()
        print("Bug description kiriting (Enter 2 marta bosing tugash uchun):")
        print("-" * 80)

        lines = []
        empty_count = 0
        while True:
            line = input()
            if not line:
                empty_count += 1
                if empty_count >= 2:
                    break
            else:
                empty_count = 0
                lines.append(line)

        bug_description = "\n".join(lines)
    else:
        # Test bug
        bug_description = """
Summary:
BUG - Yaxlitlash xatoligi

Description:
📌 ЗАДАЧА: Valyutada yaxlitlash (Тип округления) va (Округление) konbinatsiyasi bilan ishlamayapti

🧯 ОПИСАНИЕ ОШИБКИ:
1) yaxlitlash "До ближайшего" (####,00000) bo'lsa, 1,65 USD zakazda 2 USD bo'lishi kerak (Joriy holatda: 1 USD ko'rsatyapti)
2) yaxlitlash "Вверх" (####,#0000) bo'lsa, 1,65 USD zakazda 1,7 USD bo'lishi kerak (Joriy holatda: 1,6 USD ko'rsatyapti)

🌐 СЕРВЕР: (xtrade, online)

Assignee: Jasur Turgunov
Reporter: QA Team
"""

    print()
    result = search_similar_bugs(bug_description)

    if result:
        print()
        print("=" * 80)
        print("📄 FULL REPORT SUMMARY")
        print("=" * 80)
        print(f"🔍 Search Stats:")
        print(f"   • Total searched: {result['search_stats']['total_searched']}")
        print(f"   • Passed threshold: {result['search_stats']['passed_threshold']}")
        print(f"   • Min similarity: {result['search_stats']['min_similarity']:.0%}")
        print()
        print(f"📋 Results:")
        print(f"   • Similar tasks found: {len(result['top_tasks'])}")
        print(f"   • Developers involved: {len(result['involved_developers'])}")
        print(f"   • Components affected: {len(result['affected_components'])}")
        print()

        if result['involved_developers']:
            print(f"👥 Developers: {', '.join(result['involved_developers'])}")

        if result['affected_components']:
            print(f"🗂️ Components: {', '.join(result['affected_components'])}")

        print()