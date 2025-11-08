from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('novo/', views.novo_chamado, name='novo_chamado'),
    path('chamado/<int:id>/', views.chamado_detalhes, name='chamado_detalhes'),
    path('dashboard/', views.dashboard, name='dashboard'),
]
