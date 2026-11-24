"""Estruturas imutáveis compartilhadas pelo núcleo e pela interface."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Document:
    """Documento de entrada com nome de identificação e texto original."""

    name: str
    text: str


@dataclass(frozen=True, slots=True)
class PreprocessingTrace:
    """Resultados intermediários que tornam a análise inspecionável."""

    lowercase_text: str
    normalized_text: str
    separated_text: str
    tokens: tuple[str, ...]
    filtered_tokens: tuple[str, ...]
    stems: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class Keyword:
    """Família de termos; a frequência soma todas as suas variantes."""

    term: str
    stem: str
    frequency: int
    variants: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class Ranking:
    """Ranking limitado a N itens, com métricas sobre toda a entrada."""

    keywords: tuple[Keyword, ...]
    total_tokens: int
    retained_tokens: int
    unique_terms: int


@dataclass(frozen=True, slots=True)
class DocumentAnalysis:
    """Análise individual que conserva o documento e seu processamento."""

    document: Document
    trace: PreprocessingTrace
    ranking: Ranking


@dataclass(frozen=True, slots=True)
class AnalysisReport:
    """Resultado consolidado e resultados individuais de uma análise."""

    overall: Ranking
    documents: tuple[DocumentAnalysis, ...]
    top_n: int
