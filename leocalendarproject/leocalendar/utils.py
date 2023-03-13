from django.db.models.query import QuerySet
import calendar
from schedule.models.calendars import Calendar
from schedule.models.events import Event
import datetime
import pytz
import json
import redis


class XCalendarManager:
    def __init__(self) -> None:
        self.start_date = datetime.datetime.now().date()
        self.day_delta = datetime.timedelta(days=1)
        self.week_delta = datetime.timedelta(days=7)

    def get_or_create_calendar(self, user):
        scalendar = Calendar.objects.get_or_create_calendar_for_object(user)
        return scalendar

    def get_events_for_calendar(self, scalendar, start_date, end_date):
        return scalendar.events.filter(
            start__gte=start_date, end__lt=end_date
        ).order_by("start")

    def get_events_for_class(self, scalendar, start_date, end_date):
        return Event.objects.filter(
            calendar=scalendar,
            start__gte=start_date,
            end__lt=end_date,
        )

    def get_events_for_day(self, scalendar, start_date=None) -> QuerySet:
        if start_date is None:
            start_date = self.start_date

        end_date = start_date + self.day_delta

        return self.get_events_for_calendar(scalendar, start_date, end_date)

    def get_events_for_week(self, scalendar, start_date=None) -> QuerySet:
        # utilizing scalendar
        # TODO: make the function similar to get_events_for_month
        if start_date is None:
            start_date = self.start_date

        end_date = start_date + self.week_delta

        return self.get_events_for_calendar(scalendar, start_date, end_date)

    def get_events_for_month(self, scalendar, current_date=None) -> QuerySet:
        if current_date is None:
            current_date = self.start_date

        (
            start_date,
            end_date,
        ) = XDatetimeManager.get_first_last_datetime_of_month(current_date)

        return self.get_events_for_calendar(scalendar, start_date, end_date)


class XDatetimeManager:
    @staticmethod
    def get_calendar_for_month(year, month) -> list:
        py_month_cal_with_day = calendar.monthcalendar(year, month)
        # TODO:test it with () generator, to reduce memory
        py_month_cal_with_datetime = [
            [datetime.datetime(year, month, day) if day != 0 else 0 for day in week]
            for week in py_month_cal_with_day
        ]

        return py_month_cal_with_datetime

    @staticmethod
    def get_first_last_datetime_of_month(current_date):
        # utilizing pycalendar
        _, num_days = calendar.monthrange(current_date.year, current_date.month)
        first_day_of_month = datetime.datetime(current_date.year, current_date.month, 1)
        last_day_of_month = datetime.datetime(
            current_date.year, current_date.month, num_days
        )

        return first_day_of_month, last_day_of_month

    @staticmethod
    def get_hours_for_day(date, start_time=0, end_time=24):
        hour_iter = (
            datetime.datetime.combine(date, datetime.time(i, 0))
            for i in range(start_time, end_time)
        )

        return hour_iter

    @staticmethod
    def get_week_dates(date) -> list:
        monday = date - datetime.timedelta(days=date.weekday())
        week_dates = [monday + datetime.timedelta(days=i) for i in range(7)]
        return week_dates

    @staticmethod
    def date_str_to_datetime(date: str, date_format: str = "%Y-%m-%d"):
        return datetime.datetime.strptime(date, date_format)

    @staticmethod
    def datetime_to_date_str(date, date_format: str = "%Y-%m-%d"):
        return date.strftime(date_format)


class TimezoneManager:
    @staticmethod
    def get_timezone_from_request(request):
        timezone_offset = request.COOKIES.get("timezone_offset")
        if timezone_offset:
            offset = datetime.timedelta(minutes=int(timezone_offset))
            # timezone = datetime.timedelta(minutes=int(timezone_offset))
            timezone = datetime.timezone(offset)
        else:
            timezone = pytz.UTC

        return timezone

    @staticmethod
    def convert_to_utc_timezone(date, timezone):
        if isinstance(timezone, str):
            tz = pytz.timezone(timezone)
        elif isinstance(timezone, pytz.tzinfo.BaseTzInfo):
            tz = timezone
        elif isinstance(timezone, datetime.timezone):
            tz = pytz.FixedOffset(int(timezone.utcoffset(date).total_seconds() // 60))
        else:
            raise ValueError("Invalid timezone type")

        local_time = tz.localize(date)
        utc_time = local_time.astimezone(pytz.utc)
        return utc_time


class SCalendarEventManager:
    def get_event_details_from_form(self, request, context_handler):
        timezone = TimezoneManager.get_timezone_from_request(request)
        event_form_dict = {}
        event_form_dict["event_title"] = request.POST.get("event_title")
        event_form_dict["event_description"] = request.POST.get("event_description")

        event_date = request.POST.get("event_date")
        event_start_time = request.POST.get("event_start_time")
        event_end_time = request.POST.get("event_end_time")

        date_obj = datetime.datetime.strptime(event_date, "%Y-%m-%d").date()

        start_date = TimezoneManager.convert_to_utc_timezone(
            datetime.datetime.combine(
                date_obj, datetime.datetime.strptime(event_start_time, "%H:%M").time()
            ),
            timezone,
        )
        event_form_dict["start_date"] = start_date

        end_date = TimezoneManager.convert_to_utc_timezone(
            datetime.datetime.combine(
                date_obj, datetime.datetime.strptime(event_end_time, "%H:%M").time()
            ),
            timezone,
        )
        event_form_dict["end_date"] = end_date

        event_form_dict["event_creator"] = request.user

        return event_form_dict

    def create_scalendar_event(self, request, context_handler):
        try:
            event_form_dict = self.get_event_details_from_form(request, context_handler)
        except Exception as e:
            print(
                f"Error {e} Caused while getting the info from request. unable to create the event!"
            )
        try:
            Event.objects.create(
                title=event_form_dict.get("event_title"),
                description=event_form_dict.get("event_description"),
                start=event_form_dict.get("start_date"),
                end=event_form_dict.get("end_date"),
                calendar=context_handler.scalendar,
                creator=event_form_dict.get("event_creator"),
            )
        except Exception as e:
            print(f"Error Caused while creating the event!")

    def edit_scalendar_event(self, request, context_handler, event_id):
        try:
            event_form_dict = self.get_event_details_from_form(request, context_handler)
        except Exception as e:
            print(
                f"Error {e} Caused while getting the info from request. unable to create the event!"
            )
        try:
            event_obj = Event.objects.filter(id=event_id)
            event_obj.update(
                title=event_form_dict.get("event_title"),
                description=event_form_dict.get("event_description"),
                start=event_form_dict.get("start_date"),
                end=event_form_dict.get("end_date"),
                calendar=context_handler.scalendar,
                creator=event_form_dict.get("event_creator"),
            )
        except Exception as e:
            print(f"Error Caused while creating the event!")


redis_connection = None


def get_session(request):
    request.session.session_key
    if not request.session.exists(request.session.session_key):
        request.session.create()
    if not request.session.session_key:
        request.session.save()
    return request.session


def get_session_key(request):
    return get_session(request).session_key


def redis_get_connection():
    global redis_connection
    if not redis_connection:
        redis_connection = redis.Redis(host="redis", port=6379, db=1, socket_timeout=1)
    return redis_connection


cache = {}


def redis_json_set(key, value, session_key=None):
    rkey = session_key + "_" + str(key) if session_key else key
    cache[rkey] = value
    redis_get_connection().set(rkey, json.dumps(value))


def redis_json_get(key, session_key=None):
    rkey = session_key + "_" + str(key) if session_key else key
    # value = redis_get_connection().get(rkey)
    # return json.loads(value.decode("utf8").replace("'", '"'))
    return cache.get(rkey, {})


def redis_json_set_session(key, value, session_key):
    redis_json_set(key, value, session_key)


def redis_json_get_session(key, session_key):
    return redis_json_get(key, session_key)
