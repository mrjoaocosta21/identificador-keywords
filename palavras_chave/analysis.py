"""Coordenação da análise e rankings individuais e consolidados."""

from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence

from .inputs import InputError, validate_documents
from .models import (
    AnalysisReport,
    Document,
    DocumentAnalysis,
    Keyword,
    Ranking,
)
from .processing import TextPreprocessor


def _build_ranking(
    groups: Mapping[str, Counter[str]],
    total_tokens: int,
    retained_tokens: int,
    top_n: int,
) -> Ranking:
    """Escolhe representantes e ordena sem limitar as métricas globais."""

    keywords = []
    for stem, variants in groups.items():
        representative = min(variants, key=lambda term: (-variants[term], term))
        keywords.append(
            Keyword(
                term=representative,
                stem=stem,
                frequency=sum(variants.values()),
                variants=tuple(sorted(variants)),
            )
        )
    keywords.sort(key=lambda keyword: (-keyword.frequency, keyword.term))
    return Ranking(
        keywords=tuple(keywords[:top_n]),
        total_tokens=total_tokens,
        retained_tokens=retained_tokens,
        unique_terms=len(groups),
    )


class AnalysisService:
    """Orquestra o processamento sem conhecer o mecanismo da interface."""

    def __init__(self, preprocessor: TextPreprocessor | None = None) -> None:
        self._preprocessor = TextPreprocessor() if preprocessor is None else preprocessor

    def analyze(self, documents: Sequence[Document], top_n: int = 10) -> AnalysisReport:
        """Analisa uma coleção e reaproveita suas contagens no consolidado."""

        if isinstance(top_n, bool) or not isinstance(top_n, int) or top_n <= 0:
            raise InputError("A quantidade de palavras-chave deve ser um inteiro positivo.")
        validate_documents(documents)

        all_groups: defaultdict[str, Counter[str]] = defaultdict(Counter)
        document_analyses: list[DocumentAnalysis] = []
        total_tokens = 0
        retained_tokens = 0

        for document in documents:
            processed = self._preprocessor.process(document)
            groups: defaultdict[str, Counter[str]] = defaultdict(Counter)
            for stem, variant in processed.occurrences:
                groups[stem][variant] += 1
                all_groups[stem][variant] += 1

            trace = processed.trace
            document_total = len(trace.tokens)
            document_retained = len(trace.filtered_tokens)
            ranking = _build_ranking(groups, document_total, document_retained, top_n)
            document_analyses.append(
                DocumentAnalysis(document=document, trace=trace, ranking=ranking)
            )
            total_tokens += document_total
            retained_tokens += document_retained

        return AnalysisReport(
            overall=_build_ranking(all_groups, total_tokens, retained_tokens, top_n),
            documents=tuple(document_analyses),
            top_n=top_n,
        )
