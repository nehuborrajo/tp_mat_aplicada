"""Políticas, supuestos de entropía y heurística reproducibles."""

import itertools
import math

import pytest

from vaultlab.services import password_generator
from vaultlab.services.laboratory import run_experiment
from vaultlab.services.password_generator import CATEGORIES, GeneratorPolicy, generate_password
from vaultlab.services.strength import estimate_strength


@pytest.mark.parametrize("length", [4, 20, 128])
@pytest.mark.parametrize(
    "categories", [combo for n in range(1, 5) for combo in itertools.combinations(CATEGORIES, n)]
)
def test_all_category_combinations(length, categories):
    policy = GeneratorPolicy(length, categories)
    result = generate_password(policy)
    assert len(result) == length
    assert set(result) <= set(policy.alphabet)
    assert policy.entropy == length * math.log2(len(policy.alphabet))


@pytest.mark.parametrize(
    "policy",
    [
        GeneratorPolicy(3),
        GeneratorPolicy(129),
        GeneratorPolicy(True),
        GeneratorPolicy(4.5),
        GeneratorPolicy(categories=()),
        GeneratorPolicy(categories=("desconocida",)),
    ],
)
def test_invalid_policy(policy):
    with pytest.raises(ValueError):
        generate_password(policy)


def test_csprng_called_per_character_without_category_bias(monkeypatch):
    calls = []

    def choice(alphabet):
        calls.append(alphabet)
        return alphabet[0]

    monkeypatch.setattr(password_generator.secrets, "choice", choice)
    policy = GeneratorPolicy(4, ("Dígitos", "Dígitos"))
    assert generate_password(policy) == "0000"
    assert calls == ["0123456789"] * 4
    assert policy.entropy == 4 * math.log2(10)


@pytest.mark.parametrize(
    "password", ["", "123456", "password1234567890", "a" * 30, "abcdEJEMPLO-MUY-LARGO"]
)
def test_weak_patterns(password):
    assert estimate_strength(password).score <= 1


def test_strength_is_labeled_heuristic():
    result = estimate_strength("Ejemplo!Ficticio-9Xz?")
    assert result.score == 4
    assert "No mide entropía real" in result.explanation


def test_lab_computes_and_never_returns_key_or_master(capsys):
    report = run_experiment()
    assert report.roundtrip and report.tamper_rejected and report.pbkdf2_verified
    assert "U₁" in report.text and "GHASH" in report.text and "log₂" in report.text
    assert "MAESTRA-FICTICIA" not in report.text
    assert set(vars(report)) == {"text", "roundtrip", "tamper_rejected", "pbkdf2_verified", "steps"}
    assert len(report.steps) == 4
    assert "01011010 ⊕ 00111100 = 01100110" in " ".join(report.steps[0].operations)
    assert "exactamente un bit" in " ".join(report.steps[3].operations)
    assert capsys.readouterr().out == ""


def test_second_lab_example_has_real_computed_trace():
    report = run_experiment(1)
    assert "OTRA-CUENTA-FICTICIA" in " ".join(report.steps[1].operations)
    assert "20 + 16 = 36 bytes" in " ".join(report.steps[1].operations)
    assert report.roundtrip and report.tamper_rejected and report.pbkdf2_verified
    assert "MAESTRA-FICTICIA" not in repr(report)


@pytest.mark.parametrize("example", [-1, 2, True, "0"])
def test_invalid_demo_never_becomes_user_secret_input(example):
    with pytest.raises(ValueError):
        run_experiment(example)
