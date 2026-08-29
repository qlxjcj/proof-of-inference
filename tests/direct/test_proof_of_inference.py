"""Direct-mode tests for Proof of Inference.

Covers the mining lifecycle: submit_task -> mine_task -> verify_task -> claim_reward.
Tests consensus mechanism, bounty distribution, and state management.

No network, no consensus: deterministic and instant.
Run: python -m pytest tests/direct/ -v   (from the project root)
"""

import json
import pytest

from conftest import (
    TASK_DESC,
    TASK_CATEGORY,
    DATA_HASH,
    VERDICT_HIGH_CONSENSUS,
    VERDICT_MEDIUM_CONSENSUS,
    LLM_PATTERN,
    make_verdict,
)

BOUNTY = "1000000000000000000"  # 1 ETH in wei


def _task(c, task_id):
    return json.loads(c.get_task(task_id))


def _submission(c, task_id, miner):
    return json.loads(c.get_submission(task_id, miner))


# ---------- submit_task ----------

def test_submit_creates_open_task(direct_vm, poi):
    vm, c = poi
    c.submit_task(TASK_DESC, TASK_CATEGORY, DATA_HASH, BOUNTY)

    assert c.get_task_count() == 1
    r = _task(c, 1)
    assert r["status"] == "OPEN"
    assert r["description"] == TASK_DESC
    assert r["category"] == TASK_CATEGORY
    assert r["data_hash"] == DATA_HASH
    assert r["creator"] is not None
    assert r["bounty"] == BOUNTY


def test_submit_rejects_short_description(direct_vm, poi):
    vm, c = poi
    with pytest.raises(Exception) as ei:
        c.submit_task("Short", TASK_CATEGORY, DATA_HASH, BOUNTY)
    assert "10" in str(ei.value)


def test_submit_rejects_invalid_category(direct_vm, poi):
    vm, c = poi
    with pytest.raises(Exception) as ei:
        c.submit_task(TASK_DESC, "INVALID", DATA_HASH, BOUNTY)
    assert "category" in str(ei.value).lower()


def test_submit_rejects_missing_data_hash(direct_vm, poi):
    vm, c = poi
    with pytest.raises(Exception) as ei:
        c.submit_task(TASK_DESC, TASK_CATEGORY, "short", BOUNTY)
    assert "hash" in str(ei.value).lower()


def test_submit_rejects_zero_bounty(direct_vm, poi):
    vm, c = poi
    with pytest.raises(Exception) as ei:
        c.submit_task(TASK_DESC, TASK_CATEGORY, DATA_HASH, "0")
    assert "bounty" in str(ei.value).lower()


# ---------- mine_task ----------

def test_mine_submits_result(direct_vm, poi):
    vm, c = poi
    c.submit_task(TASK_DESC, TASK_CATEGORY, DATA_HASH, BOUNTY)
    c.mine_task(1, "Genuine luxury watch detected", 85)

    r = _task(c, 1)
    assert r["status"] == "MINING"
    assert r["miner_count"] == 1


def test_mine_rejects_nonexistent_task(direct_vm, poi):
    vm, c = poi
    with pytest.raises(Exception) as ei:
        c.mine_task(99, "Some result", 50)
    assert "not found" in str(ei.value).lower()


def test_mine_rejects_completed_task(direct_vm, poi, direct_bob):
    vm, c = poi
    c.submit_task(TASK_DESC, TASK_CATEGORY, DATA_HASH, BOUNTY)
    c.mine_task(1, "Result A", 80)

    vm.sender = direct_bob
    c.mine_task(1, "Result B", 75)

    vm.clear_mocks()
    vm.mock_llm(LLM_PATTERN, make_verdict(VERDICT_HIGH_CONSENSUS, "0xbBbBBBBbbBBBbbbBbbBbbbbBBbBbbbbBbBbbBBbB"))
    c.verify_task(1)

    with pytest.raises(Exception) as ei:
        vm.sender = direct_bob
        c.mine_task(1, "Result C", 90)
    assert "not available" in str(ei.value).lower()


def test_mine_rejects_short_result(direct_vm, poi):
    vm, c = poi
    c.submit_task(TASK_DESC, TASK_CATEGORY, DATA_HASH, BOUNTY)
    with pytest.raises(Exception) as ei:
        c.mine_task(1, "Hi", 50)
    assert "short" in str(ei.value).lower()


def test_mine_rejects_invalid_confidence(direct_vm, poi):
    vm, c = poi
    c.submit_task(TASK_DESC, TASK_CATEGORY, DATA_HASH, BOUNTY)
    with pytest.raises(Exception) as ei:
        c.mine_task(1, "Valid result here", 150)
    assert "confidence" in str(ei.value).lower()


def test_mine_rejects_duplicate_submission(direct_vm, poi):
    vm, c = poi
    c.submit_task(TASK_DESC, TASK_CATEGORY, DATA_HASH, BOUNTY)
    c.mine_task(1, "First submission", 80)
    with pytest.raises(Exception) as ei:
        c.mine_task(1, "Second submission", 90)
    assert "already" in str(ei.value).lower()


# ---------- verify_task ----------

def test_verify_completes_task(direct_vm, poi, direct_bob):
    vm, c = poi
    c.submit_task(TASK_DESC, TASK_CATEGORY, DATA_HASH, BOUNTY)
    c.mine_task(1, "Result from Alice", 85)

    vm.sender = direct_bob
    c.mine_task(1, "Result from Bob", 90)

    vm.clear_mocks()
    vm.mock_llm(LLM_PATTERN, make_verdict(VERDICT_HIGH_CONSENSUS, "0xbBbBBBBbbBBBbbbBbbBbbbbBBbBbbbbBbBbbBBbB"))
    c.verify_task(1)

    r = _task(c, 1)
    assert r["status"] == "COMPLETED"
    assert r["winner"] is not None
    assert r["result"] != ""


def test_verify_rejects_nonexistent_task(direct_vm, poi):
    vm, c = poi
    with pytest.raises(Exception) as ei:
        c.verify_task(99)
    assert "not found" in str(ei.value).lower()


def test_verify_rejects_non_mining_task(direct_vm, poi):
    vm, c = poi
    c.submit_task(TASK_DESC, TASK_CATEGORY, DATA_HASH, BOUNTY)
    with pytest.raises(Exception) as ei:
        c.verify_task(1)
    assert "mining" in str(ei.value).lower()


def test_verify_rejects_no_submissions(direct_vm, poi):
    vm, c = poi
    c.submit_task(TASK_DESC, TASK_CATEGORY, DATA_HASH, BOUNTY)
    # Force status to MINING without submissions
    r = _task(c, 1)
    assert r["miner_count"] == 0
    with pytest.raises(Exception) as ei:
        c.verify_task(1)
    assert "mining" in str(ei.value).lower()


# ---------- claim_reward ----------

def test_claim_reward_transfers_bounty(direct_vm, poi, direct_bob):
    vm, c = poi
    c.submit_task(TASK_DESC, TASK_CATEGORY, DATA_HASH, BOUNTY)
    c.mine_task(1, "Alice result", 85)

    vm.sender = direct_bob
    c.mine_task(1, "Bob result", 90)

    vm.clear_mocks()
    vm.mock_llm(LLM_PATTERN, make_verdict(VERDICT_HIGH_CONSENSUS, "0xbBbBBBBbbBBBbbbBbbBbbbbBBbBbbbbBbBbbBBbB"))
    c.verify_task(1)

    vm.sender = direct_bob
    c.claim_reward(1)

    r = _task(c, 1)
    assert r["bounty"] == "0"


def test_claim_reward_rejects_non_winner(direct_vm, poi, direct_bob):
    vm, c = poi
    original_sender = vm.sender
    c.submit_task(TASK_DESC, TASK_CATEGORY, DATA_HASH, BOUNTY)
    c.mine_task(1, "Alice result", 85)

    vm.sender = direct_bob
    c.mine_task(1, "Bob result", 90)

    vm.clear_mocks()
    vm.mock_llm(LLM_PATTERN, make_verdict(VERDICT_HIGH_CONSENSUS, "0xbBbBBBBbbBBBbbbBbbBbbbbBBbBbbbbBbBbbBBbB"))
    c.verify_task(1)

    # Reset sender to original (Alice) who is NOT the winner
    vm.sender = original_sender
    with pytest.raises(Exception) as ei:
        c.claim_reward(1)
    assert "winner" in str(ei.value).lower()


def test_claim_reward_rejects_incomplete_task(direct_vm, poi):
    vm, c = poi
    c.submit_task(TASK_DESC, TASK_CATEGORY, DATA_HASH, BOUNTY)
    with pytest.raises(Exception) as ei:
        c.claim_reward(1)
    assert "completed" in str(ei.value).lower()


# ---------- get_task_submissions ----------

def test_get_task_submissions(direct_vm, poi, direct_bob, direct_charlie):
    vm, c = poi
    c.submit_task(TASK_DESC, TASK_CATEGORY, DATA_HASH, BOUNTY)
    c.mine_task(1, "Alice result", 85)

    vm.sender = direct_bob
    c.mine_task(1, "Bob result", 90)

    vm.sender = direct_charlie
    c.mine_task(1, "Charlie result", 70)

    subs = c.get_task_submissions(1)
    assert len(subs) == 3


# ---------- stats ----------

def test_stats_tracks_tasks(direct_vm, poi, direct_bob):
    vm, c = poi
    c.submit_task(TASK_DESC, TASK_CATEGORY, DATA_HASH, BOUNTY)
    c.mine_task(1, "Result A", 85)

    vm.sender = direct_bob
    c.mine_task(1, "Result B", 90)

    vm.clear_mocks()
    vm.mock_llm(LLM_PATTERN, make_verdict(VERDICT_HIGH_CONSENSUS, "0xbBbBBBBbbBBBbbbBbbBbbbbBBbBbbbbBbBbbBBbB"))
    c.verify_task(1)

    s = c.get_stats()
    assert s["total_tasks"] == 1
    assert s["completed_tasks"] == 1
    assert s["total_mined"] == 1


def test_stats_counts_open_tasks(direct_vm, poi):
    vm, c = poi
    c.submit_task(TASK_DESC, TASK_CATEGORY, DATA_HASH, BOUNTY)
    c.submit_task("Another task description for testing purposes", "ANALYSIS", DATA_HASH, BOUNTY)

    s = c.get_stats()
    assert s["total_tasks"] == 2
    assert s["open_tasks"] == 2
    assert s["completed_tasks"] == 0


# ---------- miner reputation ----------

def test_miner_reputation_updates_on_completion(direct_vm, poi, direct_bob):
    vm, c = poi
    from genlayer import Address
    # Default sender is Bob, so we use a different address for Alice
    alice_addr = Address("0x" + "aa" * 20)
    vm.sender = alice_addr
    c.submit_task(TASK_DESC, TASK_CATEGORY, DATA_HASH, BOUNTY)
    c.mine_task(1, "Alice result", 85)

    vm.sender = direct_bob
    c.mine_task(1, "Bob result", 90)

    vm.clear_mocks()
    vm.mock_llm(LLM_PATTERN, make_verdict(VERDICT_HIGH_CONSENSUS, "0xbBbBBBBbbBBBbbbBbbBbbbbBBbBbbbbBbBbbBBbB"))
    c.verify_task(1)

    # Bob won, so his reputation should increase
    bob_profile = json.loads(c.get_miner_profile("0xbBbBBBBbbBBBbbbBbbBbbbbBBbBbbbbBbBbbBBbB"))
    assert bob_profile["tasks_completed"] == 1
    assert bob_profile["tasks_won"] == 1
    assert bob_profile["reputation_score"] == 100

    # Alice lost, so her reputation should be lower
    alice_profile = json.loads(c.get_miner_profile(alice_addr.as_hex))
    assert alice_profile["tasks_completed"] == 1
    assert alice_profile["tasks_won"] == 0
    assert alice_profile["reputation_score"] == 0


def test_miner_reputation_default_for_new(direct_vm, poi):
    vm, c = poi
    # New miner should have default reputation of 50
    rep = c.get_miner_reputation("0x" + "aa" * 20)
    assert rep == 50


def test_miner_reputation_multiple_tasks(direct_vm, poi, direct_bob, direct_charlie):
    vm, c = poi
    alice_addr = "0x" + "dc18aa3db8bc91a6e390a35e7d0811246ff3ab01"  # Default sender
    
    # Task 1: Alice wins
    c.submit_task(TASK_DESC, TASK_CATEGORY, DATA_HASH, BOUNTY)
    c.mine_task(1, "Alice result 1", 85)
    vm.sender = direct_bob
    c.mine_task(1, "Bob result 1", 90)
    vm.clear_mocks()
    vm.mock_llm(LLM_PATTERN, make_verdict(VERDICT_HIGH_CONSENSUS, alice_addr))
    c.verify_task(1)
    
    # Task 2: Bob wins
    vm.sender = vm.sender  # Keep Bob as sender
    c.submit_task("Another task description for testing", "ANALYSIS", DATA_HASH, BOUNTY)
    c.mine_task(2, "Bob result 2", 95)
    vm.sender = direct_charlie
    c.mine_task(2, "Charlie result 2", 80)
    vm.clear_mocks()
    vm.mock_llm(LLM_PATTERN, make_verdict(VERDICT_HIGH_CONSENSUS, "0xbBbBBBBbbBBBbbbBbbBbbbbBBbBbbbbBbBbbBBbB"))
    c.verify_task(2)
    
    # Bob: 2 completed, 1 won = 50% win rate
    bob_profile = json.loads(c.get_miner_profile("0xbBbBBBBbbBBBbbbBbbBbbbbBBbBbbbbBbBbbBBbB"))
    assert bob_profile["tasks_completed"] == 2
    assert bob_profile["tasks_won"] == 1
    assert bob_profile["reputation_score"] == 50


# ---------- cancel_task ----------

def test_cancel_task_refunds_bounty(direct_vm, poi):
    vm, c = poi
    c.submit_task(TASK_DESC, TASK_CATEGORY, DATA_HASH, BOUNTY)
    c.cancel_task(1)
    
    r = _task(c, 1)
    assert r["status"] == "CANCELLED"
    assert r["bounty"] == "0"


def test_cancel_task_rejects_non_creator(direct_vm, poi, direct_bob):
    vm, c = poi
    c.submit_task(TASK_DESC, TASK_CATEGORY, DATA_HASH, BOUNTY)
    
    vm.sender = direct_bob
    with pytest.raises(Exception) as ei:
        c.cancel_task(1)
    assert "creator" in str(ei.value).lower()


def test_cancel_task_rejects_completed(direct_vm, poi, direct_bob):
    vm, c = poi
    c.submit_task(TASK_DESC, TASK_CATEGORY, DATA_HASH, BOUNTY)
    c.mine_task(1, "Result A", 85)

    vm.sender = direct_bob
    c.mine_task(1, "Result B", 90)

    vm.clear_mocks()
    vm.mock_llm(LLM_PATTERN, make_verdict(VERDICT_HIGH_CONSENSUS, "0xbBbBBBBbbBBBbbbBbbBbbbbBBbBbbbbBbBbbBBbB"))
    c.verify_task(1)

    # Bob (not creator) tries to cancel - should fail
    with pytest.raises(Exception) as ei:
        c.cancel_task(1)
    assert "creator" in str(ei.value).lower()


def test_cancel_task_with_mining_status(direct_vm, poi, direct_bob):
    vm, c = poi
    c.submit_task(TASK_DESC, TASK_CATEGORY, DATA_HASH, BOUNTY)
    c.mine_task(1, "Result A", 85)
    
    # Can cancel even with submissions (status is MINING)
    c.cancel_task(1)
    r = _task(c, 1)
    assert r["status"] == "CANCELLED"


# ---------- IPFS data reference ----------

def test_submit_with_ipfs_hash(direct_vm, poi):
    vm, c = poi
    ipfs_hash = "QmXnnyufdzAWL5CqZ2RnSNgPbvCc1ALT73s6epPrRnZ1Xy"
    c.submit_task(TASK_DESC, TASK_CATEGORY, ipfs_hash, BOUNTY)
    
    r = _task(c, 1)
    assert r["data_hash"] == ipfs_hash
    assert r["data_ref_type"] == "ipfs"


def test_submit_with_ipfs_url(direct_vm, poi):
    vm, c = poi
    ipfs_url = "https://ipfs.io/ipfs/QmXnnyufdzAWL5CqZ2RnSNgPbvCc1ALT73s6epPrRnZ1Xy"
    c.submit_task(TASK_DESC, TASK_CATEGORY, ipfs_url, BOUNTY)
    
    r = _task(c, 1)
    assert r["data_hash"] == "QmXnnyufdzAWL5CqZ2RnSNgPbvCc1ALT73s6epPrRnZ1Xy"
    assert r["data_ref_type"] == "ipfs"


def test_submit_with_ipfs_protocol(direct_vm, poi):
    vm, c = poi
    ipfs_url = "ipfs://QmXnnyufdzAWL5CqZ2RnSNgPbvCc1ALT73s6epPrRnZ1Xy"
    c.submit_task(TASK_DESC, TASK_CATEGORY, ipfs_url, BOUNTY)
    
    r = _task(c, 1)
    assert r["data_hash"] == "QmXnnyufdzAWL5CqZ2RnSNgPbvCc1ALT73s6epPrRnZ1Xy"
    assert r["data_ref_type"] == "ipfs"


def test_submit_with_http_url(direct_vm, poi):
    vm, c = poi
    http_url = "https://example.com/data.json"
    c.submit_task(TASK_DESC, TASK_CATEGORY, http_url, BOUNTY)
    
    r = _task(c, 1)
    assert r["data_hash"] == http_url
    assert r["data_ref_type"] == "url"


def test_submit_with_plain_hash(direct_vm, poi):
    vm, c = poi
    plain_hash = "abc123def456"
    c.submit_task(TASK_DESC, TASK_CATEGORY, plain_hash, BOUNTY)
    
    r = _task(c, 1)
    assert r["data_hash"] == plain_hash
    assert r["data_ref_type"] == "hash"


def test_get_data_url_ipfs(direct_vm, poi):
    vm, c = poi
    ipfs_hash = "QmXnnyufdzAWL5CqZ2RnSNgPbvCc1ALT73s6epPrRnZ1Xy"
    c.submit_task(TASK_DESC, TASK_CATEGORY, ipfs_hash, BOUNTY)
    
    url = c.get_data_url(1)
    assert url == f"https://ipfs.io/ipfs/{ipfs_hash}"


def test_get_data_url_http(direct_vm, poi):
    vm, c = poi
    http_url = "https://example.com/data.json"
    c.submit_task(TASK_DESC, TASK_CATEGORY, http_url, BOUNTY)
    
    url = c.get_data_url(1)
    assert url == http_url
