package br.com.fiap.acessibilidade.ia;

import java.util.Map;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

/**
 * Transforma os erros da integração com a IA em respostas JSON claras.
 * Se o projeto já tiver um @RestControllerAdvice, copiem só o método para lá.
 */
@RestControllerAdvice
public class IaExceptionHandler {

    @ExceptionHandler(IaException.class)
    public ResponseEntity<Map<String, String>> tratarErroIa(IaException e) {
        // entrada inválida (foto ou coordenadas) -> 400; IA fora do ar -> 503
        return ResponseEntity.status(e.getStatus()).body(Map.of("erro", e.getMessage()));
    }
}
