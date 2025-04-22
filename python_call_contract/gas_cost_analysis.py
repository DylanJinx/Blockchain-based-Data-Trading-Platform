#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
gas_cost_analysis.py - 分析BDTP系统主要功能的Gas消耗

使用方法:
  python gas_cost_analysis.py

功能:
  - 执行系统主要功能并记录Gas消耗
  - 以表格形式输出各功能的Gas消耗统计
  - 保存结果到CSV文件以便进一步分析
"""

import json
import sys
import os
import pandas as pd
import warnings
import requests
from web3 import Web3, HTTPProvider
from web3.logs import DISCARD

# ============ 1. 配置 ============
RPC_URL = "http://127.0.0.1:8545"

# 账户配置（从Anvil获取）
admin_address = "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266"
admin_privkey = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"

agent_address = "0x70997970C51812dc3A010C7d01b50e0d17dc79C8"
agent_privkey = "0x59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d"

# 测试用户地址
alice_address = "0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC"
alice_privkey = "0x5de4111afa1a4b94908f83103eb1f1706367c2e68ca870fc3fb9a804cdab365a"

bob_address = "0x90F79bf6EB2c4f870365E785982E1f101E93b906"
bob_privkey = "0x7c852118294e51e653712a81e05800f419141751be58f605c371e15141b007a6"

# ============ 2. 初始化Web3 ============
session = requests.Session()
session.trust_env = False
w3 = Web3(HTTPProvider(RPC_URL, session=session))

if not w3.is_connected():
    print("无法连接到Anvil，请检查RPC_URL。")
    sys.exit(1)

# ============ 3. 加载合约信息 ============
with open("deploy_address.json", "r") as f:
    deploy_info = json.load(f)

data_registration_addr = deploy_info["DataRegistration"]
data_tradingplatform_addr = deploy_info["DataTradingPlatform"]
escrow_deposit_addr = deploy_info["EscrowDeposit"]

def load_abi(json_path):
    with open(json_path, "r") as f:
        artifact = json.load(f)
        return artifact["abi"]

data_registration_abi = load_abi("../BDTP_contract/out/DataRegistration.sol/DataRegistration.json")
data_tradingplatform_abi = load_abi("../BDTP_contract/out/DataTradingPlatform.sol/DataTradingPlatform.json")
escrow_deposit_abi = load_abi("../BDTP_contract/out/EscrowDeposit.sol/EscrowDeposit.json")

DataRegistration = w3.eth.contract(address=data_registration_addr, abi=data_registration_abi)
DataTradingPlatform = w3.eth.contract(address=data_tradingplatform_addr, abi=data_tradingplatform_abi)
EscrowDeposit = w3.eth.contract(address=escrow_deposit_addr, abi=escrow_deposit_abi)

warnings.filterwarnings("ignore", category=UserWarning)

# ============ 4. 辅助函数 ============
def send_tx_and_get_gas(contract_func, from_address, privkey, value=0):
    """
    发送交易并返回Gas消耗
    """
    tx_data = contract_func.build_transaction({
        'from': from_address,
        'nonce': w3.eth.get_transaction_count(from_address),
        'gas': 5_000_000,  # 设置较高的gas限制，以确保交易成功
        'gasPrice': w3.to_wei("1", "gwei"),
        'value': value
    })
    
    signed_tx = w3.eth.account.sign_transaction(tx_data, privkey)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    
    gas_used = receipt.gasUsed
    
    return {
        'tx_hash': receipt.transactionHash.hex(),
        'gas_used': gas_used,
        'status': receipt.status,
        'receipt': receipt
    }

# ============ 5. 主要功能Gas分析 ============
def analyze_gas_costs():
    gas_results = []
    
    # 测试CID和价格
    test_cid = "test_cid_for_gas_analysis"
    test_price = w3.to_wei(1, "ether")
    stake_amount = w3.to_wei(3, "ether")
    
    print("开始Gas消耗分析...\n")
    
    # ========== 1. 铸造NFT (registerData) ==========
    print("1. 测试 registerData (铸造NFT)...")
    try:
        register_result = send_tx_and_get_gas(
            DataRegistration.functions.registerData(test_cid, alice_address),
            agent_address,
            agent_privkey,
            value=stake_amount
        )
        token_id = None
        
        # 从事件中提取tokenId
        logs = DataRegistration.events.DataRegistered().process_receipt(register_result['receipt'], errors=DISCARD)
        if len(logs) > 0:
            token_id = logs[0]["args"]["tokenId"]
            print(f"  NFT铸造成功，tokenId = {token_id}")
        else:
            print("  警告: 未能从事件中提取tokenId")
            
        gas_results.append({
            'function': 'registerData',
            'description': '铸造NFT',
            'gas_used': register_result['gas_used'],
            'status': 'success' if register_result['status'] == 1 else 'failed',
            'tx_hash': register_result['tx_hash']
        })
    except Exception as e:
        print(f"  registerData 失败: {e}")
        gas_results.append({
            'function': 'registerData',
            'description': '铸造NFT',
            'gas_used': 0,
            'status': 'error',
            'tx_hash': 'N/A'
        })
        token_id = None
    
    if not token_id:
        print("无法继续测试，未获取有效tokenId")
        return gas_results
        
    # ========== 2. 上架NFT (listNFT) ==========
    print("\n2. 测试 listNFT (上架NFT)...")
    try:
        list_result = send_tx_and_get_gas(
            DataTradingPlatform.functions.listNFT(token_id, test_price),
            agent_address,
            agent_privkey
        )
        
        gas_results.append({
            'function': 'listNFT',
            'description': '上架NFT',
            'gas_used': list_result['gas_used'],
            'status': 'success' if list_result['status'] == 1 else 'failed',
            'tx_hash': list_result['tx_hash']
        })
        print(f"  NFT上架成功，gas消耗 = {list_result['gas_used']}")
    except Exception as e:
        print(f"  listNFT 失败: {e}")
        gas_results.append({
            'function': 'listNFT',
            'description': '上架NFT',
            'gas_used': 0,
            'status': 'error',
            'tx_hash': 'N/A'
        })
    
    # ========== 3. 购买NFT (purchaseNFT) ==========
    print("\n3. 测试 purchaseNFT (购买NFT)...")
    try:
        # 为测试购买准备一个加密的CID
        encrypted_cid = "encrypted_cid_for_purchase_test"
        
        purchase_result = send_tx_and_get_gas(
            DataTradingPlatform.functions.purchaseNFT(token_id, bob_address, encrypted_cid),
            agent_address,
            agent_privkey,
            value=test_price
        )
        
        gas_results.append({
            'function': 'purchaseNFT',
            'description': '购买NFT',
            'gas_used': purchase_result['gas_used'],
            'status': 'success' if purchase_result['status'] == 1 else 'failed',
            'tx_hash': purchase_result['tx_hash']
        })
        print(f"  NFT购买成功，gas消耗 = {purchase_result['gas_used']}")
    except Exception as e:
        print(f"  purchaseNFT 失败: {e}")
        gas_results.append({
            'function': 'purchaseNFT',
            'description': '购买NFT',
            'gas_used': 0,
            'status': 'error',
            'tx_hash': 'N/A'
        })
    
    # ========== 4. 铸造第二个NFT用于测试举报 ==========
    print("\n4. 铸造第二个NFT用于测试举报...")
    try:
        register_result2 = send_tx_and_get_gas(
            DataRegistration.functions.registerData("second_test_cid", alice_address),
            agent_address,
            agent_privkey,
            value=stake_amount
        )
        
        token_id2 = None
        logs = DataRegistration.events.DataRegistered().process_receipt(register_result2['receipt'], errors=DISCARD)
        if len(logs) > 0:
            token_id2 = logs[0]["args"]["tokenId"]
            print(f"  第二个NFT铸造成功，tokenId = {token_id2}")
        
        # 上架第二个NFT
        list_result2 = send_tx_and_get_gas(
            DataTradingPlatform.functions.listNFT(token_id2, test_price),
            agent_address,
            agent_privkey
        )
        print(f"  第二个NFT上架成功")
        
    except Exception as e:
        print(f"  准备举报测试环境失败: {e}")
        token_id2 = None
    
    if not token_id2:
        print("无法继续举报测试，未获取第二个有效tokenId")
        return gas_results
    
    # ========== 5. 举报保证金 (informerDeposit) ==========
    print("\n5. 测试 informerDeposit (举报保证金)...")
    informer_deposit = w3.to_wei(2, "ether")
    try:
        inform_result = send_tx_and_get_gas(
            EscrowDeposit.functions.informerDeposit(bob_address, token_id, token_id2, informer_deposit),
            agent_address,
            agent_privkey,
            value=informer_deposit
        )
        
        gas_results.append({
            'function': 'informerDeposit',
            'description': '举报保证金',
            'gas_used': inform_result['gas_used'],
            'status': 'success' if inform_result['status'] == 1 else 'failed',
            'tx_hash': inform_result['tx_hash']
        })
        print(f"  举报保证金交易成功，gas消耗 = {inform_result['gas_used']}")
    except Exception as e:
        print(f"  informerDeposit 失败: {e}")
        gas_results.append({
            'function': 'informerDeposit',
            'description': '举报保证金',
            'gas_used': 0,
            'status': 'error',
            'tx_hash': 'N/A'
        })
    
    # ========== 6. 举报成功处理 (claimInformerSuccess) ==========
    print("\n6. 测试 claimInformerSuccess (举报成功处理)...")
    try:
        claim_result = send_tx_and_get_gas(
            EscrowDeposit.functions.claimInformerSuccess(bob_address, token_id, token_id2),
            agent_address,
            agent_privkey
        )
        
        gas_results.append({
            'function': 'claimInformerSuccess',
            'description': '举报成功处理',
            'gas_used': claim_result['gas_used'],
            'status': 'success' if claim_result['status'] == 1 else 'failed',
            'tx_hash': claim_result['tx_hash']
        })
        print(f"  举报成功处理完成，gas消耗 = {claim_result['gas_used']}")
    except Exception as e:
        print(f"  claimInformerSuccess 失败: {e}")
        gas_results.append({
            'function': 'claimInformerSuccess',
            'description': '举报成功处理',
            'gas_used': 0,
            'status': 'error',
            'tx_hash': 'N/A'
        })
    
    # ========== 7. 测试下架NFT (unlistNFT) ==========
    # 为测试下架，需要先创建一个新的NFT并上架
    print("\n7. 铸造第三个NFT用于测试下架...")
    try:
        register_result3 = send_tx_and_get_gas(
            DataRegistration.functions.registerData("third_test_cid", alice_address),
            agent_address,
            agent_privkey,
            value=stake_amount
        )
        
        token_id3 = None
        logs = DataRegistration.events.DataRegistered().process_receipt(register_result3['receipt'], errors=DISCARD)
        if len(logs) > 0:
            token_id3 = logs[0]["args"]["tokenId"]
            print(f"  第三个NFT铸造成功，tokenId = {token_id3}")
        
        # 上架第三个NFT
        list_result3 = send_tx_and_get_gas(
            DataTradingPlatform.functions.listNFT(token_id3, test_price),
            agent_address,
            agent_privkey
        )
        print(f"  第三个NFT上架成功")
        
        # 下架第三个NFT
        print("\n8. 测试 unlistNFT (下架NFT)...")
        unlist_result = send_tx_and_get_gas(
            DataTradingPlatform.functions.unlistNFT(token_id3),
            agent_address,
            agent_privkey
        )
        
        gas_results.append({
            'function': 'unlistNFT',
            'description': '下架NFT',
            'gas_used': unlist_result['gas_used'],
            'status': 'success' if unlist_result['status'] == 1 else 'failed',
            'tx_hash': unlist_result['tx_hash']
        })
        print(f"  NFT下架成功，gas消耗 = {unlist_result['gas_used']}")
        
        # 测试退还保证金
        print("\n9. 测试 withdrawListDeposit (退还保证金)...")
        withdraw_result = send_tx_and_get_gas(
            EscrowDeposit.functions.withdrawListDeposit(alice_address, token_id3),
            agent_address,
            agent_privkey
        )
        
        gas_results.append({
            'function': 'withdrawListDeposit',
            'description': '退还保证金',
            'gas_used': withdraw_result['gas_used'],
            'status': 'success' if withdraw_result['status'] == 1 else 'failed',
            'tx_hash': withdraw_result['tx_hash']
        })
        print(f"  保证金退还成功，gas消耗 = {withdraw_result['gas_used']}")
        
    except Exception as e:
        print(f"  测试下架NFT失败: {e}")
        gas_results.append({
            'function': 'unlistNFT',
            'description': '下架NFT',
            'gas_used': 0,
            'status': 'error',
            'tx_hash': 'N/A'
        })
        
        gas_results.append({
            'function': 'withdrawListDeposit',
            'description': '退还保证金',
            'gas_used': 0,
            'status': 'error',
            'tx_hash': 'N/A'
        })
    
    # ========== 10. 测试举报恶意处理 (confiscateInformerDeposit) ==========
    print("\n10. 铸造额外NFT用于测试举报没收...")
    try:
        register_result4 = send_tx_and_get_gas(
            DataRegistration.functions.registerData("fourth_test_cid", alice_address),
            agent_address,
            agent_privkey,
            value=stake_amount
        )
        
        token_id4 = None
        logs = DataRegistration.events.DataRegistered().process_receipt(register_result4['receipt'], errors=DISCARD)
        if len(logs) > 0:
            token_id4 = logs[0]["args"]["tokenId"]
            print(f"  第四个NFT铸造成功，tokenId = {token_id4}")
        
        # 上架第四个NFT
        list_result4 = send_tx_and_get_gas(
            DataTradingPlatform.functions.listNFT(token_id4, test_price),
            agent_address,
            agent_privkey
        )
        print(f"  第四个NFT上架成功")
        
        # 测试举报保证金
        inform_result2 = send_tx_and_get_gas(
            EscrowDeposit.functions.informerDeposit(bob_address, token_id3, token_id4, informer_deposit),
            agent_address,
            agent_privkey,
            value=informer_deposit
        )
        print(f"  举报保证金提交成功")
        
        # 测试没收举报保证金
        print("\n11. 测试 confiscateInformerDeposit (没收举报保证金)...")
        confiscate_result = send_tx_and_get_gas(
            EscrowDeposit.functions.confiscateInformerDeposit(bob_address, token_id3, token_id4),
            agent_address,
            agent_privkey
        )
        
        gas_results.append({
            'function': 'confiscateInformerDeposit',
            'description': '没收举报保证金',
            'gas_used': confiscate_result['gas_used'],
            'status': 'success' if confiscate_result['status'] == 1 else 'failed',
            'tx_hash': confiscate_result['tx_hash']
        })
        print(f"  没收举报保证金成功，gas消耗 = {confiscate_result['gas_used']}")
        
    except Exception as e:
        print(f"  测试没收举报保证金失败: {e}")
        gas_results.append({
            'function': 'confiscateInformerDeposit',
            'description': '没收举报保证金',
            'gas_used': 0,
            'status': 'error',
            'tx_hash': 'N/A'
        })
    
    return gas_results

# ============ 6. 输出结果 ============
def output_results(gas_results):
    # 创建DataFrame并排序
    df = pd.DataFrame(gas_results)
    if not df.empty:
        # 按gas消耗从高到低排序
        df = df.sort_values(by='gas_used', ascending=False)
        
        # 输出表格
        print("\n============ BDTP系统Gas消耗分析 ============")
        print(f"{'功能':<25} {'描述':<20} {'Gas消耗':<15} {'状态':<10}")
        print("-" * 70)
        
        for _, row in df.iterrows():
            print(f"{row['function']:<25} {row['description']:<20} {row['gas_used']:<15} {row['status']:<10}")
        
        # 保存到CSV
        df.to_csv('BDTP_gas_analysis.csv', index=False)
        print("\n分析结果已保存到 BDTP_gas_analysis.csv")
    else:
        print("\n没有收集到有效的Gas消耗数据")

# ============ 主函数 ============
def main():
    print("===== BDTP系统Gas消耗分析工具 =====\n")
    print("本工具将执行系统的主要功能并记录Gas消耗。\n")
    
    try:
        # 执行分析
        gas_results = analyze_gas_costs()
        
        # 输出结果
        output_results(gas_results)
        
    except Exception as e:
        print(f"分析过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import requests  # 在这里导入requests是为了避免循环导入问题
    main()