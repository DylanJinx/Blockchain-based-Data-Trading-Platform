import subprocess
import re
import requests
import sys
import os
import zipfile
import shutil
import json
import time
from config import logging

def register_data(metadata_url: str, user_address: str = None):
    """
    第一个功能: 数据登记(铸造NFT)
    1. 从 metadata_url 获取 JSON (包含 zip_cid 等字段)
    2. 使用 decryptCid.js 解密出 dataset.zip 的真实 CID
    3. 从IPFS下载数据集并解压
    4. 使用 checkForWatermark.py 检测是否水印
       - 若返回 1 => 有水印 => 禁止铸造
       - 若返回 0 => 无水印 => 调用 function_1_mint_nft.py 进行铸造
    """

    logging.info(f"[register_data] 开始登记数据集: {metadata_url}")

    # 1) 获取元数据 JSON
    try:
        resp = requests.get(metadata_url)
        resp.raise_for_status()
        metadata = resp.json()
    except Exception as e:
        logging.error(f"无法获取或解析 metadata_url 的内容: {e}")
        print("获取元数据失败，无法登记数据。")
        return

    # 提取 zip_cid
    zip_cid_encrypted = metadata.get("zip_cid")
    if not zip_cid_encrypted:
        logging.error("metadata 中未找到 zip_cid 字段。")
        print("元数据格式错误，无法登记数据。")
        return

    logging.info(f"在元数据中发现加密后的 zip_cid: {zip_cid_encrypted}")

    # 2) 调用 decryptCid.js 解密
    #    node ../BDTP/decryptCid.js <zip_cid_encrypted>
    #    输出示例: "Decrypted CID: QmXZ4goAz..."
    try:
        decrypt_cmd = ["node", "../BDTP/decryptCid.js", zip_cid_encrypted]
        logging.info(f"执行解密命令: {decrypt_cmd}")
        result = subprocess.run(
            decrypt_cmd, 
            cwd="../BDTP",
            capture_output=True, 
            text=True, 
            check=True
        )
        output = result.stdout.strip()
        logging.info(f"解密脚本输出: {output}")

        # 解析 output 中的 "Decrypted CID: XXXXXX"
        match = re.search(r"Decrypted CID:\s*(\S+)", output)
        if match:
            decrypted_cid = match.group(1)
            logging.info(f"解密得到真实CID: {decrypted_cid}")
        else:
            logging.error("未能在解密脚本输出中找到'Decrypted CID:'字段。")
            print("解密失败，无法登记数据。")
            return
    except subprocess.CalledProcessError as e:
        logging.error(f"解密脚本执行失败: {e}")
        print("解密脚本运行失败，无法登记数据。")
        return

    # 3) 下载数据集并解压
    data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    dataset_zip_path = os.path.join(data_dir, "dataset.zip")
    dataset_folder = os.path.join(data_dir, "dataset")

    # 清理旧文件
    if os.path.exists(dataset_folder):
        shutil.rmtree(dataset_folder)
    if os.path.isfile(dataset_zip_path):
        os.remove(dataset_zip_path)
    
    # 创建dataset文件夹
    os.makedirs(dataset_folder, exist_ok=True)

    try:
        # 下载数据集
        download_cmd = ["node", "downloadFromIPFS.js", decrypted_cid, "../my_agent_project/data/dataset.zip"]
        logging.info(f"执行下载命令: {download_cmd}")
        subprocess.run(download_cmd, cwd="../BDTP", capture_output=True, text=True, check=True)
        logging.info(f"已成功下载: CID={decrypted_cid} => {dataset_zip_path}")
    except subprocess.CalledProcessError as e:
        logging.error(f"下载脚本执行失败: {e}")
        print(f"从IPFS下载dataset.zip失败，无法继续登记: {e}")
        return

    # 解压文件
    try:
        with zipfile.ZipFile(dataset_zip_path, 'r') as zip_ref:
            zip_ref.extractall(dataset_folder)
        logging.info(f"已解压 {dataset_zip_path} 到 {dataset_folder}")
        
        # ============ 处理macOS生成的特殊文件夹 ============
        # 删除 __MACOSX 文件夹
        macosx_dir = os.path.join(dataset_folder, "__MACOSX")
        if os.path.exists(macosx_dir):
            shutil.rmtree(macosx_dir)
            logging.info(f"已删除: {macosx_dir}")
        
        # 检查并处理子文件夹
        subdirs = [d for d in os.listdir(dataset_folder) 
                   if os.path.isdir(os.path.join(dataset_folder, d)) and not d.startswith('__MACOSX')]
        
        for subdir in subdirs:
            subdir_path = os.path.join(dataset_folder, subdir)
            for filename in os.listdir(subdir_path):
                src = os.path.join(subdir_path, filename)
                dst = os.path.join(dataset_folder, filename)
                shutil.move(src, dst)
            shutil.rmtree(subdir_path)
            logging.info(f"已移动并删除子文件夹: {subdir_path}")
    except Exception as e:
        logging.error(f"解压文件失败: {e}")
        print(f"解压文件失败，无法继续登记: {e}")
        return

    # 4) 调用 checkForWatermark.py 查看是否有水印
    #    如果返回 1 => 有水印 => 禁止铸造
    #    如果返回 0 => 无水印 => 继续
    try:
        # 指定输入目录为刚解压的dataset文件夹
        wm_cmd = ["python", "features/checkForWatermark.py", "--input", dataset_folder, "--verbose"]
        logging.info(f"执行水印检测命令: {wm_cmd}")
        wm_result = subprocess.run(wm_cmd, capture_output=True, text=True, check=True)
        wm_output = wm_result.stdout.strip()
        logging.info(f"水印检测脚本输出: {wm_output}")

        # 检查输出的第一行是否为 0 或 1
        result_line = wm_output.split('\n')[0] if '\n' in wm_output else wm_output
        
        if result_line == "1":
            logging.warning("检测到水印，疑似转售行为，禁止铸造NFT")
            print("检测到水印，数据疑似转售行为。禁止铸造NFT。")
            return
        elif result_line == "0":
            logging.info("未检测到水印，可以进行铸造NFT。")
        else:
            logging.warning(f"水印检测脚本返回未知值: {result_line}")
            print("水印检测结果不明，暂不进行铸造。")
            return

    except subprocess.CalledProcessError as e:
        logging.error(f"水印检测脚本执行失败: {e}")
        print("水印检测失败，无法判断是否能铸造。")
        return

    # 5) 若通过水印检测 => 调用合约铸造脚本
    try:
        # 将metadata_url和user_address作为参数传递给function_1_mint_nft.py
        mint_cmd = ["python", "../python_call_contract/function_1_mint_nft.py", metadata_url]
        if user_address:
            mint_cmd.append(user_address)
            
        logging.info(f"开始调用合约铸造脚本: {mint_cmd}")
        
        # 创建日志目录(如果不存在)
        log_dir = os.path.join(os.path.dirname(__file__))
        os.makedirs(log_dir, exist_ok=True)
        
        # 确保日志文件存在
        log_file_path = os.path.join(log_dir, "mint_nft.log")
        if not os.path.exists(log_file_path):
            with open(log_file_path, "w") as f:
                f.write("# NFT铸造日志\n")
        
        # 获取当前时间戳用于标记铸造会话
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        session_id = int(time.time())
        
        # 创建状态跟踪文件
        status_file_path = os.path.join(log_dir, f"mint_status_{session_id}.json")
        status_data = {
            "session_id": session_id,
            "timestamp": timestamp,
            "metadata_url": metadata_url,
            "user_address": user_address,
            "status": "started",
            "start_time": time.time()
        }
        
        with open(status_file_path, "w") as status_file:
            json.dump(status_data, status_file)
        
        # 打开日志文件以追加模式写入
        with open(log_file_path, "a") as log_file:
            log_file.write(f"\n\n--- 新铸造请求 {metadata_url} {user_address} (会话ID: {session_id}) ---\n")
            log_file.flush()
            
            # 使用subprocess.Popen运行铸造脚本
            process = subprocess.Popen(
                mint_cmd, 
                cwd="../python_call_contract",
                stdout=log_file,
                stderr=log_file,
                text=True
            )
            
            # 更新状态文件，记录进程PID
            status_data["process_id"] = process.pid
            status_data["status"] = "running"
            with open(status_file_path, "w") as status_file:
                json.dump(status_data, status_file)
            
            # 记录进程信息到日志
            logging.info(f"铸造进程已启动，PID: {process.pid}, 会话ID: {session_id}, 日志文件: {log_file_path}")
            logging.info(f"铸造命令: {' '.join(mint_cmd)}")
            
            # 简化监控过程，不使用复杂的Python代码字符串
            # 直接返回处理状态
        
        print("NFT铸造请求已提交（后台处理中）。")
        
        # 返回最初的状态信息给调用者
        return {
            "status": "processing",
            "message": "NFT铸造请求已提交，正在后台处理",
            "session_id": session_id
        }
    except Exception as error:  # 修改这里，使用error变量名而不是e
        logging.error(f"提交铸造脚本失败: {error}")  # 使用error变量名
        print("提交铸造脚本失败。")
        raise  # 不要raise error，保留原始异常