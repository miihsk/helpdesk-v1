from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Chamado, Mensagem, Categoria, Usuario
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm

@login_required
def index(request):
    chamados = Chamado.objects.filter(usuario=request.user)
    return render(request, 'atendimento/index.html', {'chamados': chamados})

@login_required
def chamado_detalhes(request, id):
    chamado = get_object_or_404(Chamado, id=id)
    mensagens = chamado.mensagens.all()
    return render(request, 'atendimento/chamado_detalhes.html', {'chamado': chamado, 'mensagens': mensagens})

@login_required
def novo_chamado(request):
    if request.method == 'POST':
        titulo = request.POST['titulo']
        descricao = request.POST['descricao']
        prioridade = request.POST['prioridade']
        categoria_id = request.POST['categoria']
        categoria = Categoria.objects.get(id=categoria_id)
        Chamado.objects.create(
            titulo=titulo,
            descricao=descricao,
            prioridade=prioridade,
            categoria=categoria,
            usuario=request.user
        )
        return redirect('index')
    categorias = Categoria.objects.all()
    return render(request, 'atendimento/novo_chamado.html', {'categorias': categorias})

@login_required
def dashboard(request):
    total_chamados = Chamado.objects.count()
    abertos = Chamado.objects.filter(status='aberto').count()
    resolvidos = Chamado.objects.filter(status='resolvido').count()
    andamento = Chamado.objects.filter(status='andamento').count()
    contexto = {
        'total': total_chamados,
        'abertos': abertos,
        'resolvidos': resolvidos,
        'andamento': andamento
    }
    return render(request, 'atendimento/dashboard.html', contexto)

# ==============================
# LOGIN E LOGOUT
# ==============================
def login_view(request):
    if request.user.is_authenticated:
        return redirect('index')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('index')
            else:
                messages.error(request, 'Usuário ou senha incorretos.')
        else:
            messages.error(request, 'Usuário ou senha incorretos.')
    else:
        form = AuthenticationForm()
    return render(request, 'atendimento/login.html', {'form': form})


@login_required
def logout_view(request):
    logout(request)
    return redirect('login')

# ==============================
# PÁGINA INICIAL / MEUS CHAMADOS
# ==============================
@login_required
def index(request):
    chamados = Chamado.objects.filter(usuario=request.user).order_by('-data_abertura')
    return render(request, 'atendimento/index.html', {'chamados': chamados})

# ==============================
# NOVO CHAMADO
# ==============================
@login_required
def novo_chamado(request):
    if request.method == 'POST':
        titulo = request.POST['titulo']
        descricao = request.POST['descricao']
        prioridade = request.POST['prioridade']
        categoria_id = request.POST['categoria']
        categoria = Categoria.objects.get(id=categoria_id)

        Chamado.objects.create(
            titulo=titulo,
            descricao=descricao,
            prioridade=prioridade,
            categoria=categoria,
            usuario=request.user
        )
        messages.success(request, 'Chamado criado com sucesso!')
        return redirect('index')

    categorias = Categoria.objects.all()
    return render(request, 'atendimento/novo_chamado.html', {'categorias': categorias})

# ==============================
# DETALHES DO CHAMADO + MENSAGENS
# ==============================
@login_required
def chamado_detalhes(request, id):
    chamado = get_object_or_404(Chamado, id=id)
    mensagens_chamado = chamado.mensagens.order_by('data_envio')

    # Somente o dono do chamado ou um admin pode ver
    if request.user != chamado.usuario and not request.user.is_staff:
        messages.error(request, "Você não tem permissão para visualizar este chamado.")
        return redirect('index')

    # Envio de nova mensagem
    if request.method == 'POST':
        texto = request.POST.get('mensagem')
        if texto:
            Mensagem.objects.create(
                chamado=chamado,
                autor=request.user,
                texto=texto
            )
            chamado.status = 'andamento'
            chamado.save()
            messages.success(request, 'Mensagem enviada!')
            return redirect('chamado_detalhes', id=id)

    return render(request, 'atendimento/chamado_detalhes.html', {
        'chamado': chamado,
        'mensagens': mensagens_chamado
    })

# ==============================
# DASHBOARD
# ==============================
@login_required
def dashboard(request):
    # Se for staff, vê tudo; senão, só seus chamados
    if request.user.is_staff:
        chamados = Chamado.objects.all()
    else:
        chamados = Chamado.objects.filter(usuario=request.user)

    total = chamados.count()
    abertos = chamados.filter(status='aberto').count()
    andamento = chamados.filter(status='andamento').count()
    resolvidos = chamados.filter(status='resolvido').count()

    contexto = {
        'total': total,
        'abertos': abertos,
        'andamento': andamento,
        'resolvidos': resolvidos
    }
    return render(request, 'atendimento/dashboard.html', contexto)

@login_required
def index(request):
    user = request.user

    if user.tipo == 'administrativo':
        chamados = Chamado.objects.all().order_by('-data_abertura')

    elif user.tipo == 'atendente':
        chamados = Chamado.objects.filter(
            usuario__tipo='cliente'
        ).exclude(status='resolvido').order_by('-data_abertura')

    else:
        chamados = Chamado.objects.filter(usuario=user).order_by('-data_abertura')

    return render(request, 'atendimento/index.html', {'chamados': chamados})

@login_required
def chamado_detalhes(request, id):
    chamado = get_object_or_404(Chamado, id=id)
    user = request.user

    if user.tipo == 'cliente' and chamado.usuario != user:
        messages.error(request, "Você não tem permissão para ver este chamado.")
        return redirect('index')

    if user.tipo == 'atendente' and chamado.usuario.tipo != 'cliente':
        messages.error(request, "Você só pode visualizar chamados de clientes.")
        return redirect('index')

    mensagens = chamado.mensagens.order_by('data_envio')

    return render(request, 'atendimento/chamado_detalhes.html', {
        'chamado': chamado,
        'mensagens': mensagens
    })