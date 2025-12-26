# utils/metadata_helper.py
from typing import Dict, Any, List


class MetadataHelper:
    """
    Excel ustunlaridan optimal metadata extraction

    Metadata ikki turga bo'linadi:
    1. Search Filters - VectorDB search uchun
    2. Display Info - Natijalarni ko'rsatish uchun
    """

    @staticmethod
    def extract_search_metadata(issue_data: Dict[str, Any]) -> Dict[str, str]:
        """
        VectorDB search filtrlari uchun metadata

        Faqat ChromaDB supported types: string, int, float, bool
        """
        metadata = {}

        # Type - BUG/TASK/STORY
        if issue_data.get('type'):
            metadata['type'] = str(issue_data['type'])

        # Status - CLOSED/DONE/TESTING
        if issue_data.get('status'):
            metadata['status'] = str(issue_data['status'])

        # Sprint ID
        if issue_data.get('sprint_id'):
            metadata['sprint_id'] = str(issue_data['sprint_id'])

        # Assignee
        if issue_data.get('assignee'):
            assignee = str(issue_data['assignee'])
            metadata['assignee'] = assignee if assignee != 'Unassigned' else 'none'

        # Reporter
        if issue_data.get('reporter'):
            reporter = str(issue_data['reporter'])
            metadata['reporter'] = reporter if reporter != 'Unknown' else 'none'

        # Priority
        if issue_data.get('priority'):
            priority = str(issue_data['priority'])
            metadata['priority'] = priority if priority != 'None' else 'none'

        # Story Points
        if issue_data.get('story_points'):
            try:
                sp = float(issue_data['story_points'])
                metadata['story_points'] = str(sp)
            except:
                metadata['story_points'] = 'none'

        # Created Date (YYYY-MM-DD format)
        if issue_data.get('created_date'):
            created = str(issue_data['created_date'])
            if created and created != 'None':
                # Extract only date part
                date_part = created[:10] if len(created) >= 10 else created
                metadata['created_date'] = date_part
            else:
                metadata['created_date'] = 'unknown'

        # Resolved Date (YYYY-MM-DD format)
        if issue_data.get('resolved_date'):
            resolved = str(issue_data['resolved_date'])
            if resolved and resolved != 'None':
                date_part = resolved[:10] if len(resolved) >= 10 else resolved
                metadata['resolved_date'] = date_part
            else:
                metadata['resolved_date'] = 'unknown'

        # Has Comments (yes/no)
        metadata['has_comments'] = 'yes' if issue_data.get('comments') else 'no'

        # Return Count
        if issue_data.get('return_count'):
            try:
                rc = int(issue_data['return_count'])
                metadata['return_count'] = str(rc)
            except:
                metadata['return_count'] = '0'
        else:
            metadata['return_count'] = '0'

        # Labels
        if issue_data.get('labels'):
            labels = str(issue_data['labels']).strip()
            metadata['labels'] = labels if labels else 'none'
        else:
            metadata['labels'] = 'none'

        # Components
        if issue_data.get('components'):
            components = str(issue_data['components']).strip()
            metadata['components'] = components if components else 'none'
        else:
            metadata['components'] = 'none'

        # PR Status
        if issue_data.get('pr_status'):
            pr_status = str(issue_data['pr_status']).strip()
            metadata['has_pr'] = 'yes' if pr_status else 'no'
            metadata['pr_status'] = pr_status if pr_status else 'none'
        else:
            metadata['has_pr'] = 'no'
            metadata['pr_status'] = 'none'

        # PR Count
        if issue_data.get('pr_count'):
            try:
                pr_count = int(issue_data['pr_count'])
                metadata['pr_count'] = str(pr_count)
            except:
                metadata['pr_count'] = '0'
        else:
            metadata['pr_count'] = '0'

        # Testing Time
        if issue_data.get('testing_time'):
            testing_time = str(issue_data['testing_time']).strip()
            metadata['testing_time'] = testing_time if testing_time else 'none'
        else:
            metadata['testing_time'] = 'none'

        # Linked Issues Count
        if issue_data.get('linked_issues'):
            linked = str(issue_data['linked_issues'])
            if linked and linked != 'None':
                # Count comma-separated issues
                link_count = len(linked.split(','))
                metadata['linked_count'] = str(link_count)
            else:
                metadata['linked_count'] = '0'
        else:
            metadata['linked_count'] = '0'

        return metadata

    @staticmethod
    def extract_display_info(issue_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Natijalarni ko'rsatish uchun display info

        Bu metadata VectorDB ga saqlanmaydi, faqat UI uchun
        """
        display = {}

        display['key'] = issue_data.get('key', 'Unknown')
        display['summary'] = issue_data.get('summary', '')[:200]  # Preview only
        display['type'] = issue_data.get('type', 'Unknown')
        display['status'] = issue_data.get('status', 'Unknown')
        display['assignee'] = issue_data.get('assignee', 'Unassigned')
        display['reporter'] = issue_data.get('reporter', 'Unknown')
        display['priority'] = issue_data.get('priority', 'None')
        display['sprint_id'] = issue_data.get('sprint_id', 'Unknown')
        display['story_points'] = str(issue_data.get('story_points', ''))
        display['return_count'] = str(issue_data.get('return_count', '0'))

        # Dates
        created = issue_data.get('created_date', '')
        display['created_date'] = created[:10] if created and len(str(created)) >= 10 else 'Unknown'

        resolved = issue_data.get('resolved_date', '')
        display['resolved_date'] = resolved[:10] if resolved and len(str(resolved)) >= 10 else 'Not resolved'

        return display

    @staticmethod
    def create_search_filters(
            types: List[str] = None,
            statuses: List[str] = None,
            sprints: List[str] = None,
            assignees: List[str] = None,
            min_return_count: int = None,
            has_pr: bool = None,
            priority: List[str] = None
    ) -> Dict[str, Any]:
        """
        ChromaDB search filters yaratish

        Example:
            filters = create_search_filters(
                types=['Bug'],
                statuses=['Closed', 'Done'],
                min_return_count=1
            )

        Returns:
            ChromaDB where clause
        """
        conditions = []

        # Type filter
        if types:
            if len(types) == 1:
                conditions.append({"type": types[0]})
            else:
                conditions.append({"type": {"$in": types}})

        # Status filter
        if statuses:
            if len(statuses) == 1:
                conditions.append({"status": statuses[0]})
            else:
                conditions.append({"status": {"$in": statuses}})

        # Sprint filter
        if sprints:
            if len(sprints) == 1:
                conditions.append({"sprint_id": sprints[0]})
            else:
                conditions.append({"sprint_id": {"$in": sprints}})

        # Assignee filter
        if assignees:
            if len(assignees) == 1:
                conditions.append({"assignee": assignees[0]})
            else:
                conditions.append({"assignee": {"$in": assignees}})

        # Return count filter
        if min_return_count is not None:
            conditions.append({"return_count": {"$gte": str(min_return_count)}})

        # PR filter
        if has_pr is not None:
            pr_value = 'yes' if has_pr else 'no'
            conditions.append({"has_pr": pr_value})

        # Priority filter
        if priority:
            if len(priority) == 1:
                conditions.append({"priority": priority[0]})
            else:
                conditions.append({"priority": {"$in": priority}})

        # Combine conditions
        if not conditions:
            return None

        if len(conditions) == 1:
            return conditions[0]

        return {"$and": conditions}

    @staticmethod
    def analyze_metadata_distribution(all_metadata: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Metadata distribution tahlili

        Qaysi ustunlar eng ko'p to'ldirilgan, qaysilari bo'sh
        """
        if not all_metadata:
            return {}

        total = len(all_metadata)
        field_counts = {}

        # Har bir field uchun to'liq ma'lumotlar sonini hisoblash
        for metadata in all_metadata:
            for field, value in metadata.items():
                if value and value not in ['none', 'unknown', '0', 'Not resolved']:
                    field_counts[field] = field_counts.get(field, 0) + 1

        # Percentage hisoblash
        distribution = {}
        for field, count in field_counts.items():
            percentage = (count / total) * 100
            distribution[field] = {
                'count': count,
                'total': total,
                'percentage': percentage,
                'completeness': 'high' if percentage > 80 else 'medium' if percentage > 50 else 'low'
            }

        return distribution

    @staticmethod
    def get_recommended_filters() -> Dict[str, List[str]]:
        """
        Qidiruv uchun tavsiya etilgan filterlar

        Eng foydali filter kombinatsiyalari
        """
        return {
            'bug_search': {
                'description': 'Bug root cause analysis',
                'filters': {
                    'types': ['Bug'],
                    'statuses': ['Closed', 'Done', 'Resolved']
                }
            },
            'recent_bugs': {
                'description': 'Recent bugs (with return history)',
                'filters': {
                    'types': ['Bug'],
                    'min_return_count': 1
                }
            },
            'critical_issues': {
                'description': 'High priority closed issues',
                'filters': {
                    'priority': ['Critical', 'High'],
                    'statuses': ['Closed', 'Done']
                }
            },
            'with_pr': {
                'description': 'Issues with pull requests',
                'filters': {
                    'has_pr': True,
                    'statuses': ['Closed', 'Done']
                }
            }
        }