# Waze da Acessibilidade · IA para relatos e zonas críticas

**Global Solution 2026/2 · CitizenTech · Artificial Intelligence & Chatbot**

App de rotas a pé para quem precisa de caminhos com menos obstáculos: idosos, pessoas com mobilidade reduzida, cadeirantes e pais com carrinho de bebê.
Esta entrega contém os **dois modelos de IA** do projeto e a **API Flask** que os disponibiliza para a API Java do grupo.

| Modelo | Tipo | O que faz |
|---|---|---|
| 1 · Autenticador de relatos | Classificação (imagens) | Analisa a foto enviada pelo cidadão e autentica o relato (buraco, calçada irregular, escada sem rampa, obstrução) ou recusa a foto |
| 2 · Zonas críticas | Agrupamento | Agrupa os obstáculos por localização e classifica cada zona em criticidade Alta, Média ou Baixa |

## Estrutura

```
GS_IA_CitizenTech/
├── integrantes.txt                  nomes, RM, turma, origem dos dados e uso de IA generativa
├── README.md
├── requirements.txt                 ambiente completo (notebooks + API)
├── Dockerfile / .dockerignore       imagem da API para o Render
├── dados/
│   ├── imagens/<classe>/            744 imagens em 5 classes
│   ├── labels.csv                   arquivo, classe, origem (dados do Modelo 1)
│   ├── embeddings.csv               embeddings MobileNetV2 (gerado pelo notebook 01)
│   └── relatos_obstaculos.csv       base sintética de relatos (dados do Modelo 2)
├── notebooks/
│   ├── 00_gerar_base_relatos.ipynb
│   ├── 01_modelo_autenticador.ipynb
│   └── 02_modelo_zonas_criticas.ipynb
├── modelos/
│   ├── autenticador.joblib          classificador + classes + limiar de confiança
│   ├── extrator_mobilenetv2.tflite  MobileNetV2 pré-treinada em formato leve (usada pela API)
│   └── zonas_criticas.joblib        Pipeline (StandardScaler + KMeans) + perfil das zonas
├── api/
│   ├── app.py                       API Flask
│   ├── extrator.py                  gera o embedding da foto (igual ao notebook 01)
│   ├── requirements.txt             dependências só da API (leves, sem TensorFlow)
│   └── testes/                      teste_api.py, exemplos_curl.txt, fotos de demonstração
└── integracao_java/                 classes Spring Boot para a API Java chamar a IA (ver LEIAME.md)
```

## Como rodar no computador

```bash
pip install -r requirements.txt
```

**Notebooks:** abra a pasta `notebooks/` no Jupyter ou no VS Code e rode na ordem 00 → 01 → 02 (*Kernel > Restart & Run All*).
Na primeira execução, o TensorFlow baixa os pesos da MobileNetV2 (~9 MB); é preciso estar com internet.

**API:**

```bash
cd api
python app.py
```

A API sobe em `http://127.0.0.1:5000`. Em outro terminal:

```bash
cd api/testes
python teste_api.py
```

## Endpoints

| Método | Rota | Entrada | Saída |
|---|---|---|---|
| GET | `/status` | — | se a API e os modelos foram carregados |
| POST | `/autenticar` | multipart/form-data: `foto` (jpg, jpeg, png, webp; até 10 MB), `latitude`, `longitude` | `autenticado`, `tipo_obstaculo`, `confianca`, `mensagem`, probabilidades e a zona do local |
| POST | `/zona-critica` | JSON ou formulário: `latitude`, `longitude` | `em_zona_critica`, `nivel`, dados da zona e `mensagem` |
| GET | `/zonas` | — | lista das zonas críticas (para desenhar no mapa) |

Erros de entrada voltam com HTTP 400/413/415 e um campo `erro` explicando o problema.

## Publicar no Render

A API usa a MobileNetV2 em formato **TensorFlow Lite** (`ai-edge-litert`) em vez do TensorFlow completo. Assim ela ocupa **menos de 220 MB** de memória e cabe no plano gratuito do Render (512 MB). O TensorFlow completo sozinho passa de 500 MB.

1. Suba esta pasta para um repositório no GitHub, com a pasta `modelos/` incluída.
2. No Render: **New → Web Service** → escolha o repositório.
3. **Language:** `Docker` (o Render encontra o `Dockerfile` na raiz). **Instance type:** `Free`.
4. **Health Check Path:** `/status`.
5. Crie o serviço e aguarde o build (alguns minutos). O endereço fica parecido com `https://<nome-do-servico>.onrender.com`.
6. Teste: `python api/testes/teste_api.py https://<nome-do-servico>.onrender.com`
7. No serviço da **API Java**, crie a variável `IA_FLASK_URL` com esse endereço.

No plano gratuito, a API "dorme" após 15 minutos sem uso, e a primeira chamada leva cerca de 1 minuto. Antes da apresentação, abra `/status` no navegador.

## Integração com a API Java

O app conversa só com a **API Java (Spring Boot)**. Ela envia a foto para `POST /autenticar` e, se `autenticado` for `true`, grava o obstáculo no Oracle.
As classes prontas para o projeto Java estão em `integracao_java/` (testadas com Spring Boot 3.5 e 4.1). Detalhes em `integracao_java/LEIAME.md`.
A API Flask também libera CORS, então o front-end pode chamá-la direto, se necessário.
