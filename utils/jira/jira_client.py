# jira_client.py - IMPROVED VERSION
"""
JIRA API Client - Task va PR ma'lumotlarini olish

YANGI: Development Status API dan PR URL olish!
"""
from jira import JIRA
from typing import Dict, List, Optional, Any
import json
import requests


class JiraClient:
    """JIRA API bilan ishlash"""

    def __init__(self):
        from config.settings import settings

        self.server = settings.JIRA_SERVER
        self.email = settings.JIRA_EMAIL
        self.token = settings.JIRA_API_TOKEN

        # Custom fields
        self.story_points_field = settings.STORY_POINTS_FIELD
        self.sprint_field = settings.SPRINT_FIELD
        self.pr_field = settings.PR_FIELD

        self._client = None

    @property
    def client(self) -> JIRA:
        """Lazy connection"""
        if self._client is None:
            self._client = JIRA(
                server=self.server,
                basic_auth=(self.email, self.token)
            )
        return self._client

    def test_connection(self) -> bool:
        """JIRA ulanishini tekshirish"""
        try:
            myself = self.client.myself()
            print(f"✅ JIRA ulandi: {myself['displayName']}")
            return True
        except Exception as e:
            print(f"❌ JIRA ulanish xatosi: {e}")
            return False

    def get_issue(self, issue_key: str, expand: str = 'changelog,renderedFields') -> Optional[Any]:
        """Bitta issue ni olish"""
        try:
            issue = self.client.issue(issue_key, expand=expand)
            return issue
        except Exception as e:
            print(f"❌ Issue olishda xatolik: {e}")
            return None

    def get_task_details(self, issue_key: str) -> Optional[Dict]:
        """Task ning asosiy ma'lumotlarini olish (TZ uchun)"""
        issue = self.get_issue(issue_key)
        if not issue:
            return None

        fields = issue.fields

        # Comments olish
        comments = []
        if hasattr(fields, 'comment') and hasattr(fields.comment, 'comments'):
            for c in fields.comment.comments:
                comments.append({
                    'author': getattr(c.author, 'displayName', 'Unknown'),
                    'body': c.body,
                    'created': c.created[:16].replace('T', ' ')
                })

        # PR URLs olish (YANGI METHOD!)
        pr_urls = self.extract_pr_urls_dev_status(issue_key)

        # Agar Dev Status API ishlamasa, eski methoddan harakat qilish
        if not pr_urls:
            pr_urls = self.extract_pr_urls_legacy(issue)

        return {
            'key': issue.key,
            'summary': fields.summary or '',
            'description': fields.description or '',
            'type': getattr(fields.issuetype, 'name', '') if fields.issuetype else '',
            'status': getattr(fields.status, 'name', '') if fields.status else '',
            'assignee': getattr(fields.assignee, 'displayName', 'Unassigned') if fields.assignee else 'Unassigned',
            'reporter': getattr(fields.reporter, 'displayName', 'Unknown') if fields.reporter else 'Unknown',
            'priority': getattr(fields.priority, 'name', 'None') if fields.priority else 'None',
            'story_points': getattr(fields, self.story_points_field, 0) or 0,
            'comments': comments,
            'pr_urls': pr_urls,
            'created': fields.created[:10] if fields.created else '',
            'resolved': fields.resolutiondate[:10] if fields.resolutiondate else '',
            'labels': list(fields.labels) if fields.labels else [],
            'components': [c.name for c in fields.components] if fields.components else []
        }

    def extract_pr_urls_dev_status(self, issue_key: str) -> List[Dict]:
        """
        YANGI METHOD: Development Status API dan PR URL olish

        API: /rest/dev-status/1.0/issue/detail
        """
        pr_urls = []

        try:
            # First, get issue ID (not key!)
            issue = self.client.issue(issue_key)
            issue_id = issue.id

            # Development Status API endpoint
            url = f"{self.server}/rest/dev-status/1.0/issue/detail"

            params = {
                'issueId': issue_id,  # Use ID, not KEY!
                'applicationType': 'GitHub',
                'dataType': 'pullrequest'
            }

            response = requests.get(
                url,
                params=params,
                auth=(self.email, self.token),
                headers={'Accept': 'application/json'},
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()

                # Parse response
                detail = data.get('detail', [])
                for item in detail:
                    pull_requests = item.get('pullRequests', [])
                    for pr in pull_requests:
                        pr_url = pr.get('url', '')
                        if pr_url:
                            pr_urls.append({
                                'url': pr_url,
                                'title': pr.get('name', pr.get('title', '')),
                                'status': pr.get('status', ''),
                                'source': 'JIRA (Dev Status API)'
                            })

                if pr_urls:
                    print(f"   ✅ Dev Status API: {len(pr_urls)} ta PR topildi!")

        except Exception as e:
            print(f"   ⚠️ Dev Status API error: {e}")

        return pr_urls

    def extract_pr_urls_legacy(self, issue) -> List[Dict]:
        """
        ESKI METHOD: Custom field dan PR URL olish

        Bu method eski JIRA integratsiyalar uchun
        """
        pr_urls = []

        try:
            pr_data = getattr(issue.fields, self.pr_field, None)

            if not pr_data:
                return pr_urls

            # String bo'lsa JSON parse
            if isinstance(pr_data, str):
                try:
                    pr_json = json.loads(pr_data)
                except json.JSONDecodeError:
                    return pr_urls
            elif isinstance(pr_data, dict):
                pr_json = pr_data
            else:
                return pr_urls

            # Format 1: Direct pullRequests array
            if 'pullRequests' in pr_json:
                for pr in pr_json['pullRequests']:
                    url = pr.get('url', '') or pr.get('source', {}).get('url', '')
                    if url:
                        pr_urls.append({
                            'url': url,
                            'title': pr.get('name', pr.get('title', '')),
                            'status': pr.get('status', pr.get('state', '')),
                            'source': 'JIRA (Legacy)'
                        })

            # Format 2: Nested in json.cachedValue
            if 'json' in pr_json:
                json_data = pr_json['json']
                if isinstance(json_data, str):
                    try:
                        json_data = json.loads(json_data)
                    except:
                        pass

                if isinstance(json_data, dict):
                    cached = json_data.get('cachedValue', {})
                    pull_requests = cached.get('pullRequests', [])
                    for pr in pull_requests:
                        url = pr.get('url', '')
                        if url:
                            pr_urls.append({
                                'url': url,
                                'title': pr.get('name', ''),
                                'status': pr.get('status', ''),
                                'source': 'JIRA (Legacy)'
                            })

            # Format 3: Development panel v2
            if 'detail' in pr_json:
                for detail in pr_json.get('detail', []):
                    prs = detail.get('pullRequests', [])
                    for pr in prs:
                        url = pr.get('url', '')
                        if url:
                            pr_urls.append({
                                'url': url,
                                'title': pr.get('name', ''),
                                'status': pr.get('status', ''),
                                'source': 'JIRA (Legacy)'
                            })

        except Exception as e:
            print(f"   ⚠️ Legacy PR extraction error: {e}")

        # Dublikatlarni olib tashlash
        seen_urls = set()
        unique_prs = []
        for pr in pr_urls:
            if pr['url'] and pr['url'] not in seen_urls:
                seen_urls.add(pr['url'])
                unique_prs.append(pr)

        return unique_prs

    def get_task_tz(self, issue_key: str) -> str:
        """Task ning TZ (Technical Zadanie) ni olish"""
        details = self.get_task_details(issue_key)
        if not details:
            return ""

        tz_parts = []

        # Summary
        if details['summary']:
            tz_parts.append(f"📋 SUMMARY:\n{details['summary']}")

        # Description (asosiy TZ)
        if details['description']:
            tz_parts.append(f"\n📝 DESCRIPTION (TZ):\n{details['description']}")

        # Metadata
        tz_parts.append(f"\n📊 METADATA:")
        tz_parts.append(f"   Type: {details['type']}")
        tz_parts.append(f"   Priority: {details['priority']}")
        tz_parts.append(f"   Assignee: {details['assignee']}")
        tz_parts.append(f"   Story Points: {details['story_points']}")

        if details['labels']:
            tz_parts.append(f"   Labels: {', '.join(details['labels'])}")

        if details['components']:
            tz_parts.append(f"   Components: {', '.join(details['components'])}")

        # Comments (qo'shimcha requirements)
        if details['comments']:
            tz_parts.append(f"\n💬 COMMENTS ({len(details['comments'])} ta):")
            for i, comment in enumerate(details['comments'][-5:], 1):
                tz_parts.append(f"\n[{comment['created']}] {comment['author']}:")
                body = comment['body']
                if len(body) > 500:
                    body = body[:500] + "..."
                tz_parts.append(f"   {body}")

        return "\n".join(tz_parts)

    def search_issues(self, jql: str, max_results: int = 50) -> List[Dict]:
        """JQL bilan issue larni qidirish"""
        try:
            issues = self.client.search_issues(
                jql,
                maxResults=max_results,
                expand='changelog'
            )

            results = []
            for issue in issues:
                results.append({
                    'key': issue.key,
                    'summary': issue.fields.summary,
                    'status': getattr(issue.fields.status, 'name', ''),
                    'type': getattr(issue.fields.issuetype, 'name', ''),
                    'assignee': getattr(issue.fields.assignee, 'displayName',
                                        'Unassigned') if issue.fields.assignee else 'Unassigned'
                })

            return results

        except Exception as e:
            print(f"❌ Search xatolik: {e}")
            return []