from django.shortcuts import render, redirect
from .utils import SCalendarEventManager
from .models import LeoEvent
from .context import ContextHandler, CalendarView
import logging
from django.contrib.auth.decorators import login_required
from .utils import get_session_key


logger = logging.getLogger(__name__)


def xcalendar_create_update_event_view(request, view, date=None):
    user = request.user
    context_handler = ContextHandler(user)
    context_handler.set_context_for_calendar(calendar_view=view, date=date)

    if request.method == "POST":
        event_id = request.POST.get("event_id")
        scalendar_manager = SCalendarEventManager()
        if event_id:
            scalendar_manager.edit_scalendar_event(
                request, context_handler, event_id=event_id
            )
        else:
            scalendar_manager.create_scalendar_event(request, context_handler)
        return render(request, "base.html", context_handler.context)

    return render(request, "components/event.html", context_handler.context)


def xcalendar_edit_event_view(request, view, event_id, date=None):
    user = request.user
    context_handler = ContextHandler(user)
    context_handler.set_context_for_calendar(calendar_view=view, date=date)
    context_handler.context["selected_event"] = LeoEvent.objects.get(id=event_id)
    return render(request, "components/event.html", context_handler.context)


def xcalendar_delete_event_view(request, view, event_id, date=None):
    user = request.user
    context_handler = ContextHandler(user)
    context_handler.set_context_for_calendar(calendar_view=view, date=date)

    try:
        LeoEvent.objects.get(id=event_id).delete()
        print(f"Event with id {event_id} has been deleted successfully!")
    except Exception as e:
        print(f"Exception occurred {e}, couldn't delete the event object")

    return render(request, "base.html", context_handler.context)


@login_required(redirect_field_name="account_login")
def calendar_view(
    request,
    calendar_view,
    class_slug=None,
    date=None,
    template_name=None,
    component_name=None,
):
    """
    Generic view to handle all calendar views (day, week, month).
    :param request: HTTP request object.
    :param calendar_view: CalendarView enum representing the view to be rendered (DAY, WEEK, MONTH).
    :param date: Date string in format yyyy-mm-dd.
    :param template_name: Name of the template to be rendered.
    :param component_name: Name of the component template to be rendered.
    :return: HTTP response object.
    """

    user = request.user
    context_handler = ContextHandler(user, session_key=get_session_key(request))
    context_handler.set_context_for_calendar(calendar_view, date)

    logger.info(
        f"Assigning {calendar_view} view with context {context_handler.context}"
    )

    # Check if request is a hx request.
    if request.META.get("HTTP_HX_REQUEST"):
        return render(
            request,
            component_name or f"components/{calendar_view}.html",
            context_handler.context,
        )

    return render(request, template_name or "base.html", context_handler.context)


def day_view(request, class_slug=None, date=None):
    try:
        return calendar_view(request, CalendarView.DAY, class_slug, date)
    except Exception as e:
        logger.exception(f"Error rendering day view. Error: {e}")


def week_view(request, class_slug=None, date=None):
    try:
        return calendar_view(request, CalendarView.WEEK, class_slug, date)
    except Exception as e:
        logger.exception(f"Error rendering week view. Error: {e}")


def month_view(request, class_slug=None, date=None):
    try:
        return calendar_view(request, CalendarView.MONTH, class_slug, date)
    except Exception as e:
        logger.exception(f"Error rendering month view. Error: {e}")
