"""
PR Debug Test - JIRA dan PR ma'lumotlarini tekshirish
"""
from jira import JIRA
from dotenv import load_dotenv
import os
import json

load_dotenv()

print("=" * 80)
print("🔍 JIRA PR DEBUG TEST")
print("=" * 80)
print()

# 1. JIRA ga ulanish
print("🔗 JIRA ga ulanilmoqda...")
jira = JIRA(
    server=os.getenv('JIRA_SERVER'),
    basic_auth=(os.getenv('JIRA_EMAIL'), os.getenv('JIRA_API_TOKEN'))
)
print("✅ JIRA ga ulandi")
print()

# 2. Issue key ni olish
issue_key = input("📌 Issue key kiriting (default: DEV-6346): ").strip() or "DEV-6346"
print()

print(f"📥 {issue_key} yuklanmoqda...")
try:
    issue = jira.issue(issue_key, expand='changelog', fields='*all')
    print(f"✅ {issue_key} yuklandi")
except Exception as e:
    print(f"❌ Xatolik: {e}")
    exit(1)

print()
print("=" * 80)
print("📊 ISSUE BASIC INFO")
print("=" * 80)
print(f"Key: {issue.key}")
print(f"Summary: {issue.fields.summary}")
print(f"Type: {issue.fields.issuetype.name}")
print(f"Status: {issue.fields.status.name}")
print()

# 3. Barcha field nomlarini ko'rish
print("=" * 80)
print("📋 BARCHA FIELD NOMLARI")
print("=" * 80)
print()

all_fields = jira.fields()
print(f"Jami {len(all_fields)} ta field mavjud")
print()

# PR bilan bog'liq fieldlarni qidirish
print("🔍 PR bilan bog'liq fieldlar:")
pr_related_fields = []
for field in all_fields:
    field_name = field['name'].lower()
    field_id = field['id']
    if any(keyword in field_name for keyword in ['pull', 'pr', 'request', 'git', 'github', 'commit']):
        pr_related_fields.append(field)
        print(f"   • {field['name']} ({field['id']})")

print()

# 4. Issue dagi barcha custom field larni ko'rish
print("=" * 80)
print("📦 ISSUE DAGI CUSTOM FIELDS")
print("=" * 80)
print()

issue_dict = issue.raw['fields']
custom_fields = {}

for field_id, field_value in issue_dict.items():
    if field_id.startswith('customfield_'):
        # Field nomini topish
        field_name = next((f['name'] for f in all_fields if f['id'] == field_id), field_id)
        custom_fields[field_id] = {
            'name': field_name,
            'value': field_value
        }

print(f"Jami {len(custom_fields)} ta custom field")
print()

# PR bilan bog'liq custom fieldlarni ko'rsatish
print("🔗 PR bilan bog'liq custom fields:")
for field_id, field_data in custom_fields.items():
    field_name = field_data['name'].lower()
    if any(keyword in field_name for keyword in ['pull', 'pr', 'request', 'git', 'github', 'commit']):
        print(f"\n   Field: {field_data['name']}")
        print(f"   ID: {field_id}")
        print(f"   Value type: {type(field_data['value'])}")
        print(f"   Value: {field_data['value']}")

print()

# 5. Eng keng tarqalgan PR field larni tekshirish
print("=" * 80)
print("🔬 KENG TARQALGAN PR FIELDLARNI TEKSHIRISH")
print("=" * 80)
print()

common_pr_fields = [
    'customfield_10000',  # Development
    'customfield_10001',  # Development (alternate)
    'customfield_10100',  # Pull Request
    'customfield_10101',  # GitHub
    'customfield_10200',  # Code Review
]

for field_id in common_pr_fields:
    try:
        value = getattr(issue.fields, field_id, None)
        if value is not None:
            print(f"✅ {field_id} topildi:")
            print(f"   Type: {type(value)}")
            print(f"   Value: {value}")
            print()

            # Agar JSON string bo'lsa, parse qilish
            if isinstance(value, str):
                try:
                    parsed = json.loads(value)
                    print(f"   📋 Parsed JSON:")
                    print(json.dumps(parsed, indent=2))
                    print()
                except:
                    pass
        else:
            print(f"❌ {field_id} topilmadi yoki bo'sh")
    except Exception as e:
        print(f"⚠️ {field_id} xatolik: {e}")
    print()

# 6. Issue Web Links tekshirish
print("=" * 80)
print("🔗 WEB LINKS VA REMOTE LINKS")
print("=" * 80)
print()

# Remote links
try:
    remote_links = jira.remote_links(issue.key)
    print(f"Remote links: {len(remote_links)} ta")
    for link in remote_links:
        print(f"\n   Link ID: {link.id}")
        print(f"   Title: {link.raw.get('object', {}).get('title', 'N/A')}")
        print(f"   URL: {link.raw.get('object', {}).get('url', 'N/A')}")

        # GitHub PR link ekanligini tekshirish
        url = link.raw.get('object', {}).get('url', '')
        if 'github.com' in url and '/pull/' in url:
            print(f"   🎯 GITHUB PR TOPILDI!")
            print(f"   PR URL: {url}")
except Exception as e:
    print(f"⚠️ Remote links xatolik: {e}")

print()

# 7. Development ma'lumoti (agar mavjud bo'lsa)
print("=" * 80)
print("💻 DEVELOPMENT INFORMATION")
print("=" * 80)
print()

# Jira Software development panel
try:
    # customfield_10000 odatda Development field
    dev_field = getattr(issue.fields, 'customfield_10000', None)
    if dev_field:
        print("✅ Development field topildi!")
        print(f"Type: {type(dev_field)}")

        if isinstance(dev_field, str):
            print("\n📋 Raw content:")
            print(dev_field)
            print()

            try:
                dev_json = json.loads(dev_field)
                print("📊 Parsed JSON:")
                print(json.dumps(dev_json, indent=2))
            except:
                pass
        elif isinstance(dev_field, dict):
            print("\n📊 Development data:")
            print(json.dumps(dev_field, indent=2))
    else:
        print("❌ Development field topilmadi")
except Exception as e:
    print(f"⚠️ Development field xatolik: {e}")

print()

# 8. FINAL SUMMARY
print("=" * 80)
print("📝 DEBUG SUMMARY")
print("=" * 80)
print()
print("🔍 PR ma'lumotlarini qayerdan topish mumkin:")
print()
print("1. Custom Fields ichida PR bilan bog'liq fieldlar:")
for field_id, field_data in custom_fields.items():
    field_name = field_data['name'].lower()
    if any(keyword in field_name for keyword in ['pull', 'pr', 'request', 'git', 'github']):
        has_value = "✅" if field_data['value'] else "❌"
        print(f"   {has_value} {field_data['name']} ({field_id})")

print()
print("2. Remote Links (Web Links):")
try:
    remote_links = jira.remote_links(issue.key)
    github_prs = [l for l in remote_links if
                  'github.com' in str(l.raw.get('object', {}).get('url', '')) and '/pull/' in str(
                      l.raw.get('object', {}).get('url', ''))]
    print(f"   GitHub PR links: {len(github_prs)} ta")
    for link in github_prs:
        print(f"   🔗 {link.raw.get('object', {}).get('url', 'N/A')}")
except:
    print("   ⚠️ Remote links tekshirib bo'lmadi")

print()
print("3. Development Field:")
dev_field = getattr(issue.fields, 'customfield_10000', None)
print(f"   {'✅' if dev_field else '❌'} customfield_10000 (Development)")

print()
print("=" * 80)
print("✅ DEBUG TUGADI")
print("=" * 80)
print()
print("💡 Agar PR topilmasa:")
print("   1. JIRA-GitHub integration sozlangan bo'lishi kerak")
print("   2. PR JIRA task bilan bog'langan bo'lishi kerak")
print("   3. GitHub token ruxsatlari to'g'ri bo'lishi kerak")
print()