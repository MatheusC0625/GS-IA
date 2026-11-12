package br.com.fiap.acessibilidade.ia;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;

/** Resposta do POST /zona-critica da API Flask (Modelo 2). */
@JsonIgnoreProperties(ignoreUnknown = true)
public record ZonaCriticaResponse(
        double latitude,
        double longitude,
        @JsonProperty("em_zona_critica") boolean emZonaCritica,
        String nivel,   // "Alta", "Média", "Baixa" ou "Sem zona crítica"
        String mensagem,
        @JsonProperty("zona_mais_proxima") ZonaMaisProxima zonaMaisProxima
) {

    @JsonIgnoreProperties(ignoreUnknown = true)
    public record ZonaMaisProxima(
            int zona,
            String bairro,
            String nivel,
            @JsonProperty("distancia_do_centro_m") int distanciaDoCentroM,
            @JsonProperty("raio_m") int raioM,
            int obstaculos,
            @JsonProperty("tipo_mais_comum") String tipoMaisComum
    ) {
    }
}
