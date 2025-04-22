#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
功能七 - 举报并检测 (一步到位)

用法:
  python function_7_informer.py report <tokenIdA> <tokenIdB> <jinxAddr>

流程:
1) 检查 tokenIdA / tokenIdB 是否都在售 (Listed)
2) 等待 jinx->agent 2 ETH
3) 根据 tokenIdToTimestamp 判定 originalTokenId / suspicionTokenId
4) 以 agent 调用 EscrowDeposit.informerDeposit(...) => InformerDeposited
5) 下载 & 解密 original / suspicion 数据 => ../my_agent_project/XRID/original_dataset & ../my_agent_project/XRID/suspicion_dataset
6) 运行 XRID 检测 => 输出是否确有转售行为
7) 根据预测结果(Predicted_Label=1/0)，调用合约 claimInformerSuccess 或 confiscateInformerDeposit
"""

import json
import time
import sys
import warnings
import os
import subprocess
import requests
import zipfile
import shutil
from web3 import Web3, HTTPProvider
from web3.logs import DISCARD

script_dir = os.path.dirname(os.path.abspath(__file__))  # 当前文件( python_call_contract/ )目录
project_dir = os.path.join(script_dir, "..", "my_agent_project")
sys.path.append(project_dir)

##############################################################################
# 1. 配置
##############################################################################

RPC_URL = "http://127.0.0.1:8545"

# ============ Agent 信息 (从Anvil打印获取) ============
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
    print("无法连接Anvil，请检查RPC_URL。")
    sys.exit(1)

##############################################################################
# 2. 读取合约 ABI & 实例化
##############################################################################

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

##############################################################################
# 3. 通用方法
##############################################################################

def send_tx_with_sign(contract_func, from_address, privkey, value=0):
    """
    发起并签名交易工具函数
    """
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

def wait_for_jinx_transaction(jinx_addr, agent_addr, required_value_eth):
    """
    轮询区块, 等 jinx_addr -> agent_addr 的 required_value_eth
    """
    required_value_wei = w3.to_wei(required_value_eth, "ether")
    print(f"等待 {jinx_addr} -> {agent_addr} {required_value_eth} ETH 转账...")
    start_block = w3.eth.block_number
    while True:
        latest_block = w3.eth.block_number
        for block_num in range(start_block, latest_block + 1):
            block = w3.eth.get_block(block_num, full_transactions=True)
            for tx in block.transactions:
                from_addr = tx["from"].lower()
                to_addr = (tx["to"] or "").lower() if tx["to"] else None
                val_wei = tx["value"]
                if from_addr == jinx_addr.lower() and to_addr == agent_addr.lower() and val_wei == required_value_wei:
                    print(f"在区块 {block_num} 找到匹配交易, hash={tx['hash'].hex()}")
                    return tx["hash"]
        start_block = latest_block + 1
        time.sleep(2)

def check_listing_status(token_id):
    """
    检查某个 tokenId 是否 Listed, 返回 "Listed" / "NotListed" / "Unlisted"
    """
    status_code = DataTradingPlatform.functions.getNFTStatus(token_id).call()
    # enum ListingStatus { NotListed=0, Listed=1, Unlisted=2 }
    if status_code == 1:
        return "Listed"
    elif status_code == 0:
        return "NotListed"
    else:
        return "Unlisted"

def get_timestamp(token_id):
    """
    需要 DataRegistration 有: mapping(uint256 => uint256) public tokenIdToTimestamp;
    """
    return DataRegistration.functions.tokenIdToTimestamp(token_id).call()

##############################################################################
# 4. 下载 & 解密 => XRID => interpret
##############################################################################

def download_and_decrypt(token_id, prefix):
    """
    1) 调用 DataRegistration.tokenURI(token_id) => metadata_url
    2) GET metadata => zip_cid
    3) node ../BDTP/decryptCid.js => raw_cid
    4) node ../BDTP/downloadFromIPFS.js raw_cid => ../my_agent_project/XRID/<prefix>_dataset.zip
    5) 解压 => ../my_agent_project/XRID/<prefix>_dataset
       - 删除 __MACOSX (如果有)
       - 将子文件夹内全部内容上移到根目录，删除子文件夹
    """
    import subprocess
    import re
    import requests
    import zipfile
    import os
    import shutil

    # 1) metadata_url
    metadata_url = DataRegistration.functions.tokenURI(token_id).call()
    print(f"tokenId={token_id}, tokenURI={metadata_url}")

    # 2) GET JSON => zip_cid
    try:
        resp = requests.get(metadata_url)
        resp.raise_for_status()
        jdata = resp.json()
        zip_cid_encrypted = jdata.get("zip_cid")
        if not zip_cid_encrypted:
            print("metadata里无 zip_cid字段.")
            sys.exit(1)
    except Exception as e:
        print("获取metadata失败:", e)
        sys.exit(1)

    # 3) decryptCid
    dec_cmd = ["node", "../BDTP/decryptCid.js", zip_cid_encrypted]
    try:
        r_dec = subprocess.run(dec_cmd, cwd="../BDTP", capture_output=True, text=True, check=True)
        dec_out = r_dec.stdout.strip()
        match = re.search(r"Decrypted CID:\s*(\S+)", dec_out)
        if not match:
            print("解密脚本输出异常:", dec_out)
            sys.exit(1)
        raw_cid = match.group(1)
        print(f"解密得到 raw_cid={raw_cid}")
    except subprocess.CalledProcessError as e:
        print("解密脚本执行失败:", e)
        sys.exit(1)

    # 4) downloadFromIPFS => ../my_agent_project/XRID/<prefix>_dataset.zip
    out_zip = f"../my_agent_project/XRID/{prefix}_dataset.zip"
    dl_cmd = ["node", "../BDTP/downloadFromIPFS.js", raw_cid, out_zip]
    try:
        subprocess.run(dl_cmd, cwd="../BDTP", check=True)
        print(f"已下载到 {out_zip}")
    except subprocess.CalledProcessError as e:
        print("下载脚本执行失败:", e)
        sys.exit(1)

    # 5) 解压 => ../my_agent_project/XRID/<prefix>_dataset
    print("当前目录:", os.getcwd())
    unzip_folder = f"../my_agent_project/XRID/{prefix}_dataset"
    if os.path.exists(unzip_folder):
        shutil.rmtree(unzip_folder)
    try:
        with zipfile.ZipFile(os.path.join(out_zip), 'r') as zf:
            zf.extractall(os.path.join(unzip_folder))
        print(f"解压完成 => {unzip_folder}")
    except Exception as e:
        print("解压失败:", e)
        sys.exit(1)

    # ============ 新增处理逻辑：删除 __MACOSX、上移子文件夹内容 ============
    macosx_dir = os.path.join(unzip_folder, "__MACOSX")
    if os.path.exists(macosx_dir):
        shutil.rmtree(macosx_dir)
        print(f"已删除: {macosx_dir}")

    subdirs = [d for d in os.listdir(unzip_folder) 
               if os.path.isdir(os.path.join(unzip_folder, d)) and not d.startswith('__MACOSX')]
    for subdir in subdirs:
        subdir_path = os.path.join(unzip_folder, subdir)
        for filename in os.listdir(subdir_path):
            src = os.path.join(subdir_path, filename)
            dst = os.path.join(unzip_folder, filename)
            shutil.move(src, dst)
        shutil.rmtree(subdir_path)
        print(f"已移动并删除子文件夹: {subdir_path}")

def run_xrid_check(original_id, suspicion_id, jinx_addr):
    """
    - 调用 feature_resale.run_xrid_commands("original_dataset", "suspicion_dataset")
    - interpret_results => 得到 prediction_label
    - 根据 label=1/0, 分别执行 claimInformerSuccess / confiscateInformerDeposit
    """
    import sys
    sys.path.append("..")  # 让 Python能找到my_agent_project包

    from my_agent_project.features.feature_resale import run_xrid_commands, interpret_results
    run_xrid_commands("original_dataset", "suspicion_dataset")
    prediction_label = interpret_results("original_dataset", "suspicion_dataset")

    if prediction_label == "1":
        print("XRID结果: 存在转售行为 => 举报成立, 准备调用 claimInformerSuccess ...")
        try:
            contract_func = EscrowDeposit.functions.claimInformerSuccess(
                jinx_addr, 
                original_id,
                suspicion_id
            )
            receipt = send_tx_with_sign(contract_func, agent_address, agent_privkey)
            if receipt.status == 1:
                print("\033[92mclaimInformerSuccess 交易成功! 您 获得了保证金奖励。\033[0m")
            else:
                print("【警告】claimInformerSuccess 执行失败/回滚。")
        except Exception as e:
            print("claimInformerSuccess 调用失败:", e)

    elif prediction_label == "0":
        print("XRID结果: 无转售行为 => 举报不成立, 准备调用 confiscateInformerDeposit ...")
        try:
            contract_func = EscrowDeposit.functions.confiscateInformerDeposit(
                jinx_addr,
                original_id,
                suspicion_id
            )
            receipt = send_tx_with_sign(contract_func, agent_address, agent_privkey)
            if receipt.status == 1:
                print("\033[92mconfiscateInformerDeposit 交易完成! 您 的保证金已被没收。\033[0m")
            else:
                print("【警告】confiscateInformerDeposit 执行失败/回滚。")
        except Exception as e:
            print("confiscateInformerDeposit 调用失败:", e)
    else:
        print("无法确认是否存在转售行为 (prediction_label 非 0/1)，不执行后续合约操作。")

##############################################################################
# 5. 主流程: "report"
##############################################################################

def main():
    if len(sys.argv) < 2:
        print("用法: python function_7_informer.py report <tokenIdA> <tokenIdB> <jinxAddr>")
        sys.exit(1)

    mode = sys.argv[1]
    if mode != "report":
        print(f"暂只支持: python function_7_informer.py report ...")
        sys.exit(1)

    if len(sys.argv) < 5:
        print("用法: python function_7_informer.py report <tokenIdA> <tokenIdB> <jinxAddr>")
        sys.exit(1)

    tokenA_str = sys.argv[2]
    tokenB_str = sys.argv[3]
    jinx_addr = sys.argv[4]

    if not tokenA_str.isdigit() or not tokenB_str.isdigit():
        print("tokenIdA / tokenIdB 非数字")
        sys.exit(1)

    tokenIdA = int(tokenA_str)
    tokenIdB = int(tokenB_str)

    # 1) 检查 listing
    stA = check_listing_status(tokenIdA)
    stB = check_listing_status(tokenIdB)
    if stA!="Listed" or stB!="Listed":
        print(f"tokenIdA={tokenIdA}({stA}), tokenIdB={tokenIdB}({stB}) => 有NFT不在售,退出.")
        sys.exit(0)
    print(f"tokenIdA={tokenIdA} 与 tokenIdB={tokenIdB} 都在售(Listed).")

    # 2) 等 2 ETH
    stake_eth = 2.0
    tx_hash = wait_for_jinx_transaction(jinx_addr, agent_address, stake_eth)
    print(f"已检测到 您->Agent {stake_eth} ETH, txHash={tx_hash}")

    # 3) original/suspicion
    tA = get_timestamp(tokenIdA)
    tB = get_timestamp(tokenIdB)
    if tA < tB:
        original_id = tokenIdA
        suspicion_id = tokenIdB
    else:
        original_id = tokenIdB
        suspicion_id = tokenIdA
    print(f"originalTokenId={original_id}, suspicionTokenId={suspicion_id}")

    # 4) informerDeposit(...)
    stake_wei = w3.to_wei(stake_eth, "ether")
    try:
        print(f"=== 以Agent informerDeposit(informer={jinx_addr}, original={original_id}, suspicion={suspicion_id}, 2ETH) ===")

        jinx_addr_checksum = w3.to_checksum_address(jinx_addr)
        contract_func = EscrowDeposit.functions.informerDeposit(jinx_addr_checksum, original_id, suspicion_id, stake_wei)
        receipt = send_tx_with_sign(contract_func, agent_address, agent_privkey, value=stake_wei)
        print("informerDeposit 交易哈希:", receipt.transactionHash.hex())
        if receipt.status == 0:
            print("【错误】交易执行失败或已回滚.")
            sys.exit(1)

        # 解析事件 InformerDeposited
        logs = EscrowDeposit.events.InformerDeposited().process_receipt(receipt, errors=DISCARD)
        if len(logs) > 0:
            evt_args = logs[0]["args"]
            i_informer = evt_args["informer"]
            i_original = evt_args["originalTokenId"]
            i_suspicion = evt_args["suspicionTokenId"]
            i_amount = evt_args["amount"]
            print(f"InformerDeposited => informer={i_informer}, original={i_original}, suspicion={i_suspicion}, amount={w3.from_wei(i_amount,'ether')} ETH")
        else:
            print("【提示】未解析到 InformerDeposited 事件,可能合约没发出或日志解析失败.")

        print("举报保证金提交成功! 接下来进行转售检测...")

    except Exception as e:
        print("informerDeposit 调用失败:", e)
        sys.exit(1)

    # 5) 下载并检测 => original_dataset / suspicion_dataset
    print("\n===== 开始下载 & 检测 originalTokenId / suspicionTokenId =====")
    download_and_decrypt(original_id, "original")
    download_and_decrypt(suspicion_id, "suspicion")

    # 6) 运行 XRID 检测 => interpret => 决定后续合约处理
    run_xrid_check(original_id, suspicion_id, jinx_addr)

    print("==== 举报 & 检测 流程完毕 ====")

if __name__=="__main__":
    main()
