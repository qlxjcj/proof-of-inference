# Proof of Inference

**AI Mining Protocol for the Agentic Economy**

Mine by doing useful AI work, not wasteful hash calculations.

## Overview

Proof of Inference is a mining protocol where miners earn by completing AI inference tasks instead of computing useless hashes. Users post tasks with ETH bounties, miners compete to run AI inference, and five independent validators verify results through consensus.

## How It Works

```
User posts task + bounty
        ↓
Miners compete (AI inference)
        ↓
5 validators reach consensus
        ↓
Winner gets paid
```

## Key Features

- **Miner Reputation System** - Tracks win rate, confidence scores, tasks completed
- **IPFS Data References** - Privacy-preserving data handling (Qm..., bafy..., ipfs://)
- **Task Lifecycle** - With deadlines and cancellation support
- **Bounty Incentives** - Economic rewards for quality work
- **Consensus Verification** - Using GenLayer's AI primitives

## Deployed Contract

| Item | Value |
|------|-------|
| Network | testnet_bradbury |
| Address | `0x15b351d1E9D3A6EC609CdF65d911dB32685bE1e3` |
| Explorer | [View on Explorer](https://explorer-bradbury.genlayer.com/address/0x15b351d1E9D3A6EC609CdF65d911dB32685bE1e3) |
| Tests | 35/35 passing |

## Smart Contract Functions

### Write Functions
- `submit_task(description, category, data_hash, bounty_amount, deadline_hours)` - Post a task with bounty
- `mine_task(task_id, result, confidence)` - Submit mining result
- `verify_task(task_id)` - Trigger AI consensus verification
- `claim_reward(task_id)` - Winner claims bounty
- `cancel_task(task_id)` - Creator cancels task (refund)

### View Functions
- `get_task(task_id)` - Get task details
- `get_stats()` - Get contract statistics
- `get_miner_profile(address)` - Get miner profile
- `get_miner_reputation(address)` - Get reputation score
- `get_data_url(task_id)` - Get IPFS/URL for task data

## Quick Start

### Run Tests
```bash
python -m pytest tests/direct/ -v
```

### Deploy Contract
```bash
python scripts/deploy.py
```

### Test on Testnet
```bash
python scripts/testnet_test.py
```

## Project Structure

```
proof-of-inference/
├── proof_of_inference.py    # Main smart contract
├── index.html               # Frontend interface
├── gltest.config.yaml       # Network configuration
├── deployment.json          # Deployment info
├── DEMO.md                  # Demo script
├── scripts/
│   ├── deploy.py            # Deployment script
│   └── testnet_test.py      # Testnet tests
├── tests/
│   └── direct/
│       ├── conftest.py      # Test fixtures
│       └── test_proof_of_inference.py
└── utils/
    └── ipfs.py              # IPFS utilities
```

## Use Cases

| Scenario | Input | Output | Privacy |
|----------|-------|--------|---------|
| Luxury Verification | Product images | Authentic/Counterfeit | Serial not public |
| Medical Diagnosis | Patient data | Diagnosis | Patient info protected |
| Legal Review | Contract files | Compliance status | Business secrets safe |
| Content Moderation | Articles/Videos | Violation detection | Source protected |

## Built For

**Agent Tank Hackathon** (Sep 3-17, 2026)
- Theme: Agentic Economy
- Prize: 5% of GenLayer Points

## License

MIT
