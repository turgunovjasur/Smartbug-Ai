# services/tz_pr_service.py
"""
TZ-PR Moslik Tekshirish Service - YANGILANGAN VERSIYA

Yangi funksiyalar:
1. UI sozlamalari support (max_files, show_full_diff)
2. TZ to'liq olinadi (task + comments)
3. PR barcha kodlar to'liq
4. AI limit checker + auto retry
5. To'liq error handling
6. Real-time status updates

Author: JASUR TURGUNOV
Version: 3.0
"""
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
import time


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
    warnings: List[str] = field(default_factory=list)

    # Yangi: AI retry info
    ai_retry_count: int = 0
    files_analyzed: int = 0
    total_prompt_size: int = 0


class TZPRService:
    """TZ va PR mosligini tekshirish - Auto-retry bilan"""

    def __init__(self):
        self._jira_client = None
        self._github_client = None
        self._gemini_helper = None

        # AI Limits
        self.MAX_TOKENS = 900000  # Gemini 2.5 Flash limit (1M dan kam)
        self.CHARS_PER_TOKEN = 4  # Taxminan
        self.MAX_RETRIES = 3

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

    def analyze_task(
            self,
            task_key: str,
            max_files: Optional[int] = None,
            show_full_diff: bool = True,
            status_callback: Optional[Callable[[str, str], None]] = None
    ) -> TZPRAnalysisResult:
        """
        Task ning TZ va PR mosligini to'liq tahlil qilish

        Args:
            task_key: JIRA task key (DEV-1234)
            max_files: Maksimal fayllar soni (None = barcha)
            show_full_diff: To'liq diff yuborish (True/False)
            status_callback: Status update callback function(status_type, message)

        Returns:
            TZPRAnalysisResult
        """

        def update_status(status_type: str, message: str):
            """Status update helper"""
            if status_callback:
                status_callback(status_type, message)
            print(f"[{status_type.upper()}] {message}")

        update_status("info", f"🔍 {task_key} tahlil qilinmoqda...")

        try:
            # 1. JIRA dan TO'LIQ TZ olish
            update_status("progress", "📋 JIRA dan TZ olinmoqda...")

            task_details = self.jira.get_task_details(task_key)

            if not task_details:
                return TZPRAnalysisResult(
                    task_key=task_key,
                    success=False,
                    error_message=f"❌ Task {task_key} topilmadi yoki access yo'q"
                )

            # TO'LIQ TZ olish (task + comments)
            tz_content = self._get_full_tz(task_key, task_details)
            update_status("success", f"✅ TZ olindi: {len(tz_content)} chars")

            # 2. PR URL larni topish
            pr_urls = task_details.get('pr_urls', [])

            if not pr_urls:
                update_status("warning", "⚠️ JIRA da PR link yo'q. GitHub'dan qidirilmoqda...")
                found_prs = self.github.search_pr_by_jira_key(task_key)

                if found_prs:
                    pr_urls = found_prs
                    update_status("success", f"✅ GitHub'da {len(found_prs)} ta PR topildi!")
                else:
                    return TZPRAnalysisResult(
                        task_key=task_key,
                        task_summary=task_details['summary'],
                        tz_content=tz_content,
                        success=False,
                        error_message="❌ Bu task uchun PR topilmadi (JIRA va GitHub'da)",
                        warnings=["JIRA da PR link yo'q", "GitHub search natija bermadi"]
                    )
            else:
                update_status("info", f"📗 JIRA'da {len(pr_urls)} ta PR topildi")

            # 3. GitHub dan PR ma'lumotlarini olish
            update_status("progress", "📥 GitHub dan kod o'zgarishlari olinmoqda...")

            all_pr_details = []
            total_files = 0
            total_additions = 0
            total_deletions = 0

            for idx, pr_info in enumerate(pr_urls, 1):
                pr_url = pr_info['url']
                update_status("progress", f"   🔗 [{idx}/{len(pr_urls)}] PR yuklanmoqda: {pr_url}")

                owner, repo, pr_number = self.github.parse_pr_url(pr_url)

                if not all([owner, repo, pr_number]):
                    update_status("warning", f"   ⚠️ PR URL parse qilinmadi: {pr_url}")
                    continue

                # PR info
                pr_details = self.github.get_pr_info(owner, repo, pr_number)
                if not pr_details:
                    update_status("warning", f"   ⚠️ PR ma'lumotlari olinmadi: #{pr_number}")
                    continue

                # PR files - BARCHA FAYLLAR!
                pr_files = self.github.get_pr_files(owner, repo, pr_number)

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

                update_status("success", f"   ✅ PR #{pr_number}: {len(pr_files)} fayl")

            if not all_pr_details:
                return TZPRAnalysisResult(
                    task_key=task_key,
                    task_summary=task_details['summary'],
                    tz_content=tz_content,
                    pr_count=len(pr_urls),
                    success=False,
                    error_message="❌ GitHub dan PR ma'lumotlari olinmadi. Token yoki permission tekshiring.",
                    warnings=["GitHub API xatosi yoki access denied"]
                )

            update_status("success", f"✅ Jami {total_files} ta fayl o'zgarishi topildi")

            # 4. AI tahlil - AUTO RETRY bilan
            update_status("progress", "🤖 Gemini AI tahlil qilmoqda...")

            ai_result = self._analyze_with_retry(
                task_key=task_key,
                task_details=task_details,
                tz_content=tz_content,
                pr_details=all_pr_details,
                max_files=max_files,
                show_full_diff=show_full_diff,
                status_callback=update_status
            )

            if not ai_result['success']:
                return TZPRAnalysisResult(
                    task_key=task_key,
                    task_summary=task_details['summary'],
                    tz_content=tz_content,
                    pr_count=len(all_pr_details),
                    files_changed=total_files,
                    total_additions=total_additions,
                    total_deletions=total_deletions,
                    pr_details=all_pr_details,
                    success=False,
                    error_message=ai_result['error'],
                    warnings=ai_result.get('warnings', [])
                )

            update_status("success", "✅ AI tahlil tugadi!")

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
                ai_analysis=ai_result['analysis'],
                success=True,
                ai_retry_count=ai_result.get('retry_count', 0),
                files_analyzed=ai_result.get('files_analyzed', total_files),
                total_prompt_size=ai_result.get('prompt_size', 0),
                warnings=ai_result.get('warnings', [])
            )

        except Exception as e:
            update_status("error", f"❌ Kritik xatolik: {str(e)}")
            return TZPRAnalysisResult(
                task_key=task_key,
                success=False,
                error_message=f"❌ Kutilmagan xatolik: {str(e)}"
            )

    def _get_full_tz(self, task_key: str, task_details: Dict) -> str:
        """
        TO'LIQ TZ olish - Task description + Comments
        """
        tz_parts = []

        # 1. Summary
        if task_details.get('summary'):
            tz_parts.append(f"📋 SUMMARY:\n{task_details['summary']}")

        # 2. Description (asosiy TZ)
        if task_details.get('description'):
            tz_parts.append(f"\n📝 DESCRIPTION (ASOSIY TZ):\n{task_details['description']}")

        # 3. Metadata
        tz_parts.append(f"\n📊 METADATA:")
        tz_parts.append(f"   Type: {task_details.get('type', 'Unknown')}")
        tz_parts.append(f"   Priority: {task_details.get('priority', 'Unknown')}")
        tz_parts.append(f"   Assignee: {task_details.get('assignee', 'Unassigned')}")
        tz_parts.append(f"   Story Points: {task_details.get('story_points', 'N/A')}")

        if task_details.get('labels'):
            labels = ', '.join(task_details['labels']) if isinstance(task_details['labels'], list) else task_details[
                'labels']
            tz_parts.append(f"   Labels: {labels}")

        if task_details.get('components'):
            components = ', '.join(task_details['components']) if isinstance(task_details['components'], list) else \
            task_details['components']
            tz_parts.append(f"   Components: {components}")

        # 4. COMMENTS - MUHIM QISM!
        comments = task_details.get('comments', [])
        if comments:
            tz_parts.append(f"\n💬 COMMENTS ({len(comments)} ta - QO'SHIMCHA TALABLAR):")

            for i, comment in enumerate(comments, 1):
                author = comment.get('author', 'Unknown')
                created = comment.get('created', '')
                body = comment.get('body', '')

                tz_parts.append(f"\n[Comment #{i} - {created}] {author}:")
                tz_parts.append(f"{body}")

        return "\n".join(tz_parts)

    def _analyze_with_retry(
            self,
            task_key: str,
            task_details: Dict,
            tz_content: str,
            pr_details: List[Dict],
            max_files: Optional[int],
            show_full_diff: bool,
            status_callback: Callable
    ) -> Dict[str, Any]:
        """
        AI tahlil - Auto retry bilan

        Agar AI limit'ga yetsa, avtomatik fayllar sonini kamaytiradi
        """
        retry_count = 0
        current_max_files = max_files
        warnings = []

        while retry_count < self.MAX_RETRIES:
            try:
                # Prompt yaratish
                prompt_result = self._generate_analysis_prompt(
                    task_key=task_key,
                    task_details=task_details,
                    tz_content=tz_content,
                    pr_details=pr_details,
                    max_files=current_max_files,
                    show_full_diff=show_full_diff
                )

                prompt = prompt_result['prompt']
                prompt_size = len(prompt)
                files_analyzed = prompt_result['files_analyzed']

                # Token estimate
                estimated_tokens = prompt_size // self.CHARS_PER_TOKEN

                status_callback("info", f"   📊 Prompt size: {prompt_size:,} chars (~{estimated_tokens:,} tokens)")
                status_callback("info", f"   📁 Files analyzed: {files_analyzed}")

                # Limit tekshirish
                if estimated_tokens > self.MAX_TOKENS:
                    status_callback("warning", f"   ⚠️ Token limit oshdi! ({estimated_tokens:,} > {self.MAX_TOKENS:,})")

                    if current_max_files is None:
                        # Birinchi marta - 50% ga kamaytirish
                        total_files = sum(len(pr['files']) for pr in pr_details)
                        current_max_files = max(5, total_files // 2)
                    else:
                        # Har safar 30% ga kamaytirish
                        current_max_files = max(5, int(current_max_files * 0.7))

                    retry_count += 1

                    if retry_count >= self.MAX_RETRIES:
                        return {
                            'success': False,
                            'error': f"❌ AI limit'ga yetdi. {self.MAX_RETRIES} marta urinildi, muvaffaqiyatsiz.",
                            'warnings': warnings + [
                                f"Prompt juda katta: {prompt_size:,} chars",
                                f"Oxirgi urinish: {current_max_files} ta fayl bilan"
                            ]
                        }

                    warning_msg = f"Fayllar soni {current_max_files} ga kamaytirildi va qayta urinilmoqda (urinish #{retry_count})"
                    warnings.append(warning_msg)
                    status_callback("warning", f"   🔄 {warning_msg}")

                    time.sleep(1)
                    continue

                # AI'ga yuborish
                status_callback("progress", f"   ⚡ AI'ga yuborilmoqda... (bu 30-60s olishi mumkin)")

                ai_analysis = self.gemini.analyze(prompt)

                return {
                    'success': True,
                    'analysis': ai_analysis,
                    'retry_count': retry_count,
                    'files_analyzed': files_analyzed,
                    'prompt_size': prompt_size,
                    'warnings': warnings
                }

            except Exception as e:
                error_msg = str(e)

                # Limit error detection
                if 'limit' in error_msg.lower() or 'quota' in error_msg.lower() or 'too large' in error_msg.lower():
                    status_callback("warning", f"   ⚠️ AI limit xatosi: {error_msg}")

                    if current_max_files is None:
                        total_files = sum(len(pr['files']) for pr in pr_details)
                        current_max_files = max(5, total_files // 2)
                    else:
                        current_max_files = max(5, int(current_max_files * 0.7))

                    retry_count += 1

                    if retry_count >= self.MAX_RETRIES:
                        return {
                            'success': False,
                            'error': f"❌ AI limit'ga yetdi va {self.MAX_RETRIES} marta urinildi. Xatolik: {error_msg}",
                            'warnings': warnings
                        }

                    warning_msg = f"AI xatosi - retry #{retry_count} ({current_max_files} fayl bilan)"
                    warnings.append(warning_msg)
                    status_callback("warning", f"   🔄 {warning_msg}")

                    time.sleep(2)
                    continue
                else:
                    # Boshqa xato
                    return {
                        'success': False,
                        'error': f"❌ AI xatosi: {error_msg}",
                        'warnings': warnings
                    }

        return {
            'success': False,
            'error': f"❌ {self.MAX_RETRIES} marta urinildi, muvaffaqiyatsiz",
            'warnings': warnings
        }

    def _generate_analysis_prompt(
            self,
            task_key: str,
            task_details: Dict,
            tz_content: str,
            pr_details: List[Dict],
            max_files: Optional[int],
            show_full_diff: bool
    ) -> Dict[str, Any]:
        """
        AI uchun prompt yaratish

        Returns:
            {
                'prompt': str,
                'files_analyzed': int,
                'total_files': int
            }
        """
        # Prompt header
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
📝 TZ (TEXNIK TOPSHIRIQ - TO'LIQ)
═══════════════════════════════════════════════════════════════════════════════

{tz_content}

═══════════════════════════════════════════════════════════════════════════════
💻 KOD O'ZGARISHLARI ({len(pr_details)} ta PR)
═══════════════════════════════════════════════════════════════════════════════
"""

        total_files_count = 0
        analyzed_files_count = 0

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

            # Fayllarni limitlash (agar kerak bo'lsa)
            files_to_include = pr['files']
            if max_files is not None:
                remaining_files = max_files - analyzed_files_count
                files_to_include = pr['files'][:remaining_files]

            total_files_count += len(pr['files'])

            # Har bir faylni qo'shish
            for i, f in enumerate(files_to_include, 1):
                patch = f.get('patch', 'No diff available')

                # Diff ko'rsatish sozlamasi
                if not show_full_diff and len(patch) > 2000:
                    patch = patch[:2000] + "\n... (qolgan qism qisqartirildi - UI sozlamasi)"

                # Katta fayl warning
                patch_warning = ""
                if len(patch) > 10000:
                    patch_warning = f" ⚠️ KATTA: {len(patch):,} chars"

                prompt += f"""
📄 [{i}] {f['filename']}
    Status: {f['status']} | +{f['additions']} -{f['deletions']}{patch_warning}

```diff
{patch}
```

"""
                analyzed_files_count += 1

                # Max files limit
                if max_files is not None and analyzed_files_count >= max_files:
                    break

            # Qolgan fayllar haqida
            if max_files is not None and len(pr['files']) > len(files_to_include):
                skipped = len(pr['files']) - len(files_to_include)
                prompt += f"\n    ⚠️ ... va yana {skipped} ta fayl (limit: {max_files})\n\n"

            if max_files is not None and analyzed_files_count >= max_files:
                break

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

        return {
            'prompt': prompt,
            'files_analyzed': analyzed_files_count,
            'total_files': total_files_count
        }

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