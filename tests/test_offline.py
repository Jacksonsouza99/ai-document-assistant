"""Testes da resposta SEM IA (banco SQLite de verdade). Rodar na raiz: python -m pytest -v"""
import pytest

from app import config
from app.keyword_store import abrir_banco, ingerir_pdf
from app.offline import responder_sem_ia
from tests.helpers import make_pdf


def montar(tmp_path, **arquivos):
    banco = abrir_banco(tmp_path / "k.db")
    for nome, paginas in arquivos.items():
        caminho = tmp_path / nome
        caminho.write_bytes(make_pdf(paginas))
        ingerir_pdf(caminho, banco)
    return banco


def test_pergunta_invalida_da_erro_claro(tmp_path):
    b = montar(tmp_path, **{"a.pdf": ["texto"]})
    for ruim in ["", "   ", None, "x" * (config.MAX_QUESTION_CHARS + 1), "o que é isso?"]:
        with pytest.raises(ValueError):
            responder_sem_ia(ruim, b)


def test_acha_a_frase_certa_com_arquivo_pagina_e_destaque(tmp_path):
    b = montar(tmp_path, **{"politica.pdf": ["A loja abre cedo.", "O prazo de devolução é de 7 dias corridos. O frete é grátis."]})
    r = responder_sem_ia("Qual é o prazo de devolução?", b)
    assert r["encontrou"] is True and r["modo"] == "sem_ia"
    assert "politica.pdf, página 2" in r["resposta"]
    assert "O **prazo** de **devolução** é de 7 dias corridos." in r["resposta"]
    fonte = r["fontes"][0]
    assert (fonte["arquivo"], fonte["pagina"]) == ("politica.pdf", 2)
    assert "2 de 2" in fonte["detalhe"]


def test_pergunta_sem_acento_acha_texto_com_acento(tmp_path):
    b = montar(tmp_path, **{"a.pdf": ["O prazo de devolução é de 7 dias"]})
    assert responder_sem_ia("prazo devolucao", b)["encontrou"] is True


def test_assunto_que_nao_esta_no_documento_diz_que_nao_encontrou(tmp_path):
    b = montar(tmp_path, **{"a.pdf": ["O prazo de devolução é de 7 dias"]})
    r = responder_sem_ia("Qual o telefone da garantia estendida?", b)
    assert r["encontrou"] is False and r["fontes"] == []
    assert r["resposta"] == config.NOT_FOUND_MESSAGE


def test_cobertura_minima_dos_termos_e_respeitada(tmp_path):
    b = montar(tmp_path, **{"a.pdf": ["O prazo de entrega é curto"]})
    pergunta = "prazo garantia reembolso"            # só 1 dos 3 termos aparece (33%)
    assert responder_sem_ia(pergunta, b)["encontrou"] is False
    assert responder_sem_ia(pergunta, b, min_cobertura=0.3)["encontrou"] is True


def test_trecho_com_todos_os_termos_vem_antes_do_que_tem_so_um(tmp_path):
    b = montar(tmp_path, **{"a.pdf": ["prazo de entrega rápido", "prazo de devolução e troca"]})
    r = responder_sem_ia("prazo devolução", b)
    assert [f["pagina"] for f in r["fontes"]] == [2, 1]


def test_cada_fonte_aponta_para_o_arquivo_certo(tmp_path):
    b = montar(tmp_path, **{"a.pdf": ["política de devolução da loja"], "b.pdf": ["manual de instalação do produto"]})
    r = responder_sem_ia("devolução da loja", b)
    assert {f["arquivo"] for f in r["fontes"]} == {"a.pdf"}


def test_k_limita_a_quantidade_de_fontes(tmp_path):
    b = montar(tmp_path, **{"a.pdf": [f"prazo item {i}" for i in range(6)]})
    assert len(responder_sem_ia("prazo", b, k=3)["fontes"]) == 3


def test_banco_vazio_diz_que_nao_encontrou(tmp_path):
    r = responder_sem_ia("prazo devolução", abrir_banco(tmp_path / "vazio.db"))
    assert r["encontrou"] is False
