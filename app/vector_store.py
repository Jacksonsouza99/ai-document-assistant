"""Ingestão de PDFs no ChromaDB.

Cada trecho guardado leva junto: arquivo, página, número do trecho e o hash
(impressão digital) do PDF. Com o hash dá para:
  - não processar de novo um PDF que já está no banco;
  - perceber que um arquivo com outro nome é igual a um já existente;
  - trocar os trechos antigos quando o mesmo arquivo for atualizado.

As partes pesadas (ChromaDB e modelo de embeddings) só são carregadas quando
precisam, e podem ser substituídas nos testes.
"""
import hashlib
from pathlib import Path

from app import config
from app.chunker import split_pages
from app.reader import PdfError, extract_pages

_modelo = None


def abrir_colecao():
    """Abre (ou cria) a coleção no banco vetorial local."""
    import chromadb

    client = chromadb.PersistentClient(path=str(config.CHROMA_DIR))
    return client.get_or_create_collection(name=config.COLLECTION_NAME)


def gerar_embeddings(textos: list[str]) -> list[list[float]]:
    """Transforma textos em vetores. O modelo é carregado uma única vez."""
    global _modelo

    if _modelo is None:
        from sentence_transformers import SentenceTransformer

        _modelo = SentenceTransformer(config.EMBEDDING_MODEL)

    return _modelo.encode(textos).tolist()


def hash_arquivo(caminho) -> str:
    """Impressão digital (SHA-256) do conteúdo do arquivo."""
    sha = hashlib.sha256()

    with open(caminho, "rb") as arquivo:
        for bloco in iter(lambda: arquivo.read(1024 * 1024), b""):
            sha.update(bloco)

    return sha.hexdigest()


def _buscar(colecao, **filtro):
    """Devolve (ids, metadados) dos registros que combinam com o filtro."""
    resultado = colecao.get(where=filtro, include=["metadatas"])
    return resultado["ids"], [m or {} for m in resultado["metadatas"]]


def ingerir_pdf(caminho, colecao, embed=None, max_mb=None, tamanho_lote=500) -> dict:
    """Grava um PDF no banco e diz o que aconteceu.

    status: "novo", "atualizado", "ja_existia" ou "duplicado".
    Levanta PdfError se o arquivo não puder ser usado.
    """
    caminho = Path(caminho)
    nome = caminho.name
    max_mb = config.MAX_PDF_MB if max_mb is None else max_mb

    # --- validações antes de gastar tempo com o arquivo ---
    if caminho.suffix.lower() != ".pdf":
        raise PdfError("Só arquivos .pdf são aceitos.")

    if not caminho.is_file():
        raise PdfError("Arquivo não encontrado.")

    if caminho.stat().st_size > max_mb * 1024 * 1024:
        raise PdfError(f"O arquivo passa do limite de {max_mb} MB.")

    # --- duplicados: o mesmo conteúdo já está no banco? ---
    hash_pdf = hash_arquivo(caminho)
    ids_iguais, metas_iguais = _buscar(colecao, hash=hash_pdf)

    if ids_iguais:
        existente = metas_iguais[0].get("arquivo", "?")

        if existente == nome:
            return {"arquivo": nome, "status": "ja_existia", "chunks": len(ids_iguais)}

        return {"arquivo": nome, "status": "duplicado", "igual_a": existente, "chunks": 0}

    # --- versão antiga do mesmo nome (conteúdo diferente)? ---
    ids_antigos, _ = _buscar(colecao, arquivo=nome)

    # --- extrair, dividir e gerar vetores (se algo falhar, o banco não muda) ---
    paginas = extract_pages(caminho)
    chunks = split_pages(paginas, config.CHUNK_SIZE, config.OVERLAP)
    vetores = (embed or gerar_embeddings)([c["text"] for c in chunks])

    ids = [f"{hash_pdf[:16]}_{c['chunk_index']}" for c in chunks]
    metadados = [
        {"arquivo": nome, "pagina": c["page"], "chunk": c["chunk_index"], "hash": hash_pdf}
        for c in chunks
    ]

    # --- gravar em lotes ---
    for i in range(0, len(ids), tamanho_lote):
        fim = i + tamanho_lote
        colecao.upsert(
            ids=ids[i:fim],
            documents=[c["text"] for c in chunks[i:fim]],
            embeddings=vetores[i:fim],
            metadatas=metadados[i:fim],
        )

    # Só depois de gravar o novo é que removemos o antigo
    if ids_antigos:
        colecao.delete(ids=ids_antigos)

    status = "atualizado" if ids_antigos else "novo"
    return {"arquivo": nome, "status": status, "chunks": len(ids)}


def ingerir_pasta(pasta=None, colecao=None, embed=None, **opcoes) -> list[dict]:
    """Processa todos os PDFs de uma pasta. Um PDF com problema não impede os outros."""
    pasta = Path(pasta or config.DOCUMENTS_DIR)

    if not pasta.is_dir():
        return []

    if colecao is None:
        colecao = abrir_colecao()

    resultados = []

    for pdf in sorted(p for p in pasta.iterdir() if p.is_file() and p.suffix.lower() == ".pdf"):
        try:
            resultados.append(ingerir_pdf(pdf, colecao, embed, **opcoes))
        except PdfError as erro:
            resultados.append({"arquivo": pdf.name, "status": "erro", "mensagem": str(erro)})

    return resultados


def remover_documento(nome: str, colecao) -> int:
    """Apaga do banco todos os trechos de um arquivo. Devolve quantos foram apagados."""
    ids, _ = _buscar(colecao, arquivo=nome)

    if ids:
        colecao.delete(ids=ids)

    return len(ids)


def listar_documentos(colecao) -> list[dict]:
    """Resumo dos documentos guardados: nome, quantidade de trechos e de páginas."""
    resultado = colecao.get(include=["metadatas"])
    resumo = {}

    for meta in resultado["metadatas"]:
        meta = meta or {}
        item = resumo.setdefault(meta.get("arquivo", "?"), {"chunks": 0, "paginas": set()})
        item["chunks"] += 1
        item["paginas"].add(meta.get("pagina"))

    return [
        {"arquivo": nome, "chunks": dados["chunks"], "paginas": len(dados["paginas"])}
        for nome, dados in sorted(resumo.items())
    ]


if __name__ == "__main__":
    colecao = abrir_colecao()

    print(f"Pasta de documentos: {config.DOCUMENTS_DIR}")

    resultados = ingerir_pasta(colecao=colecao)

    if not resultados:
        print("Nenhum PDF encontrado.")

    for r in resultados:
        extra = r.get("mensagem") or (f"igual a {r['igual_a']}" if "igual_a" in r else f"{r['chunks']} trechos")
        print(f"- {r['arquivo']}: {r['status']} ({extra})")

    print(f"\nTotal de registros na coleção '{config.COLLECTION_NAME}': {colecao.count()}")
