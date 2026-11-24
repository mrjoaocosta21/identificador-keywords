"""Exercita a interface Streamlit com os componentes reais da aplicação."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

APP_PATH = Path(__file__).resolve().parents[1] / "app.py"


@pytest.fixture
def app():
    instance = AppTest.from_file(str(APP_PATH), default_timeout=15).run()
    assert not instance.exception
    return instance


def click(app, label):
    return next(button for button in app.button if button.label == label).click().run()


def submit_text(app, text):
    app.text_area(key="text_content").set_value(text)
    return click(app, "Analisar conteúdo")


def test_initial_page_explains_how_to_start(app):
    assert app.title[0].value == "Identificador de palavras-chave"
    assert app.text_area(key="text_content").value == ""
    assert any("para começar" in message.value for message in app.info)
    assert "report" not in app.session_state


def test_empty_text_submission_shows_validation_error(app):
    click(app, "Analisar conteúdo")

    assert not app.exception
    assert app.error
    assert "report" not in app.session_state
    assert not app.success


def test_example_loads_and_produces_a_ranking(app):
    click(app, "Usar texto de exemplo")
    assert app.text_area(key="text_content").value.strip()

    click(app, "Analisar conteúdo")

    assert not app.exception
    assert app.success
    assert not app.error
    assert app.session_state["report"].overall.keywords
    assert not app.dataframe[0].value.empty


def test_only_stopwords_produces_empty_state_without_an_exception(app):
    submit_text(app, "o e de as não")

    assert not app.exception
    assert app.success
    assert not app.error
    assert any("Nenhuma palavra-chave" in message.value for message in app.info)
    assert app.session_state["report"].overall.keywords == ()
    assert not app.dataframe


def test_top_n_can_be_changed_and_reanalyzed(app):
    app.number_input(key="top_n").set_value(1)
    submit_text(app, "dados dados redes textos")
    assert len(app.session_state["report"].overall.keywords) == 1

    app.number_input(key="top_n").set_value(2)
    click(app, "Analisar conteúdo")

    assert not app.exception
    assert app.session_state["report"].top_n == 2
    assert len(app.dataframe[0].value) == 2
    assert app.session_state["report"].overall.unique_terms == 3


def test_reset_clears_text_and_previous_results(app):
    submit_text(app, "dados dados redes")
    assert app.success

    click(app, "Limpar análise")

    assert not app.exception
    assert app.text_area(key="text_content").value == ""
    assert "report" not in app.session_state
    assert not app.success
    assert not app.dataframe


def test_invalid_resubmission_discards_previous_successful_report(app):
    submit_text(app, "dados dados redes")
    assert app.success

    submit_text(app, "")

    assert not app.exception
    assert app.error
    assert "report" not in app.session_state
    assert not app.success
    assert not app.dataframe


def test_upload_mode_requires_at_least_one_file(app):
    app.radio(key="input_mode").set_value("Enviar arquivos .txt").run()
    click(app, "Analisar conteúdo")

    assert not app.exception
    assert app.error
    assert "pelo menos um arquivo" in app.error[0].value
    assert "report" not in app.session_state


def test_real_utf8_upload_is_analyzed_and_keeps_accents(app):
    app.radio(key="input_mode").set_value("Enviar arquivos .txt").run()
    app.file_uploader[0].set_value(
        ("ciência.txt", "química químicas química".encode(), "text/plain")
    )
    click(app, "Analisar conteúdo")

    assert not app.exception
    assert app.success
    report = app.session_state["report"]
    assert report.documents[0].document.name == "ciência.txt"
    assert report.overall.keywords[0].term == "química"
    assert report.overall.keywords[0].frequency == 3


def test_two_real_uploads_support_individual_rankings_and_trace(app):
    app.radio(key="input_mode").set_value("Enviar arquivos .txt").run()
    app.file_uploader[0].set_value(
        [
            ("primeiro.txt", b"dados dados redes", "text/plain"),
            ("segundo.txt", b"redes textos dados", "text/plain"),
        ]
    )
    click(app, "Analisar conteúdo")

    assert not app.exception
    report = app.session_state["report"]
    assert len(report.documents) == 2
    assert report.overall.keywords[0].frequency == 3
    app.selectbox(key="result_scope").set_value(1).run()
    assert not app.exception
    assert set(app.dataframe[0].value["Frequência do grupo"]) == {1}
    assert app.code[0].value == "redes textos dados"

    app.selectbox(key="trace_stage").set_value("Stemming e agrupamento").run()
    assert not app.exception
    assert "→" in app.code[0].value


def test_invalid_utf8_upload_shows_error_and_no_results(app):
    app.radio(key="input_mode").set_value("Enviar arquivos .txt").run()
    app.file_uploader[0].set_value(("texto.txt", b"dados\xff", "text/plain"))
    click(app, "Analisar conteúdo")

    assert not app.exception
    assert app.error
    assert "UTF-8" in app.error[0].value
    assert "report" not in app.session_state


def test_changing_input_mode_discards_previous_ranking(app):
    submit_text(app, "dados redes")
    assert app.success

    app.radio(key="input_mode").set_value("Enviar arquivos .txt").run()

    assert not app.exception
    assert "report" not in app.session_state
    assert not app.success
    assert app.file_uploader
