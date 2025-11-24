from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('novo/', views.novo_chamado, name='novo_chamado'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('chamado/<int:id>/', views.chamado_detalhes, name='chamado_detalhes'),
    path('chamado/<int:id>/fechar/', views.fechar_chamado, name='fechar_chamado'),
]
