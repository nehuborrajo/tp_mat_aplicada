"""Modelo y parsers: solo datos ficticios, sin escritura de secretos."""

import json
from dataclasses import asdict, replace

import pytest

from vaultlab.crypto.encryption import EncryptedData
from vaultlab.crypto.key_derivation import MIN_ITERATIONS, KdfParameters
from vaultlab.domain.models import Credential, Vault
from vaultlab.storage.format import (
    VaultFormatError,
    decode_envelope,
    decode_vault,
    encode_envelope,
    encode_vault,
)


def sample_credential() -> Credential:
    return Credential(
        id="12345678-1234-5678-1234-567812345678", name="Cuenta ficticia ñ",
        username="alumno@example.test", password="CLAVE-DEMO-NO-REAL",
        url="https://example.test", notes='Texto ficticio con \\ y " y [ ] { }',
        created_at="2026-10-25T12:00:00Z", updated_at="2026-10-25T12:00:00Z",
    )


def sample_packet() -> EncryptedData:
    return EncryptedData(KdfParameters(b"S" * 16, MIN_ITERATIONS), b"N" * 12, b"C" * 20)


def test_model_json_roundtrip_and_private_repr() -> None:
    credential = sample_credential()
    vault = Vault((credential,))
    assert decode_vault(encode_vault(vault)) == vault
    assert decode_vault(encode_vault(Vault())) == Vault()
    assert credential.password not in repr(credential)
    assert credential.name not in repr(vault)


@pytest.mark.parametrize(("field", "value"), [
    ("id", "no-es-uuid"), ("id", None), ("name", " "), ("name", "N" * 257),
    ("username", "U" * 513), ("password", ""), ("password", "P" * 1025),
    ("url", "U" * 2049), ("notes", "N" * 4097), ("notes", None),
    ("notes", "\ud800"), ("created_at", "2026-10-25"),
    ("created_at", "2026-10-25T12:00:00"),
    ("updated_at", "2026-10-24T12:00:00Z"),
    ("updated_at", "2026-10-25T12:00:00+03:00"),
])
def test_invalid_credential(field: str, value: object) -> None:
    with pytest.raises(ValueError):
        replace(sample_credential(), **{field: value})


def test_invalid_vault_collections_and_versions() -> None:
    for credentials in ([sample_credential()], (None,),
                        (sample_credential(), sample_credential()), (sample_credential(),) * 10001):
        with pytest.raises(ValueError):
            Vault(credentials)
    for version in (True, 2, "1"):
        with pytest.raises(ValueError):
            Vault(schema_version=version)


def test_envelope_roundtrip() -> None:
    packet = sample_packet()
    assert decode_envelope(encode_envelope(packet)) == packet
    assert set(json.loads(encode_envelope(packet))) == {
        "format", "version", "kdf", "cipher", "ciphertext_b64",
    }


@pytest.mark.parametrize(("path", "value"), [
    (("format",), "otro"), (("version",), 2), (("version",), True),
    (("version",), "1"), (("extra",), "no"), (("cipher", "extra"), 0),
    (("kdf", "name"), "Argon2"), (("cipher", "name"), "AES-ECB"),
    (("kdf", "iterations"), 0), (("kdf", "iterations"), True),
    (("kdf", "iterations"), 5_000_001), (("kdf", "iterations"), "600000"),
    (("kdf", "salt_b64"), "Uw=="), (("kdf", "salt_b64"), "!" * 24),
    (("kdf", "salt_b64"), "U" * 100),
    (("cipher", "nonce_b64"), "Tg=="), (("ciphertext_b64",), "Qw=="),
    (("ciphertext_b64",), None), (("ciphertext_b64",), "é"),
    # Mismos bytes decodificados, bits sobrantes no canónicos.
    (("ciphertext_b64",), "Q0NDQ0NDQ0NDQ0NDQ0NDQ0NDQ0N="),
])
def test_invalid_envelopes(path: tuple[str, ...], value: object) -> None:
    root = json.loads(encode_envelope(sample_packet()))
    target = root
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    with pytest.raises(VaultFormatError):
        decode_envelope(json.dumps(root).encode())


@pytest.mark.parametrize("raw", [
    b"", b"{", b"[]", b"null", b"\xff", b'{"version":1,"version":1}',
    b'{"a":NaN}', b'{"a":1.2}', b'{"a":12345678901}',
    b"[" * 9 + b"0" + b"]" * 9,
])
def test_malformed_json(raw: bytes) -> None:
    for decoder in (decode_envelope, decode_vault):
        with pytest.raises(VaultFormatError):
            decoder(raw)


@pytest.mark.parametrize("mutation", ["schema", "extra", "duplicate", "field", "type"])
def test_invalid_inner_schema(mutation: str) -> None:
    root = asdict(Vault((sample_credential(),)))
    root["credentials"] = list(root["credentials"])
    if mutation == "schema":
        root["schema_version"] = True
    elif mutation == "extra":
        root["extra"] = "no"
    elif mutation == "duplicate":
        root["credentials"] *= 2
    elif mutation == "field":
        root["credentials"][0]["extra"] = "no"
    else:
        root["credentials"] = {}
    with pytest.raises(VaultFormatError):
        decode_vault(json.dumps(root).encode())
