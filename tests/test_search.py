"""Testes da busca. Rodar na raiz do projeto: python -m pytest -v"""
from app.search import buscar, similaridade
from tests.fakes import ColecaoFalsa, EmbedFalso, EmbedMapa, colecao_com

COL = lambda: colecao_com(
    ("a", "Prazo de devolução de 7 dias", [0.0, 0.0], "politica.pdf", 3),
    ("b", "Horário de atendimento", [1.0, 0.0], "politica.pdf", 5),
    ("c", "Assunto sem relação", [5.0, 5.0], "outro.pdf", 1),
)
EMB = lambda: EmbedMapa({"qual o prazo?": [0.1, 0.0]})


def test_colecao_vazia_devolve_lista_vazia_sem_gerar_vetor():
    emb = EmbedFalso()
    assert buscar("qualquer coisa", ColecaoFalsa(), emb) == []
    assert emb.chamadas == 0


def test_resultados_vem_do_mais_para_o_menos_parecido():
    r = buscar("qual o prazo?", COL(), EMB(), k=3)
    assert [x["arquivo"] for x in r] == ["politica.pdf", "politica.pdf", "outro.pdf"]
    assert [x["pagina"] for x in r] == [3, 5, 1]
    assert r[0]["distancia"] < r[1]["distancia"] < r[2]["distancia"]


def test_relevante_depende_do_limite_de_distancia():
    r = buscar("qual o prazo?", COL(), EMB(), k=3, max_distancia=1.3)
    assert [x["relevante"] for x in r] == [True, True, False]
    r = buscar("qual o prazo?", COL(), EMB(), k=3, max_distancia=0.5)
    assert [x["relevante"] for x in r] == [True, False, False]


def test_k_limita_a_quantidade_e_k_maior_que_o_total_nao_quebra():
    assert len(buscar("qual o prazo?", COL(), EMB(), k=2)) == 2
    assert len(buscar("qual o prazo?", COL(), EMB(), k=50)) == 3


def test_metadado_sem_pagina_nao_quebra():
    col = colecao_com(("a", "texto", [0.0, 0.0], "x.pdf", None))
    r = buscar("qual o prazo?", col, EMB())
    assert r[0]["pagina"] is None and r[0]["arquivo"] == "x.pdf"


def test_similaridade_fica_entre_0_e_1():
    assert similaridade(0.0) == 1.0
    assert similaridade(1.0) == 0.5
    assert similaridade(3.0) == 0.0
    assert 0.0 <= similaridade(-0.5) <= 1.0
