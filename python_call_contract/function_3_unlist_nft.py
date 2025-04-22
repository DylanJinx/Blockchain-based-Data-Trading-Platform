# python_call_contract/function_3_unlist_nft.py

import json
import requests
import warnings
import sys
from web3 import Web3, HTTPProvider
from web3.logs import DISCARD

# ========== 1. 配置及读取部署信息 ==========

RPC_URL = "http://127.0.0.1:8545"

# Agent 信息 (从Anvil打印获取)
agent_address = "0x70997970C51812dc3A010C7d01b50e0d17dc79C8"
agent_privkey = "0x59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d"

with open("deploy_address.json", "r") as f:
    deploy_info = json.load(f)

data_registration_addr = deploy_info["DataRegistration"]
data_tradingplatform_addr = deploy_info["DataTradingPlatform"]
escrow_deposit_addr = deploy_info["EscrowDeposit"]

session = requests.Session()
session.trust_env = False
w3 = Web3(HTTPProvider(RPC_URL, session=session))

if not w3.is_connected():
    print("无法连接 Anvil，请检查 RPC_URL")
    sys.exit(1)

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

def send_tx_with_sign(contract_func, from_address, privkey, value=0):
    tx_data = contract_func.build_transaction({
        'from': from_address,
        'nonce': w3.eth.get_transaction_count(from_address),
        'gas': 3_000_000,
        'gasPrice': w3.to_wei("1", "gwei"),
        'value': value
    })
    signed_tx = w3.eth.account.sign_transaction(tx_data, privkey)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    return receipt

def main():
    """
    用法: python function_3_unlist_nft.py <alice_addr> <token_id>
    """

    if len(sys.argv) < 3:
        print("用法: python function_3_unlist_nft.py <alice_addr> <token_id>")
        sys.exit(1)

    alice_addr = sys.argv[1].strip()
    token_id_str = sys.argv[2].strip()

    if not w3.is_address(alice_addr):
        print(f"您地址无效: {alice_addr}")
        sys.exit(1)

    if not token_id_str.isdigit():
        print(f"tokenId 不是数字: {token_id_str}")
        sys.exit(1)
    token_id = int(token_id_str)

    # 重要修复：将地址转换为校验和格式
    alice_addr = w3.to_checksum_address(alice_addr)

    print(f"===== 场景：Alice 下架 tokenId={token_id} 并退还保证金 =====")

    # 1) 验证 Alice 是否真拥有该 tokenId
    try:
        owner = DataRegistration.functions.ownerOf(token_id).call()
    except Exception as e:
        print("查询 ownerOf(tokenId) 出错:", e)
        sys.exit(1)

    if owner.lower() != alice_addr.lower():
        print(f"错误: tokenId={token_id} 的持有者是 {owner}，不是您({alice_addr})。无法下架。")
        sys.exit(1)
    else:
        print(f"校验成功: tokenId={token_id} 属于 {alice_addr}。")

    # 2) 调用 DataTradingPlatform.unlistNFT(tokenId)
    try:
        print(f"\n=== 以 Agent 调用 unlistNFT(tokenId={token_id}) ===")
        receipt_unlist = send_tx_with_sign(
            DataTradingPlatform.functions.unlistNFT(token_id),
            agent_address,
            agent_privkey
        )
        print("unlistNFT 交易哈希:", receipt_unlist.transactionHash.hex())

        # 检查交易是否成功
        if receipt_unlist.status == 0:
            print("【错误】unlistNFT 交易已回滚，可能是 tokenId 未上架 或其它条件不满足。")
            sys.exit(1)

        # 解析事件 NFTUnlisted
        logs_unlist = DataTradingPlatform.events.NFTUnlisted().process_receipt(receipt_unlist, errors=DISCARD)
        if len(logs_unlist) > 0:
            event_agent = logs_unlist[0]["args"]["agent"]
            event_token = logs_unlist[0]["args"]["tokenId"]
            print(f"下架事件: agent={event_agent}, tokenId={event_token}")
        else:
            print("【提示】未解析到 NFTUnlisted 事件，可能合约未发出或解析失败。")

    except Exception as e:
        print("unlistNFT 调用失败:", e)
        sys.exit(1)

    # 3) 调用 EscrowDeposit.withdrawListDeposit(alice_addr, tokenId)
    try:
        print(f"\n=== 以 Agent 调用 withdrawListDeposit(dataOwner={alice_addr}, tokenId={token_id}) ===")
        # 确保这里使用的是校验和格式的地址
        receipt_withdraw = send_tx_with_sign(
            EscrowDeposit.functions.withdrawListDeposit(alice_addr, token_id),
            agent_address,
            agent_privkey
        )
        print("withdrawListDeposit 交易哈希:", receipt_withdraw.transactionHash.hex())

        if receipt_withdraw.status == 0:
            print("【错误】withdrawListDeposit 交易已回滚，无法退还保证金。")
            sys.exit(1)

        # 解析事件 ListWithdrawn
        logs_wd = EscrowDeposit.events.ListWithdrawn().process_receipt(receipt_withdraw, errors=DISCARD)
        if len(logs_wd) > 0:
            wd_owner = logs_wd[0]["args"]["dataOwner"]
            wd_token = logs_wd[0]["args"]["tokenId"]
            wd_amount = logs_wd[0]["args"]["amount"]
            eth_amount = w3.from_wei(wd_amount, 'ether')
            print(f"保证金退还事件: dataOwner={wd_owner}, tokenId={wd_token}, amount={eth_amount} ETH")
            print(f"\033[92m=== 下架成功, tokenId={token_id}, 已退还保证金给 {wd_owner} ===\033[0m")
        else:
            print("\n【提示】未解析到 ListWithdrawn 事件，可能合约未发出或解析失败。")

    except Exception as e:
        print("withdrawListDeposit 调用失败:", e)
        sys.exit(1)

if __name__ == "__main__":
    main()