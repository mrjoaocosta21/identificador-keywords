"""Interface local do identificador de palavras-chave.

Execute com: python -m streamlit run app.py
"""

import logging
from pathlib import Path

import streamlit as st

from palavras_chave import AnalysisReport, AnalysisService, Document, InputError, Ranking
from palavras_chave.export import ranking_csv, ranking_rows
from palavras_chave.inputs import (
    MAX_DOCUMENTS,
    MAX_FILE_BYTES,
    MAX_TOTAL_CHARACTERS,
    decode_text_file,
)
from palavras_chave.models import DocumentAnalysis

LOGGER = logging.getLogger(__name__)
BASE_DIR = Path(__file__).resolve().parent
TEXT_MODE = "Colar texto"
FILE_MODE = "Enviar arquivos .txt"
PREVIEW_CHARACTERS = 4_000
PREVIEW_TOKENS = 200


def clear_report() -> None:
    """Descarta o resultado anterior quando a origem da entrada é alterada."""
    st.session_state.pop("report", None)
    st.session_state.pop("input_error", None)


def reset_workspace() -> None:
    """Limpa o texto, os resultados e recria o campo de arquivos enviados."""
    clear_report()
    st.session_state["text_content"] = ""
    st.session_state["upload_generation"] = st.session_state.get("upload_generation", 0) + 1


def load_example() -> None:
    """Carrega um texto curto para a primeira análise e para o seminário."""
    clear_report()
    st.session_state["input_mode"] = TEXT_MODE
    st.session_state["text_content"] = (BASE_DIR / "exemplos" / "pln.txt").read_text(
        encoding="utf-8"
    )


def render_input() -> None:
    """Reúne a entrada e só inicia o processamento após a confirmação do formulário."""
    with st.container(border=True):
        st.header("1. Adicione o conteúdo")
        st.radio(
            "Origem do conteúdo",
            [TEXT_MODE, FILE_MODE],
            horizontal=True,
            key="input_mode",
            on_change=clear_report,
        )
        example_column, reset_column = st.columns(2)
        example_column.button("Usar texto de exemplo", on_click=load_example, width="stretch")
        reset_column.button("Limpar análise", on_click=reset_workspace, width="stretch")

        with st.form("analysis_form"):
            uploads = []
            text = ""
            if st.session_state["input_mode"] == TEXT_MODE:
                text = st.text_area(
                    "Texto para analisar",
                    key="text_content",
                    height=220,
                    max_chars=MAX_TOTAL_CHARACTERS,
                    placeholder="Cole um texto em português ou use o exemplo acima.",
                    help="O texto é processado na sessão e não é salvo em arquivo.",
                )
            else:
                uploads = st.file_uploader(
                    "Selecione os documentos",
                    type=["txt"],
                    accept_multiple_files=True,
                    key=f"uploads_{st.session_state.get('upload_generation', 0)}",
                    help="Até 20 arquivos .txt, com 1 MB por arquivo, em UTF-8.",
                )
                st.caption("A análise usa todos os arquivos selecionados, sem gravá-los no disco.")

            top_n = st.number_input(
                "Quantidade de palavras-chave (N)",
                min_value=1,
                value=10,
                step=1,
                key="top_n",
                help="Se houver menos grupos de termos que N, todos serão exibidos.",
            )
            st.caption(
                "Depois de alterar o conteúdo ou N, selecione Analisar conteúdo para atualizar."
            )
            submitted = st.form_submit_button("Analisar conteúdo", type="primary", width="stretch")

    if not submitted:
        return

    clear_report()
    try:
        with st.spinner("Preparando os termos e calculando as frequências…"):
            if st.session_state["input_mode"] == TEXT_MODE:
                if not text.strip():
                    raise InputError("Cole um texto ou use o exemplo antes de iniciar a análise.")
                documents = [Document(name="Texto colado", text=text)]
            else:
                if not uploads:
                    raise InputError("Selecione pelo menos um arquivo .txt para analisar.")
                if len(uploads) > MAX_DOCUMENTS:
                    raise InputError(f"Selecione no máximo {MAX_DOCUMENTS} documentos por análise.")
                documents = []
                for upload in uploads:
                    if upload.size > MAX_FILE_BYTES:
                        raise InputError(f"O arquivo {upload.name!r} ultrapassa o limite de 1 MB.")
                    documents.append(decode_text_file(upload.name, upload.getvalue()))
            st.session_state["report"] = AnalysisService().analyze(documents, top_n=int(top_n))
            st.session_state["result_scope"] = -1
            st.session_state["trace_document"] = 0
    except InputError as error:
        st.session_state["input_error"] = str(error)
    except OSError:
        LOGGER.exception("Falha ao ler os recursos locais do processamento.")
        st.session_state["input_error"] = (
            "Não foi possível carregar os recursos da análise. "
            "Verifique se a pasta palavras_chave/data acompanha o projeto."
        )


def render_ranking(ranking: Ranking, top_n: int, scope: int) -> None:
    """Mostra contagens completas e o recorte solicitado do ranking."""
    metrics = st.columns(3)
    metrics[0].metric("Palavras identificadas", f"{ranking.total_tokens:,}".replace(",", "."))
    metrics[1].metric("Após remover stopwords", f"{ranking.retained_tokens:,}".replace(",", "."))
    metrics[2].metric("Radicais distintos", f"{ranking.unique_terms:,}".replace(",", "."))

    if not ranking.keywords:
        st.info(
            "Nenhuma palavra-chave foi encontrada. O conteúdo pode conter apenas "
            "stopwords, números ou pontuação. Experimente um texto com mais conteúdo."
        )
        return

    st.caption(
        "Cada linha reúne palavras com o mesmo radical. A frequência soma as ocorrências "
        "do grupo; o termo exibido é sua variante mais frequente."
    )
    rows = ranking_rows(ranking)
    st.dataframe(
        rows,
        hide_index=True,
        width="stretch",
        column_config={
            "Posição": st.column_config.NumberColumn(format="%d", width="small"),
            "Termo": st.column_config.TextColumn("Termo representativo"),
            "Frequência do grupo": st.column_config.NumberColumn(format="%d"),
            "Variantes": st.column_config.TextColumn("Variantes encontradas", width="large"),
        },
    )
    if top_n > ranking.unique_terms:
        st.caption(
            f"Você pediu {top_n} resultados. Foram encontrados {ranking.unique_terms} grupos; "
            "todos estão na tabela."
        )

    st.download_button(
        "Baixar ranking em CSV",
        data=ranking_csv(ranking),
        file_name="ranking-geral.csv" if scope == -1 else f"ranking-documento-{scope + 1}.csv",
        mime="text/csv",
        on_click="ignore",
        help="Exporta as linhas exibidas, com frequência, radical e variantes.",
    )

    with st.expander("Comparar frequências no gráfico"):
        chart_keywords = ranking.keywords[:15]
        st.bar_chart(
            {
                "Termo": [item.term for item in chart_keywords],
                "Frequência": [item.frequency for item in chart_keywords],
            },
            x="Termo",
            y="Frequência",
            horizontal=True,
            sort="-Frequência",
            color="#155E75",
            height=max(240, len(chart_keywords) * 30),
            alt=(
                "Comparação das frequências dos primeiros termos do ranking. "
                "Os mesmos valores estão disponíveis na tabela acima."
            ),
        )
        st.caption("O gráfico compara até 15 grupos. A tabela contém todos os resultados pedidos.")


def render_trace(analysis: DocumentAnalysis) -> None:
    """Expõe uma prévia limitada das transformações, sem alterar a análise completa."""
    trace = analysis.trace
    stages = {
        "Texto original": analysis.document.text,
        "Conversão para minúsculas": trace.lowercase_text,
        "Remoção de acentos": trace.normalized_text,
        "Separação por pontuação": trace.separated_text,
        "Palavras separadas (tokens)": " · ".join(trace.tokens[:PREVIEW_TOKENS]),
        "Remoção de stopwords": " · ".join(trace.filtered_tokens[:PREVIEW_TOKENS]),
        "Stemming e agrupamento": "\n".join(
            f"{token} → {stem}"
            for token, stem in zip(
                trace.filtered_tokens[:PREVIEW_TOKENS], trace.stems[:PREVIEW_TOKENS], strict=True
            )
        ),
    }
    selected = st.selectbox("Etapa do processamento", list(stages), key="trace_stage")
    preview = stages[selected]
    st.code(
        preview[:PREVIEW_CHARACTERS] or "Nenhum termo nesta etapa.", language=None, wrap_lines=True
    )
    st.caption(
        "Esta prévia mostra até 4.000 caracteres ou 200 termos. "
        "A contagem considera todo o documento."
    )
    st.caption(
        "O stemming usa uma cópia com acentos para preservar as regras do português. "
        "A comparação de stopwords e os radicais finais usam a forma sem acentos."
    )


def render_results(report: AnalysisReport) -> None:
    """Permite explorar o consolidado e cada documento do relatório."""
    count = len(report.documents)
    document_label = "documento processado" if count == 1 else "documentos processados"
    st.success(f"Análise concluída: {count} {document_label}.")
    st.header("2. Explore os resultados")
    scope = -1
    if count > 1:
        scope = st.selectbox(
            "Resultado para visualizar",
            [-1, *range(count)],
            format_func=lambda index: (
                "Todos os documentos"
                if index == -1
                else f"{index + 1}. {report.documents[index].document.name}"
            ),
            key="result_scope",
        )
    ranking = report.overall if scope == -1 else report.documents[scope].ranking
    render_ranking(ranking, report.top_n, scope)

    with st.expander("3. Entenda o processamento"):
        trace_index = scope if scope >= 0 else 0
        if count > 1 and scope == -1:
            trace_index = st.selectbox(
                "Documento para acompanhar as etapas",
                list(range(count)),
                format_func=lambda index: f"{index + 1}. {report.documents[index].document.name}",
                key="trace_document",
            )
        render_trace(report.documents[trace_index])


def main() -> None:
    """Compõe a página com entrada, feedback e exploração do relatório da sessão."""
    st.set_page_config(
        page_title="Identificador de palavras-chave",
        page_icon="🔎",
        layout="centered",
    )
    st.caption("PROCESSAMENTO DE LINGUAGEM NATURAL · PORTUGUÊS")
    st.title("Identificador de palavras-chave")
    st.write(
        "Explore os termos mais frequentes de um texto e acompanhe "
        "como cada etapa do processamento transforma o resultado."
    )
    render_input()

    if error := st.session_state.get("input_error"):
        st.error(error)
    if report := st.session_state.get("report"):
        render_results(report)
    elif not st.session_state.get("input_error"):
        st.info("Adicione um texto ou documentos e selecione Analisar conteúdo para começar.")

    with st.expander("Como interpretar os resultados"):
        st.write(
            "Stopwords são palavras comuns, como artigos e preposições, retiradas antes "
            "da contagem. Stemming reduz as palavras a radicais para agrupar algumas "
            "variações. Esses radicais podem não ser palavras completas."
        )
        st.write(
            "A relevância usada aqui é a frequência absoluta. Ela indica repetição, "
            "mas não garante importância semântica. O stemming também pode reunir "
            "palavras com sentidos diferentes."
        )
        st.write(
            "O ranking consolidado soma ocorrências de todos os documentos. "
            "Textos maiores podem contribuir com mais ocorrências. "
            "Empates são resolvidos pela ordem alfabética do termo representativo."
        )
        st.caption(
            "Limites: 20 documentos, 1 MB por arquivo e 2 milhões de caracteres por análise. "
            "Arquivos .txt devem estar em UTF-8. Números isolados são desconsiderados."
        )
    st.caption("Projeto acadêmico · Inteligência Artificial · Engenharia da Computação")


if __name__ == "__main__":
    main()
