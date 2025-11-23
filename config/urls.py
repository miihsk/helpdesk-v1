from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from calendario import views as cal 


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('atendimento.urls')),
    path("calendario/", include("calendario.urls")),  # página + API
    path("calendario/", cal.pagina_calendario, name="pagina_calendario"),
    path("calendario/api/listar/", cal.listar_lembretes, name="listar_lembretes"),
    path("calendario/api/criar/", cal.criar_lembrete, name="criar_lembrete"),
    path("calendario/api/editar/<int:id>/", cal.editar_lembrete, name="editar_lembrete"),
    path("calendario/api/excluir/<int:id>/", cal.excluir_lembrete, name="excluir_lembrete"),
    path('login/', auth_views.LoginView.as_view(template_name='atendimento/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
]
