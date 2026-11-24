"""Normalização, filtragem de stopwords e stemming do português."""

import unicodedata
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path

from nltk.stem import SnowballStemmer

from .models import Document, PreprocessingTrace


def _without_accents(text: str) -> str:
    """Remove marcas diacríticas sem depender de tabelas externas."""

    return "".join(
        character
        for character in unicodedata.normalize("NFD", text)
        if unicodedata.category(character) != "Mn"
    )


def _separate_words(text: str) -> str:
    """Substitui pontuação, números e símbolos por separadores."""

    return "".join(
        character if character.isalpha() or character.isspace() else " " for character in text
    )


def _load_stopwords() -> tuple[str, ...]:
    """Lê a lista local, mantendo a análise disponível sem downloads."""

    path = Path(__file__).parent / "data" / "stopwords_pt.txt"
    return tuple(
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    )


@dataclass(frozen=True, slots=True)
class ProcessedDocument:
    """Rastro visível e pares de radical e variante para a contagem."""

    trace: PreprocessingTrace
    occurrences: tuple[tuple[str, str], ...]


class TextPreprocessor:
    """Executa o pipeline com stopwords e stemmer substituíveis."""

    def __init__(
        self,
        stopwords: Iterable[str] | None = None,
        stemmer: Callable[[str], str] | None = None,
    ) -> None:
        words = _load_stopwords() if stopwords is None else stopwords
        self._stopwords = frozenset(
            _without_accents(unicodedata.normalize("NFC", word.lower().strip()))
            for word in words
            if word.strip()
        )
        self._stemmer = SnowballStemmer("portuguese").stem if stemmer is None else stemmer

    def process(self, document: Document) -> ProcessedDocument:
        """Processa sem perder os acentos exigidos pelo stemmer português.

        O rastro apresenta as formas normalizadas. Em paralelo, a grafia
        original em minúsculas é conservada para o stemming e a exibição.
        Somente sequências de letras são consideradas palavras.
        """

        lowercase_text = unicodedata.normalize("NFC", document.text.lower())
        normalized_text = _without_accents(lowercase_text)
        separated_text = _separate_words(normalized_text)

        original_tokens = _separate_words(lowercase_text).split()
        tokens: list[str] = []
        filtered_tokens: list[str] = []
        stems: list[str] = []
        occurrences: list[tuple[str, str]] = []

        for original_token in original_tokens:
            token = _without_accents(original_token)
            tokens.append(token)
            if token in self._stopwords:
                continue
            filtered_tokens.append(token)
            stem = _without_accents(self._stemmer(original_token).lower())
            stems.append(stem)
            occurrences.append((stem, original_token))

        trace = PreprocessingTrace(
            lowercase_text=lowercase_text,
            normalized_text=normalized_text,
            separated_text=separated_text,
            tokens=tuple(tokens),
            filtered_tokens=tuple(filtered_tokens),
            stems=tuple(stems),
        )
        return ProcessedDocument(trace=trace, occurrences=tuple(occurrences))
