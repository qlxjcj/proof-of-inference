# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
"""
POI Token - Proof of Inference ERC-20 Token

Token Economics:
- Total Supply: 1,000,000,000 POI (1 billion)
- Distribution:
  - 5% Developers (50M)
  - 10% Task Creators (100M)
  - 20% Miners (200M)
  - 65% Pool Rewards (650M)

Pool Release Mechanism:
- First 5000 blocks: 65M POI
- Every 5000 blocks: reduce 10%
- Until pool exhausted

Block Reward Distribution (1:2 ratio):
- Task Creators: 1/3
- Miners: 2/3
"""

import json
from dataclasses import dataclass
from genlayer import *


@allow_storage
@dataclass
class Balance:
    address: str
    amount: u256


@allow_storage
@dataclass
class Allowance:
    owner: str
    spender: str
    amount: u256


class POIToken(gl.Contract):
    # ERC-20 Basic Info
    name: str
    symbol: str
    decimals: u256
    total_supply: u256
    
    # Balances and Allowances
    balances: TreeMap[str, u256]
    allowances: TreeMap[str, u256]
    
    # Supply Limits
    max_supply: u256
    
    # Distribution Pools
    developer_pool: u256
    creator_pool: u256
    miner_pool: u256
    reward_pool: u256
    
    # Distributed Amounts
    developer_distributed: u256
    creator_distributed: u256
    miner_distributed: u256
    reward_distributed: u256
    
    # Block Reward Mechanism
    current_block: u256
    blocks_per_phase: u256
    current_phase: u256
    base_reward_per_block: u256
    reward_decay_rate: u256  # 10% = 1000 (basis points)
    
    # Owner
    owner: str

    def __init__(self):
        self.name = "Proof of Inference"
        self.symbol = "POI"
        self.decimals = 18
        self.total_supply = 0
        self.max_supply = 1000000000 * (10 ** 18)  # 1 billion
        
        # Pool allocations (in wei)
        self.developer_pool = 50000000 * (10 ** 18)    # 5%
        self.creator_pool = 100000000 * (10 ** 18)     # 10%
        self.miner_pool = 200000000 * (10 ** 18)       # 20%
        self.reward_pool = 650000000 * (10 ** 18)      # 65%
        
        # Distributed amounts
        self.developer_distributed = 0
        self.creator_distributed = 0
        self.miner_distributed = 0
        self.reward_distributed = 0
        
        # Block reward parameters
        self.current_block = 0
        self.blocks_per_phase = 5000
        self.current_phase = 0
        self.base_reward_per_block = 13000 * (10 ** 18)  # 13,000 POI per block
        self.reward_decay_rate = 1000  # 10% in basis points (1000/10000)
        
        # Owner is the contract deployer
        self.owner = gl.message.sender_address.as_hex

    def _mint(self, to: str, amount: u256):
        """Internal mint function"""
        if self.total_supply + amount > self.max_supply:
            raise gl.vm.UserError("Max supply exceeded")
        
        current_balance = self.balances.get(to, 0)
        self.balances[to] = current_balance + amount
        self.total_supply += amount

    def _get_current_reward_per_block(self) -> u256:
        """Calculate current reward per block based on phase"""
        phase = self.current_block // self.blocks_per_phase
        if phase != self.current_phase:
            self.current_phase = phase
            # Reduce reward by 10% for each phase
            self.base_reward_per_block = self.base_reward_per_block * 9000 // 10000
        
        return self.base_reward_per_block

    @gl.public.write
    def mint_block_reward(self, creator: str, miner: str, validator_count: int) -> bool:
        """Mint block reward (called by main contract)"""
        if gl.message.sender_address.as_hex != self.owner:
            raise gl.vm.UserError("Only owner can mint")
        
        # Check if reward pool has enough
        if self.reward_distributed >= self.reward_pool:
            raise gl.vm.UserError("Reward pool exhausted")
        
        # Get current reward per block
        reward_per_block = self._get_current_reward_per_block()
        
        # Calculate distribution (1:2 ratio)
        creator_reward = reward_per_block // 3  # 1/3
        miner_reward = reward_per_block * 2 // 3  # 2/3
        
        # Check if reward pool has enough for this block
        remaining_pool = self.reward_pool - self.reward_distributed
        if reward_per_block > remaining_pool:
            reward_per_block = remaining_pool
            creator_reward = reward_per_block // 3
            miner_reward = reward_per_block * 2 // 3
        
        # Mint rewards
        self._mint(creator, creator_reward)
        self._mint(miner, miner_reward)
        
        # Update distributed amounts
        self.creator_distributed += creator_reward
        self.miner_distributed += miner_reward
        self.reward_distributed += reward_per_block
        
        # Update block counter
        self.current_block += 1
        
        return True

    @gl.public.write
    def mint_developer_reward(self, to: str, amount: u256) -> bool:
        """Mint developer rewards (owner only)"""
        if gl.message.sender_address.as_hex != self.owner:
            raise gl.vm.UserError("Only owner can mint")
        
        if self.developer_distributed + amount > self.developer_pool:
            raise gl.vm.UserError("Developer pool exhausted")
        
        self._mint(to, amount)
        self.developer_distributed += amount
        return True

    @gl.public.write
    def transfer(self, to: str, amount: u256) -> bool:
        """Transfer tokens"""
        sender = gl.message.sender_address.as_hex
        sender_balance = self.balances.get(sender, 0)
        
        if sender_balance < amount:
            raise gl.vm.UserError("Insufficient balance")
        
        self.balances[sender] = sender_balance - amount
        recipient_balance = self.balances.get(to, 0)
        self.balances[to] = recipient_balance + amount
        return True

    @gl.public.write
    def approve(self, spender: str, amount: u256) -> bool:
        """Approve spender"""
        owner = gl.message.sender_address.as_hex
        key = f"{owner}:{spender}"
        self.allowances[key] = amount
        return True

    @gl.public.write
    def transfer_from(self, from_addr: str, to: str, amount: u256) -> bool:
        """Transfer from approved amount"""
        spender = gl.message.sender_address.as_hex
        key = f"{from_addr}:{spender}"
        allowance = self.allowances.get(key, 0)
        
        if allowance < amount:
            raise gl.vm.UserError("Insufficient allowance")
        
        from_balance = self.balances.get(from_addr, 0)
        if from_balance < amount:
            raise gl.vm.UserError("Insufficient balance")
        
        self.balances[from_addr] = from_balance - amount
        self.allowances[key] = allowance - amount
        
        to_balance = self.balances.get(to, 0)
        self.balances[to] = to_balance + amount
        return True

    @gl.public.view
    def balance_of(self, address: str) -> u256:
        """Get balance of address"""
        return self.balances.get(address, 0)

    @gl.public.view
    def allowance(self, owner: str, spender: str) -> u256:
        """Get allowance"""
        key = f"{owner}:{spender}"
        return self.allowances.get(key, 0)

    @gl.public.view
    def get_name(self) -> str:
        return self.name

    @gl.public.view
    def get_symbol(self) -> str:
        return self.symbol

    @gl.public.view
    def get_decimals(self) -> u256:
        return self.decimals

    @gl.public.view
    def get_total_supply(self) -> u256:
        return self.total_supply

    @gl.public.view
    def get_max_supply(self) -> u256:
        return self.max_supply

    @gl.public.view
    def get_pools_info(self) -> dict:
        """Get pool distribution info"""
        return {
            "developer_pool": str(self.developer_pool),
            "developer_distributed": str(self.developer_distributed),
            "developer_remaining": str(self.developer_pool - self.developer_distributed),
            "creator_pool": str(self.creator_pool),
            "creator_distributed": str(self.creator_distributed),
            "creator_remaining": str(self.creator_pool - self.creator_distributed),
            "miner_pool": str(self.miner_pool),
            "miner_distributed": str(self.miner_distributed),
            "miner_remaining": str(self.miner_pool - self.miner_distributed),
            "reward_pool": str(self.reward_pool),
            "reward_distributed": str(self.reward_distributed),
            "reward_remaining": str(self.reward_pool - self.reward_distributed),
        }

    @gl.public.view
    def get_block_reward_info(self) -> dict:
        """Get block reward information"""
        current_reward = self._get_current_reward_per_block()
        return {
            "current_block": str(self.current_block),
            "current_phase": str(self.current_phase),
            "blocks_per_phase": str(self.blocks_per_phase),
            "current_reward_per_block": str(current_reward),
            "creator_reward_per_block": str(current_reward // 3),
            "miner_reward_per_block": str(current_reward * 2 // 3),
            "reward_decay_rate": str(self.reward_decay_rate),
        }

    @gl.public.write
    def transfer_ownership(self, new_owner: str) -> bool:
        """Transfer contract ownership"""
        if gl.message.sender_address.as_hex != self.owner:
            raise gl.vm.UserError("Only owner can transfer")
        self.owner = new_owner
        return True
