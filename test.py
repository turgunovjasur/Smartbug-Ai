# test_dev_status_api.py
"""
Test JIRA Development Status API
"""
import os
from dotenv import load_dotenv
import requests

load_dotenv()

# Config
JIRA_SERVER = os.getenv('JIRA_SERVER')
JIRA_EMAIL = os.getenv('JIRA_EMAIL')
JIRA_API_TOKEN = os.getenv('JIRA_API_TOKEN')
ISSUE_KEY = "DEV-6959"

print("=" * 80)
print("🧪 JIRA DEVELOPMENT STATUS API TEST")
print("=" * 80)
print()

# Get issue ID first
print(f"1️⃣ Getting issue ID for {ISSUE_KEY}...")

from jira import JIRA

jira = JIRA(
    server=JIRA_SERVER,
    basic_auth=(JIRA_EMAIL, JIRA_API_TOKEN)
)

issue = jira.issue(ISSUE_KEY)
issue_id = issue.id

print(f"   ✅ Issue ID: {issue_id}")
print()

# Test Dev Status API
print("2️⃣ Testing Development Status API...")
print()

url = f"{JIRA_SERVER}/rest/dev-status/1.0/issue/detail"

params = {
    'issueId': issue_id,
    'applicationType': 'GitHub',
    'dataType': 'pullrequest'
}

print(f"   URL: {url}")
print(f"   Params: {params}")
print()

response = requests.get(
    url,
    params=params,
    auth=(JIRA_EMAIL, JIRA_API_TOKEN),
    headers={'Accept': 'application/json'},
    timeout=10
)

print(f"   Status Code: {response.status_code}")
print()

if response.status_code == 200:
    import json

    data = response.json()

    print("3️⃣ Response Data:")
    print(json.dumps(data, indent=2))
    print()

    # Parse PR URLs
    print("4️⃣ Extracted PR URLs:")
    detail = data.get('detail', [])

    pr_count = 0
    for item in detail:
        pull_requests = item.get('pullRequests', [])
        for pr in pull_requests:
            pr_count += 1
            print(f"\n   PR #{pr_count}:")
            print(f"   - URL: {pr.get('url', 'N/A')}")
            print(f"   - Title: {pr.get('name', 'N/A')}")
            print(f"   - Status: {pr.get('status', 'N/A')}")

    if pr_count == 0:
        print("   ❌ No PRs found in response")
    else:
        print(f"\n   ✅ Total: {pr_count} PR(s) found!")

else:
    print(f"   ❌ Error: {response.status_code}")
    print(f"   Response: {response.text}")

print()
print("=" * 80)
print("✅ TEST COMPLETE")
print("=" * 80)