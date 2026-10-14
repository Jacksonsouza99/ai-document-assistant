from pathlib import Path
from pypdf import PdfReader


class PdfError(Exception):
    """Erro com mensagem amigável, pronta para mostrar ao usuário."""


def extract_text(pdf_path: str) -> str:
    reader = PdfReader(pdf_path)

    pages = []

    for page in reader.pages:
        text = page.extract_text()

        if text:
            # Remove quebras de linha criadas pela formatação do PDF
            text = text.replace("\n", " ")

            # Remove espaços duplicados
            text = " ".join(text.split())

            pages.append(text)

    return "\n\n".join(pages)


def extract_pages(pdf_path: str) -> list[dict]:
    """Lê o PDF e devolve uma lista com uma entrada por página que tem texto:

        [{"page": 1, "text": "..."}, {"page": 3, "text": "..."}]

    O número da página é o do PDF (começa em 1), mesmo que páginas em branco
    no meio sejam ignoradas. Se o PDF não puder ser lido, levanta PdfError.
    """
    caminho = Path(pdf_path)

    if not caminho.is_file():
        raise PdfError("Arquivo não encontrado.")

    try:
        reader = PdfReader(str(caminho))

        # PDF protegido: tenta abrir com senha vazia (alguns são só "travados")
        if reader.is_encrypted and not reader.decrypt(""):
            raise PdfError("O PDF está protegido por senha.")

        paginas = []

        for numero, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            text = " ".join(text.replace("\n", " ").split())

            if text:
                paginas.append({"page": numero, "text": text})

    except PdfError:
        raise
    except Exception as erro:
        raise PdfError(
            "Não foi possível ler o PDF. O arquivo pode estar corrompido ou não ser um PDF válido."
        ) from erro

    if not paginas:
        raise PdfError(
            "O PDF não tem texto que possa ser extraído. "
            "Ele pode ser um documento escaneado (somente imagens)."
        )

    return paginas


if __name__ == "__main__":
    pdfs = list(Path("documents").glob("*.pdf"))

    if not pdfs:
        print("Nenhum PDF encontrado na pasta documents.")
        raise SystemExit(1)

    pdf = pdfs[0]

    print(f"Lendo: {pdf.name}")
    print("-" * 60)

    paginas = extract_pages(str(pdf))

    print(f"{len(paginas)} página(s) com texto")

    for item in paginas[:3]:
        print(f"\n--- PÁGINA {item['page']} ---")
        print(item["text"][:500])