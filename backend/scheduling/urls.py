from django.urls import path

from . import views

urlpatterns = [
    path("schedules/", views.ScheduleListView.as_view()),
]
