"""Representações do ranking para a interface e para planilhas."""

import csv
from io import StringIO

from palavras_chave.models import Ranking

COLUMNS = ("Posição", "Termo", "Radical", "Frequência do grupo", "Variantes")


def ranking_rows(ranking: Ranking) -> list[dict[str, str | int]]:
    """Converte o ranking em registros, preservando a ordem da análise."""
    return [
        dict(
            zip(
                COLUMNS,
                (position, item.term, item.stem, item.frequency, ", ".join(item.variants)),
                strict=True,
            )
        )
        for position, item in enumerate(ranking.keywords, start=1)
    ]


def ranking_csv(ranking: Ranking) -> bytes:
    """Exporta CSV com separador local e BOM para preservar acentos em planilhas."""
    output = StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=COLUMNS, delimiter=";")
    writer.writeheader()
    writer.writerows(ranking_rows(ranking))
    return output.getvalue().encode("utf-8-sig")
