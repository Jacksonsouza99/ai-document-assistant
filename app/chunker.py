def split_text(text: str, chunk_size: int = 1000, overlap: int = 200):
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

        # Volta 200 caracteres para criar o overlap
        start = corte - overlap

        # Garante que o próximo chunk comece em uma palavra inteira
        espaco = text.find(" ", start, corte)

        if espaco != -1:
            start = espaco + 1

    return chunks

if __name__ == "__main__":
    from reader import extract_text
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