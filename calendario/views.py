from django.http import JsonResponse
from django.utils.dateparse import parse_datetime
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
import json
from django.utils import timezone

from .models import Lembrete

User = get_user_model()


@login_required
def listar_lembretes(request):
    lembretes = Lembrete.objects.filter(usuario=request.user)

    eventos = [{
        "id": l.id,
        "title": l.titulo,
        "start": l.data.isoformat(),
        "descricao": l.descricao,
    } for l in lembretes]

    return JsonResponse(eventos, safe=False)


from django.utils import timezone

@csrf_exempt
@login_required
def criar_lembrete(request):
    if request.method != "POST":
        return JsonResponse({"erro": "Método inválido"}, status=405)

    try:
        data = json.loads(request.body)
    except:
        return JsonResponse({"erro": "JSON inválido"}, status=400)

    titulo = data.get("titulo")
    data_evento = data.get("data")

    if not titulo or not data_evento:
        return JsonResponse({"erro": "Título e data são obrigatórios"}, status=400)

    dt = parse_datetime(data_evento)
    if not dt:
        return JsonResponse({"erro": "Data inválida"}, status=400)

    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt)

    lembrete = Lembrete.objects.create(
        usuario=request.user,
        titulo=titulo,
        descricao=data.get("descricao", ""),
        data=dt
    )

    return JsonResponse({
        "id": lembrete.id,
        "title": lembrete.titulo,
        "start": lembrete.data.isoformat(),
        "descricao": lembrete.descricao,
    })

@csrf_exempt
@login_required
def editar_lembrete(request, id):
    if request.method != "POST":
        return JsonResponse({"erro": "Método inválido"}, status=405)

    data = json.loads(request.body)

    try:
        lembrete = Lembrete.objects.get(id=id, usuario=request.user)
    except Lembrete.DoesNotExist:
        return JsonResponse({"erro": "Lembrete não encontrado"}, status=404)

    dt = parse_datetime(data.get("data"))
    if not dt:
        return JsonResponse({"erro": "Data inválida"}, status=400)

    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt)

    lembrete.titulo = data.get("titulo", lembrete.titulo)
    lembrete.descricao = data.get("descricao", "")
    lembrete.data = dt
    lembrete.save()

    return JsonResponse({
        "id": lembrete.id,
        "title": lembrete.titulo,
        "start": lembrete.data.isoformat(),
        "descricao": lembrete.descricao
    })



@csrf_exempt
@login_required
def excluir_lembrete(request, id):
    if request.method == "DELETE":
        lembrete = Lembrete.objects.get(id=id, usuario=request.user)
        lembrete.delete()
        return JsonResponse({"status": "ok"})


@login_required
def pagina_calendario(request):
    return render(request, "calendario/calendario.html")