#!/usr/bin/env python3
"""
Test Proof of Inference contract on GenLayer testnet.
"""

import os
import sys
import json
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
os.environ["GLTEST_CONFIG"] = str(project_root / "gltest.config.yaml")


def test_contract():
    try:
        from gltest import get_contract_factory, get_gl_client
        from gltest_cli.config.general import get_general_config
        from gltest_cli.config.user import load_user_config
    except ImportError:
        print("Error: gltest not installed")
        sys.exit(1)
    
    deployment_file = project_root / "deployment.json"
    with open(deployment_file) as f:
        deployment = json.load(f)
    
    address = deployment["address"]
    network = deployment["network"]
    
    print(f"Testing contract at {address}")
    print("="*50)
    
    config = get_general_config()
    user_config = load_user_config(os.environ["GLTEST_CONFIG"])
    config.user_config = user_config
    config.plugin_config.network_name = network
    config.plugin_config.contracts_dir = Path('.')
    config.plugin_config.artifacts_dir = Path('artifacts')
    
    client = get_gl_client()
    factory = get_contract_factory(contract_file_path='proof_of_inference.py')
    contract = factory.build_contract(address)
    
    print("[OK] Contract loaded")
    
    # Test 1: Get stats
    print("\n[Test 1] Getting contract stats...")
    try:
        stats = contract.get_stats()
        print(f"  Total tasks: {stats.get('total_tasks', 'N/A')}")
        print(f"  Open tasks: {stats.get('open_tasks', 'N/A')}")
        print(f"  Mining tasks: {stats.get('mining_tasks', 'N/A')}")
        print(f"  Completed tasks: {stats.get('completed_tasks', 'N/A')}")
        print(f"  Total bounty: {stats.get('total_bounty', 'N/A')}")
        print(f"  Total mined: {stats.get('total_mined', 'N/A')}")
        print("  [OK] Stats retrieved successfully")
    except Exception as e:
        print(f"  [FAIL] Error: {e}")
        return False
    
    # Test 2: Get task count
    print("\n[Test 2] Getting task count...")
    try:
        count = contract.get_task_count()
        print(f"  Task count: {count}")
        print("  [OK] Task count retrieved successfully")
    except Exception as e:
        print(f"  [FAIL] Error: {e}")
        return False
    
    # Test 3: Get miner reputation
    print("\n[Test 3] Getting miner reputation...")
    try:
        test_addr = "0x" + "aa" * 20
        rep = contract.get_miner_reputation(test_addr)
        print(f"  Reputation score: {rep}")
        print("  [OK] Miner reputation retrieved successfully")
    except Exception as e:
        print(f"  [FAIL] Error: {e}")
        return False
    
    print("\n" + "="*50)
    print("All tests passed!")
    print("="*50)
    return True


if __name__ == "__main__":
    success = test_contract()
    sys.exit(0 if success else 1)
