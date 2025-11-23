from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.http import JsonResponse
from .models import Chamado, Mensagem, Categoria, Usuario
import io
import base64
from django.db.models import Count, Avg, F, ExpressionWrapper, DurationField
from django.utils import timezone
import pandas as pd
import matplotlib.pyplot as plt
from calendar import monthrange

def login_view(request):
    """Página de login"""
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
    """Finaliza a sessão do usuário"""
    logout(request)
    return redirect('login')


# ==============================
# PÁGINA INICIAL / LISTA DE CHAMADOS
# ==============================

@login_required
def index(request):
    """Mostra os chamados dependendo do tipo de usuário"""
    user = request.user

    if user.tipo == 'administrativo':
        chamados = Chamado.objects.all().order_by('-data_abertura')

    elif user.tipo == 'atendente':
        chamados = Chamado.objects.filter(
            usuario__tipo='cliente'
        ).exclude(status='resolvido').order_by('-data_abertura')

    else:  # cliente
        chamados = Chamado.objects.filter(usuario=user).order_by('-data_abertura')

    return render(request, 'atendimento/index.html', {'chamados': chamados})


# ==============================
# NOVO CHAMADO
# ==============================

@login_required
def novo_chamado(request):
    """Criação de novo chamado por cliente"""
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
    """Exibe detalhes e permite interação com o chamado"""
    chamado = get_object_or_404(Chamado, id=id)
    user = request.user

    # Impede cliente de ver chamado que não é dele
    if user.tipo == 'cliente' and chamado.usuario != user:
        messages.error(request, "Você não tem permissão para ver este chamado.")
        return redirect('index')

    # POST: Envio de mensagens ou encerramento
    if request.method == 'POST':
        # Envio de nova mensagem
        if 'mensagem' in request.POST:
            if chamado.status == 'resolvido':
                messages.warning(request, "Este chamado já foi encerrado. Não é possível enviar novas mensagens.")
            else:
                texto = request.POST.get('mensagem')
                if texto:
                    Mensagem.objects.create(chamado=chamado, autor=user, texto=texto)
                    messages.success(request, "Mensagem enviada com sucesso.")

                    # 🔥 Atualiza status para "andamento" quando atendente responde
                    if user.tipo in ['atendente', 'administrativo'] and chamado.status == 'aberto':
                        chamado.status = 'andamento'
                        chamado.save(update_fields=['status'])
            return redirect('chamado_detalhes', id=id)

        # Encerramento do chamado
        elif 'mensagem_final' in request.POST:
            if user.tipo in ['atendente', 'administrativo']:
                texto = request.POST.get('mensagem_final', '')
                if texto:
                    Mensagem.objects.create(chamado=chamado, autor=user, texto=f"[ENCERRAMENTO] {texto}")
                chamado.status = 'resolvido'
                chamado.save(update_fields=['status'])
                messages.success(request, "Chamado encerrado com sucesso.")
            else:
                messages.error(request, "Você não tem permissão para encerrar chamados.")
            return redirect('chamado_detalhes', id=id)

    # Busca todas as mensagens
    mensagens = chamado.mensagens.order_by('data_envio')

    return render(request, 'atendimento/chamado_detalhes.html', {
        'chamado': chamado,
        'mensagens': mensagens
    })

@login_required
def fechar_chamado(request, id):
    """Encerramento do chamado com observação"""
    chamado = get_object_or_404(Chamado, id=id)
    user = request.user

    if user.tipo not in ['atendente', 'administrativo']:
        messages.error(request, "Você não tem permissão para fechar chamados.")
        return redirect('index')

    if request.method == 'POST':
        texto = request.POST.get('mensagem_final')
        if texto:
            Mensagem.objects.create(chamado=chamado, autor=user, texto=f"[ENCERRAMENTO] {texto}")

        chamado.status = 'resolvido'
        chamado.save(update_fields=['status'])
        messages.success(request, f"O chamado '{chamado.titulo}' foi fechado com sucesso.")
        return redirect('chamado_detalhes', id=id)

    return render(request, 'atendimento/fechar_chamado.html', {'chamado': chamado})

@login_required
def dashboard(request):
    # --- filtros do formulário ---
    status_filtro = request.GET.get('status', 'todos')
    mes_inicio = request.GET.get('mes_inicio')
    mes_fim = request.GET.get('mes_fim')

    chamados = Chamado.objects.all()

    # Filtra por status
    if status_filtro != 'todos':
        chamados = chamados.filter(status=status_filtro)

    # Filtra por datas
    if mes_inicio:
        chamados = chamados.filter(data_abertura__gte=mes_inicio + "-01")
    if mes_fim:
        ano, mes = map(int, mes_fim.split("-"))
        ultimo_dia = monthrange(ano, mes)[1]  # retorna 30 para novembro
        chamados = chamados.filter(data_abertura__lte=f"{ano}-{mes:02d}-{ultimo_dia}")

    df = pd.DataFrame(list(chamados.values(
        "id",
        "data_abertura",
        "data_atualizacao",
        "status",
        "categoria__nome",
    )))

    if df.empty:
        return render(request, "atendimento/dashboard.html", {"msg": "Nenhum chamado encontrado."})

    images = {}

    # Chamados abertos por mês (linha)
    df['mes'] = df['data_abertura'].dt.to_period('M')
    df_abertos_mes = df.groupby('mes').size()
    fig, ax = plt.subplots(figsize=(8,4))
    df_abertos_mes.plot(kind='line', marker='o', color='dodgerblue', ax=ax)
    ax.set_title("Chamados abertos por mês")
    ax.set_xlabel("Mês")
    ax.set_ylabel("Quantidade")
    ax.grid(True, linestyle='--', alpha=0.5)
    images['abertos_mes'] = fig_to_base64(fig)

    # Chamados por categoria (linha)
    df_categoria = df.groupby('categoria__nome').size()
    fig, ax = plt.subplots(figsize=(8,4))
    df_categoria.plot(kind='line', marker='o', color='orange', ax=ax)
    ax.set_title("Chamados por categoria")
    ax.set_xlabel("Categoria")
    ax.set_ylabel("Quantidade")
    ax.grid(True, linestyle='--', alpha=0.5)
    images['por_categoria'] = fig_to_base64(fig)

    # Chamados por status (pizza)
    df_status = df['status'].value_counts()
    fig, ax = plt.subplots(figsize=(6,6))
    df_status.plot(kind='pie', autopct="%1.1f%%", colors=["green", "red", "blue"], ax=ax)
    ax.set_ylabel("")
    ax.set_title("Chamados por status")
    images['abertos_fechados'] = fig_to_base64(fig)

    # Tempo médio de atendimento (linha)
    df['tempo_atendimento'] = (df['data_atualizacao'] - df['data_abertura']).dt.total_seconds() / 3600
    media_horas = df['tempo_atendimento'].mean()
    fig, ax = plt.subplots(figsize=(8,4))
    ax.plot(['Tempo médio'], [media_horas], marker='o', color='purple')
    ax.set_ylabel("Horas")
    ax.set_title("Tempo médio de atendimento")
    ax.grid(True, linestyle='--', alpha=0.5)
    images['tempo_medio'] = fig_to_base64(fig)

    return render(request, "atendimento/dashboard.html", {
        "images": images,
        "status_filtro": status_filtro,
        "mes_inicio": mes_inicio,
        "mes_fim": mes_fim,
    })


def fig_to_base64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.getvalue()).decode('utf-8')