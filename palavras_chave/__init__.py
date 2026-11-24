"""API pública do identificador estatístico de palavras-chave."""

from .analysis import AnalysisService
from .inputs import (
    MAX_DOCUMENTS,
    MAX_FILE_BYTES,
    MAX_TOTAL_CHARACTERS,
    InputError,
    decode_text_file,
    validate_documents,
)
from .models import (
    AnalysisReport,
    Document,
    DocumentAnalysis,
    Keyword,
    PreprocessingTrace,
    Ranking,
)
from .processing import TextPreprocessor

__all__ = [
    "AnalysisReport",
    "AnalysisService",
    "Document",
    "DocumentAnalysis",
    "InputError",
    "Keyword",
    "MAX_DOCUMENTS",
    "MAX_FILE_BYTES",
    "MAX_TOTAL_CHARACTERS",
    "PreprocessingTrace",
    "Ranking",
    "TextPreprocessor",
    "decode_text_file",
    "validate_documents",
]
