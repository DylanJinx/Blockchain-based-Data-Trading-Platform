#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
from requests import Session
from web3 import Web3, HTTPProvider

session = Session()
session.trust_env = False  # 不信任系统环境代理，也就不会走 http_proxy/https_proxy

# ============ 1. 配置部分 ============

# Anvil本地RPC，若你自定义端口请修改
RPC_URL = "http://127.0.0.1:8545"

# 账户信息（从Anvil输出获取）
# 假设:
#   - 第0号账户为admin
#   - 第1号账户为agent
admin_address = "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266"
admin_privkey = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"

agent_address = "0x70997970C51812dc3A010C7d01b50e0d17dc79C8"
# 如果你不需要在部署阶段使用 agent_privkey，则可以不写

# 部署/调用时的 gasLimit 和 gasPrice
gas_limit = 3_000_000
gas_price = Web3.to_wei("1", "gwei")

# ============ 2. 读取ABI与Bytecode ============

def load_abi_bytecode(json_path):
    """
    从 Foundry 产物 JSON 文件里读取 abi & bytecode
    注意该 JSON 中结构大致为:
    {
      "abi": [...],
      "bytecode": {
        "object": "0x6080...."
        ...
      },
      "deployedBytecode": {...}
    }
    我们主要用 "bytecode.object" 作为待部署的字节码。
    """
    with open(json_path, "r") as f:
        artifact = json.load(f)
        abi = artifact["abi"]
        bytecode = artifact["bytecode"]["object"]  # 注意这里取 "object"
        return abi, bytecode

# 根据你的实际路径进行修改
ESCROW_JSON_PATH = "../BDTP_contract/out/EscrowDeposit.sol/EscrowDeposit.json"
DATAREG_JSON_PATH = "../BDTP_contract/out/DataRegistration.sol/DataRegistration.json"
DATATRADE_JSON_PATH = "../BDTP_contract/out/DataTradingPlatform.sol/DataTradingPlatform.json"

escrow_abi, escrow_bytecode = load_abi_bytecode(ESCROW_JSON_PATH)
datareg_abi, datareg_bytecode = load_abi_bytecode(DATAREG_JSON_PATH)
dplatform_abi, dplatform_bytecode = load_abi_bytecode(DATATRADE_JSON_PATH)

# ============ 3. 初始化 web3 ============

w3 = Web3(Web3.HTTPProvider(RPC_URL, session=session))
if not w3.is_connected():
    print("无法连接到 Anvil，请检查RPC_URL。")
    exit(1)

# ============ 4. 帮助函数：构建 & 签名 & 发送交易 ============

def send_tx_with_sign(tx, privkey):
    """
    对交易进行签名并发送，返回Receipt
    """
    signed_tx = w3.eth.account.sign_transaction(tx, privkey)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    return receipt

def deploy_contract(abi, bytecode, constructor_args=()):
    """
    部署合约，传入构造函数参数
    """
    # 注意：constructor_args 是一个tuple，如 constructor_args=(param1, param2, ...)
    contract = w3.eth.contract(abi=abi, bytecode=bytecode)
    construct_txn = contract.constructor(*constructor_args).build_transaction({
        'from': admin_address,
        'nonce': w3.eth.get_transaction_count(admin_address),
        'gas': gas_limit,
        'gasPrice': gas_price,
    })
    receipt = send_tx_with_sign(construct_txn, admin_privkey)
    contract_address = receipt.contractAddress
    return contract_address

# ============ 5. 主流程 ============

def main():
    print("==================== 部署流程开始 ====================\n")
    print("1) 部署 DataRegistration...")
    # DataRegistration 无需构造参数
    datareg_addr = deploy_contract(datareg_abi, datareg_bytecode)
    print("   => DataRegistration 合约地址:", datareg_addr)

    print("2) 部署 EscrowDeposit...")
    # EscrowDeposit 同样没有构造函数参数
    escrow_addr = deploy_contract(escrow_abi, escrow_bytecode)
    print("   => EscrowDeposit 合约地址:", escrow_addr)

    print("3) 部署 DataTradingPlatform...")
    # DataTradingPlatform 构造函数需要传 dataRegistrationContract
    # 所以我们把 datareg_addr 作为 constructor 参数
    dtp_addr = deploy_contract(dplatform_abi, dplatform_bytecode, (datareg_addr,))
    print("   => DataTradingPlatform 合约地址:", dtp_addr)

    print("\n===== 合约已部署成功，下面进行初始化调用 =====\n")

    # 分别构建合约对象
    DataReg = w3.eth.contract(address=datareg_addr, abi=datareg_abi)
    Escrow  = w3.eth.contract(address=escrow_addr, abi=escrow_abi)
    DTP     = w3.eth.contract(address=dtp_addr, abi=dplatform_abi)

    # ---------- DataRegistration 初始化：setAgent & setEscrowContract ----------
    print("4) DataRegistration.setAgent ->", agent_address)
    tx = DataReg.functions.setAgent(agent_address).build_transaction({
        'from': admin_address,
        'nonce': w3.eth.get_transaction_count(admin_address),
        'gas': gas_limit,
        'gasPrice': gas_price
    })
    send_tx_with_sign(tx, admin_privkey)

    print("5) DataRegistration.setEscrowContract ->", escrow_addr)
    tx = DataReg.functions.setEscrowContract(escrow_addr).build_transaction({
        'from': admin_address,
        'nonce': w3.eth.get_transaction_count(admin_address),
        'gas': gas_limit,
        'gasPrice': gas_price
    })
    send_tx_with_sign(tx, admin_privkey)

    # ---------- EscrowDeposit 初始化：setAgent & setDataRegistrationContract ----------
    print("6) EscrowDeposit.setAgent ->", agent_address)
    tx = Escrow.functions.setAgent(agent_address).build_transaction({
        'from': admin_address,
        'nonce': w3.eth.get_transaction_count(admin_address),
        'gas': gas_limit,
        'gasPrice': gas_price
    })
    send_tx_with_sign(tx, admin_privkey)

    print("7) EscrowDeposit.setDataRegistrationContract ->", datareg_addr)
    tx = Escrow.functions.setDataRegistrationContract(datareg_addr).build_transaction({
        'from': admin_address,
        'nonce': w3.eth.get_transaction_count(admin_address),
        'gas': gas_limit,
        'gasPrice': gas_price
    })
    send_tx_with_sign(tx, admin_privkey)

    # ---------- DataTradingPlatform 初始化：setAgent ----------
    print("8) DataTradingPlatform.setAgent ->", agent_address)
    tx = DTP.functions.setAgent(agent_address).build_transaction({
        'from': admin_address,
        'nonce': w3.eth.get_transaction_count(admin_address),
        'gas': gas_limit,
        'gasPrice': gas_price
    })
    send_tx_with_sign(tx, admin_privkey)

    print("\n===== 所有初始化操作完成！ =====\n")

    # 最后把部署信息输出到 JSON，以便后续脚本使用
    deploy_info = {
        "DataRegistration": datareg_addr,
        "EscrowDeposit": escrow_addr,
        "DataTradingPlatform": dtp_addr
    }
    with open("deploy_address.json", "w") as f:
        json.dump(deploy_info, f, indent=2)

    print("已将部署信息写入 deploy_address.json。")
    print("===== 部署脚本执行结束 =====\n")

if __name__ == "__main__":
    main()
