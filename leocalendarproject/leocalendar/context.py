from .utils import (
    XCalendarManager,
    XDatetimeManager,
    redis_json_get_session,
    redis_json_set_session,
)
import datetime
from collections import defaultdict
from django.contrib.auth import get_user_model


class CalendarView:
    DAY = "day"
    WEEK = "week"
    MONTH = "month"


class ContextHandler:
    def __init__(self, user: get_user_model(), session_key=None) -> None:

        self.session_key = session_key

        self.context = {}

        self.user = user
        self.xcalendar_manager = XCalendarManager()

        self.scalendar = None
        self.initialize()

        self.view_mapping = {
            CalendarView.DAY: self.set_context_for_day_view,
            CalendarView.WEEK: self.set_context_for_week_view,
            CalendarView.MONTH: self.set_context_for_month_view,
        }

    def get_or_create_context_session(self):
        if self.session_key:
            return redis_json_get_session("context", self.session_key)
        else:
            return {}

    def initialize(self):
        try:
            self.scalendar = self.xcalendar_manager.get_or_create_calendar(
                user=self.user
            )
        except Exception as e:
            print(f"Exception occured while creating the Schdular Calendar object")

        self.context["viewname"] = "calendar"

    def set_context_for_day_view(self, date):
        if self.scalendar:
            self.context["events"] = self.xcalendar_manager.get_events_for_day(
                self.scalendar, start_date=date
            )
        else:
            print(f"Scheduler has not been set, Couldn't set the events for the day")

        self.context["calendar_view"] = CalendarView.DAY

    def set_context_for_week_view(self, date):
        self.context["week"] = XDatetimeManager.get_week_dates(date)

        first_date_of_week = date
        try:
            first_date_of_week = self.context["week"][0].date()
        except Exception as e:
            print(
                f"Exception {e} occured while fetching the first date of the week! Setting the date to current_date"
            )

        if self.scalendar:
            events_queryset = self.xcalendar_manager.get_events_for_week(
                self.scalendar,
                start_date=first_date_of_week,
            )

            self.set_context_for_events(events_queryset)

        else:
            print(f"Scheduler has not been set, Couldn't set the events for the week")

        self.context["calendar_view"] = CalendarView.WEEK

    def set_context_for_month_view(self, date):

        if self.scalendar:
            events_queryset = self.xcalendar_manager.get_events_for_month(
                self.scalendar, current_date=date
            )

            self.set_context_for_events(events_queryset)

        else:
            print(f"Scheduler has not been set, Couldn't set the events for the month")

        self.context["calendar_view"] = CalendarView.MONTH

    def set_context_for_events(self, events_queryset):
        events_dict = defaultdict(list)
        for event in events_queryset:
            date_str = XDatetimeManager.datetime_to_date_str(event.start)
            events_dict[date_str].append(event)

        # Add the dictionary to the context
        self.context["events"] = events_dict

    def set_context_for_calendar(self, calendar_view, date):
        if date is None:
            date = str(datetime.datetime.now().date())

        date = XDatetimeManager.date_str_to_datetime(date)
        self.set_common_context(date)

        context_view_method = self.view_mapping.get(calendar_view)
        if context_view_method:
            context_view_method(date)
            print(
                f"The method for the calendar view {calendar_view} is available, and has executed successfully "
            )
        else:
            print(f"No context view method available for {calendar_view}.")

    def set_common_context(self, date):
        """
        It takes a date, and sets the context to the current date, the weeks in the month, the current date,
        and the hours in the day

        :param date: The date to display the calendar for
        """
        try:
            self.context["current_date"] = date
            self.context["weeks"] = XDatetimeManager.get_calendar_for_month(
                date.year, date.month
            )

            self.get_or_set_from_session("todays_date", datetime.datetime.now().date)
            self.get_or_set_from_session(
                "hours", XDatetimeManager.get_hours_for_day(date)
            )

            print(f"Common context for the view has been set {self.context}")
        except Exception as e:
            print(f"Error {e} occurred while setting common context")

    def get_or_set_from_session(self, key, value):
        val = redis_json_get_session(key, self.session_key)
        if val == dict():
            try:
                redis_json_set_session(key, value, self.session_key)
                print("context has been set to cache!")
            except Exception as e:
                print(e)

        self.context[key] = value
