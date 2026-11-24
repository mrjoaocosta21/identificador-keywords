"""Verifica o comportamento estatístico e linguístico público da análise."""

import pytest

from palavras_chave import AnalysisService, Document, TextPreprocessor


def identity_service(*, stopwords=()):
    """Isola as regras de contagem das regras de um stemmer específico."""
    return AnalysisService(TextPreprocessor(stopwords=stopwords, stemmer=lambda word: word))


def test_punctuation_separates_words_and_numbers_are_not_keywords():
    report = identity_service().analyze(
        [Document("exemplo", "Dados,textos;redes\nIA! dados. 123 456")]
    )

    assert [(item.term, item.frequency) for item in report.overall.keywords] == [
        ("dados", 2),
        ("ia", 1),
        ("redes", 1),
        ("textos", 1),
    ]
    assert report.overall.total_tokens == 5


def test_stopwords_are_compared_with_the_same_accent_normalization():
    report = identity_service(stopwords={"não", "é", "e"}).analyze(
        [Document("exemplo", "NÃO nao É e dados")]
    )

    assert [(item.term, item.frequency) for item in report.overall.keywords] == [("dados", 1)]
    assert report.overall.total_tokens == 5
    assert report.overall.retained_tokens == 1


def test_stemmer_receives_lowercase_accented_words():
    received = []

    def stem(word):
        received.append(word)
        return "ÁRVOR"

    service = AnalysisService(TextPreprocessor(stopwords={"e"}, stemmer=stem))
    report = service.analyze([Document("exemplo", "ÁRVORES e Árvore")])

    assert received == ["árvores", "árvore"]
    assert report.overall.keywords[0].stem == "arvor"
    assert report.overall.keywords[0].frequency == 2


def test_variants_share_frequency_and_most_frequent_form_is_displayed():
    def stem(word):
        return "estud" if word in {"estudar", "estudos"} else word

    service = AnalysisService(TextPreprocessor(stopwords=(), stemmer=stem))
    report = service.analyze([Document("exemplo", "Estudar estudos estudos tecnologia tecnologia")])

    keyword = report.overall.keywords[0]
    assert keyword.term == "estudos"
    assert keyword.stem == "estud"
    assert keyword.frequency == 3
    assert keyword.variants == ("estudar", "estudos")
    assert report.overall.retained_tokens == 5
    assert report.overall.unique_terms == 2


def test_representative_form_uses_alphabetical_tiebreaker():
    service = AnalysisService(TextPreprocessor(stopwords=(), stemmer=lambda word: "estud"))
    report = service.analyze([Document("exemplo", "estudos estudar")])

    assert report.overall.keywords[0].term == "estudar"


def test_keyword_ties_are_alphabetical_and_independent_of_input_order():
    service = identity_service()
    first = service.analyze([Document("primeiro", "banana abacate cenoura")])
    second = service.analyze([Document("segundo", "cenoura banana abacate")])

    assert [item.term for item in first.overall.keywords] == [
        "abacate",
        "banana",
        "cenoura",
    ]
    assert first.overall.keywords == second.overall.keywords


def test_top_n_limits_results_without_changing_document_statistics():
    report = identity_service().analyze([Document("exemplo", "dados dados redes textos")], top_n=1)

    assert report.top_n == 1
    assert len(report.overall.keywords) == 1
    assert report.overall.keywords[0].term == "dados"
    assert report.overall.total_tokens == 4
    assert report.overall.retained_tokens == 4
    assert report.overall.unique_terms == 3


def test_top_n_larger_than_vocabulary_returns_all_available_keywords():
    report = identity_service().analyze([Document("exemplo", "dados redes")], top_n=100)

    assert len(report.overall.keywords) == 2


@pytest.mark.parametrize("top_n", [0, -1, 1.5, "2", True, None])
def test_invalid_top_n_is_rejected(top_n):
    with pytest.raises(ValueError):
        identity_service().analyze([Document("exemplo", "dados")], top_n=top_n)


def test_multiple_documents_keep_individual_and_consolidated_counts():
    report = identity_service().analyze(
        [
            Document("primeiro.txt", "dados dados redes"),
            Document("segundo.txt", "redes textos dados"),
        ]
    )

    assert {item.term: item.frequency for item in report.overall.keywords} == {
        "dados": 3,
        "redes": 2,
        "textos": 1,
    }
    first, second = report.documents
    assert first.document.name == "primeiro.txt"
    assert second.document.name == "segundo.txt"
    assert {item.term: item.frequency for item in first.ranking.keywords} == {
        "dados": 2,
        "redes": 1,
    }
    assert {item.term: item.frequency for item in second.ranking.keywords} == {
        "dados": 1,
        "redes": 1,
        "textos": 1,
    }
    assert report.overall.total_tokens == sum(
        item.ranking.total_tokens for item in report.documents
    )


def test_no_remaining_terms_returns_an_explainable_empty_result():
    report = identity_service(stopwords={"e", "de"}).analyze([Document("exemplo", "e, de! 123")])

    assert report.overall.keywords == ()
    assert report.overall.total_tokens == 2
    assert report.overall.retained_tokens == 0
    assert report.overall.unique_terms == 0
    assert report.documents[0].trace.filtered_tokens == ()
    assert report.documents[0].trace.stems == ()


def test_trace_explains_normalization_filtering_and_grouping():
    service = AnalysisService(TextPreprocessor(stopwords={"e"}, stemmer=lambda word: "químic"))
    report = service.analyze([Document("exemplo", "QUÍMICO,e químicas!")])
    trace = report.documents[0].trace

    assert trace.lowercase_text == "químico,e químicas!"
    assert trace.normalized_text == "quimico,e quimicas!"
    assert trace.tokens == ("quimico", "e", "quimicas")
    assert trace.filtered_tokens == ("quimico", "quimicas")
    assert trace.stems == ("quimic", "quimic")


def test_default_portuguese_stemmer_groups_real_inflections_offline():
    report = AnalysisService().analyze(
        [Document("exemplo", "O químico e as químicas estudam química.")]
    )

    chemistry = next(item for item in report.overall.keywords if item.stem == "quimic")
    assert chemistry.frequency == 3
    assert chemistry.variants == ("química", "químicas", "químico")
    assert all(item.term not in {"o", "e", "as"} for item in report.overall.keywords)


def test_empty_document_collection_is_rejected():
    with pytest.raises(ValueError):
        identity_service().analyze([])
