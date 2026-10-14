"""Testes do llm.py sem chamar a API. Rodar na raiz do projeto: python -m pytest -v"""
import os
import subprocess
import sys
from pathlib import Path

import pytest

from app import config
from app.llm import LLMError, gerar_resposta, montar_prompt


def test_importar_o_modulo_nao_exige_a_chave():
    """Em um processo separado e SEM a variável GEMINI_API_KEY, o import não pode falhar."""
    raiz = Path(__file__).resolve().parent.parent
    ambiente = {k: v for k, v in os.environ.items() if k != "GEMINI_API_KEY"}
    r = subprocess.run([sys.executable, "-c", "import app.llm"], cwd=raiz, env=ambiente,
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr


def test_prompt_tem_pergunta_trechos_e_a_palavra_de_recusa():
    p = montar_prompt("Qual o prazo?", "[1] (a.pdf, página 3)\n7 dias")
    assert "Qual o prazo?" in p and "7 dias" in p and config.NO_ANSWER_TOKEN in p
    assert "SOMENTE" in p


def test_usa_o_gerador_informado_e_limpa_espacos():
    assert gerar_resposta("p", "c", lambda prompt: "  resposta  \n") == "resposta"


def test_erro_inesperado_vira_mensagem_amigavel_sem_vazar_detalhes():
    def quebrado(prompt):
        raise RuntimeError("detalhe-secreto-123")
    with pytest.raises(LLMError) as erro:
        gerar_resposta("p", "c", quebrado)
    assert "detalhe-secreto-123" not in str(erro.value)


def test_llm_error_do_gerador_passa_intacto():
    def recusa(prompt):
        raise LLMError("sem chave")
    with pytest.raises(LLMError) as erro:
        gerar_resposta("p", "c", recusa)
    assert str(erro.value) == "sem chave"
