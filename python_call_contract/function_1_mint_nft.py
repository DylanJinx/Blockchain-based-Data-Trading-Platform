import json
import time
import requests
import sys
from web3 import Web3, HTTPProvider
from web3.logs import STRICT, IGNORE, DISCARD, WARN

# ============ 1. 基本配置 ============

RPC_URL = "http://127.0.0.1:8545"

# Agent 信息 (从 Anvil 控制台查看)
agent_address = "0x70997970C51812dc3A010C7d01b50e0d17dc79C8"
agent_privkey = "0x59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d"

# 需要 3 ETH 作为上架保证金
REQUIRED_ETHER = 3

# ============ 2. 读取部署信息 & 初始化 web3 ============

with open("deploy_address.json", "r") as f:
    deploy_info = json.load(f)

data_registration_addr = deploy_info["DataRegistration"]

# 不使用系统代理，防止本地连接被代理阻断
session = requests.Session()
session.trust_env = False
w3 = Web3(HTTPProvider(RPC_URL, session=session))

if not w3.is_connected():
    print("无法连接到本地 Anvil，请检查 RPC_URL。")
    exit(1)

# ============ 3. 读取 ABI ============

def load_abi(json_path):
    with open(json_path, "r") as f:
        artifact = json.load(f)
        return artifact["abi"]

data_registration_abi = load_abi("../BDTP_contract/out/DataRegistration.sol/DataRegistration.json")

data_registration_contract = w3.eth.contract(
    address=data_registration_addr,
    abi=data_registration_abi
)

# ============ 4. 发送交易的辅助函数 ============

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

# ============ 5. 在区块中寻找"从 您 发给 Agent 的 3 ETH"那笔交易 ============

def wait_for_alice_transaction(alice_addr, agent_addr, required_value_wei):
    """
    轮询区块，从当前区块开始，查找是否有来自 `alice_addr` -> `agent_addr` 且 value = required_value_wei 的交易
    找到后返回交易哈希，否则一直等待(或超时)
    """
    print(f"开始轮询区块，以查找 {alice_addr} -> Agent 的 3 ETH 交易。需要的金额(wei): {required_value_wei}")
    
    # 首先记录起始区块，轮询时只查看新区块
    start_block = w3.eth.block_number
    print(f"当前区块高度: {start_block}，将从此开始监听新区块")
    
    # 设置最大等待时间（5分钟）
    max_wait_time = 300
    start_time = time.time()
    
    while time.time() - start_time < max_wait_time:
        latest_block = w3.eth.block_number
        
        # 只查看新出现的区块
        for block_num in range(start_block, latest_block + 1):
            print(f"检查区块 {block_num}...")
            block = w3.eth.get_block(block_num, full_transactions=True)
            
            for tx in block.transactions:
                from_addr = tx["from"].lower()
                to_addr = (tx["to"] or "").lower()  # to 可能是None (合约创建), 做个安全处理
                value_wei = tx["value"]
                
                # 判断是否匹配
                if from_addr == alice_addr.lower() and to_addr == agent_addr.lower() and value_wei == required_value_wei:
                    print(f"在区块 {block_num} 找到匹配交易，hash={tx['hash'].hex()}")
                    return tx["hash"]
        
        # 更新起始区块，下次只查看更新的区块
        start_block = latest_block + 1
        
        # 每10秒输出一次等待状态，让用户知道脚本仍在运行
        elapsed = time.time() - start_time
        remaining = max_wait_time - elapsed
        print(f"仍在等待转账... 已等待: {int(elapsed)}秒, 剩余: {int(remaining)}秒")
        
        time.sleep(10)  # 每10秒轮询一次新区块
    
    print("等待超时（5分钟），未检测到转账交易。")
    return None

# ============ 6. 主流程：让 您 转 3 ETH，确认后调用 registerData ============

def main():
    # 从命令行获取要登记的cid/url（如果没传，默认"cid_1"）
    if len(sys.argv) > 1:
        cid_to_register = sys.argv[1]
    else:
        cid_to_register = "cid_1"
        
    # 从命令行获取用户地址（必须传入）
    if len(sys.argv) > 2:
        alice_address = sys.argv[2]
        print(f"注册NFT的用户地址: {alice_address}")
    else:
        print("错误: 未提供用户地址")
        print(json.dumps({
            "status": "error",
            "message": "未提供用户地址",
        }))
        exit(1)
    
    if not w3.is_address(alice_address):
        print(f"错误: 提供的用户地址不合法 {alice_address}")
        print(json.dumps({
            "status": "error",
            "message": f"提供的用户地址不合法: {alice_address}",
        }))
        exit(1)
    
    alice_address = w3.to_checksum_address(alice_address)

    print(f"\n===== 场景：用户 {alice_address} 想要登记数据集（NFT），CID = '{cid_to_register}' =====")
    print(f"\n需要用户转 3 ETH 到 Agent: {agent_address}")
    print(f"等待用户转账...\n")
    
    # 格式化输出JSON结果，让前端知道需要转账
    transfer_info = {
        "status": "waiting_for_transfer",
        "message": f"请转 3 ETH 到以下地址",
        "agent_address": agent_address,
        "required_eth": REQUIRED_ETHER
    }
    print(json.dumps(transfer_info))
    
    required_value_wei = w3.to_wei(REQUIRED_ETHER, "ether")

    # 等待转账交易
    tx_hash = wait_for_alice_transaction(alice_address, agent_address, required_value_wei)
    
    if not tx_hash:
        print("未检测到转账，无法继续铸造NFT。")
        print(json.dumps({
            "status": "error",
            "message": "未检测到转账，无法继续铸造NFT。请确保转账3 ETH到指定地址后重试。",
        }))
        exit(1)
    
    print(f"确认收到来自用户的 3 ETH，交易哈希: {tx_hash.hex()}")

    # 调用 registerData("<cid_to_register>", alice_address) 并附带 3 ETH
    print(f"\n=== 调用 DataRegistration.registerData({cid_to_register}, {alice_address})，附带 3 ETH ===")
    try:
        receipt = send_tx_with_sign(
            data_registration_contract.functions.registerData(cid_to_register, alice_address),
            agent_address,
            agent_privkey,
            value=required_value_wei
        )
        print("registerData() 交易已上链，hash =", receipt.transactionHash.hex())

        # 解析事件 DataRegistered
        logs = data_registration_contract.events.DataRegistered().process_receipt(receipt, errors=DISCARD)
        if len(logs) > 0:
            token_id = logs[0]["args"]["tokenId"]
            data_owner = logs[0]["args"]["dataOwner"]
            print(f"\n=== 登记成功！tokenId={token_id}, dataOwner={data_owner} ===")
            
            # 输出JSON结果，让前端能够解析
            success_info = {
                "status": "success",
                "message": "数据集登记成功！",
                "token_id": str(token_id),
                "data_owner": data_owner,
                "tx_hash": receipt.transactionHash.hex()
            }
            print(json.dumps(success_info))
        else:
            print("\n【警告】未在事件日志中解析到 DataRegistered，可能需检查合约或日志解析。")
            print(json.dumps({
                "status": "warning",
                "message": "交易已上链，但未能确认登记结果。请检查链上状态。",
                "tx_hash": receipt.transactionHash.hex()
            }))
    except Exception as e:
        print(f"调用合约失败: {str(e)}")
        print(json.dumps({
            "status": "error",
            "message": f"调用合约失败: {str(e)}",
        }))
        exit(1)

if __name__ == "__main__":
    main()