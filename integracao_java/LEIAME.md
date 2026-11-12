# Integração da API Java (Spring Boot) com a API de IA (Flask)

```
App (front) ──► API Java (Spring Boot, Render) ──► API Flask de IA (Render)
                     │                                  ├─ POST /autenticar   (Modelo 1)
                     └─► Oracle (DAO JDBC)              └─ POST /zona-critica (Modelo 2)
```

O app conversa **só com a API Java**. A API Java chama a API Flask quando precisa da IA e, se o relato for autenticado, grava o obstáculo no Oracle com o DAO do projeto.

Testado com **Spring Boot 3.5.16 e 4.1.2** (Java 21), com `spring-boot-starter-web`. Não precisa de nenhuma dependência extra.

## Arquivos (pacote `br.com.fiap.acessibilidade.ia`, troquem pelo pacote do projeto)

| Arquivo | Para que serve |
|---|---|
| `IaFlaskClient.java` | Cliente HTTP (`RestClient`) que chama `/autenticar` e `/zona-critica` |
| `AutenticacaoIaResponse.java` | DTO da resposta do Modelo 1 |
| `ZonaCriticaResponse.java` | DTO da resposta do Modelo 2 |
| `CoordenadaRequest.java` | DTO enviado ao `/zona-critica` |
| `IaException.java` + `IaExceptionHandler.java` | Erros da IA viram JSON: 400 (entrada inválida) ou 503 (IA fora do ar) |
| `RelatoIaController.java` | **Exemplo** de endpoints `POST /relatos` e `GET /relatos/zona-critica`. Adaptem à camada service/DAO do projeto |

## Configuração

`application.properties`:

```properties
ia.flask.url=${IA_FLASK_URL:http://localhost:5000}
spring.servlet.multipart.max-file-size=10MB
spring.servlet.multipart.max-request-size=10MB
```

No **Render**, no serviço da API Java: *Environment* → adicionar `IA_FLASK_URL` = endereço da API Flask (ex.: `https://waze-acessibilidade-ia.onrender.com`, sem barra no final).

## Contrato da API Java (para o front-end)

| Método | Rota | Entrada | Resposta |
|---|---|---|---|
| POST | `/relatos` | multipart: `foto`, `latitude`, `longitude` | **201** relato autenticado (gravar no banco) · **422** foto recusada (mostrar `mensagem`) · **400** entrada inválida · **503** IA fora do ar |
| GET | `/relatos/zona-critica?latitude=..&longitude=..` | — | **200** com `em_zona_critica`, `nivel`, `mensagem` |

## O que gravar no Oracle quando `autenticado = true`

Sugestão de colunas, no padrão da disciplina de banco: `tb_obstaculo (cd_obstaculo, ds_tipo, nr_latitude, nr_longitude, vl_confianca, dt_relato)`.
Use `resposta.tipoObstaculo()`, a latitude/longitude recebidas e `resposta.confianca()`.

## Atenção: plano gratuito do Render

A API Flask "dorme" após 15 minutos sem uso, e a primeira chamada depois disso leva cerca de 1 minuto. O `IaFlaskClient` já espera até 90 segundos.
**Antes da apresentação**, abram `https://<api-flask>/status` no navegador para "acordar" a API.
