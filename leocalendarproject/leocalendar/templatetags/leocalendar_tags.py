import datetime
import calendar
from django.template import Library, loader
from django import template
from django.utils.html import format_html

register = Library()

@register.filter
def add_view_to_string(calendar_name):
    return f"{calendar_name}-view"

@register.filter
def get_previous_month_date(date):
    res = date.replace(day=1) - datetime.timedelta(days=1)
    return f"{res.year}-{res.month}-{res.day}"


@register.filter
def get_next_month_date(date):
    next_month = date.replace(day=1) + datetime.timedelta(days=32)
    return f"{next_month.year}-{next_month.month}-{next_month.day}"

@register.filter
def get_date_for_calendar(date, day):
    return f"{date.year}-{date.month}-{day}"

@register.filter
def get_yesterday_date(current_date):
    res = current_date - datetime.timedelta(days=1)
    return f"{res.year}-{res.month}-{res.day}"

@register.filter
def get_tomorrow_date(current_date):
    res = current_date + datetime.timedelta(days=1)
    return f"{res.year}-{res.month}-{res.day}"

@register.filter
def get_previous_week_date(current_date):
    current_date = current_date.date()
    current_monday = current_date - datetime.timedelta(days=current_date.weekday())
    previous_monday = current_monday - datetime.timedelta(days=7)
    return previous_monday

@register.filter
def get_next_week_date(current_date):
    current_date = current_date.date()
    current_monday = current_date - datetime.timedelta(days=current_date.weekday())
    next_monday = current_monday + datetime.timedelta(days=7)
    return next_monday

@register.simple_tag
def get_events_for_month(events, current_date):
    end_date = current_date + datetime.timedelta(days=1)

    # TODO:database query | need to improve the approach
    filtered_events = events.filter(start__gte=current_date, end__lt=end_date)
    return filtered_events

@register.filter
def get_events_for_day(events, current_date):
    end_date = current_date + datetime.timedelta(days=1)
    # TODO:database query | need to improve the approach
    return events.filter(start__gte=current_date, end__lt=end_date)

@register.filter
def get_item(dictionary, key):
    if dictionary:
        return dictionary.get(str(key))
