from django.urls import path

from . import views

urlpatterns = [
    path("schedules/", views.ScheduleListCreateView.as_view()),
    path("schedules/<int:pk>/", views.ScheduleDetailView.as_view()),
    path("schedules/<int:pk>/visits/", views.ScheduleVisitListView.as_view()),
    path("schedules/<int:pk>/generate/", views.ScheduleGenerateView.as_view()),
    path("pos/", views.PointOfSaleListView.as_view()),
    path("promoters/", views.PromoterListView.as_view()),
]
