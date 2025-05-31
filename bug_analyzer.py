from datetime import datetime, timezone

class BugAnalyzer:
    def __init__(self):
        pass

    def analyze_bugs(self, bugs_data):
        """Analyze bugs to calculate average age and active duration"""
        created_dates = []
        activated_dates = []
        now = datetime.now(timezone.utc)

        for bug_id, title, description, url, created, activated in bugs_data:
            if created:
                created_dates.append((bug_id, datetime.fromisoformat(created.rstrip("Z")).replace(tzinfo=timezone.utc)))
            if activated:
                activated_dates.append((bug_id, datetime.fromisoformat(activated.rstrip("Z")).replace(tzinfo=timezone.utc)))

        total_bugs = len(bugs_data)
        if created_dates:
            avg_age_days = sum((now - dt).days for _, dt in created_dates) / len(created_dates)
        else:
            avg_age_days = 0
        if activated_dates:
            avg_active_days = sum((now - dt).days for _, dt in activated_dates) / len(activated_dates)
        else:
            avg_active_days = 0

        return avg_age_days, avg_active_days