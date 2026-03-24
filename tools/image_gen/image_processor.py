"""
image_processor.py — Validação e processamento de assets para @cadeiaparamaustratossp
Redimensiona, valida e converte imagens para os formatos aceitos pela Graph API do Instagram.

Formatos suportados:
  - Feed quadrado:  1080x1080px
  - Feed retrato:   1080x1350px
  - Reels/Stories:  1080x1920px

Uso:
    python tools/image_gen/image_processor.py caminho/da/imagem.jpg --formato feed_quadrado
    ou via código:
        from tools.image_gen.image_processor import ImageProcessor
        processor = ImageProcessor()
        resultado = processor.processar("imagem.jpg", "feed_retrato")
"""

import argparse
import logging
import os
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from PIL import Image, ImageOps

load_dotenv()
logger = logging.getLogger(__name__)
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))

TEMP_DIR = "temp"

# ──────────────────────────────────────────────
# Especificações por formato
# ──────────────────────────────────────────────

FORMATOS = {
    "feed_quadrado": {
        "largura": 1080,
        "altura": 1080,
        "descricao": "Feed quadrado (1:1)",
    },
    "feed_retrato": {
        "largura": 1080,
        "altura": 1350,
        "descricao": "Feed retrato (4:5)",
    },
    "reel": {
        "largura": 1080,
        "altura": 1920,
        "descricao": "Reel / Story (9:16)",
    },
}

MAX_TAMANHO_MB = 8
QUALIDADE_JPEG = 90
QUALIDADE_JPEG_FALLBACK = 80  # usado se arquivo ainda > 8MB após primeira compressão


# ──────────────────────────────────────────────
# Dataclass de resultado
# ──────────────────────────────────────────────

@dataclass
class ResultadoProcessamento:
    sucesso: bool
    caminho_saida: str = ""
    formato: str = ""
    largura: int = 0
    altura: int = 0
    tamanho_mb: float = 0.0
    mensagem: str = ""
    avisos: list = None

    def __post_init__(self):
        if self.avisos is None:
            self.avisos = []

    def __str__(self):
        status = "✅ OK" if self.sucesso else "❌ ERRO"
        linhas = [
            f"{status} — {self.mensagem}",
            f"   Arquivo: {self.caminho_saida}",
            f"   Dimensões: {self.largura}x{self.altura}px",
            f"   Tamanho: {self.tamanho_mb:.2f} MB",
        ]
        if self.avisos:
            linhas.append(f"   ⚠️ Avisos: {'; '.join(self.avisos)}")
        return "\n".join(linhas)


# ──────────────────────────────────────────────
# Processador principal
# ──────────────────────────────────────────────

class ImageProcessor:

    def __init__(self, saida_dir: str = TEMP_DIR):
        self.saida_dir = saida_dir
        os.makedirs(saida_dir, exist_ok=True)

    def validar(self, caminho: str) -> list[str]:
        """Valida um arquivo de imagem sem modificá-lo. Retorna lista de problemas."""
        problemas = []
        path = Path(caminho)

        if not path.exists():
            return [f"Arquivo não encontrado: {caminho}"]

        if path.suffix.lower() not in (".jpg", ".jpeg", ".png"):
            problemas.append(f"Formato não suportado: {path.suffix}. Use JPEG ou PNG.")

        tamanho_mb = path.stat().st_size / (1024 * 1024)
        if tamanho_mb > MAX_TAMANHO_MB:
            problemas.append(f"Arquivo muito grande: {tamanho_mb:.1f}MB (máx {MAX_TAMANHO_MB}MB).")

        try:
            with Image.open(caminho) as img:
                w, h = img.size
                formato_detectado = self._detectar_formato(w, h)
                if not formato_detectado:
                    problemas.append(
                        f"Dimensões {w}x{h}px não correspondem a nenhum formato Instagram. "
                        f"Use: {', '.join(f'{v[\"largura\"]}x{v[\"altura\"]}' for v in FORMATOS.values())}"
                    )
        except Exception as e:
            problemas.append(f"Imagem corrompida ou ilegível: {e}")

        return problemas

    def processar(self, caminho_entrada: str, formato: str,
                  nome_saida: str = None) -> ResultadoProcessamento:
        """
        Processa uma imagem: redimensiona, converte para JPEG e valida tamanho.

        Args:
            caminho_entrada: Caminho da imagem original.
            formato: Um de 'feed_quadrado', 'feed_retrato', 'reel'.
            nome_saida: Nome do arquivo de saída (sem extensão). Gerado automaticamente se None.

        Returns:
            ResultadoProcessamento com status e caminho do arquivo processado.
        """
        avisos = []

        if formato not in FORMATOS:
            return ResultadoProcessamento(
                sucesso=False,
                mensagem=f"Formato inválido: '{formato}'. Opções: {list(FORMATOS.keys())}",
            )

        if not Path(caminho_entrada).exists():
            return ResultadoProcessamento(
                sucesso=False,
                mensagem=f"Arquivo não encontrado: {caminho_entrada}",
            )

        spec = FORMATOS[formato]
        largura_alvo, altura_alvo = spec["largura"], spec["altura"]

        try:
            with Image.open(caminho_entrada) as img:
                # Converter para RGB (elimina transparência / modo P)
                if img.mode != "RGB":
                    avisos.append(f"Modo {img.mode} convertido para RGB.")
                    img = img.convert("RGB")

                w_orig, h_orig = img.size

                # Redimensionar se necessário (crop centralizado para manter proporção)
                if (w_orig, h_orig) != (largura_alvo, altura_alvo):
                    avisos.append(
                        f"Redimensionado de {w_orig}x{h_orig}px para {largura_alvo}x{altura_alvo}px."
                    )
                    img = self._redimensionar_com_crop(img, largura_alvo, altura_alvo)

                # Definir caminho de saída
                if not nome_saida:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    nome_saida = f"post_{formato}_{timestamp}"

                caminho_saida = os.path.join(self.saida_dir, f"{nome_saida}.jpg")

                # Salvar com qualidade alta
                img.save(caminho_saida, format="JPEG", quality=QUALIDADE_JPEG, optimize=True)

                # Verificar tamanho final
                tamanho_mb = Path(caminho_saida).stat().st_size / (1024 * 1024)

                if tamanho_mb > MAX_TAMANHO_MB:
                    avisos.append(f"Arquivo ainda > {MAX_TAMANHO_MB}MB ({tamanho_mb:.1f}MB). Recomprimindo...")
                    img.save(caminho_saida, format="JPEG", quality=QUALIDADE_JPEG_FALLBACK, optimize=True)
                    tamanho_mb = Path(caminho_saida).stat().st_size / (1024 * 1024)

                    if tamanho_mb > MAX_TAMANHO_MB:
                        return ResultadoProcessamento(
                            sucesso=False,
                            caminho_saida=caminho_saida,
                            tamanho_mb=tamanho_mb,
                            mensagem=f"Arquivo permanece acima de {MAX_TAMANHO_MB}MB mesmo após compressão. "
                                     f"Reduza a resolução da imagem original.",
                            avisos=avisos,
                        )

                return ResultadoProcessamento(
                    sucesso=True,
                    caminho_saida=caminho_saida,
                    formato=formato,
                    largura=largura_alvo,
                    altura=altura_alvo,
                    tamanho_mb=tamanho_mb,
                    mensagem=f"Imagem processada com sucesso ({spec['descricao']}).",
                    avisos=avisos,
                )

        except Exception as e:
            return ResultadoProcessamento(
                sucesso=False,
                mensagem=f"Erro ao processar imagem: {e}",
                avisos=avisos,
            )

    def processar_lote(self, caminhos: list[str], formato: str) -> list[ResultadoProcessamento]:
        """Processa múltiplas imagens (slides de carrossel, por exemplo)."""
        resultados = []
        for i, caminho in enumerate(caminhos, 1):
            nome = f"slide_{i:02d}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            resultado = self.processar(caminho, formato, nome_saida=nome)
            resultados.append(resultado)
            status = "✅" if resultado.sucesso else "❌"
            logger.info(f"{status} Slide {i}/{len(caminhos)}: {resultado.mensagem}")
        return resultados

    def checklist_instagram_curator(self, caminho: str, formato: str) -> dict:
        """
        Executa o checklist completo do Instagram Curator para um asset.
        Retorna dict com cada item e True/False.
        """
        checklist = {}
        path = Path(caminho)

        checklist["arquivo_existe"] = path.exists()
        if not path.exists():
            return checklist

        spec = FORMATOS.get(formato, {})
        tamanho_mb = path.stat().st_size / (1024 * 1024)
        checklist["tamanho_ok"] = tamanho_mb <= MAX_TAMANHO_MB

        try:
            with Image.open(caminho) as img:
                w, h = img.size
                checklist["dimensoes_corretas"] = (
                    w == spec.get("largura") and h == spec.get("altura")
                ) if spec else False
                checklist["modo_rgb"] = img.mode == "RGB"
                checklist["formato_jpeg_png"] = path.suffix.lower() in (".jpg", ".jpeg", ".png")
        except Exception:
            checklist["imagem_legivel"] = False

        return checklist

    def formatar_checklist(self, checklist: dict) -> str:
        labels = {
            "arquivo_existe": "Arquivo existe",
            "tamanho_ok": f"Tamanho ≤ {MAX_TAMANHO_MB}MB",
            "dimensoes_corretas": "Dimensões corretas para o formato",
            "modo_rgb": "Modo de cor RGB",
            "formato_jpeg_png": "Formato JPEG ou PNG",
            "imagem_legivel": "Imagem legível / não corrompida",
        }
        linhas = ["## Checklist Instagram Curator"]
        for chave, ok in checklist.items():
            emoji = "✅" if ok else "❌"
            linhas.append(f"{emoji} {labels.get(chave, chave)}")
        aprovado = all(checklist.values())
        linhas.append(f"\n**Resultado: {'APROVADO ✅' if aprovado else 'REPROVADO ❌'}**")
        return "\n".join(linhas)

    # ──────────────────────────────────────────────
    # Métodos privados
    # ──────────────────────────────────────────────

    @staticmethod
    def _detectar_formato(largura: int, altura: int) -> str | None:
        for nome, spec in FORMATOS.items():
            if spec["largura"] == largura and spec["altura"] == altura:
                return nome
        return None

    @staticmethod
    def _redimensionar_com_crop(img: Image.Image, largura: int, altura: int) -> Image.Image:
        """
        Redimensiona mantendo proporção e faz crop centralizado para atingir
        exatamente as dimensões alvo — sem distorção.
        """
        img = ImageOps.fit(img, (largura, altura), method=Image.LANCZOS, centering=(0.5, 0.5))
        return img


# ──────────────────────────────────────────────
# Entry point para execução direta
# ──────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Processa imagens para o Instagram @cadeiaparamaustratossp"
    )
    parser.add_argument("imagem", help="Caminho da imagem de entrada")
    parser.add_argument(
        "--formato",
        choices=list(FORMATOS.keys()),
        default="feed_retrato",
        help="Formato de saída (padrão: feed_retrato)",
    )
    parser.add_argument(
        "--validar-apenas",
        action="store_true",
        help="Apenas valida sem processar",
    )
    parser.add_argument(
        "--checklist",
        action="store_true",
        help="Executa checklist do Instagram Curator",
    )
    args = parser.parse_args()

    processor = ImageProcessor()

    if args.validar_apenas:
        problemas = processor.validar(args.imagem)
        if problemas:
            print("❌ Problemas encontrados:")
            for p in problemas:
                print(f"   • {p}")
        else:
            print("✅ Imagem válida.")

    elif args.checklist:
        checklist = processor.checklist_instagram_curator(args.imagem, args.formato)
        print(processor.formatar_checklist(checklist))

    else:
        resultado = processor.processar(args.imagem, args.formato)
        print(resultado)
