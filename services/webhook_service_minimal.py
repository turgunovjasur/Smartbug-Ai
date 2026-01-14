"""
JIRA Webhook Service - MINIMAL VERSION
=======================================

Task "Ready to Test" statusiga o'tganda avtomatik TZ-PR tekshirish
Sprint close bo'lganda avtomatik Excel download va embedding

Author: JASUR TURGUNOV
Date: 2025-12-26
"""
from fastapi import FastAPI, BackgroundTasks, Request
from pydantic import BaseModel
from typing import Optional, Dict, Any
import uvicorn
from datetime import datetime
import logging
import sys
import os

# Loyiha root path qo'shish
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Imports
from services.tz_pr_service import TZPRService
from utils.jira.jira_comment_writer import JiraCommentWriter

# ============================================================================
# LOGGING SETUP
# ============================================================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('webhook.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ============================================================================
# FASTAPI APP
# ============================================================================
app = FastAPI(
    title="JIRA TZ-PR Auto Checker",
    description="Avtomatik TZ-PR moslik tekshirish",
    version="1.0.0"
)

# Services (lazy loading)
_tz_pr_service = None
_comment_writer = None


def get_tz_pr_service():
    """TZ-PR service - singleton"""
    global _tz_pr_service
    if _tz_pr_service is None:
        _tz_pr_service = TZPRService()
    return _tz_pr_service


def get_comment_writer():
    """Comment writer - singleton"""
    global _comment_writer
    if _comment_writer is None:
        _comment_writer = JiraCommentWriter()
    return _comment_writer


# ============================================================================
# WEBHOOK MODELS
# ============================================================================

class WebhookPayload(BaseModel):
    """JIRA webhook payload (simplified)"""
    webhookEvent: str
    issue: Dict[str, Any]
    changelog: Optional[Dict[str, Any]] = None


# ============================================================================
# MAIN WEBHOOK ENDPOINT
# ============================================================================

@app.post("/webhook/jira")
async def jira_webhook(
        request: Request,
        background_tasks: BackgroundTasks
):
    """
    JIRA webhook endpoint

    JIRA bu endpoint'ga har safar issue update bo'lganda request yuboradi
    """
    try:
        # Raw data olish
        body = await request.json()

        logger.info("=" * 80)
        logger.info(f"Webhook received: {body.get('webhookEvent', 'unknown')}")

        # Webhook event type
        event = body.get('webhookEvent')

        # Faqat issue update'larni qabul qilamiz
        if event != "jira:issue_updated":
            logger.info(f"⏭️  Event '{event}' ignored (not issue update)")
            return {"status": "ignored", "reason": f"event is '{event}'"}

        # Issue data
        issue = body.get('issue', {})
        task_key = issue.get('key')

        if not task_key:
            logger.warning(" No task key found")
            return {"status": "error", "reason": "no task key"}

        # Changelog tekshirish
        changelog = body.get('changelog', {})
        items = changelog.get('items', [])

        # Status o'zgarishini topish
        status_changed = False
        new_status = None
        old_status = None

        for item in items:
            if item.get('field') == 'status':
                old_status = item.get('fromString')
                new_status = item.get('toString')
                status_changed = True
                break

        if not status_changed:
            logger.info(f"⏭️  {task_key}: No status change")
            return {"status": "ignored", "reason": "status not changed"}

        logger.info(f"{task_key}: {old_status} → {new_status}")

        # "Ready to Test" statusini tekshirish
        target_statuses = [
            "Ready to Test",
            "READY TO TEST",
            "Ready To Test",
            "TESTING",
            "Testing"
        ]

        if new_status not in target_statuses:
            logger.info(f"⏭️  Status '{new_status}' ignored")
            return {
                "status": "ignored",
                "reason": f"status is '{new_status}', not in {target_statuses}"
            }

        # BINGO! Ready to Test statusiga o'tdi
        logger.info(f"{task_key} → {new_status} - Starting TZ-PR check...")

        # Background task qo'shish
        background_tasks.add_task(
            check_tz_pr_and_comment,
            task_key=task_key,
            new_status=new_status
        )

        return {
            "status": "processing",
            "task_key": task_key,
            "old_status": old_status,
            "new_status": new_status,
            "message": "TZ-PR check started"
        }

    except Exception as e:
        logger.error(f"Webhook error: {e}", exc_info=True)
        return {"status": "error", "error": str(e)}


# ============================================================================
# BACKGROUND TASK - TZ-PR CHECK
# ============================================================================

async def check_tz_pr_and_comment(task_key: str, new_status: str):
    """
    Background task: TZ-PR mosligini tekshirish va comment yozish

    Bu function webhook response qaytarilgandan KEYIN ishlaydi
    """
    try:
        logger.info(f"[{task_key}] TZ-PR check started...")

        # Services
        tz_pr_service = get_tz_pr_service()
        comment_writer = get_comment_writer()

        # 1. TZ-PR tahlil qilish
        logger.info(f"[{task_key}] Analyzing with AI...")
        result = tz_pr_service.analyze_task(task_key)

        if not result.success:
            logger.error(f"[{task_key}] Analysis failed: {result.error_message}")

            # Xatolikni ham commentga yozamiz
            error_comment = format_error_comment(task_key, result.error_message, new_status)
            comment_writer.add_comment(task_key, error_comment)
            return

        # 2. Natijani format qilish
        logger.info(f"[{task_key}] Formatting comment...")
        comment_text = format_success_comment(result, new_status)

        # 3. JIRA ga comment yozish
        logger.info(f"[{task_key}] Writing comment to JIRA...")
        success = comment_writer.add_comment(task_key, comment_text)

        if success:
            logger.info(f"[{task_key}] Comment added successfully!")
        else:
            logger.error(f"[{task_key}] Failed to add comment")

    except Exception as e:
        logger.error(f"[{task_key}] Background task error: {e}", exc_info=True)

        # Critical error ham yoziladi
        try:
            error_comment = format_critical_error(task_key, str(e), new_status)
            comment_writer = get_comment_writer()
            comment_writer.add_comment(task_key, error_comment)
        except:
            pass


# ============================================================================
# COMMENT FORMATTERS
# ============================================================================

def format_success_comment(result, new_status: str) -> str:
    """Muvaffaqiyatli tahlil natijasini format qilish"""

    # Emoji va status
    status_emoji = "🎯" if new_status == "Ready to Test" else "🧪"

    comment = f"""
{status_emoji} *Avtomatik TZ-PR Moslik Tekshiruvi*

----

*Task:* {result.task_key}
*Vaqt:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
*Status:* {new_status}

----

*Statistika:*
• Pull Requests: {result.pr_count} ta
• O'zgargan fayllar: {result.files_changed} ta
• Qo'shilgan qatorlar: {{color:green}}+{result.total_additions}{{color}}
• O'chirilgan qatorlar: {{color:red}}-{result.total_deletions}{{color}}

----

*AI Tahlili (Gemini 2.5 Flash):*

{result.ai_analysis}

----

_Bu komment AI tomonidan avtomatik yaratilgan. Savollar bo'lsa QA Team ga murojaat qiling._
"""

    return comment


def format_error_comment(task_key: str, error_message: str, new_status: str) -> str:
    """Xatolik holatida comment"""

    comment = f"""
*Avtomatik TZ-PR Tekshiruvi - Xatolik*

----

*Task:* {task_key}
*Vaqt:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
*Status:* {new_status}

----

*Xatolik:*

{error_message}

----

*Mumkin sabablar:*
• Task uchun PR topilmadi
• GitHub access xatoligi
• TZ (Description) bo'sh

----

_Manual tekshirish kerak. QA Team'ga xabar bering._
"""

    return comment


def format_critical_error(task_key: str, error: str, new_status: str) -> str:
    """Kritik xatolik"""

    comment = f"""
*Avtomatik TZ-PR Tekshiruvi - Kritik Xatolik*

----

*Task:* {task_key}
*Vaqt:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
*Status:* {new_status}

----

*Kritik Xatolik:*

```
{error}
```

----

_System administrator'ga xabar berildi._
"""

    return comment


# ============================================================================
# HEALTH CHECK ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint - service holatini ko'rsatish"""
    return {
        "service": "JIRA TZ-PR Auto Checker",
        "status": "running",
        "version": "1.0.0",
        "endpoints": {
            "webhook": "/webhook/jira",
            "manual_check": "/manual/check/{task_key}",
            "health": "/health"
        },
        "timestamp": datetime.now().isoformat()
    }


@app.get("/health")
async def health_check():
    """Health check - monitoring uchun"""

    # Services tekshirish
    health = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {}
    }

    try:
        tz_pr = get_tz_pr_service()
        health["services"]["tz_pr"] = "ok" if tz_pr else "error"
    except Exception as e:
        health["services"]["tz_pr"] = f"error: {str(e)}"
        health["status"] = "unhealthy"

    try:
        writer = get_comment_writer()
        health["services"]["jira_comment"] = "ok" if writer.jira else "error"
    except Exception as e:
        health["services"]["jira_comment"] = f"error: {str(e)}"
        health["status"] = "unhealthy"

    return health


@app.post("/manual/check/{task_key}")
async def manual_check(task_key: str, background_tasks: BackgroundTasks):
    """
    Manual trigger - testing uchun

    Usage:
        curl -X POST http://localhost:8000/manual/check/DEV-1234
    """
    logger.info(f"Manual check triggered for {task_key}")

    background_tasks.add_task(
        check_tz_pr_and_comment,
        task_key=task_key,
        new_status="Manual Check"
    )

    return {
        "status": "processing",
        "task_key": task_key,
        "message": f"Manual TZ-PR check started for {task_key}"
    }


# ============================================================================
# STARTUP EVENT
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Service boshlanganda"""
    logger.info("=" * 80)
    logger.info("JIRA TZ-PR Auto Checker Started")
    logger.info("=" * 80)
    logger.info(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Listening on: http://0.0.0.0:8000")
    logger.info(f"Webhook endpoint: /webhook/jira")
    logger.info("=" * 80)


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    # Server ishga tushirish
    uvicorn.run(
        "webhook_service_minimal:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Development uchun - production'da False
        log_level="info"
    )