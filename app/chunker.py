def split_text(text: str, chunk_size: int = 1000, overlap: int = 200):
    # Proteção: se o overlap for >= ao tamanho do chunk, o texto nunca avançaria
    if overlap >= chunk_size:
        raise ValueError("overlap precisa ser menor que chunk_size")

    chunks = []
    start = 0

    while start < len(text):

        end = start + chunk_size

        # Se chegou ao final do texto
        if end >= len(text):
            chunk = text[start:]

            if chunk.strip():
                chunks.append(chunk.strip())

            break

        # Procura o último espaço antes do limite
        corte = text.rfind(" ", start, end)

        # Se não encontrou espaço válido
        if corte <= start:
            corte = end

        chunk = text[start:corte]

        if chunk.strip():
            chunks.append(chunk.strip())

        # Volta "overlap" caracteres para criar a sobreposição
        proximo = corte - overlap

        # CORREÇÃO: o início do próximo chunk SEMPRE precisa avançar.
        # Antes, um bloco longo sem espaços fazia o início voltar para trás
        # e o laço while nunca terminava.
        start = proximo if proximo > start else corte

        # Garante que o próximo chunk comece em uma palavra inteira
        espaco = text.find(" ", start, corte)

        if espaco != -1:
            start = espaco + 1

    return chunks

def split_pages(pages: list[dict], chunk_size: int = 1000, overlap: int = 200) -> list[dict]:
    """Divide cada página em chunks, lembrando de qual página cada um veio.

    Recebe o que extract_pages devolve e devolve:

        [{"text": "...", "page": 1, "chunk_index": 0}, ...]

    Os chunks não atravessam páginas: assim cada fonte aponta para UMA página.
    """
    resultado = []

    for pagina in pages:
        for chunk in split_text(pagina["text"], chunk_size, overlap):
            resultado.append(
                {
                    "text": chunk,
                    "page": pagina["page"],
                    "chunk_index": len(resultado),
                }
            )

    return resultado


if __name__ == "__main__":
    from app.reader import extract_text
    from pathlib import Path

    pdfs = list(Path("documents").glob("*.pdf"))

    if not pdfs:
        print("Nenhum PDF encontrado.")
        raise SystemExit(1)

    text = extract_text(str(pdfs[0]))

    chunks = split_text(text)

    print(f"Documento dividido em {len(chunks)} chunks.\n")

    for i, chunk in enumerate(chunks[:3], start=1):
        print(f"--- CHUNK {i} ---")
        print(f"Tamanho: {len(chunk)} caracteres")
        print(f"Início: {chunk[:150]}")
        print(f"Final: {chunk[-150:]}")
        print()