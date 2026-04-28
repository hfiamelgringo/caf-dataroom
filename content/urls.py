from django.urls import path
from . import views

app_name = "content"

urlpatterns = [
    path("", views.home, name="home"),
    path("recommendations/", views.recommendations, name="recommendations"),
    path("recommendations/<slug:slug>/", views.recommendation_detail, name="recommendation_detail"),
    path("interviews/", views.interviews_list, name="interviews_list"),
    path("interviews/<slug:slug>/", views.interview_detail, name="interview_detail"),
    path("country/<str:country_code>/", views.country_detail, name="country_detail"),
    path("section/<slug:slug>/", views.section_detail, name="section_detail"),
    path("review/<str:token>/", views.consent_review, name="consent_review"),
    path("review/<str:token>/back/<str:step>/", views.consent_step_back, name="consent_step_back"),
    path("review/<str:token>/reset/", views.consent_reset, name="consent_reset"),
    path("review/<str:token>/consent/", views.consent_step_consent, name="consent_step_consent"),
    path("review/<str:token>/name/edit/", views.consent_step_name_edit, name="consent_step_name_edit"),
    path("review/<str:token>/name/show/", views.consent_step_name_show, name="consent_step_name_show"),
    path("review/<str:token>/name/", views.consent_step_name_save, name="consent_step_name_save"),
    path("review/<str:token>/summary/<int:row_id>/edit/", views.consent_step_summary_edit, name="consent_step_summary_edit"),
    path("review/<str:token>/summary/<int:row_id>/show/", views.consent_step_summary_show, name="consent_step_summary_show"),
    path("review/<str:token>/summary/<int:row_id>/", views.consent_step_summary_save, name="consent_step_summary_save"),
]
