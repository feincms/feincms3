from django.urls import path


app_name = "translated-articles"
urlpatterns = [path("<int:pk>/", lambda request, pk: None, name="detail")]
