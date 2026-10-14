"""Salva com segurança os arquivos enviados pelo usuário."""
import re
from pathlib import Path

from app import config
from app.reader import PdfError


def nome_seguro(nome: str) -> str:
    """Deixa só o nome do arquivo (sem pastas) e troca caracteres perigosos."""
    base = Path(str(nome).replace("\\", "/")).name
    base = re.sub(r"[^\w.\- ]", "_", base).strip(" .")
    stem = Path(base).stem.strip(" .") or "documento"

    return stem[:80] + ".pdf"


def salvar_upload(nome: str, conteudo: bytes, pasta=None, max_mb=None) -> Path:
    """Valida e grava o PDF enviado. Levanta PdfError com mensagem clara se algo estiver errado."""
    pasta = Path(pasta or config.DOCUMENTS_DIR)
    max_mb = config.MAX_PDF_MB if max_mb is None else max_mb

    if not str(nome).lower().endswith(".pdf"):
        raise PdfError("Só arquivos .pdf são aceitos.")

    if not conteudo:
        raise PdfError("O arquivo está vazio.")

    if len(conteudo) > max_mb * 1024 * 1024:
        raise PdfError(f"O arquivo passa do limite de {max_mb} MB.")

    # Todo PDF começa com "%PDF-" (alguns têm um pouco de lixo antes)
    if b"%PDF-" not in conteudo[:1024]:
        raise PdfError("O arquivo não parece ser um PDF válido.")

    pasta.mkdir(parents=True, exist_ok=True)
    destino = pasta / nome_seguro(nome)

    if destino.resolve().parent != pasta.resolve():
        raise PdfError("Nome de arquivo inválido.")

    destino.write_bytes(conteudo)

    return destino
