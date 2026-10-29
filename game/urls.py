from django.urls import path
from . import views

urlpatterns = [
    path('', views.title_view, name='title'),

    path(
        'start/',
        views.start_game,
        name='start_game'
    ),

    path(
        'dashboard/',
        views.dashboard_view,
        name='dashboard'
    ),

    path(
        'result/',
        views.result_view,
        name='result'
    ),

    path(
        'next-day/',
        views.next_day,
        name='next_day'
    ),

    path(
        "ending/",
        views.ending_view,
        name="ending"
    ),

    path(
        "select-staff/",
        views.select_staff_view,
        name="select_staff"
    ),
]