from pathlib import Path
from pypdf import PdfReader


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


if __name__ == "__main__":
    pdfs = list(Path("documents").glob("*.pdf"))

    if not pdfs:
        print("Nenhum PDF encontrado na pasta documents.")
        raise SystemExit(1)

    pdf = pdfs[0]

    print(f"Lendo: {pdf.name}")
    print("-" * 60)

    text = extract_text(str(pdf))

    print(text[:5000])