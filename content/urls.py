from django.urls import path
from . import views

app_name = "content"

urlpatterns = [
    path("", views.home, name="home"),
    path("recommendations/", views.recommendations, name="recommendations"),
    path("recommendations/<slug:slug>/", views.recommendation_detail, name="recommendation_detail"),
    path("country/<str:country_code>/", views.country_detail, name="country_detail"),
    path("section/<slug:slug>/", views.section_detail, name="section_detail"),
]
