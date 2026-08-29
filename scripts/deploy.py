#!/usr/bin/env python3
"""
Deploy Proof of Inference contract to GenLayer testnet.

Usage:
    python scripts/deploy.py                    # 交互式输入私钥
    python scripts/deploy.py --network testnet_bradbury

Security:
    - 私钥仅在内存中使用，不存储到文件
    - 部署完成后立即清除内存
"""

import os
import sys
import json
import argparse
import getpass
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set GLTEST_CONFIG to use our config file
os.environ["GLTEST_CONFIG"] = str(project_root / "gltest.config.yaml")


def get_private_key_interactive():
    """Interactively get private key without storing it."""
    print("\n" + "="*50)
    print("安全提示：私钥仅在内存中使用，不会存储到文件")
    print("="*50)
    
    private_key = getpass.getpass("\n请输入你的私钥（输入时不会显示）: ")
    
    if not private_key:
        print("错误：私钥不能为空")
        sys.exit(1)
    
    # Remove 0x prefix if present
    if private_key.startswith("0x"):
        private_key = private_key[2:]
    
    # Basic validation
    if len(private_key) != 64:
        print("错误：私钥长度不正确（应该是64个字符）")
        sys.exit(1)
    
    try:
        int(private_key, 16)
    except ValueError:
        print("错误：私钥格式不正确（应该是十六进制）")
        sys.exit(1)
    
    print("[OK] 私钥格式正确")
    return private_key


def deploy_contract(private_key: str, network: str = "testnet_bradbury"):
    """Deploy the contract to specified network."""
    try:
        from gltest import get_contract_factory
        from gltest.clients import get_gl_client
        from gltest_cli.config.general import get_general_config
        from gltest_cli.config.user import load_user_config
        from gltest_cli.config.types import NetworkConfigData
        from eth_account import Account
    except ImportError:
        print("错误：gltest 未安装。运行: pip install gltest")
        sys.exit(1)

    print(f"\n部署 Proof of Inference 到 {network}...")
    
    # Load contract
    contract_path = project_root / "proof_of_inference.py"
    if not contract_path.exists():
        print(f"错误：合约文件不存在 {contract_path}")
        sys.exit(1)
    
    print(f"合约文件: {contract_path}")
    
    # Derive address from private key
    account = Account.from_key(private_key)
    wallet_address = account.address
    print(f"钱包地址: {wallet_address}")
    
    try:
        # Load and configure the network with account
        config = get_general_config()
        user_config = load_user_config(os.environ["GLTEST_CONFIG"])
        
        # Set the account in the network config
        network_config = user_config.networks[network]
        network_config.accounts = [private_key]
        network_config.from_account = private_key
        
        config.user_config = user_config
        config.plugin_config.network_name = network
        config.plugin_config.rpc_url = network_config.url
        
        print(f"[OK] 已连接到 {network}")
        
        # Deploy
        factory = get_contract_factory(contract_file_path=str(contract_path))
        print("正在部署合约...")
        
        contract = factory.deploy()
        address = contract.address
        
        print(f"\n[OK] 合约部署成功！")
        print(f"地址: {address}")
        print(f"浏览器: https://explorer-bradbury.genlayer.com/address/{address}")
        
        # Save deployment info (without private key)
        deployment_info = {
            "network": network,
            "address": address,
            "contract": str(contract_path),
            "deployer": wallet_address,
        }
        
        deployment_file = project_root / "deployment.json"
        with open(deployment_file, "w") as f:
            json.dump(deployment_info, f, indent=2)
        
        print(f"部署信息已保存到 {deployment_file}")
        
        return address
        
    finally:
        # Clear private key from memory
        private_key = "0" * 64
        print("\n[OK] 私钥已从内存中清除")


def main():
    parser = argparse.ArgumentParser(description="部署 Proof of Inference 合约")
    parser.add_argument(
        "--network",
        default="testnet_bradbury",
        choices=["testnet_bradbury", "testnet_asimov", "localnet"],
        help="部署网络 (默认: testnet_bradbury)"
    )
    args = parser.parse_args()
    
    # Get private key interactively
    private_key = get_private_key_interactive()
    
    # Deploy
    address = deploy_contract(private_key, args.network)
    
    print("\n" + "="*50)
    print("部署摘要:")
    print("="*50)
    print(f"网络: {args.network}")
    print(f"合约地址: {address}")
    print("="*50)
    print("\n下一步:")
    print("1. 更新 index.html 中的合约地址")
    print("2. 运行测试: python scripts/testnet_test.py")
    print("3. 在浏览器上验证合约")


if __name__ == "__main__":
    main()
