"""Platform abstraction layer (some may be simulated)"""
from dateutil.tz import tzutc
from pytz import timezone
import datetime
import time


class LinuxPlatform(object):
    """Platform corresponding to to the "real" world"""

    def __init__(self):
        pass

    def time_monotonic(self):
        """Get a monotonic time value as a floating point value in seconds

        This could be a unix timestamp value or could be something completely
        different (like uptime).
        """
        return time.time()

    def time_unix(self):
        """Get the number of seconds since the unix epoch in seconds"""
        return time.time()

    def time_sleep(self, number_seconds):
        """Suspend thread execution for at least `number_seconds`"""
        return time.sleep(number_seconds)

    def time_datetime_now(self):
        """Get the current datetime (datetime.datetime) object"""
        return datetime.datetime.now(tzutc())

    def local_time(self):
        local_timezone = timezone(self.settings.get("SYS_TIMEZONE"))
        start_dt = self.time_datetime_now()
        start_dt = start_dt.astimezone(local_timezone)
        start_dt = local_timezone.normalize(start_dt)
        return start_dt
