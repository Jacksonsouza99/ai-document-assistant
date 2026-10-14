"""Testes do reader. Os PDFs de teste são criados aqui mesmo (sem arquivos externos).
Rodar na raiz do projeto: python -m pytest -v"""
import io

import pytest
from pypdf import PdfReader, PdfWriter

from app.reader import PdfError, extract_pages, extract_text
from tests.helpers import make_pdf


def salvar(tmp_path, nome, conteudo):
    caminho = tmp_path / nome
    caminho.write_bytes(conteudo)
    return str(caminho)


def test_devolve_uma_entrada_por_pagina_com_o_numero_certo(tmp_path):
    pdf = salvar(tmp_path, "a.pdf", make_pdf(["Primeira pagina", "Segunda pagina", "Terceira pagina"]))
    paginas = extract_pages(pdf)
    assert [p["page"] for p in paginas] == [1, 2, 3]
    assert paginas[1]["text"] == "Segunda pagina"


def test_acentos_sao_preservados(tmp_path):
    pdf = salvar(tmp_path, "a.pdf", make_pdf(["ação, coração e informação"]))
    assert extract_pages(pdf)[0]["text"] == "ação, coração e informação"


def test_pagina_em_branco_e_ignorada_mas_a_numeracao_continua(tmp_path):
    pdf = salvar(tmp_path, "a.pdf", make_pdf(["Pagina um", "", "Pagina tres"]))
    assert [p["page"] for p in extract_pages(pdf)] == [1, 3]


def test_espacos_e_quebras_sao_normalizados(tmp_path):
    pdf = salvar(tmp_path, "a.pdf", make_pdf(["muito     espaco    aqui"]))
    assert extract_pages(pdf)[0]["text"] == "muito espaco aqui"


def test_pdf_sem_texto_da_erro_claro(tmp_path):
    pdf = salvar(tmp_path, "a.pdf", make_pdf(["", ""]))
    with pytest.raises(PdfError) as erro:
        extract_pages(pdf)
    assert "escaneado" in str(erro.value)


def test_arquivo_que_nao_e_pdf_da_erro_claro(tmp_path):
    falso = salvar(tmp_path, "falso.pdf", b"isto nao e um pdf, so texto qualquer")
    with pytest.raises(PdfError) as erro:
        extract_pages(falso)
    assert "PDF" in str(erro.value)


def test_arquivo_inexistente_da_erro_claro(tmp_path):
    with pytest.raises(PdfError) as erro:
        extract_pages(str(tmp_path / "nao_existe.pdf"))
    assert "não encontrado" in str(erro.value)


def test_pdf_com_senha_da_erro_claro(tmp_path):
    escritor = PdfWriter()
    escritor.append_pages_from_reader(PdfReader(io.BytesIO(make_pdf(["segredo"]))))
    try:
        escritor.encrypt("senha-forte", algorithm="RC4-128")
        buf = io.BytesIO()
        escritor.write(buf)
    except Exception:
        pytest.skip("esta versão do pypdf não consegue criar PDF protegido")
    pdf = salvar(tmp_path, "a.pdf", buf.getvalue())
    with pytest.raises(PdfError) as erro:
        extract_pages(pdf)
    assert "senha" in str(erro.value)


def test_extract_text_antigo_continua_funcionando(tmp_path):
    pdf = salvar(tmp_path, "a.pdf", make_pdf(["Pagina um", "Pagina dois"]))
    assert extract_text(pdf) == "Pagina um\n\nPagina dois"
