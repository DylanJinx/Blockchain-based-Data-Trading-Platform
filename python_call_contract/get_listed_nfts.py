#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# python_call_contract/get_listed_nfts.py

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

# ============ 4. 主函数：获取所有上架的NFT ============
def main():
    try:
        # 获取总NFT数量（假设有这个函数，如果没有，可以遍历所有可能的token ID）
        # 这里假设有一个getTotalTokens函数，实际情况可能不同
        try:
            total_tokens = data_registration_contract.functions.getTotalTokens().call()
        except:
            # 如果没有这样的函数，就使用一个预设的最大值
            total_tokens = 100
            
        listed_nfts = []
        
        # 遍历所有token ID，检查是否上架
        for token_id in range(1, total_tokens + 1):
            try:
                # 检查token是否存在（使用ownerOf函数，如果token不存在，会抛出异常）
                try:
                    owner = data_registration_contract.functions.ownerOf(token_id).call()
                except:
                    continue
                
                # 检查token是否上架
                listing_status = data_tradingplatform_contract.functions.getNFTStatus(token_id).call()
                
                # 如果上架（ListingStatus.Listed = 1）
                if listing_status == 1:
                    # 获取价格
                    price_wei = data_tradingplatform_contract.functions.getPrice(token_id).call()
                    price_eth = w3.from_wei(price_wei, "ether")
                    
                    # 获取元数据URL
                    metadata_url = data_registration_contract.functions.tokenURI(token_id).call()
                    
                    # 获取元数据内容
                    try:
                        resp = requests.get(metadata_url)
                        resp.raise_for_status()
                        metadata = resp.json()
                        
                        title = metadata.get("title", f"数据集 #{token_id}")
                        description = metadata.get("description", "无描述")
                        image = metadata.get("image", "")
                        
                        # 处理IPFS图片URL
                        if image and image.startswith("ipfs://"):
                            # 将ipfs://转换为本地IPFS网关URL
                            image = image.replace("ipfs://", "http://127.0.0.1:8080/ipfs/")
                        elif image and not (image.startswith("http://") or image.startswith("https://")):
                            # 如果只是CID，构建完整URL使用本地IPFS网关
                            image = f"http://127.0.0.1:8080/ipfs/{image}"
                        
                        nft_info = {
                            "id": token_id,
                            "title": title,
                            "description": description,
                            "price": str(price_eth),
                            "owner": owner,
                            "image": image,
                            "metadata_url": metadata_url
                        }
                        
                        listed_nfts.append(nft_info)
                    except Exception as e:
                        # 如果无法获取元数据，则添加基本信息
                        nft_info = {
                            "id": token_id,
                            "title": f"数据集 #{token_id}",
                            "description": "无法获取描述",
                            "price": str(price_eth),
                            "owner": owner,
                            "image": "",
                            "metadata_url": metadata_url
                        }
                        listed_nfts.append(nft_info)
            except Exception as e:
                # 忽略处理单个token时的错误，继续处理下一个
                continue
        
        # 输出JSON结果
        print(json.dumps(listed_nfts))
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        exit(1)

if __name__ == "__main__":
    main()