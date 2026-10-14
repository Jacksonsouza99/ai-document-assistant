"""Testes da ingestão. Usam um banco falso em memória e vetores de mentira,
então rodam em segundos e não precisam de ChromaDB nem do modelo de IA.
Rodar na raiz do projeto: python -m pytest -v"""
import pytest

from app.reader import PdfError
from app.vector_store import (
    hash_arquivo,
    ingerir_pasta,
    ingerir_pdf,
    listar_documentos,
    remover_documento,
)
from tests.fakes import ColecaoFalsa, EmbedFalso
from tests.helpers import make_pdf


def pdf(tmp_path, nome, paginas):
    caminho = tmp_path / nome
    caminho.write_bytes(make_pdf(paginas))
    return caminho


def test_pdf_novo_grava_trechos_com_arquivo_pagina_e_hash(tmp_path):
    col, emb = ColecaoFalsa(), EmbedFalso()
    arquivo = pdf(tmp_path, "a.pdf", ["Texto da pagina um", "Texto da pagina dois"])
    r = ingerir_pdf(arquivo, col, emb)
    assert r["status"] == "novo" and r["chunks"] == 2
    metas = [d["meta"] for d in col.dados.values()]
    assert {m["pagina"] for m in metas} == {1, 2}
    assert {m["arquivo"] for m in metas} == {"a.pdf"}
    assert {m["hash"] for m in metas} == {hash_arquivo(arquivo)}


def test_mesmo_arquivo_de_novo_nao_e_processado_outra_vez(tmp_path):
    col, emb = ColecaoFalsa(), EmbedFalso()
    arquivo = pdf(tmp_path, "a.pdf", ["Algum texto"])
    ingerir_pdf(arquivo, col, emb)
    r = ingerir_pdf(arquivo, col, emb)
    assert r["status"] == "ja_existia"
    assert emb.chamadas == 1 and col.count() == 1


def test_mesmo_conteudo_com_outro_nome_e_duplicado(tmp_path):
    col, emb = ColecaoFalsa(), EmbedFalso()
    ingerir_pdf(pdf(tmp_path, "a.pdf", ["Conteudo igual"]), col, emb)
    r = ingerir_pdf(pdf(tmp_path, "copia.pdf", ["Conteudo igual"]), col, emb)
    assert r["status"] == "duplicado" and r["igual_a"] == "a.pdf"
    assert col.count() == 1 and emb.chamadas == 1


def test_arquivo_atualizado_troca_os_trechos_antigos(tmp_path):
    col, emb = ColecaoFalsa(), EmbedFalso()
    ingerir_pdf(pdf(tmp_path, "a.pdf", ["Versao antiga um", "Versao antiga dois", "Versao antiga tres"]), col, emb)
    antigos = set(col.dados)
    r = ingerir_pdf(pdf(tmp_path, "a.pdf", ["Versao nova"]), col, emb)
    assert r["status"] == "atualizado" and r["chunks"] == 1
    assert col.count() == 1 and not (antigos & set(col.dados))
    assert list(col.dados.values())[0]["doc"] == "Versao nova"


def test_documentos_diferentes_nao_se_misturam(tmp_path):
    col, emb = ColecaoFalsa(), EmbedFalso()
    ingerir_pdf(pdf(tmp_path, "a.pdf", ["Texto A"]), col, emb)
    ingerir_pdf(pdf(tmp_path, "b.pdf", ["Texto B"]), col, emb)
    por_arquivo = {d["meta"]["arquivo"]: d["doc"] for d in col.dados.values()}
    assert por_arquivo == {"a.pdf": "Texto A", "b.pdf": "Texto B"}


def test_ingerir_pasta_ignora_nao_pdf_e_isola_erros(tmp_path):
    pdf(tmp_path, "bom.pdf", ["Texto valido"])
    (tmp_path / "quebrado.pdf").write_bytes(b"isto nao e um pdf")
    (tmp_path / "notas.txt").write_text("nao deve ser lido")
    col = ColecaoFalsa()
    resultados = {r["arquivo"]: r for r in ingerir_pasta(tmp_path, col, EmbedFalso())}
    assert set(resultados) == {"bom.pdf", "quebrado.pdf"}
    assert resultados["bom.pdf"]["status"] == "novo"
    assert resultados["quebrado.pdf"]["status"] == "erro" and "PDF" in resultados["quebrado.pdf"]["mensagem"]
    assert col.count() == 1


def test_pasta_que_nao_existe_devolve_lista_vazia(tmp_path):
    assert ingerir_pasta(tmp_path / "nao_existe", ColecaoFalsa(), EmbedFalso()) == []


def test_arquivo_grande_demais_e_recusado_sem_gravar_nada(tmp_path):
    col = ColecaoFalsa()
    with pytest.raises(PdfError) as erro:
        ingerir_pdf(pdf(tmp_path, "a.pdf", ["Texto"]), col, EmbedFalso(), max_mb=0)
    assert "limite" in str(erro.value) and col.count() == 0


def test_extensao_errada_e_recusada(tmp_path):
    arquivo = tmp_path / "a.txt"
    arquivo.write_text("oi")
    with pytest.raises(PdfError):
        ingerir_pdf(arquivo, ColecaoFalsa(), EmbedFalso())


def test_pdf_sem_texto_nao_altera_o_banco(tmp_path):
    col = ColecaoFalsa()
    with pytest.raises(PdfError):
        ingerir_pdf(pdf(tmp_path, "a.pdf", ["", ""]), col, EmbedFalso())
    assert col.count() == 0


def test_gravacao_em_lotes_guarda_tudo(tmp_path):
    col, emb = ColecaoFalsa(), EmbedFalso()
    texto = " ".join(f"palavra{i}" for i in range(400))
    r = ingerir_pdf(pdf(tmp_path, "a.pdf", [texto]), col, emb, tamanho_lote=2)
    assert r["chunks"] > 2 and col.upserts == -(-r["chunks"] // 2) and col.count() == r["chunks"]


def test_remover_documento_apaga_so_aquele_arquivo(tmp_path):
    col, emb = ColecaoFalsa(), EmbedFalso()
    ingerir_pdf(pdf(tmp_path, "a.pdf", ["Texto A", "Mais A"]), col, emb)
    ingerir_pdf(pdf(tmp_path, "b.pdf", ["Texto B"]), col, emb)
    assert remover_documento("a.pdf", col) == 2
    assert {d["meta"]["arquivo"] for d in col.dados.values()} == {"b.pdf"}
    assert remover_documento("nao_existe.pdf", col) == 0


def test_listar_documentos_resume_trechos_e_paginas(tmp_path):
    col, emb = ColecaoFalsa(), EmbedFalso()
    ingerir_pdf(pdf(tmp_path, "a.pdf", ["Um", "Dois", "Tres"]), col, emb)
    ingerir_pdf(pdf(tmp_path, "b.pdf", ["Unico"]), col, emb)
    assert listar_documentos(col) == [
        {"arquivo": "a.pdf", "chunks": 3, "paginas": 3},
        {"arquivo": "b.pdf", "chunks": 1, "paginas": 1},
    ]


def test_os_ids_sao_estaveis_ao_reingerir(tmp_path):
    col, emb = ColecaoFalsa(), EmbedFalso()
    arquivo = pdf(tmp_path, "a.pdf", ["Texto estavel", "Outra pagina"])
    ingerir_pdf(arquivo, col, emb)
    ids1 = set(col.dados)
    remover_documento("a.pdf", col)
    ingerir_pdf(arquivo, col, emb)
    assert set(col.dados) == ids1
