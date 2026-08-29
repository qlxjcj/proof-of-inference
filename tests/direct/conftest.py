"""Shared fixtures for Proof of Inference direct-mode tests."""

import json
import os
import pytest

CONTRACT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "proof_of_inference.py",
)

TASK_DESC = "Analyze this image and determine if it shows a genuine luxury watch"
TASK_CATEGORY = "VERIFICATION"
DATA_HASH = "QmXnnyufdzAWL5CqZ2RnSNgPbvCc1ALT73s6epPrRnZ1Xy"

VERDICT_HIGH_CONSENSUS = json.dumps({
    "consensus_result": "The image shows a genuine Rolex Submariner with correct engravings",
    "consensus_confidence": 92,
    "winner": "",
    "agreement_level": "HIGH",
    "reasoning": "All miners agreed on authenticity indicators",
})

VERDICT_MEDIUM_CONSENSUS = json.dumps({
    "consensus_result": "Likely genuine but some details are unclear",
    "consensus_confidence": 65,
    "winner": "",
    "agreement_level": "MEDIUM",
    "reasoning": "Miners partially agreed, some disagreement on细节",
})

VERDICT_LOW_CONSENSUS = json.dumps({
    "consensus_result": "Cannot determine authenticity with confidence",
    "consensus_confidence": 30,
    "winner": "",
    "agreement_level": "LOW",
    "reasoning": "Miners strongly disagreed on the verdict",
})

LLM_PATTERN = r".*AI inference verification engine.*"


def make_verdict(template, winner):
    v = json.loads(template)
    v["winner"] = winner
    return json.dumps(v)


@pytest.fixture
def poi(direct_vm, direct_deploy):
    vm = direct_vm
    vm.mock_llm(LLM_PATTERN, VERDICT_HIGH_CONSENSUS)
    c = direct_deploy(CONTRACT)
    return vm, c


@pytest.fixture
def direct_alice(direct_vm):
    return direct_vm.sender


@pytest.fixture
def direct_bob(direct_vm):
    from genlayer import Address
    return Address("0x" + "bb" * 20)


@pytest.fixture
def direct_charlie(direct_vm):
    from genlayer import Address
    return Address("0x" + "cc" * 20)
