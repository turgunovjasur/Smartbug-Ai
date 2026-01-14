# services/testcase_generator_service.py
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field
import json


@dataclass
class TestCase:
    id: str
    title: str
    description: str
    preconditions: str
    steps: List[str]
    expected_result: str
    test_type: str
    priority: str
    severity: str
    tags: List[str] = field(default_factory=list)


@dataclass
class TestCaseGenerationResult:
    task_key: str
    task_summary: str
    test_cases: List[TestCase] = field(default_factory=list)
    tz_content: str = ""
    pr_count: int = 0
    files_changed: int = 0
    task_full_details: Dict = field(default_factory=dict)
    task_overview: str = ""
    comment_changes_detected: bool = False
    comment_summary: str = ""
    comment_details: List[str] = field(default_factory=list)
    total_test_cases: int = 0
    by_type: Dict[str, int] = field(default_factory=dict)
    by_priority: Dict[str, int] = field(default_factory=dict)
    success: bool = True
    error_message: str = ""
    warnings: List[str] = field(default_factory=list)


class TestCaseGeneratorService:
    def __init__(self):
        self._jira_client = None
        self._github_client = None
        self._gemini_helper = None

    @property
    def jira(self):
        if self._jira_client is None:
            from utils.jira.jira_client import JiraClient
            self._jira_client = JiraClient()
        return self._jira_client

    @property
    def github(self):
        if self._github_client is None:
            from utils.github.github_client import GitHubClient
            self._github_client = GitHubClient()
        return self._github_client

    @property
    def gemini(self):
        if self._gemini_helper is None:
            from utils.gemini_helper import GeminiHelper
            self._gemini_helper = GeminiHelper()
        return self._gemini_helper

    def generate_test_cases(self, task_key: str, include_pr: bool = True, test_types: List[str] = None,
                            status_callback: Optional[Callable[[str, str], None]] = None) -> TestCaseGenerationResult:
        def update_status(stype: str, msg: str):
            if status_callback:
                status_callback(stype, msg)
            print(f"[{stype}] {msg}")

        try:
            if not test_types:
                test_types = ['positive', 'negative']

            update_status("info", f"🔍 {task_key} tahlil qilinmoqda...")

            # 1. JIRA
            task_details = self.jira.get_task_details(task_key)
            if not task_details:
                return TestCaseGenerationResult(task_key=task_key, task_summary="", success=False,
                                                error_message=f"❌ {task_key} topilmadi")

            # 2. TZ va Comment tahlili
            tz_content, comment_analysis = self._get_tz_with_comments(task_details)
            update_status("success", f"✅ TZ: {len(task_details.get('comments', []))} comment")

            # 3. PR
            pr_info = None
            if include_pr:
                pr_info = self._get_pr_multi_strategy(task_key, task_details, update_status)
                if pr_info:
                    update_status("success", f"✅ PR: {pr_info['pr_count']} ta")

            # 4. Overview
            overview = self._create_overview(task_details, comment_analysis, pr_info)

            # 5. AI
            update_status("progress", "🤖 AI test case'lar yaratmoqda...")
            ai_result = self._generate_ai(task_key, task_details, tz_content, comment_analysis, pr_info, test_types)

            if not ai_result['success']:
                return TestCaseGenerationResult(task_key=task_key, task_summary=task_details['summary'],
                                                task_full_details=task_details, task_overview=overview,
                                                success=False, error_message=ai_result['error'])

            # 6. Parse
            test_cases = self._parse_tc(ai_result['raw'])
            by_type = {}
            by_priority = {}
            for tc in test_cases:
                by_type[tc.test_type] = by_type.get(tc.test_type, 0) + 1
                by_priority[tc.priority] = by_priority.get(tc.priority, 0) + 1

            update_status("success", f"✅ {len(test_cases)} ta test case yaratildi!")

            return TestCaseGenerationResult(
                task_key=task_key, task_summary=task_details['summary'], test_cases=test_cases,
                tz_content=tz_content, pr_count=pr_info['pr_count'] if pr_info else 0,
                files_changed=pr_info['files_changed'] if pr_info else 0,
                task_full_details=task_details, task_overview=overview,
                comment_changes_detected=comment_analysis['has_changes'],
                comment_summary=comment_analysis['summary'],
                comment_details=comment_analysis.get('important_comments', []),
                total_test_cases=len(test_cases), by_type=by_type, by_priority=by_priority, success=True
            )

        except Exception as e:
            import traceback
            print(traceback.format_exc())
            return TestCaseGenerationResult(task_key=task_key, success=False, error_message=f"❌ {str(e)}")

    def _get_tz_with_comments(self, td: Dict) -> tuple:
        """TZ va Comment'lar - TO'LIQ"""
        parts = [f"📋 SUMMARY: {td.get('summary', '')}"]

        desc = td.get('description', '')
        if desc:
            parts.append(f"\n📝 DESCRIPTION:\n{desc}")

        parts.append(f"\n📊 METADATA:")
        parts.append(
            f"Type: {td.get('type', 'N/A')}, Priority: {td.get('priority', 'N/A')}, Status: {td.get('status', 'N/A')}")
        parts.append(f"Assignee: {td.get('assignee', 'Unassigned')}, Created: {td.get('created', 'N/A')}")

        comments = td.get('comments', [])
        ca = self._analyze_comments(desc, comments)

        if comments:
            parts.append(f"\n💬 COMMENTS ({len(comments)} ta) - MUHIM!")
            parts.append("=" * 80)
            parts.append("⚠️ DIQQAT: Comment'lar TZ'ni o'zgartirishi, yangi talab qo'shishi mumkin!")
            parts.append("⚠️ AI: Comment'larni diqqat bilan o'qing va test case'larda hisobga oling!")
            parts.append("=" * 80)

            for i, c in enumerate(comments, 1):
                author = c.get('author', 'Unknown')
                created = c.get('created', '')
                body = c.get('body', '').strip()
                if body:
                    parts.append(f"\n[Comment #{i}] {author} ({created}):")
                    parts.append(body)
                    parts.append("-" * 80)

        return "\n".join(parts), ca

    def _analyze_comments(self, desc: str, comments: List[Dict]) -> Dict:
        """Comment tahlili"""
        if not comments:
            return {'has_changes': False, 'summary': 'Comment yo\'q', 'change_count': 0, 'important_comments': []}

        keywords = ['ozgardi', 'ozgarsin', 'yangilandi', 'update', 'change', 'qoshilsin', 'add', 'remove',
                    'orniga', 'kerak emas', 'yangi', 'new', 'qoshimcha', 'endi']

        count = 0
        important = []
        for c in comments:
            body = c.get('body', '').lower()
            if any(kw in body for kw in keywords):
                count += 1
                important.append(f"[{c.get('author')}] {c.get('body', '')[:200]}...")

        has = count > 0
        summary = f"⚠️ {count} ta comment'da o'zgarish!" if has else f"ℹ️ {len(comments)} comment, o'zgarish yo'q"

        return {'has_changes': has, 'summary': summary, 'change_count': count, 'important_comments': important}

    def _create_overview(self, td: Dict, ca: Dict, pr: Optional[Dict]) -> str:
        """Task overview - to'liq ma'lumot"""
        lines = [
            f"**Type:** {td.get('type', 'N/A')}",
            f"**Priority:** {td.get('priority', 'N/A')}",
            f"**Status:** {td.get('status', 'N/A')}",
            f"**Assignee:** {td.get('assignee', 'Unassigned')}",
            f"**Reporter:** {td.get('reporter', 'Unknown')}",
            f"**Created:** {td.get('created', 'N/A')}",
            f"**Story Points:** {td.get('story_points', 'N/A')}"
        ]

        if td.get('labels'):
            lines.append(f"**Labels:** {', '.join(td['labels'])}")
        if td.get('components'):
            lines.append(f"**Components:** {', '.join(td['components'])}")

        lines.append(f"\n**Comment Tahlili:**")
        lines.append(ca['summary'])
        if ca['has_changes'] and ca.get('important_comments'):
            lines.append(f"\nMuhim comment'lar:")
            for ic in ca['important_comments'][:3]:
                lines.append(f"• {ic}")

        lines.append(f"\n**Kod O'zgarishlari:**")
        if pr:
            lines.append(f"• PR: {pr['pr_count']} ta")
            lines.append(f"• Fayllar: {pr['files_changed']} ta")
            lines.append(f"• +{pr['total_additions']} / -{pr['total_deletions']} qator")
        else:
            lines.append("• PR topilmadi")

        return "\n".join(lines)

    def _get_pr_multi_strategy(self, key: str, td: Dict, us) -> Optional[Dict]:
        try:
            urls = td.get('pr_urls', [])
            if not urls:
                found = self.github.search_pr_by_jira_key(key)
                urls = found if found else []

            if not urls:
                return None

            details = []
            tf, ta, tdel = 0, 0, 0

            for item in urls:
                url = item.get('url', '')
                if not url:
                    continue
                owner, repo, num = self.github.parse_pr_url(url)
                if not all([owner, repo, num]):
                    continue

                pr = self.github.get_pr_info(owner, repo, num)
                if not pr:
                    continue

                files = self.github.get_pr_files(owner, repo, num)
                tf += len(files)
                ta += pr.get('additions', 0)
                tdel += pr.get('deletions', 0)
                details.append({'files': files})

            if not details:
                return None

            return {
                'pr_count': len(details),
                'files_changed': tf,
                'total_additions': ta,
                'total_deletions': tdel,
                'files': [f for d in details for f in d['files']]
            }
        except:
            return None

    def _generate_ai(self, key, td, tz, ca, pr, types) -> Dict:
        try:
            prompt = self._prompt(key, td, tz, ca, pr, types)
            resp = self.gemini.analyze(prompt)
            return {'success': True, 'raw': resp}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _prompt(self, key, td, tz, ca, pr, types) -> str:
        """AI Prompt - UZBEK TILIDA, Comment'lar EMPHASIZED"""
        tstr = ", ".join(types)

        p = f"""
**VAZIFA:** {key} uchun QA test case'lar yaratish

╔═══════════════════════════════════════════════════════════════════════════════
║ 📋 TASK
╚═══════════════════════════════════════════════════════════════════════════════

**Key:** {key}
**Summary:** {td['summary']}

╔═══════════════════════════════════════════════════════════════════════════════
║ 📝 TEXNIK TOPSHIRIQ VA COMMENTLAR
╚═══════════════════════════════════════════════════════════════════════════════

**COMMENT TAHLILI:** {ca['summary']}

⚠️ ⚠️ ⚠️ JUDA MUHIM ⚠️ ⚠️ ⚠️
Comment'larda TZ o'zgarishi, yangi talablar bo'lishi mumkin!
Comment'larni DIQQAT bilan o'qing va test case yaratishda ALBATTA hisobga oling!
Comment'lardagi har bir yangi talab uchun test case yozing!

{tz}

"""

        if pr and pr['pr_count'] > 0:
            p += f"""
╔═══════════════════════════════════════════════════════════════════════════════
║ 💻 KOD
╚═══════════════════════════════════════════════════════════════════════════════

PR: {pr['pr_count']} ta, Files: {pr['files_changed']} ta

"""

        p += f"""
╔═══════════════════════════════════════════════════════════════════════════════
║ 🎯 TALABLAR
╚═══════════════════════════════════════════════════════════════════════════════

⚠️⚠️⚠️ JUDA MUHIM: Test case'lar FAQAT O'ZBEK TILIDA yozilsin! ⚠️⚠️⚠️

Test Types: {tstr}

**JSON Format (Faqat JSON ber, boshqa hech narsa yo'q!):**

```json
{{
  "test_cases": [
    {{
      "id": "TC-001",
      "title": "Login sahifasiga kirish imkoniyati",
      "description": "Foydalanuvchi to'g'ri login va parol bilan tizimga kirishi mumkinligini tekshirish",
      "preconditions": "Foydalanuvchi ro'yxatdan o'tgan bo'lishi kerak",
      "steps": [
        "1. Login sahifasini ochish",
        "2. To'g'ri login kiriting",
        "3. To'g'ri parol kiriting", 
        "4. 'Kirish' tugmasini bosing"
      ],
      "expected_result": "Foydalanuvchi tizimga muvaffaqiyatli kirishi va bosh sahifa ochilishi kerak",
      "test_type": "positive",
      "priority": "High",
      "severity": "Critical",
      "tags": ["login", "authentication"]
    }}
  ]
}}
```

**QOIDALAR:**
1. ⚠️ Test case'lar FAQAT O'ZBEK TILIDA!
2. ⚠️ Comment'larni ALBATTA hisobga oling! Comment'lardagi yangi talablar uchun test case yozing!
3. Comment'da agar TZ o'zgargan bo'lsa, yangi variant uchun test yozing!
4. Kamida 5-10 ta test case
5. Har bir test mustaqil
6. Expected result konkret

╔═══════════════════════════════════════════════════════════════════════════════
║ 🚀 ENDI YARATING! (O'ZBEK TILIDA! Comment'larni hisobga oling!)
╚═══════════════════════════════════════════════════════════════════════════════
"""

        return p

    def _parse_tc(self, resp: str) -> List[TestCase]:
        tcs = []
        try:
            s = resp.find('{')
            e = resp.rfind('}') + 1
            js = resp[s:e] if s != -1 else resp
            data = json.loads(js)

            for t in data.get('test_cases', []):
                tcs.append(TestCase(
                    id=t.get('id', 'TC-?'), title=t.get('title', ''), description=t.get('description', ''),
                    preconditions=t.get('preconditions', ''), steps=t.get('steps', []),
                    expected_result=t.get('expected_result', ''), test_type=t.get('test_type', 'positive'),
                    priority=t.get('priority', 'Medium'), severity=t.get('severity', 'Major'),
                    tags=t.get('tags', [])
                ))
        except Exception as e:
            print(f"Parse error: {e}")
            tcs.append(TestCase(
                id="TC-ERROR", title="Parse xatolik", description=resp[:300],
                preconditions="", steps=[], expected_result="", test_type="error",
                priority="Low", severity="Minor", tags=["error"]
            ))
        return tcs

    def export_test_cases_to_markdown(self, r: TestCaseGenerationResult) -> str:
        md = f"""# Test Cases - {r.task_key}

**Task:** {r.task_summary}
**Total:** {r.total_test_cases} ta

---

## Task Ma'lumotlari

{r.task_overview}

---

## Statistics

"""
        for t, c in r.by_type.items():
            md += f"- **{t}:** {c}\n"

        md += "\n---\n\n"

        bt = {}
        for tc in r.test_cases:
            if tc.test_type not in bt:
                bt[tc.test_type] = []
            bt[tc.test_type].append(tc)

        for typ, tcs in bt.items():
            md += f"## {typ.upper()} ({len(tcs)} ta)\n\n"
            for tc in tcs:
                md += f"### {tc.id}: {tc.title}\n\n"
                md += f"**Desc:** {tc.description}\n\n"
                md += f"**Pre:** {tc.preconditions}\n\n"
                md += f"**Steps:**\n"
                for s in tc.steps:
                    md += f"{s}\n"
                md += f"\n**Expected:** {tc.expected_result}\n\n---\n\n"

        return md