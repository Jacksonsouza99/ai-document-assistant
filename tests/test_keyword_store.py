"""Testes do banco SQLite do modo sem IA (usa SQLite de verdade, em pasta temporária).
Rodar na raiz do projeto: python -m pytest -v"""
import pytest

from app.keyword_store import (
    abrir_banco, buscar_trechos, ingerir_pasta, ingerir_pdf, listar_documentos, remover_documento,
)
from app.reader import PdfError
from tests.helpers import make_pdf


def banco(tmp_path):
    return abrir_banco(tmp_path / "k.db")


def pdf(tmp_path, nome, paginas):
    caminho = tmp_path / nome
    caminho.write_bytes(make_pdf(paginas))
    return caminho


def total(b):
    return b.execute("select count(*) from trechos").fetchone()[0]


def test_pdf_novo_grava_trechos_com_arquivo_e_pagina(tmp_path):
    b = banco(tmp_path)
    r = ingerir_pdf(pdf(tmp_path, "a.pdf", ["Texto da pagina um", "Texto da pagina dois"]), b)
    assert r["status"] == "novo" and r["chunks"] == 2
    assert listar_documentos(b) == [{"arquivo": "a.pdf", "chunks": 2, "paginas": 2}]


def test_mesmo_arquivo_de_novo_nao_duplica(tmp_path):
    b = banco(tmp_path)
    arquivo = pdf(tmp_path, "a.pdf", ["Algum texto"])
    ingerir_pdf(arquivo, b)
    r = ingerir_pdf(arquivo, b)
    assert r["status"] == "ja_existia" and r["chunks"] == 1 and total(b) == 1


def test_mesmo_conteudo_com_outro_nome_e_duplicado(tmp_path):
    b = banco(tmp_path)
    ingerir_pdf(pdf(tmp_path, "a.pdf", ["Conteudo igual"]), b)
    r = ingerir_pdf(pdf(tmp_path, "copia.pdf", ["Conteudo igual"]), b)
    assert r["status"] == "duplicado" and r["igual_a"] == "a.pdf" and total(b) == 1


def test_arquivo_atualizado_troca_os_trechos_antigos(tmp_path):
    b = banco(tmp_path)
    ingerir_pdf(pdf(tmp_path, "a.pdf", ["Versao antiga um", "Versao antiga dois", "Versao antiga tres"]), b)
    r = ingerir_pdf(pdf(tmp_path, "a.pdf", ["Versao nova"]), b)
    assert r["status"] == "atualizado" and total(b) == 1
    assert b.execute("select texto from trechos").fetchone()[0] == "Versao nova"


def test_pdf_sem_texto_nao_estraga_a_versao_que_ja_estava_no_banco(tmp_path):
    b = banco(tmp_path)
    ingerir_pdf(pdf(tmp_path, "a.pdf", ["Versao boa"]), b)
    with pytest.raises(PdfError):
        ingerir_pdf(pdf(tmp_path, "a.pdf", ["", ""]), b)
    assert total(b) == 1 and b.execute("select texto from trechos").fetchone()[0] == "Versao boa"


def test_ingerir_pasta_ignora_nao_pdf_e_isola_erros(tmp_path):
    pdf(tmp_path, "bom.pdf", ["Texto valido"])
    (tmp_path / "quebrado.pdf").write_bytes(b"isto nao e um pdf")
    (tmp_path / "notas.txt").write_text("nao deve ser lido")
    b = banco(tmp_path)
    res = {r["arquivo"]: r for r in ingerir_pasta(tmp_path, b)}
    assert set(res) == {"bom.pdf", "quebrado.pdf"}
    assert res["bom.pdf"]["status"] == "novo" and res["quebrado.pdf"]["status"] == "erro"
    assert total(b) == 1


def test_pasta_inexistente_devolve_lista_vazia(tmp_path):
    assert ingerir_pasta(tmp_path / "nao_existe", banco(tmp_path)) == []


def test_recusa_arquivo_grande_e_extensao_errada_sem_gravar(tmp_path):
    b = banco(tmp_path)
    with pytest.raises(PdfError) as erro:
        ingerir_pdf(pdf(tmp_path, "a.pdf", ["Texto"]), b, max_mb=0)
    assert "limite" in str(erro.value)
    (tmp_path / "a.txt").write_text("oi")
    with pytest.raises(PdfError):
        ingerir_pdf(tmp_path / "a.txt", b)
    assert total(b) == 0


def test_remover_documento_apaga_so_aquele_arquivo(tmp_path):
    b = banco(tmp_path)
    ingerir_pdf(pdf(tmp_path, "a.pdf", ["Texto A", "Mais A"]), b)
    ingerir_pdf(pdf(tmp_path, "b.pdf", ["Texto B"]), b)
    assert remover_documento("a.pdf", b) == 2
    assert [d["arquivo"] for d in listar_documentos(b)] == ["b.pdf"]
    assert remover_documento("nao_existe.pdf", b) == 0


def test_busca_ignora_acentos_e_maiusculas_e_devolve_a_pagina(tmp_path):
    b = banco(tmp_path)
    ingerir_pdf(pdf(tmp_path, "a.pdf", ["Introdução geral", "O prazo de devolução é de 7 dias"]), b)
    for consulta in ['"devolucao"', '"DEVOLUÇÃO"', '"devol"*']:
        r = buscar_trechos(b, consulta, 5)
        assert [(x["arquivo"], x["pagina"]) for x in r] == [("a.pdf", 2)], consulta


def test_busca_ordena_pelo_trecho_mais_parecido(tmp_path):
    b = banco(tmp_path)
    ingerir_pdf(pdf(tmp_path, "a.pdf", ["prazo de entrega", "prazo de devolução e devolução parcial", "assunto outro"]), b)
    r = buscar_trechos(b, '"praz"* OR "devol"*', 5)
    assert r[0]["pagina"] == 2 and len(r) == 2


def test_consulta_vazia_e_k_funcionam(tmp_path):
    b = banco(tmp_path)
    ingerir_pdf(pdf(tmp_path, "a.pdf", ["alfa", "alfa beta", "alfa gama"]), b)
    assert buscar_trechos(b, "", 5) == []
    assert len(buscar_trechos(b, '"alfa"', 2)) == 2


def test_os_dados_continuam_ali_depois_de_fechar_e_abrir(tmp_path):
    b = banco(tmp_path)
    ingerir_pdf(pdf(tmp_path, "a.pdf", ["Texto que fica salvo"]), b)
    b.close()
    assert total(banco(tmp_path)) == 1
