package br.com.fiap.acessibilidade.ia;

/** Corpo JSON enviado ao POST /zona-critica: {"latitude": ..., "longitude": ...} */
public record CoordenadaRequest(double latitude, double longitude) {
}
