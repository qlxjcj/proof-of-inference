# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
import json
import re
from dataclasses import dataclass
from genlayer import *


def is_valid_ipfs_hash(hash_str: str) -> bool:
    """Validate IPFS CID (Content Identifier) format."""
    if not hash_str or not isinstance(hash_str, str):
        return False
    hash_str = hash_str.strip()
    # CIDv0: starts with Qm, 46 chars, base58btc
    if hash_str.startswith("Qm") and len(hash_str) == 46:
        base58_chars = set("123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz")
        return all(c in base58_chars for c in hash_str)
    # CIDv1: starts with bafy, bafk, etc.
    if hash_str.startswith("ba") and len(hash_str) >= 50:
        base32_chars = set("abcdefghijklmnopqrstuvwxyz234567")
        return all(c in base32_chars for c in hash_str[2:])
    return False


def extract_ipfs_hash(url: str) -> str:
    """Extract IPFS hash from various URL formats."""
    if not url or not isinstance(url, str):
        return ""
    url = url.strip()
    # Raw hash
    if is_valid_ipfs_hash(url):
        return url
    # ipfs:// protocol
    if url.startswith("ipfs://"):
        hash_part = url[7:]
        if is_valid_ipfs_hash(hash_part):
            return hash_part
    # Gateway URLs
    patterns = [
        r"/ipfs/(Qm[a-zA-Z0-9]{44})",
        r"/ipfs/(ba[a-z2-7]{50,})",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match and is_valid_ipfs_hash(match.group(1)):
            return match.group(1)
    return ""


@allow_storage
@dataclass
class Task:
    task_id: str
    creator: str
    description: str
    category: str
    data_hash: str
    data_ref_type: str  # "ipfs", "url", "hash"
    bounty: str
    status: str
    result: str
    winner: str
    miner_count: int
    deadline: str


@allow_storage
@dataclass
class MinerSubmission:
    task_id: str
    miner: str
    result: str
    confidence: int
    timestamp: str


@allow_storage
@dataclass
class MinerProfile:
    address: str
    tasks_completed: int
    tasks_won: int
    total_confidence: int
    reputation_score: int
    last_active: str


class ProofOfInference(gl.Contract):
    tasks: TreeMap[str, str]
    submissions: TreeMap[str, str]
    miner_profiles: TreeMap[str, str]
    task_count: u256
    total_bounty: u256
    total_mined: u256

    CATEGORIES = ("VERIFICATION", "DIAGNOSIS", "ANALYSIS", "CLASSIFICATION", "OTHER")
    STATUSES = ("OPEN", "MINING", "VERIFYING", "COMPLETED", "FAILED")

    def __init__(self):
        self.total_bounty = 0
        self.total_mined = 0

    @gl.public.write
    def submit_task(self, description: str, category: str, data_hash: str, bounty_amount: str = "0", deadline_hours: int = 24) -> str:
        if not description or len(description.strip()) < 10:
            raise gl.vm.UserError("Description must be at least 10 characters")
        if category not in self.CATEGORIES:
            raise gl.vm.UserError(f"Category must be one of {self.CATEGORIES}")
        if not data_hash or len(data_hash) < 8:
            raise gl.vm.UserError("Data hash required for verification")
        if deadline_hours < 1 or deadline_hours > 168:
            raise gl.vm.UserError("Deadline must be 1-168 hours")
        
        # Determine data reference type
        data_ref_type = "hash"
        ipfs_hash = extract_ipfs_hash(data_hash)
        if ipfs_hash:
            data_ref_type = "ipfs"
            data_hash = ipfs_hash
        elif data_hash.startswith("http://") or data_hash.startswith("https://"):
            data_ref_type = "url"
        
        sender = gl.message.sender_address
        bounty = int(bounty_amount) if bounty_amount != "0" else gl.message.value
        if bounty <= 0:
            raise gl.vm.UserError("Bounty required to incentivize miners")

        self.task_count += 1
        task_id = str(self.task_count)

        task = Task(
            task_id=task_id,
            creator=sender.as_hex,
            description=description.strip(),
            category=category,
            data_hash=data_hash.strip(),
            data_ref_type=data_ref_type,
            bounty=str(bounty),
            status="OPEN",
            result="",
            winner="",
            miner_count=0,
            deadline=str(deadline_hours),
        )
        self.tasks[task_id] = json.dumps(task.__dict__)
        self.total_bounty += bounty
        return task_id

    @gl.public.write
    def mine_task(self, task_id: str, result: str, confidence: int):
        task_id = str(task_id)
        task = json.loads(self.tasks.get(task_id, "{}"))
        if not task:
            raise gl.vm.UserError("Task not found")
        if task["status"] not in ("OPEN", "MINING"):
            raise gl.vm.UserError("Task not available for mining")
        if not result or len(result.strip()) < 5:
            raise gl.vm.UserError("Result too short")
        if confidence < 0 or confidence > 100:
            raise gl.vm.UserError("Confidence must be 0-100")

        sender = gl.message.sender_address
        sub_key = f"{task_id}:{sender.as_hex}"
        if self.submissions.get(sub_key, ""):
            raise gl.vm.UserError("Already submitted for this task")

        submission = MinerSubmission(
            task_id=task_id,
            miner=sender.as_hex,
            result=result.strip(),
            confidence=confidence,
            timestamp="0",
        )
        self.submissions[sub_key] = json.dumps(submission.__dict__)

        task["miner_count"] = task.get("miner_count", 0) + 1
        if task["status"] == "OPEN":
            task["status"] = "MINING"
        self.tasks[task_id] = json.dumps(task)

    @gl.public.write
    def verify_task(self, task_id: str):
        task_id = str(task_id)
        task = json.loads(self.tasks.get(task_id, "{}"))
        if not task:
            raise gl.vm.UserError("Task not found")
        if task["status"] != "MINING":
            raise gl.vm.UserError("Task not in mining state")
        if task.get("miner_count", 0) < 1:
            raise gl.vm.UserError("No submissions to verify")

        task["status"] = "VERIFYING"
        self.tasks[task_id] = json.dumps(task)

        def run_verification() -> dict:
            submissions = []
            for key, val in self.submissions.items():
                if key.startswith(f"{task_id}:"):
                    sub = json.loads(val)
                    submissions.append(sub)

            # Get data reference info
            data_hash = task.get("data_hash", "")
            data_ref_type = task.get("data_ref_type", "hash")
            data_url = ""
            if data_ref_type == "ipfs":
                data_url = f"https://ipfs.io/ipfs/{data_hash}"
            elif data_ref_type == "url":
                data_url = data_hash

            task_prompt = f"""
You are an AI inference verification engine. Multiple miners have submitted
inference results for a task. Evaluate the results for consistency and quality.

TASK: {task['description']}
CATEGORY: {task['category']}
DATA REFERENCE: {data_hash}
DATA TYPE: {data_ref_type}
DATA URL: {data_url}

MINER SUBMISSIONS:
{json.dumps(submissions, indent=2)}

Analyze all submissions. Determine:
1. Which result is most likely correct based on consensus
2. The confidence level of the consensus
3. Whether miners agree or disagree

Respond ONLY in JSON:
{{
    "consensus_result": str,
    "consensus_confidence": int,
    "winner": str (address of best miner),
    "agreement_level": "HIGH" | "MEDIUM" | "LOW",
    "reasoning": str
}}
"""
            result = gl.nondet.exec_prompt(task_prompt, response_format="json")
            if isinstance(result, str):
                result = json.loads(result.replace("```json", "").replace("```", ""))
            return result

        principle = (
            "Two results are equivalent if consensus_result matches exactly, "
            "consensus_confidence values differ by at most 10 points, "
            "winner is the same address, and agreement_level matches exactly. "
            "reasoning wording may differ."
        )
        verdict = gl.eq_principle.prompt_comparative(run_verification, principle)

        if not isinstance(verdict, dict):
            task["status"] = "FAILED"
            self.tasks[task_id] = json.dumps(task)
            raise gl.vm.UserError("Verification failed")

        winner = verdict.get("winner", "")
        if not winner:
            task["status"] = "FAILED"
            self.tasks[task_id] = json.dumps(task)
            raise gl.vm.UserError("No winner determined")

        task["status"] = "COMPLETED"
        task["result"] = verdict.get("consensus_result", "")
        task["winner"] = winner
        self.tasks[task_id] = json.dumps(task)
        self.total_mined += 1

        # Update miner profiles
        for key, val in self.submissions.items():
            if key.startswith(f"{task_id}:"):
                sub = json.loads(val)
                miner_addr = sub["miner"]
                profile = json.loads(self.miner_profiles.get(miner_addr, "{}"))
                if not profile:
                    profile = {
                        "address": miner_addr,
                        "tasks_completed": 0,
                        "tasks_won": 0,
                        "total_confidence": 0,
                        "reputation_score": 50,
                        "last_active": "0",
                    }
                profile["tasks_completed"] = profile.get("tasks_completed", 0) + 1
                profile["total_confidence"] = profile.get("total_confidence", 0) + sub["confidence"]
                if miner_addr == winner:
                    profile["tasks_won"] = profile.get("tasks_won", 0) + 1
                # Reputation: win_rate * 100, capped at 100
                win_rate = profile["tasks_won"] / profile["tasks_completed"] if profile["tasks_completed"] > 0 else 0
                profile["reputation_score"] = min(100, int(win_rate * 100))
                self.miner_profiles[miner_addr] = json.dumps(profile)

    def _send_value(self, recipient: Address, amount: u256):
        @gl.evm.contract_interface
        class _Recipient:
            class View:
                pass
            class Write:
                pass
        _Recipient(recipient).emit_transfer(value=amount)

    @gl.public.write
    def claim_reward(self, task_id: str):
        task_id = str(task_id)
        task = json.loads(self.tasks.get(task_id, "{}"))
        if not task:
            raise gl.vm.UserError("Task not found")
        if task["status"] != "COMPLETED":
            raise gl.vm.UserError("Task not completed")
        sender = gl.message.sender_address
        if task["winner"] != sender.as_hex:
            raise gl.vm.UserError("Not the winner")
        bounty = int(task["bounty"])
        if bounty <= 0:
            raise gl.vm.UserError("No bounty to claim")
        task["bounty"] = "0"
        self.tasks[task_id] = json.dumps(task)
        self.total_bounty -= bounty
        self._send_value(sender, u256(bounty))

    @gl.public.write
    def cancel_task(self, task_id: str):
        task_id = str(task_id)
        task = json.loads(self.tasks.get(task_id, "{}"))
        if not task:
            raise gl.vm.UserError("Task not found")
        sender = gl.message.sender_address
        if task["creator"] != sender.as_hex:
            raise gl.vm.UserError("Only creator can cancel")
        if task["status"] not in ("OPEN", "MINING"):
            raise gl.vm.UserError("Task cannot be cancelled")
        bounty = int(task["bounty"])
        if bounty <= 0:
            raise gl.vm.UserError("No bounty to refund")
        task["status"] = "CANCELLED"
        task["bounty"] = "0"
        self.tasks[task_id] = json.dumps(task)
        self.total_bounty -= bounty
        self._send_value(sender, u256(bounty))

    @gl.public.view
    def get_task(self, task_id: str) -> str:
        return self.tasks.get(str(task_id), "{}")

    @gl.public.view
    def get_submission(self, task_id: str, miner: str) -> str:
        key = f"{task_id}:{miner}"
        return self.submissions.get(key, "{}")

    @gl.public.view
    def get_task_count(self) -> int:
        return self.task_count

    @gl.public.view
    def get_stats(self) -> dict:
        open_tasks = 0
        mining_tasks = 0
        completed_tasks = 0
        for val in self.tasks.values():
            task = json.loads(val)
            status = task.get("status", "")
            if status == "OPEN":
                open_tasks += 1
            elif status in ("MINING", "VERIFYING"):
                mining_tasks += 1
            elif status == "COMPLETED":
                completed_tasks += 1
        return {
            "total_tasks": self.task_count,
            "open_tasks": open_tasks,
            "mining_tasks": mining_tasks,
            "completed_tasks": completed_tasks,
            "total_bounty": str(self.total_bounty),
            "total_mined": self.total_mined,
        }

    @gl.public.view
    def get_task_submissions(self, task_id: str) -> list:
        result = []
        prefix = f"{task_id}:"
        for key, val in self.submissions.items():
            if key.startswith(prefix):
                result.append(json.loads(val))
        return result

    @gl.public.view
    def get_miner_profile(self, miner_address: str) -> str:
        return self.miner_profiles.get(miner_address, "{}")

    @gl.public.view
    def get_miner_reputation(self, miner_address: str) -> int:
        profile = json.loads(self.miner_profiles.get(miner_address, "{}"))
        if not profile:
            return 50  # Default reputation for new miners
        return profile.get("reputation_score", 50)

    @gl.public.view
    def get_data_url(self, task_id: str) -> str:
        """Get the full URL for task data based on reference type."""
        task = json.loads(self.tasks.get(str(task_id), "{}"))
        if not task:
            return ""
        data_hash = task.get("data_hash", "")
        ref_type = task.get("data_ref_type", "hash")
        if ref_type == "ipfs":
            return f"https://ipfs.io/ipfs/{data_hash}"
        elif ref_type == "url":
            return data_hash
        return data_hash
