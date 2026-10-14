"""Testes do split_pages. Rodar na raiz do projeto: python -m pytest -v"""
import pytest

from app.chunker import split_pages


def pagina(numero, prefixo, quantidade):
    texto = " ".join(f"{prefixo}{i}" for i in range(quantidade))
    return {"page": numero, "text": texto}


def test_lista_vazia_devolve_lista_vazia():
    assert split_pages([]) == []


def test_pagina_curta_vira_um_chunk_com_a_pagina_certa():
    resultado = split_pages([{"page": 7, "text": "texto curto"}])
    assert resultado == [{"text": "texto curto", "page": 7, "chunk_index": 0}]


def test_pagina_longa_gera_varios_chunks_da_mesma_pagina():
    resultado = split_pages([pagina(2, "w", 800)], chunk_size=300, overlap=60)
    assert len(resultado) > 1
    assert {c["page"] for c in resultado} == {2}


def test_chunks_nao_misturam_paginas():
    paginas = [pagina(1, "a", 400), pagina(2, "b", 400), pagina(5, "c", 400)]
    for c in split_pages(paginas, chunk_size=300, overlap=60):
        prefixos = {palavra[0] for palavra in c["text"].split()}
        assert prefixos == {{1: "a", 2: "b", 5: "c"}[c["page"]]}


def test_pagina_sem_texto_nao_gera_chunks():
    assert split_pages([{"page": 1, "text": "   "}]) == []


def test_chunk_index_e_sequencial_atravessando_paginas():
    resultado = split_pages([pagina(1, "a", 300), pagina(2, "b", 300)], chunk_size=300, overlap=60)
    assert [c["chunk_index"] for c in resultado] == list(range(len(resultado)))


def test_ordem_das_paginas_e_mantida():
    resultado = split_pages([pagina(3, "a", 300), pagina(9, "b", 300)], chunk_size=300, overlap=60)
    paginas = [c["page"] for c in resultado]
    assert paginas == sorted(paginas)


def test_parametros_invalidos_continuam_dando_erro_claro():
    with pytest.raises(ValueError):
        split_pages([{"page": 1, "text": "abc"}], chunk_size=100, overlap=100)
