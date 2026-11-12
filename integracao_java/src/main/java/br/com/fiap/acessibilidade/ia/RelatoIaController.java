package br.com.fiap.acessibilidade.ia;

import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

/**
 * EXEMPLO de como a API Java expõe a IA para o front-end.
 * Adaptem ao padrão do projeto (camada service, DTOs, DAO com JDBC).
 *
 * Fluxo do relato:
 *   front --(foto + lat/lon)--> POST /relatos (Java) --> POST /autenticar (Flask)
 *   se autenticado: o DAO grava o obstáculo no Oracle e o Java responde 201
 *   se recusado:    nada é gravado e o Java responde 422 com a mensagem da IA
 */
@RestController
@RequestMapping("/relatos")
public class RelatoIaController {

    private final IaFlaskClient ia;

    public RelatoIaController(IaFlaskClient ia) {
        this.ia = ia;
    }

    @PostMapping(consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public ResponseEntity<AutenticacaoIaResponse> criarRelato(@RequestParam("foto") MultipartFile foto,
                                                              @RequestParam double latitude,
                                                              @RequestParam double longitude) {
        AutenticacaoIaResponse resposta = ia.autenticar(foto, latitude, longitude);

        if (resposta.autenticado()) {
            // TODO (grupo de Java): gravar com o DAO do projeto, por exemplo:
            // obstaculoDao.inserir(new Obstaculo(resposta.tipoObstaculo(), latitude, longitude, resposta.confianca()));
            return ResponseEntity.status(201).body(resposta);
        }
        return ResponseEntity.status(422).body(resposta); // foto recusada: o front mostra resposta.mensagem()
    }

    @GetMapping("/zona-critica")
    public ResponseEntity<ZonaCriticaResponse> zonaCritica(@RequestParam double latitude,
                                                           @RequestParam double longitude) {
        return ResponseEntity.ok(ia.consultarZona(latitude, longitude));
    }
}
