from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Categoria, Chamado, Mensagem, Usuario

# ==============================
# PERSONALIZAÇÕES DE ADMIN
# ==============================

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('id', 'nome')
    search_fields = ('nome',)
    ordering = ('nome',)


class MensagemInline(admin.TabularInline):
    model = Mensagem
    extra = 1
    readonly_fields = ('autor', 'data_envio')
    can_delete = False


@admin.register(Chamado)
class ChamadoAdmin(admin.ModelAdmin):
    list_display = ('id', 'titulo', 'usuario', 'categoria', 'prioridade', 'status', 'data_abertura', 'data_atualizacao')
    list_filter = ('status', 'prioridade', 'categoria', 'data_abertura')
    search_fields = ('titulo', 'descricao', 'usuario__username')
    list_per_page = 10
    ordering = ('-data_abertura',)
    inlines = [MensagemInline]

    fieldsets = (
        ('Informações Principais', {
            'fields': ('titulo', 'descricao', 'categoria', 'prioridade', 'status')
        }),
        ('Informações do Usuário', {
            'fields': ('usuario',)
        }),
        ('Datas', {
            'fields': ('data_abertura', 'data_atualizacao'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('data_abertura', 'data_atualizacao')


@admin.register(Mensagem)
class MensagemAdmin(admin.ModelAdmin):
    list_display = ('id', 'chamado', 'autor', 'data_envio')
    search_fields = ('texto', 'autor__username', 'chamado__titulo')
    list_filter = ('data_envio',)
    ordering = ('-data_envio',)
    readonly_fields = ('data_envio',)

@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'tipo', 'is_staff')
    list_filter = ('tipo', 'is_staff', 'is_superuser')
    fieldsets = UserAdmin.fieldsets + (
        ('Informações do Sistema', {'fields': ('tipo',)}),
    )
