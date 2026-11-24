"""Verifica limites e mensagens de erro na entrada dos documentos."""

import pytest

from palavras_chave import Document
from palavras_chave.inputs import (
    MAX_DOCUMENTS,
    MAX_FILE_BYTES,
    MAX_TOTAL_CHARACTERS,
    InputError,
    decode_text_file,
    validate_documents,
)


def test_utf8_file_preserves_text_and_accepts_uppercase_extension():
    document = decode_text_file("Texto.TXT", "Ciência e informação.".encode())

    assert document.name == "Texto.TXT"
    assert document.text == "Ciência e informação."


def test_utf8_bom_is_removed_before_processing():
    document = decode_text_file("texto.txt", b"\xef\xbb\xbfdados")

    assert document.text == "dados"


@pytest.mark.parametrize(
    ("name", "content"),
    [
        ("texto.pdf", b"dados"),
        ("texto.txt.exe", b"dados"),
        ("texto", b"dados"),
        ("", b"dados"),
        ("texto.txt", b""),
        ("texto.txt", b" \n\t"),
        ("texto.txt", b"\x00dados"),
        ("texto.txt", b"a\xffb"),
    ],
)
def test_invalid_uploaded_document_is_rejected(name, content):
    with pytest.raises(InputError) as error:
        decode_text_file(name, content)

    assert str(error.value).strip()


def test_file_larger_than_byte_limit_is_rejected():
    with pytest.raises(InputError):
        decode_text_file("grande.txt", b"a" * (MAX_FILE_BYTES + 1))


def test_file_at_byte_limit_is_accepted():
    document = decode_text_file("limite.txt", b"a" * MAX_FILE_BYTES)

    assert len(document.text) == MAX_FILE_BYTES


def test_document_count_limit_is_enforced():
    documents = [Document(f"texto-{index}", "dados") for index in range(MAX_DOCUMENTS)]
    validate_documents(documents)

    with pytest.raises(InputError):
        validate_documents([*documents, Document("extra", "dados")])


def test_total_text_limit_is_enforced_across_documents():
    first_size = MAX_TOTAL_CHARACTERS // 2
    documents = [
        Document("primeiro", "a" * first_size),
        Document("segundo", "b" * (MAX_TOTAL_CHARACTERS - first_size)),
    ]
    validate_documents(documents)

    with pytest.raises(InputError):
        validate_documents([*documents, Document("extra", "c")])


def test_document_collection_requires_at_least_one_document():
    with pytest.raises(InputError):
        validate_documents([])


@pytest.mark.parametrize("name", ["", " \n\t"])
def test_document_name_cannot_be_blank(name):
    with pytest.raises(InputError):
        validate_documents([Document(name, "dados")])


def test_text_with_only_stopwords_or_punctuation_is_valid_input():
    validate_documents([Document("stopwords", "e de o"), Document("sinais", "...!")])
