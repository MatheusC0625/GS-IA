package br.com.fiap.acessibilidade.ia;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;

/** Resposta do POST /autenticar da API Flask (Modelo 1). */
@JsonIgnoreProperties(ignoreUnknown = true)
public record AutenticacaoIaResponse(
        boolean autenticado,
        @JsonProperty("tipo_obstaculo") String tipoObstaculo,    // null quando o relato é recusado
        @JsonProperty("classe_prevista") String classePrevista,
        double confianca,
        double limiar,
        String mensagem,
        @JsonProperty("zona_critica") ZonaCriticaResponse zonaCritica // só vem quando autenticado
) {
}
