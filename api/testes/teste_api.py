"""
Testa a API do Waze da Acessibilidade.

1) Em um terminal, suba a API:   cd api  ->  python app.py
2) Em outro terminal, rode:      cd api/testes  ->  python teste_api.py

Para testar outro endereço (ex.: API em outro computador):
   python teste_api.py http://192.168.0.10:5000
"""
import json
import os
import sys

import requests

URL = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:5000"
PASTA = os.path.dirname(os.path.abspath(__file__))
FOTOS = os.path.join(PASTA, "fotos_demo")

# Praça da Sé (centro de São Paulo)
LAT, LON = -23.5503, -46.6340


def mostrar(titulo, resposta):
    print("=" * 70)
    print(f"{titulo}  ->  HTTP {resposta.status_code}")
    print(json.dumps(resposta.json(), indent=2, ensure_ascii=False))


def enviar_foto(nome_arquivo, lat=LAT, lon=LON):
    with open(os.path.join(FOTOS, nome_arquivo), "rb") as f:
        return requests.post(f"{URL}/autenticar",
                             files={"foto": (nome_arquivo, f, "image/jpeg")},
                             data={"latitude": lat, "longitude": lon}, timeout=60)


if __name__ == "__main__":
    # 1. status
    mostrar("GET /status", requests.get(f"{URL}/status", timeout=10))

    # 2. Modelo 1: foto de buraco -> deve ser AUTENTICADA
    r = enviar_foto("buraco.jpg")
    mostrar("POST /autenticar (buraco.jpg)", r)
    assert r.status_code == 200 and r.json()["autenticado"] is True

    # 3. Modelo 1: selfie -> deve ser RECUSADA
    r = enviar_foto("selfie.jpg")
    mostrar("POST /autenticar (selfie.jpg)", r)
    assert r.status_code == 200 and r.json()["autenticado"] is False

    # 4. Modelo 2: ponto dentro de uma zona crítica (Escadaria do Bixiga)
    r = requests.post(f"{URL}/zona-critica", json={"latitude": -23.5585, "longitude": -46.6450}, timeout=10)
    mostrar("POST /zona-critica (Escadaria do Bixiga)", r)
    assert r.status_code == 200 and r.json()["em_zona_critica"] is True

    # 5. Modelo 2: ponto longe dos focos (Parque Ibirapuera)
    r = requests.post(f"{URL}/zona-critica", json={"latitude": -23.5874, "longitude": -46.6576}, timeout=10)
    mostrar("POST /zona-critica (Parque Ibirapuera)", r)
    assert r.status_code == 200 and r.json()["em_zona_critica"] is False

    # 6. Validações: todas devem devolver erro com mensagem clara
    mostrar("Erro: /autenticar sem foto",
            requests.post(f"{URL}/autenticar", data={"latitude": LAT, "longitude": LON}, timeout=10))
    mostrar("Erro: arquivo que não é imagem",
            requests.post(f"{URL}/autenticar", files={"foto": ("relato.jpg", b"isto nao e uma imagem", "image/jpeg")},
                          data={"latitude": LAT, "longitude": LON}, timeout=10))
    mostrar("Erro: formato .pdf",
            requests.post(f"{URL}/autenticar", files={"foto": ("relato.pdf", b"%PDF-1.4", "application/pdf")},
                          data={"latitude": LAT, "longitude": LON}, timeout=10))
    mostrar("Erro: foto sem localização", enviar_foto("buraco.jpg", lat="", lon=""))
    mostrar("Erro: latitude fora do intervalo",
            requests.post(f"{URL}/zona-critica", json={"latitude": 123, "longitude": -46.6}, timeout=10))
    mostrar("Erro: coordenada em texto",
            requests.post(f"{URL}/zona-critica", json={"latitude": "abc", "longitude": -46.6}, timeout=10))

    print("=" * 70)
    print("Todos os testes principais passaram.")
