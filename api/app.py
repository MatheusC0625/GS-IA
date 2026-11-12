"""
API REST do Waze da Acessibilidade (Global Solution 2026/2 - CitizenTech).

Endpoints:
  GET  /status        -> informa se a API e os modelos foram carregados
  POST /autenticar    -> Modelo 1: recebe a foto + localização e autentica (ou recusa) o relato
  POST /zona-critica  -> Modelo 2: recebe latitude/longitude e devolve a zona e o nível de criticidade
  GET  /zonas         -> lista as zonas críticas (para o app desenhar no mapa)

Os modelos são CARREGADOS dos arquivos .joblib exportados pelos notebooks.
Nenhum treinamento acontece aqui dentro.

Como rodar (dentro da pasta api/):
  python app.py                      (desenvolvimento, na porta 5000)
  gunicorn -b 0.0.0.0:5000 app:app   (produção, como no Render)
"""
import os

import joblib
import numpy as np
from flask import Flask, jsonify, request
from PIL import Image, UnidentifiedImageError

from extrator import ExtratorEmbeddings

PASTA_API = os.path.dirname(os.path.abspath(__file__))
PASTA_MODELOS = os.path.join(PASTA_API, "..", "modelos")
ARQ_AUTENTICADOR = os.path.join(PASTA_MODELOS, "autenticador.joblib")
ARQ_ZONAS = os.path.join(PASTA_MODELOS, "zonas_criticas.joblib")
ARQ_EXTRATOR = os.path.join(PASTA_MODELOS, "extrator_mobilenetv2.tflite")

EXTENSOES_ACEITAS = {"jpg", "jpeg", "png", "webp"}

# nomes "amigáveis" para as mensagens mostradas ao usuário
NOMES = {
    "buraco": "buraco",
    "calcada_irregular": "calçada irregular",
    "escada_sem_rampa": "escada sem rampa",
    "obstrucao_calcada": "obstrução da calçada",
    "nao_obstaculo": "não é obstáculo",
}
TAMANHO_MAXIMO_MB = 10

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = TAMANHO_MAXIMO_MB * 1024 * 1024
app.json.ensure_ascii = False  # mostra acentos normalmente no JSON
app.json.sort_keys = False     # mantém a ordem dos campos como escrevemos


# ----------------------------------------------------------------------------
# Carregamento dos modelos (uma vez, quando a API inicia)
# ----------------------------------------------------------------------------
modelos = {"autenticador": None, "zonas": None, "extrator": None}
erros_carregamento = {}

try:
    modelos["autenticador"] = joblib.load(ARQ_AUTENTICADOR)
except Exception as e:
    erros_carregamento["autenticador"] = str(e)

try:
    modelos["zonas"] = joblib.load(ARQ_ZONAS)
except Exception as e:
    erros_carregamento["zonas"] = str(e)

try:
    modelos["extrator"] = ExtratorEmbeddings(ARQ_EXTRATOR)
except Exception as e:
    erros_carregamento["extrator"] = str(e)


# ----------------------------------------------------------------------------
# Funções auxiliares
# ----------------------------------------------------------------------------
def erro(mensagem, status=400):
    return jsonify({"erro": mensagem}), status


def ler_coordenadas(dados):
    """Lê latitude/longitude de um dicionário e valida. Devolve (lat, lon, mensagem_de_erro)."""
    if dados is None:
        return None, None, "Envie 'latitude' e 'longitude'."
    lat_txt, lon_txt = dados.get("latitude"), dados.get("longitude")
    if lat_txt is None or lon_txt is None or str(lat_txt).strip() == "" or str(lon_txt).strip() == "":
        return None, None, "Os campos 'latitude' e 'longitude' são obrigatórios."
    try:
        lat, lon = float(lat_txt), float(lon_txt)
    except (TypeError, ValueError):
        return None, None, "Latitude e longitude devem ser números (use ponto como separador decimal, ex.: -23.5503)."
    if np.isnan(lat) or np.isnan(lon) or not (-90 <= lat <= 90):
        return None, None, "Latitude fora do intervalo permitido (-90 a 90)."
    if not (-180 <= lon <= 180):
        return None, None, "Longitude fora do intervalo permitido (-180 a 180)."
    return lat, lon, None


def consultar_zona(lat, lon):
    """Usa o Modelo 2 (Pipeline StandardScaler + KMeans) para achar a zona do ponto."""
    pacote = modelos["zonas"]
    zona = int(pacote["pipeline"].predict([[lat, lon]])[0])
    perfil = next(p for p in pacote["perfis"] if p["zona"] == zona)

    # mesma conta de distância usada no notebook 02
    distancia = float(np.sqrt(((lat - perfil["centro_lat"]) * pacote["metros_por_grau_lat"]) ** 2 +
                              ((lon - perfil["centro_lon"]) * pacote["metros_por_grau_lon"]) ** 2))
    em_zona_critica = bool(perfil["critica"]) and distancia <= perfil["raio_m"]

    resposta = {
        "latitude": lat,
        "longitude": lon,
        "em_zona_critica": em_zona_critica,
        "nivel": perfil["nivel"] if em_zona_critica else "Sem zona crítica",
        "zona_mais_proxima": {
            "zona": zona,
            "bairro": perfil["bairro_predominante"],
            "nivel": perfil["nivel"],
            "distancia_do_centro_m": int(round(distancia)),
            "raio_m": perfil["raio_m"],
            "obstaculos": perfil["obstaculos"],
            "tipo_mais_comum": perfil["tipo_mais_comum"],
        },
    }
    if em_zona_critica:
        resposta["mensagem"] = (f"Atenção: este ponto está em uma zona de criticidade {perfil['nivel'].upper()} "
                                f"({perfil['bairro_predominante']}), com {perfil['obstaculos']} obstáculos relatados. "
                                f"Problema mais comum: {NOMES[perfil['tipo_mais_comum']]}.")
    else:
        resposta["mensagem"] = "Este ponto não está em uma zona crítica de acessibilidade."
    return resposta


# ----------------------------------------------------------------------------
# CORS: permite que o front-end (outro endereço) chame a API direto do navegador
# ----------------------------------------------------------------------------
@app.after_request
def liberar_cors(resposta):
    resposta.headers["Access-Control-Allow-Origin"] = "*"
    resposta.headers["Access-Control-Allow-Headers"] = "Content-Type"
    resposta.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return resposta


# ----------------------------------------------------------------------------
# Endpoints
# ----------------------------------------------------------------------------
@app.get("/status")
def status():
    aut, zon = modelos["autenticador"], modelos["zonas"]
    tudo_ok = all(modelos.values())
    return jsonify({
        "api": "online",
        "pronta": tudo_ok,
        "modelos": {
            "autenticador": {
                "carregado": aut is not None,
                "arquivo": "modelos/autenticador.joblib",
                "algoritmo": aut["nome_modelo"] if aut else None,
                "classes": aut["classes"] if aut else None,
                "limiar_confianca": aut["limiar"] if aut else None,
            },
            "extrator_embeddings": {
                "carregado": modelos["extrator"] is not None,
                "arquivo": "modelos/extrator_mobilenetv2.tflite",
                "rede": "MobileNetV2 pré-treinada (ImageNet), formato TensorFlow Lite",
            },
            "zonas_criticas": {
                "carregado": zon is not None,
                "arquivo": "modelos/zonas_criticas.joblib",
                "algoritmo": "K-Means" if zon else None,
                "quantidade_zonas": zon["metricas"]["k"] if zon else None,
                "zonas_criticas": sum(p["critica"] for p in zon["perfis"]) if zon else None,
            },
        },
        "erros": erros_carregamento,
    }), (200 if tudo_ok else 503)


@app.post("/autenticar")
def autenticar():
    if modelos["autenticador"] is None or modelos["extrator"] is None:
        return erro("Modelo de autenticação não carregado. Verifique GET /status.", 503)

    # 1) validação da foto
    if "foto" not in request.files:
        return erro("Envie a imagem no campo 'foto' usando multipart/form-data.")
    arquivo = request.files["foto"]
    if arquivo.filename == "":
        return erro("Nenhum arquivo foi selecionado no campo 'foto'.")
    extensao = arquivo.filename.rsplit(".", 1)[-1].lower() if "." in arquivo.filename else ""
    if extensao not in EXTENSOES_ACEITAS:
        return erro(f"Formato '{extensao or 'sem extensão'}' não aceito. Use: {', '.join(sorted(EXTENSOES_ACEITAS))}.", 415)
    try:
        imagem = Image.open(arquivo.stream)
        imagem.load()  # força a leitura completa: detecta arquivo corrompido
    except (UnidentifiedImageError, OSError):
        return erro("O arquivo enviado não é uma imagem válida ou está corrompido.")

    # 2) validação da localização (vem nos campos do formulário)
    lat, lon, msg = ler_coordenadas(request.form)
    if msg:
        return erro(msg)

    # 3) Modelo 1: embedding + classificador
    pacote = modelos["autenticador"]
    embedding = modelos["extrator"].gerar(imagem)
    probabilidades = pacote["modelo"].predict_proba(embedding)[0]
    indice = int(np.argmax(probabilidades))
    classe = pacote["classes"][indice]
    confianca = float(probabilidades[indice])

    eh_obstaculo = classe != pacote["classe_negativa"]
    autenticado = eh_obstaculo and confianca >= pacote["limiar"]

    if autenticado:
        mensagem = (f"Relato autenticado: {NOMES[classe]} identificado(a) com {confianca:.0%} de confiança. "
                    "O obstáculo foi registrado. Obrigado por deixar a cidade mais acessível!")
    elif not eh_obstaculo:
        mensagem = ("Relato recusado: a foto não parece mostrar um obstáculo de acessibilidade. "
                    "Envie uma foto do buraco, calçada, escada ou obstrução.")
    else:
        mensagem = (f"Relato recusado: a foto parece mostrar {NOMES[classe]}, mas a confiança "
                    f"({confianca:.0%}) ficou abaixo do mínimo de {pacote['limiar']:.0%}. "
                    "Tire outra foto mais de perto e com boa iluminação.")

    resposta = {
        "autenticado": autenticado,
        "tipo_obstaculo": classe if autenticado else None,
        "classe_prevista": classe,
        "confianca": round(confianca, 4),
        "limiar": pacote["limiar"],
        "mensagem": mensagem,
        "localizacao": {"latitude": lat, "longitude": lon},
        "probabilidades": {c: round(float(p), 4) for c, p in zip(pacote["classes"], probabilidades)},
    }
    # integração entre os modelos: se o relato foi aceito, já informamos a zona do local
    if autenticado and modelos["zonas"] is not None:
        resposta["zona_critica"] = consultar_zona(lat, lon)
    return jsonify(resposta), 200


@app.post("/zona-critica")
def zona_critica():
    if modelos["zonas"] is None:
        return erro("Modelo de zonas críticas não carregado. Verifique GET /status.", 503)
    # aceita JSON {"latitude": .., "longitude": ..} ou formulário
    dados = request.get_json(silent=True) if request.is_json else request.form
    lat, lon, msg = ler_coordenadas(dados)
    if msg:
        return erro(msg)
    return jsonify(consultar_zona(lat, lon)), 200


@app.get("/zonas")
def listar_zonas():
    if modelos["zonas"] is None:
        return erro("Modelo de zonas críticas não carregado. Verifique GET /status.", 503)
    campos = ["zona", "bairro_predominante", "nivel", "centro_lat", "centro_lon", "raio_m",
              "obstaculos", "indice_criticidade", "tipo_mais_comum"]
    zonas = [{c: p[c] for c in campos} for p in modelos["zonas"]["perfis"] if p["critica"]]
    return jsonify({"quantidade": len(zonas), "zonas": zonas}), 200


# ----------------------------------------------------------------------------
# Erros gerais devolvidos em JSON (em vez da página HTML padrão do Flask)
# ----------------------------------------------------------------------------
@app.errorhandler(413)
def arquivo_grande(_):
    return erro(f"Arquivo muito grande. O tamanho máximo é {TAMANHO_MAXIMO_MB} MB.", 413)


@app.errorhandler(404)
def nao_encontrado(_):
    return erro("Endpoint não encontrado. Use GET /status, POST /autenticar, POST /zona-critica ou GET /zonas.", 404)


@app.errorhandler(405)
def metodo_errado(_):
    return erro("Método HTTP não permitido para este endpoint.", 405)


if __name__ == "__main__":
    print("Modelos carregados:", {k: v is not None for k, v in modelos.items()})
    if erros_carregamento:
        print("ATENÇÃO, erros ao carregar:", erros_carregamento)
    # o Render informa a porta pela variável de ambiente PORT; no computador usamos 5000
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
