# utils/github/github_client.py - IMPROVED VERSION
"""
GitHub API Client - PR va kod olish

YANGI: Branch name bilan ham PR qidirish!
"""
import requests
import base64
import re
from typing import List, Dict, Optional, Tuple
import time


class GitHubClient:
    """GitHub API bilan ishlash"""

    def __init__(self, token: str = None):
        """
        Args:
            token: GitHub Personal Access Token
        """
        from config.settings import settings

        self.token = token or settings.GITHUB_TOKEN
        self.base_url = settings.GITHUB_API_URL
        self.org = settings.GITHUB_ORG

        self.headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'JIRA-Bug-Analyzer'
        }

        if self.token:
            self.headers['Authorization'] = f'token {self.token}'

        # Rate limit tracking
        self.rate_limit_remaining = 5000
        self.rate_limit_reset = 0

    def _make_request(self, url: str, accept_header: str = None, params: Dict = None) -> requests.Response:
        """API so'rov yuborish (rate limit bilan)"""
        headers = self.headers.copy()
        if accept_header:
            headers['Accept'] = accept_header

        # Rate limit tekshirish
        if self.rate_limit_remaining < 10:
            wait_time = self.rate_limit_reset - time.time()
            if wait_time > 0:
                print(f"⏳ Rate limit kutish: {wait_time:.0f} sekund")
                time.sleep(wait_time + 1)

        response = requests.get(url, headers=headers, params=params, timeout=30)

        # Rate limit yangilash
        self.rate_limit_remaining = int(response.headers.get('X-RateLimit-Remaining', 5000))
        self.rate_limit_reset = int(response.headers.get('X-RateLimit-Reset', 0))

        return response

    def parse_pr_url(self, pr_url: str) -> Tuple[Optional[str], Optional[str], Optional[int]]:
        """
        PR URL dan owner, repo, pr_number ajratish

        Supports:
        - https://github.com/owner/repo/pull/123
        - https://github.com/owner/repo/pull/123/files
        - github.com/owner/repo/pull/123

        Returns:
            (owner, repo, pr_number) yoki (None, None, None)
        """
        patterns = [
            r'github\.com/([^/]+)/([^/]+)/pull/(\d+)',
            r'github\.com/([^/]+)/([^/]+)/pulls/(\d+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, pr_url)
            if match:
                return match.group(1), match.group(2), int(match.group(3))

        return None, None, None

    def get_pr_info(self, owner: str, repo: str, pr_number: int) -> Optional[Dict]:
        """PR asosiy ma'lumotlarini olish"""
        url = f'{self.base_url}/repos/{owner}/{repo}/pulls/{pr_number}'
        response = self._make_request(url)

        if response.status_code != 200:
            print(f"❌ PR info olishda xatolik: {response.status_code}")
            return None

        data = response.json()

        return {
            'title': data.get('title', ''),
            'state': data.get('state', ''),
            'merged': data.get('merged', False),
            'user': data.get('user', {}).get('login', ''),
            'created_at': data.get('created_at', ''),
            'merged_at': data.get('merged_at', ''),
            'base': data.get('base', {}).get('ref', ''),
            'head': data.get('head', {}).get('ref', ''),
            'commits': data.get('commits', 0),
            'additions': data.get('additions', 0),
            'deletions': data.get('deletions', 0),
            'changed_files': data.get('changed_files', 0),
            'body': data.get('body', '')
        }

    def get_pr_files(self, owner: str, repo: str, pr_number: int) -> List[Dict]:
        """PR da o'zgargan fayllar ro'yxatini olish"""
        url = f'{self.base_url}/repos/{owner}/{repo}/pulls/{pr_number}/files'

        all_files = []
        page = 1
        per_page = 100

        while True:
            paginated_url = f'{url}?page={page}&per_page={per_page}'
            response = self._make_request(paginated_url)

            if response.status_code != 200:
                print(f"❌ PR files olishda xatolik: {response.status_code}")
                break

            files = response.json()
            if not files:
                break

            for f in files:
                all_files.append({
                    'filename': f.get('filename', ''),
                    'status': f.get('status', ''),
                    'additions': f.get('additions', 0),
                    'deletions': f.get('deletions', 0),
                    'changes': f.get('changes', 0),
                    'patch': f.get('patch', ''),
                    'blob_url': f.get('blob_url', ''),
                    'raw_url': f.get('raw_url', ''),
                    'sha': f.get('sha', ''),
                    'previous_filename': f.get('previous_filename', '')
                })

            if len(files) < per_page:
                break
            page += 1

        return all_files

    def get_file_content(self, owner: str, repo: str, path: str, ref: str = 'main') -> Optional[str]:
        """Faylning to'liq mazmunini olish"""
        url = f'{self.base_url}/repos/{owner}/{repo}/contents/{path}?ref={ref}'
        response = self._make_request(url)

        if response.status_code != 200:
            print(f"❌ File content olishda xatolik: {response.status_code} - {path}")
            return None

        data = response.json()

        # Base64 decode
        content = data.get('content', '')
        if content:
            try:
                return base64.b64decode(content).decode('utf-8')
            except Exception as e:
                print(f"⚠️ Decode xatolik: {e}")
                return None

        return None

    def get_pr_diff(self, owner: str, repo: str, pr_number: int) -> Optional[str]:
        """PR ning to'liq diff'ini olish"""
        url = f'{self.base_url}/repos/{owner}/{repo}/pulls/{pr_number}'
        response = self._make_request(url, accept_header='application/vnd.github.v3.diff')

        if response.status_code == 200:
            return response.text

        return None

    def get_pr_commits(self, owner: str, repo: str, pr_number: int) -> List[Dict]:
        """PR dagi commitlar ro'yxati"""
        url = f'{self.base_url}/repos/{owner}/{repo}/pulls/{pr_number}/commits'
        response = self._make_request(url)

        if response.status_code != 200:
            return []

        commits = []
        for c in response.json():
            commits.append({
                'sha': c.get('sha', '')[:7],
                'message': c.get('commit', {}).get('message', ''),
                'author': c.get('commit', {}).get('author', {}).get('name', ''),
                'date': c.get('commit', {}).get('author', {}).get('date', '')
            })

        return commits

    def check_rate_limit(self) -> Dict:
        """Rate limit holatini tekshirish"""
        url = f'{self.base_url}/rate_limit'
        response = self._make_request(url)

        if response.status_code == 200:
            data = response.json()
            core = data.get('resources', {}).get('core', {})
            return {
                'limit': core.get('limit', 0),
                'remaining': core.get('remaining', 0),
                'reset': core.get('reset', 0),
                'used': core.get('used', 0)
            }

        return {}

    def test_connection(self) -> bool:
        """GitHub ulanishini tekshirish"""
        try:
            rate_info = self.check_rate_limit()
            if rate_info:
                print(f"✅ GitHub ulandi!")
                print(f"   Rate limit: {rate_info['remaining']}/{rate_info['limit']}")
                return True
        except Exception as e:
            print(f"❌ GitHub ulanish xatosi: {e}")

        return False

    def search_pr_by_jira_key(self, jira_key: str) -> List[Dict]:
        """
        Jira Key (masalan DEV-6959) bo'yicha GitHub dan PR qidirish.
        Bu metod Jira link bermagan holatlar uchun zaxira yo'li.

        YANGI: Multi-strategy search!
        1. Title/body'da JIRA key bor PR'lar
        2. Branch name'da JIRA key bor PR'lar (head:branch-name)
        """
        url = f"{self.base_url}/search/issues"
        found_prs = []

        # Strategy 1: Search in title and body
        query1 = f'org:{self.org} "{jira_key}" is:pr'
        print(f"   🔍 GitHub Search (title/body): {query1}")

        try:
            response1 = self._make_request(url, params={'q': query1, 'sort': 'updated'})

            if response1.status_code == 200:
                items = response1.json().get('items', [])
                for item in items:
                    found_prs.append({
                        'url': item.get('html_url'),
                        'title': item.get('title'),
                        'status': item.get('state'),
                        'source': 'GitHub (title/body)'
                    })

                if items:
                    print(f"   ✅ Title/body search: {len(items)} ta topildi!")
            else:
                print(f"   ⚠️ Title/body search error: {response1.status_code}")
        except Exception as e:
            print(f"   ⚠️ Title/body search exception: {e}")

        # Strategy 2: Search in branch names (if not found in title/body)
        if not found_prs:
            print(f"   🔍 Branch name search...")

            # Common branch patterns
            branch_patterns = [
                jira_key,  # DEV-6959
                jira_key.lower(),  # dev-6959
                jira_key.replace('-', '_'),  # DEV_6959
                f"feature/{jira_key}",  # feature/DEV-6959
                f"bugfix/{jira_key}",  # bugfix/DEV-6959
                f"fix/{jira_key}",  # fix/DEV-6959
            ]

            for pattern in branch_patterns:
                query2 = f'org:{self.org} head:{pattern} is:pr'

                try:
                    response2 = self._make_request(url, params={'q': query2, 'sort': 'updated'})

                    if response2.status_code == 200:
                        items = response2.json().get('items', [])
                        for item in items:
                            pr_url = item.get('html_url')
                            # Avoid duplicates
                            if not any(pr['url'] == pr_url for pr in found_prs):
                                found_prs.append({
                                    'url': pr_url,
                                    'title': item.get('title'),
                                    'status': item.get('state'),
                                    'source': f'GitHub (branch:{pattern})'
                                })

                        # If found, break
                        if items:
                            print(f"   ✅ Branch search: {len(items)} ta topildi (pattern: {pattern})!")
                            break
                except Exception as e:
                    print(f"   ⚠️ Branch search exception ({pattern}): {e}")
                    continue

        # Final result
        if found_prs:
            print(f"   ✅ JAMI: {len(found_prs)} ta PR topildi!")
        else:
            print(f"   ❌ Hech qanday PR topilmadi")

        return found_prs