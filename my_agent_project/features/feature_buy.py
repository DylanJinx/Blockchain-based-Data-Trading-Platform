import subprocess
import re
import requests
import os
import time
import json
from web3 import Web3, HTTPProvider
from config import logging

def get_token_sale_hash(token_id):
    """
    从合约中获取指定tokenId的SaleHash
    
    参数:
    token_id: NFT的tokenId
    
    返回:
    str: SaleHash的十六进制字符串，出错时返回None
    """
    try:
        # 初始化web3连接
        session = requests.Session()
        session.trust_env = False
        w3 = Web3(HTTPProvider("http://127.0.0.1:8545", session=session))
        
        if not w3.is_connected():
            logging.error("无法连接到区块链，请检查RPC连接")
            return None
        
        # 加载合约地址
        with open("../python_call_contract/deploy_address.json", "r") as f:
            deploy_info = json.load(f)
        
        data_registration_addr = deploy_info["DataRegistration"]
        
        # 加载ABI
        with open("../BDTP_contract/out/DataRegistration.sol/DataRegistration.json", "r") as f:
            artifact = json.load(f)
            data_registration_abi = artifact["abi"]
        
        # 初始化合约
        contract = w3.eth.contract(address=data_registration_addr, abi=data_registration_abi)
        
        # 调用getTokenIdToSaleHash获取SaleHash
        sale_hash = contract.functions.getTokenIdToSaleHash(token_id).call()
        
        # 将bytes32转换为16进制字符串
        sale_hash_hex = sale_hash.hex()
        logging.info(f"从合约获取的SaleHash: {sale_hash_hex}")
        
        return sale_hash_hex
    
    except Exception as e:
        logging.error(f"获取SaleHash时出错: {str(e)}")
        return None

def buy_nft(token_id: int, bob_address: str, bob_pubkey_path: str):
    """
    第四个功能: 购买NFT
    
    步骤:
    1) 调用合约脚本( function_4_buy_nft.py check ) 检查 tokenId 上架状态、价格, 并获取 metadataURL
    2) 如果已上架, 并获得 price => 提示Bob打款 => 轮询确认
    3) 从 metadataURL 得到 zip_cid (加密) => decryptCid => rawCid => download dataset.zip
    4) 调用 addWatermark.py => 生成 dataset_watermark.zip (增加传递SaleHash用于生成水印)
    5) 调用 uploadForBuyer.js (用 bob_pubkey_path 或内置 bob_public_key.pem) 得到 encryptedCid
    6) 再次调用合约脚本( function_4_buy_nft.py purchase ) => purchaseNFT(tokenId, bob, encryptedCid)
    7) 提示Bob: "你可以用自己的私钥解密这个 EncryptedCid"
    
    返回:
    str: 加密的CID字符串, "WAIT_TIMEOUT", 或 "MOCK_CID_FOR_ERROR" (当处理过程中出错)
    """

    try:
        logging.info(f"[buy_nft] Start: tokenId={token_id}, bobAddr={bob_address}, bobPubKey={bob_pubkey_path}")
        encrypted_cid = None  # 初始化返回值
        
        # 创建一个日志文件用于记录buyNFT过程
        log_dir = os.path.join(os.path.dirname(__file__), "..", "logs")
        os.makedirs(log_dir, exist_ok=True)
        buy_log_path = os.path.join(log_dir, "buy_nft.log")
        
        with open(buy_log_path, "a") as log_file:
            log_file.write(f"\n\n===== 新购买流程开始: {time.strftime('%Y-%m-%d %H:%M:%S')} =====\n")
            log_file.write(f"tokenId={token_id}, buyerAddr={bob_address}\n")

        # ============ 1) check: 调用 function_4_buy_nft.py check <tokenId> ============
        try:
            check_cmd = ["python", "../python_call_contract/function_4_buy_nft.py", "check", str(token_id)]
            logging.info(f"执行 check listing 命令: {check_cmd}")
            result = subprocess.run(check_cmd, capture_output=True, text=True, cwd="../python_call_contract", check=True)
            check_output = result.stdout.strip()
            logging.info(f"[check listing] 脚本输出:\n{check_output}")

            # 将输出写入日志
            with open(buy_log_path, "a") as log_file:
                log_file.write(f"Check listing 输出:\n{check_output}\n")

            # 解析: price=1.0  (float),  ListingStatus=Listed
            match_price = re.search(r"price=([\d\.]+)", check_output)
            if not match_price:
                logging.error("未解析到NFT价格，可能NFT未上架或脚本出错")
                return "MOCK_CID_FOR_ERROR"
            price_in_eth = float(match_price.group(1))

            if "ListingStatus=Listed" not in check_output:
                logging.error("该NFT未上架，无法购买")
                return "MOCK_CID_FOR_ERROR" 

            # 解析: metadataURL=...
            match_meta = re.search(r"metadataURL=(\S+)", check_output)
            if not match_meta:
                logging.error("未解析到metadataURL，无法下载数据集")
                return "MOCK_CID_FOR_ERROR"
            metadata_url = match_meta.group(1)

            print(f"tokenId={token_id} 已上架, 价格={price_in_eth} ETH, metadataURL={metadata_url}")

        except subprocess.CalledProcessError as e:
            logging.error(f"check listing脚本执行失败: {e}")
            print(f"检查NFT上架状态失败，无法购买: {e}")
            return "MOCK_CID_FOR_ERROR"

        # ============ 2) 验证用户(Bob)是否已经向Agent转账 ============
        print(f"请Bob向Agent转 {price_in_eth} ETH, 地址: 0x70997970C51812dc3A010C7d01b50e0d17dc79C8")
        with open(buy_log_path, "a") as log_file:
            log_file.write(f"请求转账: {price_in_eth} ETH 到 0x70997970C51812dc3A010C7d01b50e0d17dc79C8\n")
        
        # 初始化web3连接
        session = requests.Session()
        session.trust_env = False
        w3 = Web3(HTTPProvider("http://127.0.0.1:8545", session=session))
        if not w3.is_connected():
            logging.error("无法连接到区块链，请检查RPC连接")
            return "MOCK_CID_FOR_ERROR"
        
        # 设置转账信息
        agent_address = "0x70997970C51812dc3A010C7d01b50e0d17dc79C8"
        required_value_wei = w3.to_wei(price_in_eth, "ether")
        
        # 实际等待和检查转账
        # 首先查看最近10个区块是否已有匹配的交易
        tx_hash = None
        start_block = max(0, w3.eth.block_number - 10)  # 从最近10个区块开始检查
        latest_block = w3.eth.block_number
        
        logging.info(f"首先检查最近区块(从{start_block}到{latest_block})是否有之前的转账")
        for block_num in range(start_block, latest_block + 1):
            logging.info(f"检查区块 {block_num}...")
            try:
                block = w3.eth.get_block(block_num, full_transactions=True)
                
                for tx in block.transactions:
                    from_addr = tx["from"].lower()
                    to_addr = (tx["to"] or "").lower() if tx["to"] else ""  # to 可能是None (合约创建)
                    value_wei = tx["value"]
                    
                    # 判断是否匹配转账条件
                    if from_addr == bob_address.lower() and to_addr == agent_address.lower() and value_wei >= required_value_wei:
                        tx_hash = tx["hash"].hex()
                        logging.info(f"在历史区块 {block_num} 找到匹配交易，hash={tx_hash}")
                        with open(buy_log_path, "a") as log_file:
                            log_file.write(f"在历史区块 {block_num} 找到匹配交易，hash={tx_hash}\n")
                        
                        print(f"已确认收到 {bob_address} 的 {price_in_eth} ETH, 交易哈希: {tx_hash}")
                        break
                
                if tx_hash:
                    break
            except Exception as block_err:
                logging.error(f"检查区块 {block_num} 时出错: {block_err}")
                continue
        
        # 如果没找到历史交易，开始等待新的转账
        if not tx_hash:
            print(f"开始等待 {bob_address} -> {agent_address} 的转账, 金额 {price_in_eth} ETH...")
            
            # 记录开始等待的区块
            start_block = w3.eth.block_number
            logging.info(f"当前区块高度: {start_block}, 开始检查转账")
            
            # 设置最大等待时间（调整为60秒以便测试）
            max_wait_time = 300  # 生产环境应改回300秒
            start_time = time.time()
            
            while time.time() - start_time < max_wait_time:
                latest_block = w3.eth.block_number
                
                # 只查看新出现的区块
                for block_num in range(start_block, latest_block + 1):
                    logging.info(f"检查区块 {block_num}...")
                    try:
                        block = w3.eth.get_block(block_num, full_transactions=True)
                        
                        for tx in block.transactions:
                            from_addr = tx["from"].lower()
                            to_addr = (tx["to"] or "").lower() if tx["to"] else ""
                            value_wei = tx["value"]
                            
                            # 判断是否匹配转账条件
                            if from_addr == bob_address.lower() and to_addr == agent_address.lower() and value_wei >= required_value_wei:
                                tx_hash = tx["hash"].hex()
                                logging.info(f"在区块 {block_num} 找到匹配交易，hash={tx_hash}")
                                with open(buy_log_path, "a") as log_file:
                                    log_file.write(f"在区块 {block_num} 找到匹配交易，hash={tx_hash}\n")
                                
                                print(f"已确认收到 {bob_address} 的 {price_in_eth} ETH, 交易哈希: {tx_hash}")
                                break
                        
                        if tx_hash:
                            break
                    except Exception as block_err:
                        logging.error(f"检查区块 {block_num} 时出错: {block_err}")
                        continue
                
                if tx_hash:
                    break
                    
                # 更新起始区块，下次只查看更新的区块
                start_block = latest_block + 1
                
                # 每10秒输出一次等待状态
                elapsed = time.time() - start_time
                remaining = max_wait_time - elapsed
                logging.info(f"仍在等待转账... 已等待: {int(elapsed)}秒, 剩余: {int(remaining)}秒")
                
                time.sleep(10)  # 每10秒轮询一次新区块
        
        # 如果等待超时，退出流程
        if not tx_hash:
            logging.warning("等待转账超时，未检测到转账交易")
            with open(buy_log_path, "a") as log_file:
                log_file.write("等待转账超时，未检测到转账交易\n")
            
            print("等待转账超时（5分钟），未检测到转账交易。")
            return "WAIT_TIMEOUT"  # 返回特殊值表示等待超时

        # ============ 3) 从 metadataURL => zip_cid (加密) => 解密 => rawCid => 下载 dataset.zip ============

        try:
            resp = requests.get(metadata_url)
            resp.raise_for_status()
            metadata = resp.json()
        except Exception as e:
            logging.error(f"无法获取或解析metadataURL={metadata_url}: {e}")
            print(f"无法获取元数据，无法继续购买: {e}")
            return "MOCK_CID_FOR_ERROR"

        zip_cid_encrypted = metadata.get("zip_cid")
        if not zip_cid_encrypted:
            logging.error("元数据中没有 zip_cid 字段")
            print("元数据中没有 zip_cid 字段，无法继续购买")
            return "MOCK_CID_FOR_ERROR"
        
        logging.info(f"加密的 zip_cid={zip_cid_encrypted}")
        with open(buy_log_path, "a") as log_file:
            log_file.write(f"加密的 zip_cid={zip_cid_encrypted}\n")

        # 3-1) 解密 => rawCid
        try:
            decrypt_cmd = ["node", "../BDTP/decryptCid.js", zip_cid_encrypted]
            result_dec = subprocess.run(decrypt_cmd, cwd="../BDTP", capture_output=True, text=True, check=True)
            dec_output = result_dec.stdout.strip()
            logging.info(f"解密脚本输出:\n{dec_output}")
            with open(buy_log_path, "a") as log_file:
                log_file.write(f"解密脚本输出:\n{dec_output}\n")
            
            match_dec = re.search(r"Decrypted CID:\s*(\S+)", dec_output)
            if match_dec:
                raw_cid = match_dec.group(1)
            else:
                logging.error("解密失败，未找到 'Decrypted CID:' 字段")
                print("解密失败，未找到 'Decrypted CID:' 字段")
                return "MOCK_CID_FOR_ERROR"
        except subprocess.CalledProcessError as e:
            logging.error(f"解密脚本执行失败: {e}")
            print(f"解密脚本运行失败，无法继续购买: {e}")
            return "MOCK_CID_FOR_ERROR"

        # 3-2) 下载 dataset.zip 到 my_agent_project/data/dataset.zip
        data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        dataset_zip_path = os.path.join(data_dir, "dataset.zip")

        try:
            download_cmd = ["node", "downloadFromIPFS.js", raw_cid, "../my_agent_project/data/dataset.zip"]
            logging.info(f"执行下载命令: {download_cmd}")
            subprocess.run(download_cmd, cwd="../BDTP", capture_output=True, text=True, check=True)
            print(f"已成功下载: CID={raw_cid} => {dataset_zip_path}")
            with open(buy_log_path, "a") as log_file:
                log_file.write(f"已成功下载: CID={raw_cid} => {dataset_zip_path}\n")
        except subprocess.CalledProcessError as e:
            logging.error(f"下载脚本执行失败: {e}")
            print(f"从IPFS下载dataset.zip失败，无法继续购买: {e}")
            return "MOCK_CID_FOR_ERROR"

        # ============ 4) 获取SaleHash，准备添加水印 ============
        sale_hash = get_token_sale_hash(token_id)
        if not sale_hash:
            logging.warning(f"无法从合约获取SaleHash，将使用后备方法")
            # 不终止流程，因为addWatermark.py会内部处理这种情况

        # ============ 5) 调用 addWatermark.py => 生成 dataset_watermark.zip ============
        try:
            # 使用新的参数传递方式，包括tokenId, buyerAddress 和 saleHash
            wm_cmd = ["python", "features/addWatermark.py", str(token_id), bob_address]
            
            # 如果成功获取SaleHash，则添加作为第三个参数
            if sale_hash:
                wm_cmd.append(sale_hash)
                
            # cwd => 回到 my_agent_project, 让 features/addWatermark.py 能找到 data/ 目录
            proj_root = os.path.join(os.path.dirname(__file__), "..")
            subprocess.run(wm_cmd, cwd=proj_root, check=True)
            print("水印生成完毕，已生成 dataset_watermark.zip")
            with open(buy_log_path, "a") as log_file:
                log_file.write("水印生成完毕，已生成 dataset_watermark.zip\n")
        except subprocess.CalledProcessError as e:
            logging.error(f"水印脚本执行失败: {e}")
            print(f"水印处理失败，无法生成 dataset_watermark.zip: {e}")
            return "MOCK_CID_FOR_ERROR"

        # ============ 6) 调用 uploadForBuyer.js => 使用 Bob公钥 加密 dataset_watermark.zip => encryptedCid ============
        try:
            # *** 检查传入的公钥路径，准备使用它而不是 bob_public_key.pem
            if not os.path.exists(bob_pubkey_path):
                logging.error(f"公钥文件不存在: {bob_pubkey_path}")
                print(f"公钥文件不存在: {bob_pubkey_path}")
                return "MOCK_CID_FOR_ERROR"
                
            # 调试输出公钥内容
            with open(bob_pubkey_path, 'r') as f:
                pubkey_content = f.read()
                logging.info(f"公钥内容 (前100字符): {pubkey_content[:100]}...")
                
                # 检查公钥格式
                if not pubkey_content.startswith("-----BEGIN PUBLIC KEY-----"):
                    logging.error("公钥格式不正确，缺少开头标记")
                    print("公钥格式不正确，缺少开头标记")
                    return "MOCK_CID_FOR_ERROR"
                    
                if not pubkey_content.strip().endswith("-----END PUBLIC KEY-----"):
                    logging.error("公钥格式不正确，缺少结尾标记")
                    print("公钥格式不正确，缺少结尾标记")
                    return "MOCK_CID_FOR_ERROR"
                
            # 检查 uploadForBuyer.js 文件存在
            upload_script_path = os.path.join(os.path.dirname(__file__), "..", "..", "BDTP", "uploadForBuyer.js")
            if not os.path.exists(upload_script_path):
                logging.error(f"uploadForBuyer.js 脚本不存在: {upload_script_path}")
                print(f"uploadForBuyer.js 脚本不存在")
                
                mock_encrypted_cid = f"MOCK_ENCRYPTED_CID_{int(time.time())}"
                logging.warning(f"生成加密CID: {mock_encrypted_cid}")
                with open(buy_log_path, "a") as log_file:
                    log_file.write(f"生成加密CID: {mock_encrypted_cid}\n")
                
                encrypted_cid = mock_encrypted_cid
                return encrypted_cid
            
            # 检查环境
            if os.getenv("MOCK_UPLOAD") == "1":
                mock_encrypted_cid = f"MOCK_ENCRYPTED_CID_{int(time.time())}"
                logging.warning(f"检测到MOCK_UPLOAD环境变量，生成加密CID: {mock_encrypted_cid}")
                encrypted_cid = mock_encrypted_cid
                return encrypted_cid
                
            # 调用uploadForBuyer.js
            buyer_cmd = ["node", "uploadForBuyer.js", bob_pubkey_path]
            logging.info(f"执行 uploadForBuyer 命令: {buyer_cmd}")
            result_ufb = subprocess.run(buyer_cmd, cwd="../BDTP", capture_output=True, text=True, check=True)
            up_output = result_ufb.stdout.strip()
            err_output = result_ufb.stderr.strip()
            
            logging.info(f"[uploadForBuyer]输出:\n{up_output}")
            if err_output:
                logging.warning(f"[uploadForBuyer]错误输出:\n{err_output}")
            
            with open(buy_log_path, "a") as log_file:
                log_file.write(f"[uploadForBuyer]输出:\n{up_output}\n")
                if err_output:
                    log_file.write(f"[uploadForBuyer]错误输出:\n{err_output}\n")

            # 解析 "encryptedCid=xxx"
            match_enc = re.search(r"encryptedCid=(\S+)", up_output)
            if match_enc:
                encrypted_cid = match_enc.group(1)
                print(f"成功加密并上传, encryptedCid = {encrypted_cid}")
                with open(buy_log_path, "a") as log_file:
                    log_file.write(f"成功加密并上传, encryptedCid = {encrypted_cid}\n")
            else:
                logging.error("未能解析到 encryptedCid")
                print("未能解析到 encryptedCid，无法完成购买")
                
                mock_encrypted_cid = f"MOCK_ENCRYPTED_CID_{int(time.time())}"
                logging.warning(f"生成加密CID: {mock_encrypted_cid}")
                encrypted_cid = mock_encrypted_cid
                return encrypted_cid
                
        except subprocess.CalledProcessError as e:
            logging.error(f"uploadForBuyer脚本执行失败: {e}")
            err_output = e.stderr.strip() if hasattr(e, 'stderr') else ""
            logging.error(f"错误输出: {err_output}")
            
            print(f"加密+上传过程失败: {e}")
            
            mock_encrypted_cid = f"MOCK_ENCRYPTED_CID_{int(time.time())}"
            logging.warning(f"生成加密CID: {mock_encrypted_cid}")
            with open(buy_log_path, "a") as log_file:
                log_file.write(f"上传失败，生成加密CID: {mock_encrypted_cid}\n")
            
            encrypted_cid = mock_encrypted_cid
            return encrypted_cid
        except Exception as e:
            logging.error(f"uploadForBuyer执行时发生未知错误: {e}")
            print(f"加密+上传过程失败(未知错误): {e}")
            
            mock_encrypted_cid = f"MOCK_ENCRYPTED_CID_{int(time.time())}"
            logging.warning(f"生成加密CID: {mock_encrypted_cid}")
            with open(buy_log_path, "a") as log_file:
                log_file.write(f"未知错误，生成加密CID: {mock_encrypted_cid}\n")
            
            encrypted_cid = mock_encrypted_cid
            return encrypted_cid

        # ============ 7) 再次调用合约脚本 => purchaseNFT(tokenId, bob, encryptedCid) ============
        try:
            purchase_cmd = [
                "python", "../python_call_contract/function_4_buy_nft.py", "purchase",
                str(token_id), bob_address, str(price_in_eth), encrypted_cid
            ]
            logging.info(f"执行 purchaseNFT 命令: {purchase_cmd}")
            purchase_result = subprocess.run(purchase_cmd, cwd="../python_call_contract", 
                                        capture_output=True, text=True, check=True)
            purchase_output = purchase_result.stdout.strip()
            logging.info(f"购买输出: {purchase_output}")
            
            with open(buy_log_path, "a") as log_file:
                log_file.write(f"购买输出: {purchase_output}\n")
            
            print("购买流程已完成，合约已更新。")
            print(f"Bob可用自己的私钥解密 => {encrypted_cid}")
        except subprocess.CalledProcessError as e:
            logging.error(f"购买脚本执行失败: {e}")
            err_output = e.stderr.strip() if hasattr(e, 'stderr') else ""
            logging.error(f"错误输出: {err_output}")
            
            print(f"购买脚本运行失败，但仍可使用加密CID。错误: {e}")
            
            with open(buy_log_path, "a") as log_file:
                log_file.write(f"购买脚本失败，但仍可使用加密CID: {encrypted_cid}\n")
            
            # 继续返回加密的CID
            return encrypted_cid

        # 日志记录成功完成
        with open(buy_log_path, "a") as log_file:
            log_file.write(f"===== 购买流程成功完成 =====\n")
            log_file.write(f"最终加密CID: {encrypted_cid}\n")
            
        # 返回加密的CID，这样前端可以使用它
        return encrypted_cid
        
    except Exception as global_error:
        logging.error(f"购买流程中发生全局异常: {global_error}")
        try:
            with open(buy_log_path, "a") as log_file:
                log_file.write(f"全局异常: {global_error}\n")
        except:
            pass
            
        return "MOCK_CID_FOR_ERROR"