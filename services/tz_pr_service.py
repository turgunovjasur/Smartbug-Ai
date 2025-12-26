# services/tz_pr_service.py
"""
TZ-PR Moslik Tekshirish Service

Bu service:
1. JIRA dan task TZ oladi
2. GitHub dan PR kod o'zgarishlarini oladi
3. Gemini AI orqali moslikni tahlil qiladi
"""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field


@dataclass
class TZPRAnalysisResult:
    """Tahlil natijasi"""
    task_key: str
    task_summary: str = ""
    tz_content: str = ""
    pr_count: int = 0
    files_changed: int = 0
    total_additions: int = 0
    total_deletions: int = 0
    pr_details: List[Dict] = field(default_factory=list)
    ai_analysis: str = ""
    compliance_score: Optional[int] = None
    success: bool = True
    error_message: str = ""


class TZPRService:
    """TZ va PR mosligini tekshirish"""

    def __init__(self):
        self._jira_client = None
        self._github_client = None
        self._gemini_helper = None

    @property
    def jira(self):
        """Lazy JIRA client"""
        if self._jira_client is None:
            from utils.jira.jira_client import JiraClient
            self._jira_client = JiraClient()
        return self._jira_client

    @property
    def github(self):
        """Lazy GitHub client"""
        if self._github_client is None:
            from utils.github.github_client import GitHubClient
            self._github_client = GitHubClient()
        return self._github_client

    @property
    def gemini(self):
        """Lazy Gemini helper"""
        if self._gemini_helper is None:
            from utils.gemini_helper import GeminiHelper
            self._gemini_helper = GeminiHelper()
        return self._gemini_helper

    def analyze_task(self, task_key: str) -> TZPRAnalysisResult:
        """
        Task ning TZ va PR mosligini to'liq tahlil qilish

        Args:
            task_key: JIRA task key (DEV-1234)

        Returns:
            TZPRAnalysisResult
        """
        print(f"🔍 {task_key} tahlil qilinmoqda...")

        # 1. JIRA dan task ma'lumotlarini olish
        print("   📋 JIRA dan TZ olinmoqda...")
        task_details = self.jira.get_task_details(task_key)

        if not task_details:
            return TZPRAnalysisResult(
                task_key=task_key,
                success=False,
                error_message=f"❌ Task {task_key} topilmadi"
            )

            # TZ olish
        tz_content = self.jira.get_task_tz(task_key)

        # 2. PR URL larni tekshirish
        pr_urls = task_details.get('pr_urls', [])

        # 🆕 O'ZGARISH: Agar Jira link bermasa, GitHub Search ishlatamiz
        if not pr_urls:
            print(f"   ⚠️ JIRA da PR link yo'q. GitHub dan '{task_key}' qidirilmoqda...")
            found_prs = self.github.search_pr_by_jira_key(task_key)

            if found_prs:
                print(f"   ✅ GitHub qidiruvida {len(found_prs)} ta PR topildi!")
                pr_urls = found_prs
            else:
                return TZPRAnalysisResult(
                    task_key=task_key,
                    task_summary=task_details['summary'],
                    tz_content=tz_content,
                    success=False,
                    error_message=f"⚠️ Bu task bo'yicha na JIRAda, na GitHubda (Search) PR topilmadi."
                )
        else:
            print(f"   🔗 JIRA da {len(pr_urls)} ta PR topildi")

        # 3. GitHub dan PR ma'lumotlarini olish
        print("   📥 GitHub dan kod o'zgarishlari olinmoqda...")

        all_pr_details = []
        total_files = 0
        total_additions = 0
        total_deletions = 0

        for pr_info in pr_urls:
            pr_url = pr_info['url']
            owner, repo, pr_number = self.github.parse_pr_url(pr_url)

            if not all([owner, repo, pr_number]):
                print(f"   ⚠️ PR URL parse qilinmadi: {pr_url}")
                continue

            # PR info
            pr_details = self.github.get_pr_info(owner, repo, pr_number)
            if not pr_details:
                continue

            # PR files
            pr_files = self.github.get_pr_files(owner, repo, pr_number)

            # Statistika
            total_files += len(pr_files)
            total_additions += pr_details.get('additions', 0)
            total_deletions += pr_details.get('deletions', 0)

            all_pr_details.append({
                'url': pr_url,
                'owner': owner,
                'repo': repo,
                'pr_number': pr_number,
                'title': pr_details.get('title', ''),
                'state': pr_details.get('state', ''),
                'merged': pr_details.get('merged', False),
                'author': pr_details.get('user', ''),
                'additions': pr_details.get('additions', 0),
                'deletions': pr_details.get('deletions', 0),
                'files': pr_files
            })

        if not all_pr_details:
            return TZPRAnalysisResult(
                task_key=task_key,
                task_summary=task_details['summary'],
                tz_content=tz_content,
                pr_count=len(pr_urls),
                success=False,
                error_message="⚠️ GitHub dan PR ma'lumotlari olinmadi. Token yoki permission tekshiring."
            )

        print(f"   ✅ {total_files} ta fayl o'zgarishi topildi")

        # 4. Gemini AI bilan tahlil
        print("   🤖 Gemini AI tahlil qilmoqda...")

        ai_analysis = self._generate_analysis(
            task_key=task_key,
            task_details=task_details,
            tz_content=tz_content,
            pr_details=all_pr_details
        )

        # 5. Natija
        return TZPRAnalysisResult(
            task_key=task_key,
            task_summary=task_details['summary'],
            tz_content=tz_content,
            pr_count=len(all_pr_details),
            files_changed=total_files,
            total_additions=total_additions,
            total_deletions=total_deletions,
            pr_details=all_pr_details,
            ai_analysis=ai_analysis,
            success=True
        )

    def _generate_analysis(
            self,
            task_key: str,
            task_details: Dict,
            tz_content: str,
            pr_details: List[Dict]
    ) -> str:
        """Gemini AI orqali TZ-Kod mosligini tahlil qilish"""

        # Prompt yaratish
        prompt = f"""
**VAZIFA:** JIRA task ning TZ (Technical Zadanie/Description) va GitHub dagi kod o'zgarishlarini solishtir.
Kod TZ talablariga to'liq javob berayotganini tekshir.

═══════════════════════════════════════════════════════════════════════════════
📋 TASK MA'LUMOTLARI
═══════════════════════════════════════════════════════════════════════════════

**Task Key:** {task_key}
**Summary:** {task_details['summary']}
**Type:** {task_details['type']}
**Priority:** {task_details['priority']}
**Assignee:** {task_details['assignee']}
**Status:** {task_details['status']}

═══════════════════════════════════════════════════════════════════════════════
📝 TZ (TEXNIK TOPSHIRIQ)
═══════════════════════════════════════════════════════════════════════════════

{tz_content}

═══════════════════════════════════════════════════════════════════════════════
💻 KOD O'ZGARISHLARI ({len(pr_details)} ta PR)
═══════════════════════════════════════════════════════════════════════════════
"""

        # PR va fayllarni qo'shish
        for pr in pr_details:
            prompt += f"""
┌─────────────────────────────────────────────────────────────────────────────
│ 🔗 PR #{pr['pr_number']}: {pr['title']}
│ 📊 Status: {pr['state']} {'(MERGED)' if pr['merged'] else ''}
│ 👤 Author: {pr['author']}
│ ➕ Additions: {pr['additions']} | ➖ Deletions: {pr['deletions']}
│ 📁 Files: {len(pr['files'])} ta
└─────────────────────────────────────────────────────────────────────────────

"""
            # Fayllarni qo'shish (max 10 ta)
            for i, f in enumerate(pr['files'][:10], 1):
                patch = f.get('patch', 'No diff available')
                # Patch ni qisqartirish
                if len(patch) > 1500:
                    patch = patch[:1500] + "\n... (qolgan qism qisqartirildi)"

                prompt += f"""
📄 [{i}] {f['filename']}
    Status: {f['status']} | +{f['additions']} -{f['deletions']}

```diff
{patch}
```

"""

            if len(pr['files']) > 10:
                prompt += f"    ... va yana {len(pr['files']) - 10} ta fayl\n"

        prompt += """
═══════════════════════════════════════════════════════════════════════════════
🎯 TAHLIL QILISH KERAK
═══════════════════════════════════════════════════════════════════════════════

1. **TZ MOSLIGI (Compliance)**
   - TZ da ko'rsatilgan har bir talabni tekshir
   - Kod shu talabni bajaradimi?
   - Qaysi talablar to'liq bajarilgan, qaysilari qisman, qaysilari yo'q?

2. **KOD SIFATI**
   - Kod yaxshi yozilganmi (clean code)?
   - Potensial buglar bormi?
   - Edge case'lar handled qilinganmi?
   - Error handling to'g'rimi?

3. **ORTIQCHA O'ZGARISHLAR**
   - TZ da yo'q, lekin kodda bor narsalar bormi?
   - Bu o'zgarishlar zarurmi yoki ortiqchami?

4. **TEST COVERAGE**
   - Bu o'zgarishlar uchun test yozilganmi?
   - Qanday test case'lar kerak?

5. **XAVF BAHOSI (Risk Assessment)**
   - Bu o'zgarishlar qanday xavf tug'dirishi mumkin?
   - Regression test kerakmi?

═══════════════════════════════════════════════════════════════════════════════
📊 JAVOB FORMATI (O'zbek tilida)
═══════════════════════════════════════════════════════════════════════════════

## 🎯 UMUMIY MOSLIK BALI: [0-100]%

## ✅ BAJARILGAN TALABLAR:
1. [Talab 1] - ✅ Bajarildi
   - Qaysi faylda: [fayl nomi]
   - Qanday: [qisqa izoh]

## ⚠️ QISMAN BAJARILGAN:
1. [Talab] - ⚠️ Qisman
   - Nima qilindi: ...
   - Nima qoldi: ...

## ❌ BAJARILMAGAN TALABLAR:
1. [Talab] - ❌ Bajarilmadi
   - Sabab: ...

## 🐛 POTENSIAL MUAMMOLAR:
1. [Muammo 1]
   - Fayl: [filename]
   - Tavsiya: ...

## 🧪 KERAKLI TEST CASE'LAR:
1. [Test case 1]
2. [Test case 2]

## 💡 TAVSIYALAR:
1. [Tavsiya 1]
2. [Tavsiya 2]

## 📝 XULOSA:
[Umumiy xulosa - 2-3 jumla]
"""

        return self.gemini.analyze(prompt)

    def get_pr_files_summary(self, pr_details: List[Dict]) -> Dict:
        """PR fayllarining qisqacha ko'rinishi"""
        summary = {
            'total_files': 0,
            'by_extension': {},
            'by_status': {},
            'large_files': []
        }

        for pr in pr_details:
            for f in pr['files']:
                summary['total_files'] += 1

                # Extension
                filename = f['filename']
                ext = '.' + filename.split('.')[-1] if '.' in filename else 'no_ext'
                summary['by_extension'][ext] = summary['by_extension'].get(ext, 0) + 1

                # Status
                status = f['status']
                summary['by_status'][status] = summary['by_status'].get(status, 0) + 1

                # Large files
                if f.get('changes', 0) > 100:
                    summary['large_files'].append({
                        'filename': filename,
                        'changes': f.get('changes', 0)
                    })

        return summary