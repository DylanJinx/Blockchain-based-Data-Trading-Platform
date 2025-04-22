import json
import requests
import warnings
import sys
from web3 import Web3, HTTPProvider
from web3.logs import DISCARD

RPC_URL = "http://127.0.0.1:8545"
agent_address = "0x70997970C51812dc3A010C7d01b50e0d17dc79C8"
agent_privkey = "0x59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d"

with open("deploy_address.json", "r") as f:
    deploy_info = json.load(f)
data_registration_addr = deploy_info["DataRegistration"]
data_tradingplatform_addr = deploy_info["DataTradingPlatform"]

session = requests.Session()
session.trust_env = False
w3 = Web3(HTTPProvider(RPC_URL, session=session))

if not w3.is_connected():
    print("无法连接 Anvil，请检查 RPC_URL。")
    sys.exit(1)

def load_abi(json_path):
    with open(json_path, "r") as f:
        artifact = json.load(f)
        return artifact["abi"]

data_registration_abi = load_abi("../BDTP_contract/out/DataRegistration.sol/DataRegistration.json")
data_tradingplatform_abi = load_abi("../BDTP_contract/out/DataTradingPlatform.sol/DataTradingPlatform.json")

DataRegistration = w3.eth.contract(address=data_registration_addr, abi=data_registration_abi)
DataTradingPlatform = w3.eth.contract(address=data_tradingplatform_addr, abi=data_tradingplatform_abi)

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
    if len(sys.argv) < 4:
        print("用法: python function_2_list_nft.py <alice_addr> <token_id> <price_in_eth>")
        sys.exit(1)

    alice_addr = sys.argv[1].strip()
    token_id_str = sys.argv[2].strip()
    price_str = sys.argv[3].strip()

    if not w3.is_address(alice_addr):
        print(f"您地址无效: {alice_addr}")
        sys.exit(1)

    if not token_id_str.isdigit():
        print(f"tokenId 不是数字: {token_id_str}")
        sys.exit(1)
    token_id = int(token_id_str)

    try:
        price_in_eth = float(price_str)
    except ValueError:
        print(f"价格输入非法: {price_str}")
        sys.exit(1)

    price_wei = w3.to_wei(price_in_eth, "ether")

    print(f"===== 场景：您 希望上架 tokenId={token_id}，售价={price_in_eth} ETH =====")

    # 1) 确认 tokenId 的所有者是否就是 alice_addr
    try:
        owner = DataRegistration.functions.ownerOf(token_id).call()
    except Exception as e:
        print("查询 ownerOf(tokenId) 出错:", e)
        sys.exit(1)

    if owner.lower() != alice_addr.lower():
        print(f"错误: tokenId={token_id} 的持有者是 {owner}，而非 您({alice_addr})。无法上架。")
        sys.exit(1)
    else:
        print(f"校验成功: tokenId={token_id} 确实属于 {alice_addr}。")

    # 2) 以 Agent 的身份调用 DataTradingPlatform.listNFT(token_id, price_wei)
    try:
        print(f"\n=== 以 Agent 调用 listNFT(tokenId={token_id}, price={price_in_eth} ETH) ===")
        receipt = send_tx_with_sign(
            DataTradingPlatform.functions.listNFT(token_id, price_wei),
            agent_address,
            agent_privkey
        )
        print("listNFT 交易哈希:", receipt.transactionHash.hex())
    except Exception as e:
        print("listNFT 调用失败:", e)
        sys.exit(1)

    # 3) 检查交易回执是否成功
    if receipt.status == 0:
        # 如果status == 0，表示交易失败或revert（require(...)没通过等）
        print(f"【错误】交易执行失败或已回滚，可能是 NFT 已经上架 或其它条件不满足。")
        sys.exit(1)

    # 4) 如果 status == 1，解析事件: NFTListed
    logs = DataTradingPlatform.events.NFTListed().process_receipt(receipt, errors=DISCARD)
    if len(logs) > 0:
        event_agent = logs[0]["args"]["agent"]
        event_token = logs[0]["args"]["tokenId"]
        event_price = logs[0]["args"]["price"]
        eth_price = w3.from_wei(event_price, 'ether')
        print(f"\n成功上架: agent={event_agent}, tokenId={event_token}, price={eth_price} ETH")
        print(f"\033[92m=== 上架完成, tokenId={token_id}, 价格={price_in_eth} ETH ===\033[0m")
    else:
        print("\n【提示】未解析到 NFTListed 事件，合约可能没有发出该事件。")
        print(f"=== 上架完成(无事件)，tokenId={token_id}, 价格={price_in_eth} ETH ===")

if __name__ == "__main__":
    main()
