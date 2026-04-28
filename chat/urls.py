from django.urls import path
from . import views

app_name = "chat"

urlpatterns = [
    path("", views.chat_api, name="chat_api"),
    path("_devsave/", views.dev_save_transcript, name="dev_save_transcript"),
]
