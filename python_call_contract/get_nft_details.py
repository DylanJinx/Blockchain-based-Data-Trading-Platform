#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# python_call_contract/get_nft_details.py

import json
import sys
import requests
from web3 import Web3, HTTPProvider
from web3.logs import DISCARD

# ============ 1. 基本配置 ============
RPC_URL = "http://127.0.0.1:8545"

# ============ 2. 读取部署信息 & 初始化 web3 ============
with open("deploy_address.json", "r") as f:
    deploy_info = json.load(f)

data_registration_addr = deploy_info["DataRegistration"]
data_tradingplatform_addr = deploy_info["DataTradingPlatform"]

# 不使用系统代理，防止本地连接被代理阻断
session = requests.Session()
session.trust_env = False
w3 = Web3(HTTPProvider(RPC_URL, session=session))

if not w3.is_connected():
    print(json.dumps({"error": "无法连接到本地 Anvil，请检查 RPC_URL。"}))
    exit(1)

# ============ 3. 读取 ABI ============
def load_abi(json_path):
    with open(json_path, "r") as f:
        artifact = json.load(f)
        return artifact["abi"]

data_registration_abi = load_abi("../BDTP_contract/out/DataRegistration.sol/DataRegistration.json")
data_tradingplatform_abi = load_abi("../BDTP_contract/out/DataTradingPlatform.sol/DataTradingPlatform.json")

data_registration_contract = w3.eth.contract(
    address=data_registration_addr,
    abi=data_registration_abi
)

data_tradingplatform_contract = w3.eth.contract(
    address=data_tradingplatform_addr,
    abi=data_tradingplatform_abi
)

# ============ 4. 主函数：获取指定NFT的详细信息 ============
def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "请提供 token_id 参数"}))
        exit(1)
        
    try:
        token_id = int(sys.argv[1])
    except ValueError:
        print(json.dumps({"error": "token_id 必须是整数"}))
        exit(1)
        
    try:
        # 检查token是否存在
        try:
            owner = data_registration_contract.functions.ownerOf(token_id).call()
        except:
            print(json.dumps({"error": f"token_id {token_id} 不存在"}))
            exit(1)
            
        # 获取上架状态
        listing_status_code = data_tradingplatform_contract.functions.getNFTStatus(token_id).call()
        listing_status = "Listed" if listing_status_code == 1 else "NotListed" if listing_status_code == 0 else "Unlisted"
        
        # 获取价格（如果上架）
        price_eth = 0
        if listing_status == "Listed":
            price_wei = data_tradingplatform_contract.functions.getPrice(token_id).call()
            price_eth = w3.from_wei(price_wei, "ether")
            
        # 获取元数据URL
        metadata_url = data_registration_contract.functions.tokenURI(token_id).call()
        
        # 获取铸造时间戳（如果合约有这个函数）
        timestamp = 0
        try:
            timestamp = data_registration_contract.functions.tokenIdToTimestamp(token_id).call()
        except:
            pass
            
        # 尝试获取元数据内容
        title = f"数据集 #{token_id}"
        description = "无描述"
        image = ""
        
        try:
            resp = requests.get(metadata_url)
            resp.raise_for_status()
            metadata = resp.json()
            
            title = metadata.get("title", title)
            description = metadata.get("description", description)
            image = metadata.get("image", "")
            
            # 处理IPFS图片URL
            if image and image.startswith("ipfs://"):
                # 将ipfs://转换为本地IPFS网关URL
                image = image.replace("ipfs://", "http://127.0.0.1:8080/ipfs/")
            elif image and not (image.startswith("http://") or image.startswith("https://")):
                # 如果只是CID，构建完整URL使用本地IPFS网关
                image = f"http://127.0.0.1:8080/ipfs/{image}"
        except:
            pass
            
        # 构建详细信息对象
        nft_details = {
            "id": token_id,
            "title": title,
            "description": description,
            "owner": owner,
            "listing_status": listing_status,
            "price": str(price_eth) if price_eth else "0",
            "image": image,
            "metadata_url": metadata_url,
            "timestamp": timestamp
        }
        
        # 输出JSON结果
        print(json.dumps(nft_details))
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        exit(1)

if __name__ == "__main__":
    main()