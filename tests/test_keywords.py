"""Testes das funções de texto do modo sem IA. Rodar na raiz do projeto: python -m pytest -v"""
from app.keywords import (
    _base, destacar, melhor_frase, montar_consulta, radical, recorte, termos_achados, termos_da_pergunta,
)


def test_termos_tiram_palavras_comuns_acento_e_maiuscula():
    assert termos_da_pergunta("Qual é o prazo de devolução?") == ["prazo", "devolucao"]
    assert termos_da_pergunta("QUAL É O PRAZO DE DEVOLUÇÃO") == ["prazo", "devolucao"]


def test_termos_sem_repeticao_e_mantendo_numeros():
    assert termos_da_pergunta("prazo prazo 7 dias") == ["prazo", "7", "dias"]


def test_pergunta_so_com_palavras_comuns_nao_gera_termos():
    assert termos_da_pergunta("o que é isso?") == []


def test_radical_junta_palavras_da_mesma_familia():
    assert radical("devolucao") == "devol" and radical("prazo") == "praz" and radical("dias") == "dias"


def test_consulta_fts_usa_prefixo_so_em_palavras_longas():
    assert montar_consulta(["prazo", "devolucao"]) == '"praz"* OR "devol"*'
    assert montar_consulta(["dias", "7"]) == '"dias" OR "7"'


def test_termos_achados_casa_a_familia_da_palavra_mas_nao_o_meio():
    texto = "O produto devolvido em até 7 dias. Prazos curtos."
    assert termos_achados(texto, ["devolucao", "prazo", "7", "garantia"]) == ["devolucao", "prazo", "7"]
    assert termos_achados("desprazer enorme", ["prazo"]) == []


def test_melhor_frase_escolhe_a_que_tem_mais_termos():
    texto = "A loja abre cedo. O prazo de devolução é de 7 dias. O frete é grátis."
    assert melhor_frase(texto, ["prazo", "devolucao"]) == "O prazo de devolução é de 7 dias."


def test_destacar_poe_negrito_e_preserva_acentos_e_maiusculas():
    assert destacar("O Prazo de DEVOLUÇÃO é 7 dias.", ["prazo", "devolucao"]) == "O **Prazo** de **DEVOLUÇÃO** é 7 dias."


def test_destacar_remove_asteriscos_do_proprio_texto():
    assert "*" not in destacar("preço *especial* do prazo", ["prazo"]).replace("**", "")


def test_base_mantem_o_mesmo_tamanho_do_texto():
    for s in ["ação coração", "ÀÉÎÕÜ", "naïve façade", "normal"]:
        assert len(_base(s)) == len(s)


def test_recorte_deixa_texto_curto_intacto_e_centra_o_longo_na_palavra():
    assert recorte("texto curto", ["curto"], 500) == "texto curto"
    longo = ("palavra " * 200) + "prazo importante " + ("palavra " * 200)
    r = recorte(longo, ["prazo"], 200)
    assert "prazo" in r and r.startswith("...") and r.endswith("...") and len(r) <= 210
