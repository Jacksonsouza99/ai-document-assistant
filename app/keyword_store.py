"""Base de documentos SEM IA: um arquivo SQLite com busca de texto (FTS5).

Não precisa de chave de API, de internet, de ChromaDB nem de modelo de
embeddings. Só biblioteca padrão do Python (sqlite3) + pypdf para ler o PDF.

Cada trecho guarda arquivo, página, número do trecho e o hash do PDF, então os
mesmos cuidados da versão com IA valem aqui: sem duplicados, versão nova do
arquivo troca a antiga, e a gravação é "tudo ou nada".
"""
import sqlite3
from pathlib import Path

from app import config
from app.chunker import split_pages
from app.reader import PdfError, extract_pages
from app.vector_store import hash_arquivo

# "remove_diacritics 2": ignora acentos ("devolucao" acha "devolução")
_SCHEMA = (
    "create virtual table if not exists trechos using fts5("
    "texto, arquivo unindexed, pagina unindexed, chunk unindexed, hash unindexed, "
    "tokenize='unicode61 remove_diacritics 2')"
)


def abrir_banco(caminho=None) -> sqlite3.Connection:
    """Abre (ou cria) o banco local."""
    caminho = Path(caminho or config.SQLITE_PATH)
    caminho.parent.mkdir(parents=True, exist_ok=True)

    banco = sqlite3.connect(caminho, check_same_thread=False, timeout=10)
    banco.execute(_SCHEMA)
    banco.commit()

    return banco


def ingerir_pdf(caminho, banco, max_mb=None) -> dict:
    """Grava um PDF no banco. status: "novo", "atualizado", "ja_existia" ou "duplicado"."""
    caminho = Path(caminho)
    nome = caminho.name
    max_mb = config.MAX_PDF_MB if max_mb is None else max_mb

    if caminho.suffix.lower() != ".pdf":
        raise PdfError("Só arquivos .pdf são aceitos.")

    if not caminho.is_file():
        raise PdfError("Arquivo não encontrado.")

    if caminho.stat().st_size > max_mb * 1024 * 1024:
        raise PdfError(f"O arquivo passa do limite de {max_mb} MB.")

    hash_pdf = hash_arquivo(caminho)
    igual = banco.execute("select arquivo from trechos where hash = ? limit 1", (hash_pdf,)).fetchone()

    if igual:
        if igual[0] == nome:
            total = banco.execute("select count(*) from trechos where hash = ?", (hash_pdf,)).fetchone()[0]
            return {"arquivo": nome, "status": "ja_existia", "chunks": total}

        return {"arquivo": nome, "status": "duplicado", "igual_a": igual[0], "chunks": 0}

    havia_antigo = banco.execute("select count(*) from trechos where arquivo = ?", (nome,)).fetchone()[0] > 0

    chunks = split_pages(extract_pages(caminho), config.CHUNK_SIZE, config.OVERLAP)

    with banco:  # transação: ou grava tudo e remove o antigo, ou não muda nada
        banco.executemany(
            "insert into trechos(texto, arquivo, pagina, chunk, hash) values (?, ?, ?, ?, ?)",
            [(c["text"], nome, c["page"], c["chunk_index"], hash_pdf) for c in chunks],
        )
        banco.execute("delete from trechos where arquivo = ? and hash <> ?", (nome, hash_pdf))

    return {"arquivo": nome, "status": "atualizado" if havia_antigo else "novo", "chunks": len(chunks)}


def ingerir_pasta(pasta=None, banco=None, **opcoes) -> list[dict]:
    """Processa todos os PDFs de uma pasta. Um PDF com problema não impede os outros."""
    pasta = Path(pasta or config.DOCUMENTS_DIR)

    if not pasta.is_dir():
        return []

    if banco is None:
        banco = abrir_banco()

    resultados = []

    for pdf in sorted(p for p in pasta.iterdir() if p.is_file() and p.suffix.lower() == ".pdf"):
        try:
            resultados.append(ingerir_pdf(pdf, banco, **opcoes))
        except PdfError as erro:
            resultados.append({"arquivo": pdf.name, "status": "erro", "mensagem": str(erro)})

    return resultados


def remover_documento(nome: str, banco) -> int:
    """Apaga do banco todos os trechos de um arquivo. Devolve quantos foram apagados."""
    with banco:
        return banco.execute("delete from trechos where arquivo = ?", (nome,)).rowcount


def listar_documentos(banco) -> list[dict]:
    linhas = banco.execute(
        "select arquivo, count(*), count(distinct pagina) from trechos group by arquivo order by arquivo"
    ).fetchall()

    return [{"arquivo": a, "chunks": c, "paginas": p} for a, c, p in linhas]


def buscar_trechos(banco, consulta: str, k: int) -> list[dict]:
    """Trechos que casam com a consulta, do melhor para o pior (ranking BM25 do SQLite)."""
    if not consulta:
        return []

    linhas = banco.execute(
        "select texto, arquivo, pagina, chunk, bm25(trechos) as nota from trechos "
        "where trechos match ? order by nota limit ?",
        (consulta, k),
    ).fetchall()

    return [{"texto": t, "arquivo": a, "pagina": p, "chunk": c, "nota": n} for t, a, p, c, n in linhas]


if __name__ == "__main__":
    banco = abrir_banco()

    print(f"Pasta de documentos: {config.DOCUMENTS_DIR}")

    resultados = ingerir_pasta(banco=banco)

    if not resultados:
        print("Nenhum PDF encontrado.")

    for r in resultados:
        extra = r.get("mensagem") or (f"igual a {r['igual_a']}" if "igual_a" in r else f"{r['chunks']} trechos")
        print(f"- {r['arquivo']}: {r['status']} ({extra})")

    total = sum(d["chunks"] for d in listar_documentos(banco))
    print(f"\nTotal de trechos no banco: {total}")
