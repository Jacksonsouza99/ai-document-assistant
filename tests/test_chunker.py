"""Testes do chunker. Rodar na raiz do projeto: python -m pytest -v"""
import random
import threading

import pytest

from app.chunker import split_text


def roda_com_limite(funcao, *args, limite=5, **kwargs):
    """Roda a função em outra thread. Se passar de `limite` segundos, o teste
    falha em vez de ficar preso para sempre (é assim que o bug antigo se manifestava)."""
    resultado = {}

    def alvo():
        resultado["valor"] = funcao(*args, **kwargs)

    t = threading.Thread(target=alvo, daemon=True)
    t.start()
    t.join(limite)
    assert not t.is_alive(), "split_text travou (laço infinito)"
    return resultado["valor"]


def test_texto_vazio_ou_so_espacos_nao_gera_chunks():
    assert split_text("") == []
    assert split_text("    \n  ") == []


def test_texto_curto_vira_um_unico_chunk():
    assert split_text("texto curto") == ["texto curto"]


def test_nenhum_chunk_passa_do_tamanho_nem_e_vazio():
    texto = " ".join(f"palavra{i}" for i in range(2000))
    chunks = split_text(texto, chunk_size=500, overlap=100)
    assert len(chunks) > 1
    assert all(c.strip() and len(c) <= 500 for c in chunks)


def test_todas_as_palavras_aparecem_em_algum_chunk():
    palavras = [f"w{i}" for i in range(1500)]
    chunks = split_text(" ".join(palavras), chunk_size=300, overlap=60)
    achadas = set(" ".join(chunks).split())
    assert set(palavras) <= achadas


def test_ha_sobreposicao_entre_chunks_vizinhos():
    texto = " ".join(f"w{i}" for i in range(1500))
    chunks = split_text(texto, chunk_size=300, overlap=60)
    for atual, proximo in zip(chunks, chunks[1:]):
        assert atual.split()[-1] in proximo.split()


def test_chunks_comecam_e_terminam_em_palavra_inteira():
    palavras = {f"w{i}" for i in range(1500)}
    chunks = split_text(" ".join(sorted(palavras)), chunk_size=300, overlap=60)
    for c in chunks:
        assert set(c.split()) <= palavras


def test_o_final_do_texto_nao_e_perdido():
    texto = " ".join(f"w{i}" for i in range(800)) + " ULTIMA"
    assert split_text(texto, chunk_size=300, overlap=60)[-1].endswith("ULTIMA")


# --- casos que travavam o código antigo ---

def test_bloco_longo_sem_espacos_nao_trava():
    chunks = roda_com_limite(split_text, "a" * 3000)
    assert chunks and all(len(c) <= 1000 for c in chunks)


def test_palavra_curta_seguida_de_bloco_sem_espacos_nao_trava():
    texto = ("palavra " * 125) + " ab " + ("z" * 1500) + " fim"
    chunks = roda_com_limite(split_text, texto)
    assert chunks[-1].endswith("fim")


def test_bloco_sem_espacos_logo_apos_o_inicio_nao_trava():
    chunks = roda_com_limite(split_text, "Oi " + "a" * 2500)
    assert chunks and "".join(chunks).count("a") >= 2500


def test_textos_aleatorios_com_blocos_longos_sempre_terminam():
    rnd = random.Random(7)
    for _ in range(150):
        partes = []
        for _ in range(rnd.randint(1, 8)):
            if rnd.random() < 0.3:
                partes.append("a" * rnd.randint(300, 2500))
            else:
                partes.append(" ".join("w" * rnd.randint(1, 12) for _ in range(rnd.randint(1, 120))))
        texto = " ".join(partes)
        chunks = roda_com_limite(split_text, texto)
        assert all(c.strip() and len(c) <= 1000 for c in chunks)
        assert texto.strip()[-15:] in chunks[-1]


def test_overlap_invalido_gera_erro_claro():
    with pytest.raises(ValueError):
        split_text("qualquer texto", chunk_size=100, overlap=100)
