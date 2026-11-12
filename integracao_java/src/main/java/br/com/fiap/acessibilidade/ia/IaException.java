package br.com.fiap.acessibilidade.ia;

/**
 * Erro ao chamar a API de IA.
 * status = 400 quando a entrada é inválida (foto ou coordenadas); 503 quando a IA está fora do ar.
 */
public class IaException extends RuntimeException {

    private final int status;

    public IaException(int status, String mensagem, Throwable causa) {
        super(mensagem, causa);
        this.status = status;
    }

    public int getStatus() {
        return status;
    }
}
