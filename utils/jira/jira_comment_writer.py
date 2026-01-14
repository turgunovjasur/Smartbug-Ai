# utils/jira/jira_comment_writer.py
"""
JIRA Comment Writer - JIRA taskga comment qo'shish

AI tahlil natijalarini JIRA comment sifatida yozadi
"""
from jira import JIRA
import os
from dotenv import load_dotenv
import logging

load_dotenv()

logger = logging.getLogger(__name__)


class JiraCommentWriter:
    """JIRA ga comment yozish"""

    def __init__(self):
        """JIRA client yaratish"""
        try:
            self.jira = JIRA(
                server=os.getenv('JIRA_SERVER'),
                basic_auth=(
                    os.getenv('JIRA_EMAIL'),
                    os.getenv('JIRA_API_TOKEN')
                )
            )
            logger.info("✅ JIRA connected for commenting")
        except Exception as e:
            logger.error(f"❌ JIRA connection failed: {e}")
            self.jira = None

    def add_comment(self, task_key: str, comment_text: str) -> bool:
        """
        Task ga comment qo'shish

        Args:
            task_key: JIRA task key (DEV-1234)
            comment_text: Comment matni (Markdown supported)

        Returns:
            True - success, False - failed
        """
        if not self.jira:
            logger.error("❌ JIRA client not initialized")
            return False

        try:
            # Comment qo'shish
            self.jira.add_comment(task_key, comment_text)

            logger.info(f"✅ Comment added to {task_key}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to add comment to {task_key}: {e}")
            return False

    def add_comment_with_visibility(
            self,
            task_key: str,
            comment_text: str,
            visibility_type: str = "role",
            visibility_value: str = "Developers"
    ) -> bool:
        """
        Comment qo'shish + visibility restriction

        Args:
            task_key: Task key
            comment_text: Comment matni
            visibility_type: "role" yoki "group"
            visibility_value: Role/group nomi (e.g., "Developers", "QA Team")

        Returns:
            True/False
        """
        if not self.jira:
            return False

        try:
            visibility = {
                "type": visibility_type,
                "value": visibility_value
            }

            self.jira.add_comment(
                task_key,
                comment_text,
                visibility=visibility
            )

            logger.info(f"✅ Restricted comment added to {task_key}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to add restricted comment: {e}")
            return False

    def update_comment(
            self,
            comment_id: str,
            new_text: str
    ) -> bool:
        """
        Mavjud commentni yangilash

        Args:
            comment_id: Comment ID
            new_text: Yangi matn
        """
        if not self.jira:
            return False

        try:
            comment = self.jira.comment(comment_id)
            comment.update(body=new_text)

            logger.info(f"✅ Comment {comment_id} updated")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to update comment: {e}")
            return False