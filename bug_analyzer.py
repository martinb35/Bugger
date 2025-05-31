from datetime import datetime, timezone

class BugAnalyzer:
    def __init__(self):
        pass

    def calculate_stats(self, created_dates, activated_dates):
        """Calculate average age and active duration from already-parsed dates"""
        now = datetime.now(timezone.utc)
        
        if created_dates:
            avg_age_days = sum((now - dt).days for _, dt in created_dates) / len(created_dates)
        else:
            avg_age_days = 0
            
        if activated_dates:
            avg_active_days = sum((now - dt).days for _, dt in activated_dates) / len(activated_dates)
        else:
            avg_active_days = 0

        return avg_age_days, avg_active_days