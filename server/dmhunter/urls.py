from django.urls import path

from . import views

app_name = 'dmhunter'

urlpatterns = [
    path('', views.index, name='index'),
    path('mpinstall', views.mpinstall, name='mpinstall'),
    path('qquninstall', views.qquninstall, name='qquninstall'),
    path('webclient', views.webclient, name='webclient'),
    path('mpcallback/<int:id>', views.mpcallback, name='mpcallback'),
    path('cqhttpcallback', views.cqhttpcallback, name='cqhttpcallback'),
]
