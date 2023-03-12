from django.conf import settings
from django.urls import path
from .views import (
    day_view,
    xcalendar_create_update_event_view,
    week_view,
    month_view,
    xcalendar_edit_event_view,
    xcalendar_delete_event_view,
)

urlpatterns = [
    # Calendar Views
    path("calendar2/day/<str:date>", day_view, name="day-view"),
    path("calendar2/day/", day_view, name="day-view"),
    path("calendar2/week/<str:date>", week_view, name="week-view"),
    path("calendar2/week/", week_view, name="week-view"),
    path("calendar2/month/<str:date>", month_view, name="month-view"),
    path("calendar2/month/", month_view, name="month-view"),
    # CRUD Event Views
    path(
        "calendar2/create-event/<str:view>/<str:date>",
        xcalendar_create_update_event_view,
        name="create-event",
    ),
    path(
        "calendar2/create-event/<str:view>/",
        xcalendar_create_update_event_view,
        name="create-event",
    ),
    path(
        "calendar2/edit-event/<str:view>/<int:event_id>/<str:date>",
        xcalendar_edit_event_view,
        name="edit-event",
    ),
    path(
        "calendar2/edit-event/<str:view>/<int:event_id>/",
        xcalendar_edit_event_view,
        name="edit-event",
    ),
    path(
        "calendar2/delete-event/<str:view>/<int:event_id>/<str:date>",
        xcalendar_delete_event_view,
        name="delete-event",
    ),
    path(
        "calendar2/delete-event/<str:view>/<int:event_id>/",
        xcalendar_delete_event_view,
        name="delete-event",
    ),
]
