"""Ajuda a escolher o limite de distância (MAX_DISTANCE).

    python -m app.calibrar "pergunta que TEM resposta" "pergunta que NÃO tem resposta"

Mostra só distância, arquivo e página (nunca o texto dos trechos).
Regra prática: as perguntas que têm resposta devem ficar abaixo do limite,
e as que não têm, acima. Teste outro limite sem editar o código com:
    $env:RAG_MAX_DISTANCE = "1.1"
"""
import sys

from app import config
from app.search import buscar, similaridade
from app.vector_store import abrir_colecao


def main(perguntas: list[str]) -> int:
    if not perguntas:
        print('Uso: python -m app.calibrar "pergunta 1" "pergunta 2"')
        return 1

    colecao = abrir_colecao()
    print(f"Limite atual (MAX_DISTANCE): {config.MAX_DISTANCE}\n")

    for pergunta in perguntas:
        print(f"Pergunta: {pergunta}")
        resultados = buscar(pergunta, colecao, max_distancia=config.MAX_DISTANCE)

        if not resultados:
            print("  (a coleção está vazia)\n")
            continue

        for r in resultados:
            marca = "dentro do limite" if r["relevante"] else "fora do limite"
            print(
                f"  distância {r['distancia']:.3f} | similaridade ~{similaridade(r['distancia']):.0%} | "
                f"{r['arquivo']}, página {r['pagina']} | {marca}"
            )
        print()

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
