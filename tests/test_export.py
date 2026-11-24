"""Garante que os resultados exportados preservam os valores da análise."""

import codecs
import csv
from io import StringIO

from palavras_chave import AnalysisService, Document, Ranking
from palavras_chave.export import COLUMNS, ranking_csv, ranking_rows


def test_rows_preserve_order_frequency_and_group_variants():
    report = AnalysisService().analyze([Document("exemplo", "química químicas química redes")])
    rows = ranking_rows(report.overall)

    assert [row["Posição"] for row in rows] == [1, 2]
    assert rows[0] == {
        "Posição": 1,
        "Termo": "química",
        "Radical": "quimic",
        "Frequência do grupo": 3,
        "Variantes": "química, químicas",
    }


def test_csv_round_trip_preserves_accents_delimiter_and_group_frequency():
    ranking = (
        AnalysisService().analyze([Document("exemplo", "química químicas química redes")]).overall
    )
    exported = ranking_csv(ranking)

    assert exported.startswith(codecs.BOM_UTF8)
    decoded = exported.decode("utf-8-sig")
    assert decoded.splitlines()[0] == ";".join(COLUMNS)
    reader = csv.DictReader(StringIO(decoded), delimiter=";")
    rows = list(reader)
    assert reader.fieldnames == list(COLUMNS)
    assert rows[0]["Termo"] == "química"
    assert rows[0]["Frequência do grupo"] == "3"
    assert rows[0]["Variantes"] == "química, químicas"
    assert len(rows) == len(ranking.keywords)


def test_empty_ranking_exports_only_column_headers():
    ranking = Ranking(keywords=(), total_tokens=3, retained_tokens=0, unique_terms=0)

    assert ranking_rows(ranking) == []
    decoded = ranking_csv(ranking).decode("utf-8-sig")
    assert decoded.splitlines() == [";".join(COLUMNS)]
    assert list(csv.DictReader(StringIO(decoded), delimiter=";")) == []
