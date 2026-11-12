"""
Extrator de embeddings usado pela API.

Faz EXATAMENTE o mesmo processamento do notebook 01_modelo_autenticador.ipynb:
foto -> RGB -> 224x224 -> pixels na escala [-1, 1] -> MobileNetV2 -> vetor de 1280 números.

A MobileNetV2 está salva em formato TensorFlow Lite (modelos/extrator_mobilenetv2.tflite),
exportado pelo notebook 01. Usamos o runtime leve "ai-edge-litert" (oficial do Google)
em vez do TensorFlow completo: a API passa a usar menos de 200 MB de memória
(o TensorFlow completo ocupa mais de 500 MB, mais que o plano gratuito do Render).
"""
import numpy as np
from ai_edge_litert.interpreter import Interpreter
from PIL import Image, ImageOps

TAMANHO = (224, 224)


class ExtratorEmbeddings:
    def __init__(self, caminho_tflite):
        self.interprete = Interpreter(model_path=caminho_tflite)
        self.interprete.allocate_tensors()
        self.entrada = self.interprete.get_input_details()[0]["index"]
        self.saida = self.interprete.get_output_details()[0]["index"]

    def gerar(self, imagem: Image.Image) -> np.ndarray:
        """Recebe uma imagem do Pillow e devolve um array com formato (1, 1280)."""
        # fotos de celular guardam a rotação no EXIF; aplicamos para a foto ficar "em pé"
        imagem = ImageOps.exif_transpose(imagem)
        imagem = imagem.convert("RGB").resize(TAMANHO)
        pixels = np.array(imagem, dtype="float32")[np.newaxis]  # (1, 224, 224, 3)
        # mesma conta do preprocess_input da MobileNetV2: pixels de 0..255 viram -1..1
        pixels = pixels / 127.5 - 1.0
        self.interprete.set_tensor(self.entrada, pixels)
        self.interprete.invoke()
        return self.interprete.get_tensor(self.saida)
