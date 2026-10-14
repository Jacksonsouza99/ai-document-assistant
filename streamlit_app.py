"""Interface web do AI Document Assistant.

Por padrão funciona SEM IA: busca por palavras-chave, offline, sem chave de API.
Um interruptor na barra lateral liga o modo opcional com IA (Gemini).

Rodar na raiz do projeto:  python -m streamlit run streamlit_app.py
"""
import os

import streamlit as st
from dotenv import load_dotenv

from app import config
from app.files import salvar_upload
from app.keyword_store import abrir_banco
from app.keyword_store import ingerir_pdf as indexar_texto
from app.keyword_store import listar_documentos
from app.keyword_store import remover_documento as remover_texto
from app.llm import LLMError
from app.offline import responder_sem_ia
from app.rag import responder
from app.reader import PdfError
from app.vector_store import abrir_colecao
from app.vector_store import ingerir_pasta as indexar_pasta_ia
from app.vector_store import ingerir_pdf as indexar_ia
from app.vector_store import remover_documento as remover_ia

load_dotenv()

st.set_page_config(page_title="AI Document Assistant", page_icon="📄", layout="wide")

STATUS = {
    "novo": "✅ processado",
    "atualizado": "🔄 versão atualizada",
    "ja_existia": "ℹ️ já estava na base",
    "duplicado": "⚠️ igual a um arquivo já enviado",
}


@st.cache_resource(show_spinner="Abrindo a base de documentos...")
def obter_banco():
    return abrir_banco()


@st.cache_resource(show_spinner="Abrindo o banco vetorial (modo IA)...")
def obter_colecao():
    return abrir_colecao()


def processar_uploads(banco, colecao_ia):
    """Salva e indexa cada PDF enviado uma única vez (o Streamlit roda o script a cada clique)."""
    feitos = st.session_state.setdefault("uploads_feitos", set())

    for arquivo in st.session_state.get("uploader_atual") or []:
        chave = (arquivo.name, arquivo.size)

        if chave in feitos:
            continue

        feitos.add(chave)

        with st.sidebar.status(f"Processando {arquivo.name}...", expanded=False) as status:
            try:
                caminho = salvar_upload(arquivo.name, arquivo.getvalue())
                resultado = indexar_texto(caminho, banco)
            except PdfError as erro:
                status.update(label=f"{arquivo.name}: {erro}", state="error")
                continue

            aviso_ia = ""

            if colecao_ia is not None:
                try:
                    indexar_ia(caminho, colecao_ia)
                except Exception:
                    aviso_ia = " (a IA não conseguiu indexar: use o botão 'Indexar documentos para a IA')"

            rotulo = STATUS.get(resultado["status"], resultado["status"])
            extra = f" (igual a {resultado['igual_a']})" if "igual_a" in resultado else ""
            status.update(label=f"{arquivo.name}: {rotulo}{extra}{aviso_ia}", state="complete")


def barra_lateral(banco):
    st.sidebar.header("⚙️ Modo")

    usar_ia = st.sidebar.toggle(
        "Usar IA (Gemini) — opcional",
        value=False,
        help="Desligado: busca por palavras-chave, funciona offline e sem chave. "
        "Ligado: respostas em linguagem natural (precisa de chave, internet e dos pacotes da IA).",
    )

    colecao_ia = None

    if usar_ia:
        try:
            colecao_ia = obter_colecao()
        except Exception:
            st.sidebar.error("Pacotes da IA não instalados. Rode: python -m pip install -r requirements-ia.txt")
            usar_ia = False

    st.sidebar.header("📚 Seus documentos")

    st.sidebar.file_uploader(
        "Envie PDFs",
        type=["pdf"],
        accept_multiple_files=True,
        key="uploader_atual",
        help=f"Até {config.MAX_PDF_MB} MB por arquivo. PDFs escaneados (só imagem) não funcionam.",
    )

    processar_uploads(banco, colecao_ia)

    documentos = listar_documentos(banco)

    if not documentos:
        st.sidebar.info("Nenhum documento ainda. Envie um PDF para começar.")

    for doc in documentos:
        st.sidebar.markdown(f"**📄 {doc['arquivo']}**  \n{doc['paginas']} pág. · {doc['chunks']} trechos")

        if st.sidebar.button("Remover da base", key=f"remover_{doc['arquivo']}"):
            remover_texto(doc["arquivo"], banco)

            if colecao_ia is not None:
                remover_ia(doc["arquivo"], colecao_ia)

            st.rerun()

    if usar_ia:
        if not os.getenv("GEMINI_API_KEY"):
            st.sidebar.warning("GEMINI_API_KEY não encontrada. Crie o arquivo .env (veja o README).")

        if st.sidebar.button("Indexar documentos para a IA", key="indexar_ia"):
            with st.sidebar.spinner("Indexando..."):
                indexar_pasta_ia(colecao=colecao_ia)

    return documentos, colecao_ia


def mostrar_resposta(item):
    with st.chat_message("user"):
        st.write(item["pergunta"])

    with st.chat_message("assistant"):
        if item.get("erro"):
            st.error(item["erro"])
            return

        resultado = item["resultado"]

        if resultado["encontrou"]:
            st.markdown(resultado["resposta"])
        else:
            st.info(resultado["resposta"])

        if resultado["fontes"]:
            with st.expander(f"📎 Fontes ({len(resultado['fontes'])})"):
                for fonte in resultado["fontes"]:
                    st.markdown(f"**[{fonte['numero']}] {fonte['arquivo']}** · página {fonte['pagina']} · {fonte['detalhe']}")
                    trecho = fonte["trecho"]
                    st.caption(trecho if len(trecho) <= 800 else trecho[:800] + "...")
        elif resultado.get("melhor_distancia") is not None:
            st.caption(f"Trecho mais próximo: distância {resultado['melhor_distancia']:.2f} (limite {config.MAX_DISTANCE}).")


def main():
    st.title("📄 AI Document Assistant")

    banco = obter_banco()
    documentos, colecao_ia = barra_lateral(banco)
    usa_ia = colecao_ia is not None

    st.caption(
        "Modo com IA (Gemini): respostas em linguagem natural, sempre com a página de origem."
        if usa_ia
        else "Modo sem IA: busca por palavras-chave. Funciona offline e sem chave de API; mostra o trecho do documento e a página."
    )

    col1, col2 = st.columns(2)
    col1.metric("Documentos", len(documentos))
    col2.metric("Trechos indexados", sum(d["chunks"] for d in documentos))

    historico = st.session_state.setdefault("historico", [])
    pergunta = st.chat_input("Pergunte algo sobre os seus documentos")

    if pergunta:
        if not documentos:
            st.warning("Envie pelo menos um PDF antes de perguntar.")
        else:
            item = {"pergunta": pergunta}

            with st.spinner("Buscando nos documentos..."):
                try:
                    item["resultado"] = responder(pergunta, colecao_ia) if usa_ia else responder_sem_ia(pergunta, banco)
                except (ValueError, LLMError) as erro:
                    item["erro"] = str(erro)

            historico.append(item)
            del historico[:-20]

    for item in historico:
        mostrar_resposta(item)

    st.divider()
    st.caption("Confira sempre as fontes. Uso local e individual: sem login nem separação entre usuários.")


main()
