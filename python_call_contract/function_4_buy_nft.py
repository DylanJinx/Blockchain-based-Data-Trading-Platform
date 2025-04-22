# python_call_contract/function_4_buy_nft.py

import json
import time
import requests
import sys
import warnings
from web3 import Web3, HTTPProvider
from web3.logs import DISCARD

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

def wait_for_bob_transaction(bob_addr, agent_addr, required_value_wei):
    """
    轮询区块，查找 bob_addr -> agent_addr 的交易 value=required_value_wei
    找到后返回 tx_hash
    """
    print(f"开始轮询区块，查找 bob->{agent_addr} 转账金额={required_value_wei} wei")
    start_block = w3.eth.block_number

    while True:
        latest_block = w3.eth.block_number
        for block_num in range(start_block, latest_block + 1):
            block = w3.eth.get_block(block_num, full_transactions=True)
            for tx in block.transactions:
                from_addr = tx["from"].lower()
                to_addr = (tx["to"] or "").lower() if tx["to"] else None
                val_wei = tx["value"]
                if from_addr == bob_addr.lower() and to_addr == agent_addr.lower() and val_wei == required_value_wei:
                    print(f"在区块 {block_num} 找到匹配交易,hash={tx['hash'].hex()}")
                    return tx["hash"]
        start_block = latest_block + 1
        time.sleep(2)

def main():
    if len(sys.argv) < 2:
        print("用法: python function_4_buy_nft.py <check|purchase> <args...>")
        sys.exit(1)

    mode = sys.argv[1]

    if mode == "check":
        """
        usage:
          python function_4_buy_nft.py check <tokenId>
        输出:
          - ListingStatus=...
          - price=...
          - metadataURL=...
        """
        if len(sys.argv) < 3:
            print("用法: python function_4_buy_nft.py check <tokenId>")
            sys.exit(1)
        token_id_str = sys.argv[2]
        if not token_id_str.isdigit():
            print("tokenId 不是数字:", token_id_str)
            sys.exit(1)
        token_id = int(token_id_str)

        try:
            # 1) 获取listing状态 & price
            status = DataTradingPlatform.functions.getNFTStatus(token_id).call()
            price_wei = DataTradingPlatform.functions.getPrice(token_id).call()
            price_eth = w3.from_wei(price_wei, "ether")

            if status == 1:
                print(f"ListingStatus=Listed, price={price_eth}")
            elif status == 0:
                print("ListingStatus=NotListed")
            else:
                print("ListingStatus=Unlisted")

            # 2) 获取metadataURL => DataRegistration.tokenURI(tokenId)
            metadata_url = DataRegistration.functions.tokenURI(token_id).call()
            print(f"metadataURL={metadata_url}")

        except Exception as e:
            print("调用合约查询失败:", e)
            sys.exit(1)

    elif mode == "purchase":
        """
        usage:
          python function_4_buy_nft.py purchase <tokenId> <bobAddr> <priceInEth> <encryptedCid>
        流程:
          - 轮询 bob->agent 的 priceInEth 交易
          - 调用 purchaseNFT(tokenId, bobAddr, encryptedCid) + msg.value=priceInEth
          - 解析事件 NFTPurchased(msg.sender, tokenId, dataOwner, msg.value, encryptedCid)
        """
        if len(sys.argv) < 6:
            print("用法: python function_4_buy_nft.py purchase <tokenId> <bobAddr> <priceInEth> <encryptedCid>")
            sys.exit(1)

        token_id_str = sys.argv[2]
        bob_addr = sys.argv[3]
        price_str = sys.argv[4]
        enc_cid = sys.argv[5]

        bob_addr = w3.to_checksum_address(bob_addr)

        if not token_id_str.isdigit():
            print("tokenId 非数字:", token_id_str)
            sys.exit(1)
        token_id = int(token_id_str)

        try:
            price_in_eth = float(price_str)
        except ValueError:
            print("priceInEth 非法:", price_str)
            sys.exit(1)

        price_wei = w3.to_wei(price_in_eth, "ether")

        # 1) 轮询bob->agent转账
        tx_hash = wait_for_bob_transaction(bob_addr, agent_address, price_wei)
        print(f"确认收到来自 {bob_addr} 的付款, 交易hash={tx_hash.hex()}")

        # 2) 调用 purchaseNFT(...)
        try:
            print(f"\n=== 调用 purchaseNFT(tokenId={token_id}, buyer={bob_addr}, encCid=...) ===")
            receipt = send_tx_with_sign(
                DataTradingPlatform.functions.purchaseNFT(token_id, bob_addr, enc_cid),
                agent_address,
                agent_privkey,
                value=price_wei
            )
            print("purchaseNFT 交易哈希:", receipt.transactionHash.hex())
            if receipt.status == 0:
                print("【错误】交易已回滚, 可能NFT未上架或其它条件不满足。")
                sys.exit(1)

            # 解析事件 NFTPurchased(msg.sender, tokenId, dataOwner, msg.value, encryptedCid)
            logs = DataTradingPlatform.events.NFTPurchased().process_receipt(receipt, errors=DISCARD)
            if len(logs) > 0:
                evt_args = logs[0]["args"]
                evt_operator = evt_args["buyer"]        # msg.sender
                evt_token = evt_args["tokenId"]
                evt_dataOwner = evt_args["dataOwner"]
                evt_value = evt_args["amount"]
                evt_encCid = evt_args["encryptedCid"]

                print(f"NFTPurchased => operator={evt_operator}, tokenId={evt_token}, dataOwner={evt_dataOwner}, ethPaid={w3.from_wei(evt_value,'ether')} ETH, encCid={evt_encCid}")
            else:
                print("【提示】未解析到 NFTPurchased 事件, 合约可能未发出或日志解析失败.")

            print("\n \033[92m=== purchaseNFT 成功, 您已获得访问权. ===\033[0m")
        except Exception as e:
            print("purchaseNFT 调用失败:", e)
            sys.exit(1)

    else:
        print(f"未知模式: {mode}")
        sys.exit(1)

if __name__ == "__main__":
    main()
