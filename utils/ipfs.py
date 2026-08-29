# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
"""
IPFS data reference utilities for Proof of Inference.

Provides functions to validate IPFS hashes and fetch data from IPFS gateways.
Privacy is preserved by storing only the hash on-chain, not the actual data.
"""

import hashlib
import re


def is_valid_ipfs_hash(hash_str: str) -> bool:
    """Validate IPFS CID (Content Identifier) format.
    
    Supports:
    - CIDv0: Qm... (base58btc, 46 chars)
    - CIDv1: bafy... (base32, varies)
    """
    if not hash_str or not isinstance(hash_str, str):
        return False
    
    hash_str = hash_str.strip()
    
    # CIDv0: starts with Qm, 46 chars, base58btc
    if hash_str.startswith("Qm") and len(hash_str) == 46:
        # Check base58btc characters
        base58_chars = set("123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz")
        return all(c in base58_chars for c in hash_str)
    
    # CIDv1: starts with bafy, bafk, etc.
    if hash_str.startswith("ba") and len(hash_str) >= 50:
        # Base32 characters
        base32_chars = set("abcdefghijklmnopqrstuvwxyz234567")
        return all(c in base32_chars for c in hash_str[2:])
    
    return False


def compute_data_hash(data: bytes) -> str:
    """Compute SHA-256 hash of data for integrity verification."""
    return hashlib.sha256(data).hexdigest()


def get_ipfs_gateway_url(ipfs_hash: str, gateway: str = "https://ipfs.io/ipfs/") -> str:
    """Get full IPFS gateway URL from hash."""
    return f"{gateway}{ipfs_hash}"


def extract_ipfs_hash(url: str) -> str:
    """Extract IPFS hash from various URL formats.
    
    Supports:
    - ipfs://Qm...
    - https://ipfs.io/ipfs/Qm...
    - https://gateway.pinata.cloud/ipfs/Qm...
    - Raw hash: Qm...
    """
    if not url or not isinstance(url, str):
        return ""
    
    url = url.strip()
    
    # Raw hash
    if is_valid_ipfs_hash(url):
        return url
    
    # ipfs:// protocol
    if url.startswith("ipfs://"):
        hash_part = url[7:]  # Remove "ipfs://"
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


def validate_data_reference(ref_type: str, ref_value: str) -> dict:
    """Validate a data reference (IPFS hash or URL).
    
    Returns:
        dict with 'valid', 'hash', 'type', 'error' keys
    """
    if not ref_value:
        return {
            "valid": False,
            "hash": "",
            "type": ref_type,
            "error": "Empty reference"
        }
    
    # Try to extract IPFS hash
    ipfs_hash = extract_ipfs_hash(ref_value)
    
    if ipfs_hash:
        return {
            "valid": True,
            "hash": ipfs_hash,
            "type": "ipfs",
            "error": ""
        }
    
    # If it looks like a hash but failed validation
    if ref_value.startswith("Qm") or ref_value.startswith("ba"):
        return {
            "valid": False,
            "hash": "",
            "type": ref_type,
            "error": "Invalid IPFS hash format"
        }
    
    # Accept other reference types (URLs, etc.)
    if ref_value.startswith("http://") or ref_value.startswith("https://"):
        return {
            "valid": True,
            "hash": ref_value,
            "type": "url",
            "error": ""
        }
    
    return {
        "valid": False,
        "hash": "",
        "type": ref_type,
        "error": "Unsupported reference type"
    }
