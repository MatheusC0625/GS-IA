package br.com.fiap.acessibilidade.ia;

import java.time.Duration;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.MediaType;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.stereotype.Component;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.client.HttpClientErrorException;
import org.springframework.web.client.ResourceAccessException;
import org.springframework.web.client.RestClient;
import org.springframework.web.multipart.MultipartFile;

/**
 * Cliente HTTP que a API Java usa para chamar a API de IA (Flask).
 *
 * URL configurada no application.properties:
 *   ia.flask.url=${IA_FLASK_URL:http://localhost:5000}
 *
 * No Render, crie a variável de ambiente IA_FLASK_URL com o endereço da API Flask
 * (ex.: https://waze-acessibilidade-ia.onrender.com).
 */
@Component
public class IaFlaskClient {

    private final RestClient restClient;

    public IaFlaskClient(@Value("${ia.flask.url}") String urlBase) {
        // No plano gratuito do Render a API "dorme" e pode levar ~1 minuto para acordar.
        SimpleClientHttpRequestFactory fabrica = new SimpleClientHttpRequestFactory();
        fabrica.setConnectTimeout(Duration.ofSeconds(10));
        fabrica.setReadTimeout(Duration.ofSeconds(90));

        this.restClient = RestClient.builder()
                .baseUrl(urlBase)
                .requestFactory(fabrica)
                .build();
    }

    /** Modelo 1: envia a foto + localização e recebe se o relato foi autenticado. */
    public AutenticacaoIaResponse autenticar(MultipartFile foto, double latitude, double longitude) {
        // corpo multipart/form-data: os mesmos campos que a API Flask espera
        MultiValueMap<String, Object> corpo = new LinkedMultiValueMap<>();
        corpo.add("foto", foto.getResource());              // mantém o nome original do arquivo
        corpo.add("latitude", String.valueOf(latitude));    // String.valueOf usa ponto decimal
        corpo.add("longitude", String.valueOf(longitude));

        try {
            return restClient.post()
                    .uri("/autenticar")
                    .contentType(MediaType.MULTIPART_FORM_DATA)
                    .body(corpo)
                    .retrieve()
                    .body(AutenticacaoIaResponse.class);
        } catch (HttpClientErrorException e) {
            // 400/413/415: a API Flask explica o problema no campo "erro"
            throw new IaException(400, "Relato inválido: " + e.getResponseBodyAsString(), e);
        } catch (ResourceAccessException e) {
            throw new IaException(503, "A API de IA não respondeu. Tente novamente em instantes.", e);
        }
    }

    /** Modelo 2: informa se um ponto está em zona crítica de acessibilidade. */
    public ZonaCriticaResponse consultarZona(double latitude, double longitude) {
        try {
            return restClient.post()
                    .uri("/zona-critica")
                    .contentType(MediaType.APPLICATION_JSON)
                    .body(new CoordenadaRequest(latitude, longitude))
                    .retrieve()
                    .body(ZonaCriticaResponse.class);
        } catch (HttpClientErrorException e) {
            throw new IaException(400, "Coordenadas inválidas: " + e.getResponseBodyAsString(), e);
        } catch (ResourceAccessException e) {
            throw new IaException(503, "A API de IA não respondeu. Tente novamente em instantes.", e);
        }
    }
}
