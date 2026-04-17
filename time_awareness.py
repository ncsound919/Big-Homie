"""
Time Awareness Module for Big Homie
Contextual understanding of dates, times, and temporal references
"""

import re
from datetime import datetime, timedelta
from datetime import time as time_type
from typing import Optional


class TimeAwareness:
    """Provides contextual time understanding and formatting"""

    def __init__(self):
        self.startup_time = datetime.now()

    def get_current_context(self) -> dict:
        """Get current time context"""
        now = datetime.now()
        return {
            "datetime": now.isoformat(),
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S"),
            "day_of_week": now.strftime("%A"),
            "month": now.strftime("%B"),
            "year": now.year,
            "hour": now.hour,
            "time_of_day": self._get_time_of_day(now),
            "is_weekend": now.weekday() >= 5,
            "is_business_hours": self._is_business_hours(now),
            "season": self._get_season(now),
            "timezone": datetime.now().astimezone().tzname() or "UTC",  # Actual local timezone
        }

    def format_context_string(self) -> str:
        """Format time context as a string for LLM"""
        ctx = self.get_current_context()
        return f"""Current Time Context:
- Date: {ctx["day_of_week"]}, {ctx["date"]}
- Time: {ctx["time"]} ({ctx["time_of_day"]})
- Season: {ctx["season"]}
- Business Hours: {"Yes" if ctx["is_business_hours"] else "No"}
- Weekend: {"Yes" if ctx["is_weekend"] else "No"}
"""

    def parse_temporal_reference(self, text: str) -> Optional[datetime]:
        """
        Parse temporal references like 'tomorrow', 'last Friday', etc.

        Args:
            text: Text containing temporal reference

        Returns:
            datetime object or None if not parseable
        """
        text_lower = text.lower().strip()
        now = datetime.now()

        # Relative references
        if text_lower in ["now", "today"]:
            return now
        elif text_lower == "tomorrow":
            return now + timedelta(days=1)
        elif text_lower == "yesterday":
            return now - timedelta(days=1)
        elif text_lower == "this morning":
            return now.replace(hour=9, minute=0, second=0)
        elif text_lower == "this afternoon":
            return now.replace(hour=14, minute=0, second=0)
        elif text_lower == "this evening":
            return now.replace(hour=18, minute=0, second=0)
        elif text_lower == "tonight":
            return now.replace(hour=20, minute=0, second=0)

        # Day of week references
        weekdays = {
            "monday": 0,
            "tuesday": 1,
            "wednesday": 2,
            "thursday": 3,
            "friday": 4,
            "saturday": 5,
            "sunday": 6,
        }

        for day_name, day_num in weekdays.items():
            if day_name in text_lower:
                if "last" in text_lower:
                    return self._get_last_weekday(now, day_num)
                elif "next" in text_lower:
                    return self._get_next_weekday(now, day_num)
                elif "this" in text_lower:
                    return self._get_this_weekday(now, day_num)

        # Relative day references
        match = re.search(r"(\d+)\s+days?\s+ago", text_lower)
        if match:
            days = int(match.group(1))
            return now - timedelta(days=days)

        match = re.search(r"in\s+(\d+)\s+days?", text_lower)
        if match:
            days = int(match.group(1))
            return now + timedelta(days=days)

        return None

    def format_relative_time(self, dt: datetime) -> str:
        """
        Format datetime as relative time (e.g., '2 hours ago')

        Args:
            dt: datetime to format

        Returns:
            Relative time string
        """
        now = datetime.now()
        diff = now - dt

        if diff.total_seconds() < 60:
            return "just now"
        elif diff.total_seconds() < 3600:
            minutes = int(diff.total_seconds() / 60)
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        elif diff.total_seconds() < 86400:
            hours = int(diff.total_seconds() / 3600)
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        elif diff.days == 1:
            return "yesterday"
        elif diff.days < 7:
            return f"{diff.days} days ago"
        elif diff.days < 30:
            weeks = diff.days // 7
            return f"{weeks} week{'s' if weeks != 1 else ''} ago"
        elif diff.days < 365:
            months = diff.days // 30
            return f"{months} month{'s' if months != 1 else ''} ago"
        else:
            years = diff.days // 365
            return f"{years} year{'s' if years != 1 else ''} ago"

    def get_session_duration(self) -> str:
        """Get how long the current session has been running"""
        datetime.now() - self.startup_time
        return self.format_relative_time(self.startup_time)

    def _get_time_of_day(self, dt: datetime) -> str:
        """Get descriptive time of day"""
        hour = dt.hour
        if 5 <= hour < 12:
            return "morning"
        elif 12 <= hour < 17:
            return "afternoon"
        elif 17 <= hour < 21:
            return "evening"
        else:
            return "night"

    def _is_business_hours(self, dt: datetime) -> bool:
        """Check if time is during business hours (9 AM - 5 PM, weekdays)"""
        if dt.weekday() >= 5:  # Weekend
            return False
        return 9 <= dt.hour < 17

    def _get_season(self, dt: datetime) -> str:
        """Get current season (Northern Hemisphere)"""
        month = dt.month
        if month in [12, 1, 2]:
            return "winter"
        elif month in [3, 4, 5]:
            return "spring"
        elif month in [6, 7, 8]:
            return "summer"
        else:
            return "fall"

    def _get_last_weekday(self, from_date: datetime, target_weekday: int) -> datetime:
        """Get the most recent occurrence of a weekday"""
        days_back = (from_date.weekday() - target_weekday) % 7
        if days_back == 0:
            days_back = 7
        return from_date - timedelta(days=days_back)

    def _get_next_weekday(self, from_date: datetime, target_weekday: int) -> datetime:
        """Get the next occurrence of a weekday"""
        days_ahead = (target_weekday - from_date.weekday()) % 7
        if days_ahead == 0:
            days_ahead = 7
        return from_date + timedelta(days=days_ahead)

    def _get_this_weekday(self, from_date: datetime, target_weekday: int) -> datetime:
        """Get 'this' weekday (current week)"""
        days_diff = target_weekday - from_date.weekday()
        return from_date + timedelta(days=days_diff)

    def is_quiet_hours(self, start_time: str = "23:00", end_time: str = "06:00") -> bool:
        """
        Check if current time is within quiet hours

        Args:
            start_time: Start of quiet hours (HH:MM)
            end_time: End of quiet hours (HH:MM)

        Returns:
            True if in quiet hours
        """
        now = datetime.now()
        current_time = now.time()

        start_parts = start_time.split(":")
        start = time_type(int(start_parts[0]), int(start_parts[1]))

        end_parts = end_time.split(":")
        end = time_type(int(end_parts[0]), int(end_parts[1]))

        if start < end:
            # Same day (e.g., 09:00 - 17:00)
            return start <= current_time <= end
        else:
            # Crosses midnight (e.g., 23:00 - 06:00)
            return current_time >= start or current_time <= end


# Global time awareness instance
time_awareness = TimeAwareness()
