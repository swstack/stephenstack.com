from dateutil.tz import tzutc
from pytz import timezone
import datetime
import time


class LinuxPlatform(object):
    def __init__(self):
        pass

    def start(self):
        pass

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
