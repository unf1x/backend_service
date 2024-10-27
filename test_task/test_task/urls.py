from django.contrib import admin
from django.urls import path, include

from nft.views import TokenCreateView, ContractGetTotalSupplyView, ListOfTokensView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('tokens/create/', TokenCreateView.as_view()),
    path('tokens/total_supply/', ContractGetTotalSupplyView.as_view()),
    path('tokens/list/', ListOfTokensView.as_view())
    #as_view пpеобразует КЛАСС представления в вызываемую функцию
]
