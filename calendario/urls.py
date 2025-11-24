from django.urls import path
from . import views

urlpatterns = [
    path("", views.pagina_calendario, name="pagina_calendario"),
    path("listar/", views.listar_lembretes),
    path("criar/", views.criar_lembrete),
    path("editar/<int:id>/", views.editar_lembrete),
    path("excluir/<int:id>/", views.excluir_lembrete),

]
