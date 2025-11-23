from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser

class Categoria(models.Model):
    nome = models.CharField(max_length=100)

    def __str__(self):
        return self.nome

class Chamado(models.Model):
    titulo = models.CharField(max_length=200)
    descricao = models.TextField()
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='chamados')
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True, blank=True)
    prioridade = models.CharField(max_length=10, choices=(('baixa', 'Baixa'), ('media', 'Média'), ('alta', 'Alta')))
    status = models.CharField(max_length=20, choices=(('aberto', 'Aberto'), ('andamento', 'Em andamento'), ('resolvido', 'Resolvido')), default='aberto')
    data_abertura = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.titulo} ({self.status})"

class Mensagem(models.Model):
    chamado = models.ForeignKey(Chamado, on_delete=models.CASCADE, related_name='mensagens')
    autor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    texto = models.TextField()
    data_envio = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Mensagem de {self.autor.username} em {self.chamado.titulo}"

class Usuario(AbstractUser):
    TIPOS_USUARIO = (('administrativo', 'Administrativo'), ('atendente', 'Atendente'), ('cliente', 'Cliente'),)
    tipo = models.CharField(max_length=20, choices=TIPOS_USUARIO, default='cliente', verbose_name='Tipo de Usuário')
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True, blank=True)


    def __str__(self):
        return f"{self.username} ({self.get_tipo_display()})"
