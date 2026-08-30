# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
"""
POI Token - Proof of Inference ERC-20 Token

Token Economics:
- Total Supply: 1,000,000,000 POI (10 billion)
- Distribution:
  - 50% Mining Rewards (5B)
  - 30% Task Creator Rewards (3B)
  - 10% Team (1B, locked)
  - 10% Ecosystem (1B)

Reward Mechanism:
- Task Creator: 1000 POI per task
- Winner Miner: 500 POI
- Participant Miner: 100 POI
- Validator: 50 POI each
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
    mining_pool: u256
    creator_pool: u256
    team_pool: u256
    ecosystem_pool: u256
    
    # Distribution
    mining_distributed: u256
    creator_distributed: u256
    team_distributed: u256
    ecosystem_distributed: u256
    
    # Owner
    owner: str

    def __init__(self):
        self.name = "Proof of Inference"
        self.symbol = "POI"
        self.decimals = 18
        self.total_supply = 0
        self.max_supply = 10000000000 * (10 ** 18)  # 10 billion
        
        # Pool allocations (in wei)
        self.mining_pool = 5000000000 * (10 ** 18)   # 50%
        self.creator_pool = 3000000000 * (10 ** 18)  # 30%
        self.team_pool = 1000000000 * (10 ** 18)     # 10%
        self.ecosystem_pool = 1000000000 * (10 ** 18) # 10%
        
        # Distributed amounts
        self.mining_distributed = 0
        self.creator_distributed = 0
        self.team_distributed = 0
        self.ecosystem_distributed = 0
        
        # Owner is the contract deployer
        self.owner = gl.message.sender_address.as_hex

    def _mint(self, to: str, amount: u256):
        """Internal mint function"""
        if self.total_supply + amount > self.max_supply:
            raise gl.vm.UserError("Max supply exceeded")
        
        current_balance = self.balances.get(to, 0)
        self.balances[to] = current_balance + amount
        self.total_supply += amount

    @gl.public.write
    def mint_mining_reward(self, to: str, amount: u256) -> bool:
        """Mint mining rewards (called by main contract)"""
        if gl.message.sender_address.as_hex != self.owner:
            raise gl.vm.UserError("Only owner can mint")
        
        if self.mining_distributed + amount > self.mining_pool:
            raise gl.vm.UserError("Mining pool exhausted")
        
        self._mint(to, amount)
        self.mining_distributed += amount
        return True

    @gl.public.write
    def mint_creator_reward(self, to: str, amount: u256) -> bool:
        """Mint creator rewards (called by main contract)"""
        if gl.message.sender_address.as_hex != self.owner:
            raise gl.vm.UserError("Only owner can mint")
        
        if self.creator_distributed + amount > self.creator_pool:
            raise gl.vm.UserError("Creator pool exhausted")
        
        self._mint(to, amount)
        self.creator_distributed += amount
        return True

    @gl.public.write
    def mint_team_reward(self, to: str, amount: u256) -> bool:
        """Mint team rewards (owner only)"""
        if gl.message.sender_address.as_hex != self.owner:
            raise gl.vm.UserError("Only owner can mint")
        
        if self.team_distributed + amount > self.team_pool:
            raise gl.vm.UserError("Team pool exhausted")
        
        self._mint(to, amount)
        self.team_distributed += amount
        return True

    @gl.public.write
    def mint_ecosystem_reward(self, to: str, amount: u256) -> bool:
        """Mint ecosystem rewards (owner only)"""
        if gl.message.sender_address.as_hex != self.owner:
            raise gl.vm.UserError("Only owner can mint")
        
        if self.ecosystem_distributed + amount > self.ecosystem_pool:
            raise gl.vm.UserError("Ecosystem pool exhausted")
        
        self._mint(to, amount)
        self.ecosystem_distributed += amount
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
            "mining_pool": str(self.mining_pool),
            "mining_distributed": str(self.mining_distributed),
            "mining_remaining": str(self.mining_pool - self.mining_distributed),
            "creator_pool": str(self.creator_pool),
            "creator_distributed": str(self.creator_distributed),
            "creator_remaining": str(self.creator_pool - self.creator_distributed),
            "team_pool": str(self.team_pool),
            "team_distributed": str(self.team_distributed),
            "team_remaining": str(self.team_pool - self.team_distributed),
            "ecosystem_pool": str(self.ecosystem_pool),
            "ecosystem_distributed": str(self.ecosystem_distributed),
            "ecosystem_remaining": str(self.ecosystem_pool - self.ecosystem_distributed),
        }

    @gl.public.write
    def transfer_ownership(self, new_owner: str) -> bool:
        """Transfer contract ownership"""
        if gl.message.sender_address.as_hex != self.owner:
            raise gl.vm.UserError("Only owner can transfer")
        self.owner = new_owner
        return True
