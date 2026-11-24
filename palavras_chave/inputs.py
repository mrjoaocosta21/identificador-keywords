"""Leitura e validação de entradas, sem dependências da interface."""

import unicodedata
from collections.abc import Sequence
from pathlib import PurePath

from .models import Document

MAX_DOCUMENTS = 20
MAX_FILE_BYTES = 1_000_000
MAX_TOTAL_CHARACTERS = 2_000_000


class InputError(ValueError):
    """Entrada inválida que pode ser explicada diretamente ao usuário."""


def _validate_text_content(text: str, name: str) -> None:
    """Rejeita caracteres de controle incompatíveis com texto simples."""

    if any(
        unicodedata.category(character) == "Cc" and character not in "\n\r\t" for character in text
    ):
        raise InputError(
            f'O documento "{name}" contém dados binários ou caracteres de '
            "controle inválidos. Utilize texto simples em UTF-8."
        )


def decode_text_file(name: str, content: bytes) -> Document:
    """Lê um arquivo .txt em UTF-8, aceitando também a marca BOM."""

    if not isinstance(name, str) or not name.strip():
        raise InputError("Informe um nome válido para o arquivo.")
    if PurePath(name).suffix.lower() != ".txt":
        raise InputError(f'O arquivo "{name}" precisa ter a extensão .txt.')
    if not isinstance(content, bytes):
        raise InputError("O conteúdo do arquivo precisa ser fornecido em bytes.")
    if len(content) > MAX_FILE_BYTES:
        raise InputError(
            f'O arquivo "{name}" excede o limite de {MAX_FILE_BYTES:,} bytes.'.replace(",", ".")
        )
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise InputError(f'Não foi possível ler "{name}". Salve o arquivo em UTF-8.') from error
    _validate_text_content(text, name)
    if not text.strip():
        raise InputError(f'O arquivo "{name}" está vazio.')
    return Document(name=name, text=text)


def validate_documents(documents: Sequence[Document]) -> None:
    """Valida quantidade, conteúdo textual e tamanho total da coleção."""

    if not isinstance(documents, Sequence) or isinstance(documents, (str, bytes)):
        raise InputError("Forneça uma coleção de documentos para análise.")
    if not documents:
        raise InputError("Adicione pelo menos um texto ou arquivo para analisar.")
    if len(documents) > MAX_DOCUMENTS:
        raise InputError(f"É possível analisar até {MAX_DOCUMENTS} documentos por vez.")

    total_characters = 0
    for document in documents:
        if not isinstance(document, Document):
            raise InputError("Todos os itens precisam ser documentos válidos.")
        if not isinstance(document.name, str) or not document.name.strip():
            raise InputError("Cada documento precisa ter um nome válido.")
        if not isinstance(document.text, str):
            raise InputError(f'O conteúdo de "{document.name}" precisa ser um texto.')
        total_characters += len(document.text)
        if total_characters > MAX_TOTAL_CHARACTERS:
            raise InputError(
                f"Os textos excedem o limite total de {MAX_TOTAL_CHARACTERS:,} caracteres.".replace(
                    ",", "."
                )
            )
        _validate_text_content(document.text, document.name)
