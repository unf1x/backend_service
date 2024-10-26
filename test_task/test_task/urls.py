from django.contrib import admin
from django.urls import path, include
from rest_framework import routers

from nft.views import TokenCreateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('tokens/create/', TokenCreateView.as_view())
    #as_view пpеобразует КЛАСС представления в вызываемую функцию
]
