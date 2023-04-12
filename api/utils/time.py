from datetime import datetime, timedelta, timezone

class TimeUtils:
    def time_ago(created_at):
        now = datetime.utcnow()
        delta = now - created_at

        if delta < timedelta(minutes=1):
            return "just now"
        elif delta < timedelta(hours=1):
            minutes = delta.seconds // 60
            return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        elif delta < timedelta(days=1):
            hours = delta.seconds // 3600
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        elif delta < timedelta(days=2):
            return "yesterday"
        elif delta < timedelta(days=7):
            days = delta.days
            return f"{days} day{'s' if days > 1 else ''} ago"
        else:
            return created_at.strftime("%d %b %Y")