# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
"""
Proof of Inference - AI Mining Protocol

Token Economics:
- Total Supply: 1,000,000,000 POI
- Distribution:
  - 5% Developers (50M)
  - 10% Task Creators (100M)
  - 20% Miners (200M)
  - 65% Pool Rewards (650M)

Block Reward Distribution (1:2 ratio):
- Task Creators: 1/3
- Miners: 2/3

Miner Distribution:
- Winner: 50% of miner reward
- Participants: 30% of miner reward
- Validators: 20% of miner reward
"""

import json
import re
from dataclasses import dataclass
from genlayer import *


def is_valid_ipfs_hash(hash_str: str) -> bool:
    """Validate IPFS CID format."""
    if not hash_str or not isinstance(hash_str, str):
        return False
    hash_str = hash_str.strip()
    if hash_str.startswith("Qm") and len(hash_str) == 46:
        base58_chars = set("123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz")
        return all(c in base58_chars for c in hash_str)
    if hash_str.startswith("ba") and len(hash_str) >= 50:
        base32_chars = set("abcdefghijklmnopqrstuvwxyz234567")
        return all(c in base32_chars for c in hash_str[2:])
    return False


def extract_ipfs_hash(url: str) -> str:
    """Extract IPFS hash from URL."""
    if not url or not isinstance(url, str):
        return ""
    url = url.strip()
    if is_valid_ipfs_hash(url):
        return url
    if url.startswith("ipfs://"):
        hash_part = url[7:]
        if is_valid_ipfs_hash(hash_part):
            return hash_part
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
    data_ref_type: str
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
    active_miners: TreeMap[str, str]
    task_count: u256
    total_mined: u256
    total_miners: u256
    
    # POI Token reference
    poi_token: str

    CATEGORIES = ("VERIFICATION", "DIAGNOSIS", "ANALYSIS", "CLASSIFICATION", "OTHER")
    STATUSES = ("OPEN", "MINING", "VERIFYING", "COMPLETED", "FAILED")

    def __init__(self):
        self.total_mined = 0
        self.total_miners = 0
        self.poi_token = ""

    def _get_validator_count(self) -> int:
        """Dynamic validator count based on total miners"""
        miners = self.total_miners
        if miners < 10:
            return 3
        elif miners < 30:
            return 5
        elif miners < 100:
            return 7
        elif miners < 300:
            return 10
        else:
            return 15

    def _get_max_miners_per_task(self) -> int:
        """Max miners per task based on network size"""
        miners = self.total_miners
        if miners < 10:
            return 10
        elif miners < 30:
            return 20
        elif miners < 100:
            return 30
        elif miners < 300:
            return 50
        else:
            return 100

    def _distribute_block_reward(self, creator: str, winner: str, participants: list):
        """Distribute block reward to creator and miners"""
        if self.poi_token == "":
            return
        
        # In production, this would call the POI token contract
        # to mint block rewards
        pass

    @gl.public.write
    def set_poi_token(self, token_address: str):
        """Set POI token contract address (owner only)"""
        if self.poi_token != "":
            raise gl.vm.UserError("POI token already set")
        self.poi_token = token_address

    @gl.public.write
    def submit_task(self, description: str, category: str, data_hash: str, deadline_hours: int = 24) -> str:
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
        
        self.task_count += 1
        task_id = str(self.task_count)

        task = Task(
            task_id=task_id,
            creator=sender.as_hex,
            description=description.strip(),
            category=category,
            data_hash=data_hash.strip(),
            data_ref_type=data_ref_type,
            status="OPEN",
            result="",
            winner="",
            miner_count=0,
            deadline=str(deadline_hours),
        )
        self.tasks[task_id] = json.dumps(task.__dict__)
        
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
        
        # Check if task is full (first-come-first-served)
        max_miners = self._get_max_miners_per_task()
        current_miners = task.get("miner_count", 0)
        if current_miners >= max_miners:
            raise gl.vm.UserError("Task is full, no more miners needed")

        submission = MinerSubmission(
            task_id=task_id,
            miner=sender.as_hex,
            result=result.strip(),
            confidence=confidence,
            timestamp="0",
        )
        self.submissions[sub_key] = json.dumps(submission.__dict__)

        task["miner_count"] = current_miners + 1
        if task["status"] == "OPEN":
            task["status"] = "MINING"
        self.tasks[task_id] = json.dumps(task)
        
        # Track unique miners
        if not self.active_miners.get(sender.as_hex, ""):
            self.active_miners[sender.as_hex] = "active"
            self.total_miners += 1

    @gl.public.write
    def verify_task(self, task_id: str):
        task_id = str(task_id)
        task = json.loads(self.tasks.get(task_id, "{}"))
        if not task:
            raise gl.vm.UserError("Task not found")
        if task["status"] != "MINING":
            raise gl.vm.UserError("Task not in mining state")
        
        # Check if enough miners submitted
        min_miners = self._get_validator_count()
        if task.get("miner_count", 0) < min_miners:
            raise gl.vm.UserError(f"Need at least {min_miners} miners to verify")

        task["status"] = "VERIFYING"
        self.tasks[task_id] = json.dumps(task)

        def run_verification() -> dict:
            submissions = []
            for key, val in self.submissions.items():
                if key.startswith(f"{task_id}:"):
                    sub = json.loads(val)
                    submissions.append(sub)

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
        
        # Handle tie: if no clear winner, select based on reputation and confidence
        if not winner:
            # Get all submissions for this task
            task_submissions = []
            for key, val in self.submissions.items():
                if key.startswith(f"{task_id}:"):
                    sub = json.loads(val)
                    task_submissions.append(sub)
            
            if not task_submissions:
                task["status"] = "FAILED"
                self.tasks[task_id] = json.dumps(task)
                raise gl.vm.UserError("No submissions found")
            
            # Sort by: 1) reputation score (desc), 2) confidence (desc)
            def get_tie_breaker(sub):
                miner_addr = sub["miner"]
                profile = json.loads(self.miner_profiles.get(miner_addr, "{}"))
                reputation = profile.get("reputation_score", 50)
                confidence = sub.get("confidence", 0)
                return (-reputation, -confidence)  # Negative for descending sort
            
            task_submissions.sort(key=get_tie_breaker)
            winner = task_submissions[0]["miner"]
            
            # Mark as tie-break winner in verdict
            verdict["tie_break"] = True
            verdict["tie_break_reason"] = "Selected based on reputation and confidence"

        task["status"] = "COMPLETED"
        task["result"] = verdict.get("consensus_result", "")
        task["winner"] = winner
        self.tasks[task_id] = json.dumps(task)
        self.total_mined += 1

        # Get participants list
        participants = []
        for key, val in self.submissions.items():
            if key.startswith(f"{task_id}:"):
                sub = json.loads(val)
                participants.append(sub["miner"])

        # Distribute block rewards
        self._distribute_block_reward(task["creator"], winner, participants)

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
                win_rate = profile["tasks_won"] / profile["tasks_completed"] if profile["tasks_completed"] > 0 else 0
                profile["reputation_score"] = min(100, int(win_rate * 100))
                self.miner_profiles[miner_addr] = json.dumps(profile)

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
        task["status"] = "CANCELLED"
        self.tasks[task_id] = json.dumps(task)

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
            "total_mined": self.total_mined,
            "total_miners": self.total_miners,
            "validator_count": self._get_validator_count(),
            "max_miners_per_task": self._get_max_miners_per_task(),
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
            return 50
        return profile.get("reputation_score", 50)

    @gl.public.view
    def get_data_url(self, task_id: str) -> str:
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

    @gl.public.view
    def get_reward_info(self) -> dict:
        """Get reward information"""
        return {
            "poi_token": self.poi_token,
            "validator_count": self._get_validator_count(),
            "max_miners_per_task": self._get_max_miners_per_task(),
        }
