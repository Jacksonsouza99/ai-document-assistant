"""Testes da validação de uploads. Rodar na raiz do projeto: python -m pytest -v"""
import pytest

from app.files import nome_seguro, salvar_upload
from app.reader import PdfError
from tests.helpers import make_pdf


def test_nome_seguro_tira_pastas_e_caminhos():
    assert nome_seguro("../../etc/passwd.pdf") == "passwd.pdf"
    assert nome_seguro("C:\\Users\\x\\relatorio.pdf") == "relatorio.pdf"


def test_nome_seguro_troca_caracteres_perigosos_e_mantem_acentos():
    assert nome_seguro("relatório final (v2).pdf") == "relatório final _v2_.pdf"
    assert nome_seguro("a<b>c|d.pdf") == "a_b_c_d.pdf"


def test_nome_seguro_nunca_devolve_nome_vazio():
    assert nome_seguro("...pdf") == "documento.pdf" or nome_seguro("...pdf").endswith(".pdf")
    assert nome_seguro("").endswith(".pdf") and len(nome_seguro("")) > 4


def test_salva_pdf_valido_na_pasta(tmp_path):
    destino = salvar_upload("meu doc.pdf", make_pdf(["texto"]), tmp_path)
    assert destino.parent == tmp_path and destino.read_bytes().startswith(b"%PDF-")


def test_nome_com_caminho_nao_escapa_da_pasta(tmp_path):
    pasta = tmp_path / "docs"
    destino = salvar_upload("../../fora.pdf", make_pdf(["texto"]), pasta)
    assert destino.resolve().parent == pasta.resolve()
    assert not (tmp_path / "fora.pdf").exists()


def test_recusa_extensao_errada_vazio_grande_e_falso(tmp_path):
    pdf = make_pdf(["texto"])
    casos = [
        ("a.txt", pdf, None, "pdf"),
        ("a.pdf", b"", None, "vazio"),
        ("a.pdf", pdf, 0, "limite"),
        ("a.pdf", b"isto nao e um pdf", None, "válido"),
    ]
    for nome, conteudo, max_mb, trecho in casos:
        with pytest.raises(PdfError) as erro:
            salvar_upload(nome, conteudo, tmp_path, max_mb)
        assert trecho in str(erro.value)
    assert list(tmp_path.iterdir()) == []   # nada foi gravado
