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

def prepare_poweroftau_for_user_contribution(dataset_folder: str, ptau_info: dict) -> dict:
    """
    为用户贡献准备Powers of Tau初始文件
    """
    try:
        logging.info("准备Powers of Tau初始文件，等待用户在浏览器中贡献")
        
        # 从ptau_info中获取配置信息，并重新创建生成器
        optimal_config = ptau_info["optimal_config"]
        user_id = ptau_info["user_id"]
        
        # 重新创建生成器实例
        from .poweroftau_generator import PowerOfTauGenerator
        generator = PowerOfTauGenerator()
        
        # 生成初始Powers of Tau文件，准备让用户在浏览器中贡献
        constraint_power = optimal_config['power']
        initial_info = generator.generate_initial_ptau_for_user_contribution(constraint_power, user_id)
        
        logging.info(f"初始Powers of Tau文件已准备完成: {initial_info['initial_ptau_path']}")
        
        return {
            "status": "ready_for_user_contribution",
            "initial_ptau_info": initial_info,
            "optimal_config": optimal_config,
            "user_id": user_id,
            "constraint_power": constraint_power,
            "message": "初始Powers of Tau文件已准备完成，等待用户在浏览器中贡献"
        }
        
    except Exception as e:
        logging.error(f"准备Powers of Tau失败: {e}")
        raise

def generate_zk_proof_for_watermark(dataset_folder: str, ptau_info: dict) -> dict:
    """
    为检测到的水印生成零知识证明
    
    Args:
        dataset_folder: 数据集文件夹路径
        ptau_info: Powers of Tau信息
    
    Returns:
        零知识证明生成结果
    """
    try:
        logging.info("检测到水印，开始生成Powers of Tau和零知识证明")
        
        # 从ptau_info中获取配置信息，并重新创建生成器
        optimal_config = ptau_info["optimal_config"]
        user_id = ptau_info["user_id"]
        
        # 重新创建生成器实例
        from .poweroftau_generator import PowerOfTauGenerator
        generator = PowerOfTauGenerator()
        
        # 1. 生成完整的Powers of Tau（模拟用户贡献过程）
        logging.info("步骤1: 生成完整的Powers of Tau")
        constraint_power = optimal_config['power']
        
        # 生成初始ptau
        initial_ptau_path = generator.generate_powers_of_tau(constraint_power, user_id)
        
        # 模拟用户贡献（这里我们创建一个模拟的贡献文件）
        user_temp_dir = os.path.join(generator.temp_dir, f"user_{user_id}")
        contributed_ptau = os.path.join(user_temp_dir, f"pot{constraint_power}_0001.ptau")
        
        # 自动生成贡献（在实际应用中，这个步骤由用户在浏览器中完成）
        logging.info("步骤2: 自动生成Powers of Tau贡献")
        generator.contribute_with_entropy(
            initial_ptau_path, 
            contributed_ptau, 
            entropy=None,  # 自动生成熵值
            name="watermark_evidence_contribution"
        )
        
        # 完成Powers of Tau仪式
        logging.info("步骤3: 完成Powers of Tau仪式")
        final_ptau_path = generator.complete_powers_of_tau_ceremony(
            contributed_ptau, user_id, constraint_power
        )
        
        # 2. 生成零知识证明所需的文件
        logging.info("步骤4: 生成零知识证明所需的文件")
        
        # 获取项目根目录和LSB_groth16目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(current_dir))
        lsb_dir = os.path.join(project_root, "LSB_groth16")
        
        # 运行create_LSB_i.py生成必要的文件
        M = optimal_config.get("M", 1)
        m = optimal_config.get("m", 1024)
        
        create_cmd = ["python", "create_LSB_i.py", "--M", str(M), "--m", str(m)]
        
        result = subprocess.run(
            create_cmd,
            cwd=lsb_dir,
            capture_output=True,
            text=True,
            check=True,
            timeout=600  # 10分钟超时
        )
        
        logging.info(f"create_LSB_i.py执行完成: {result.stdout}")
        
        # 检查是否生成了所需的文件
        lsb_i_dir = os.path.join(lsb_dir, "LSB_i")
        if not os.path.exists(lsb_i_dir):
            raise RuntimeError("LSB_i目录未生成")
        
        # 查找生成的电路文件
        circuit_files = [f for f in os.listdir(lsb_i_dir) if f.endswith('.r1cs')]
        if not circuit_files:
            raise RuntimeError("未找到生成的电路文件(.r1cs)")
        
        logging.info(f"零知识证明完整流程完成，最终ptau文件: {final_ptau_path}")
        logging.info(f"电路文件: {circuit_files}")
        
        return {
            "status": "success",
            "circuit_files": circuit_files,
            "lsb_i_dir": lsb_i_dir,
            "optimal_config": optimal_config,
            "final_ptau_path": final_ptau_path,
            "message": "Powers of Tau和零知识证明文件生成完成"
        }
        
    except subprocess.CalledProcessError as e:
        logging.error(f"零知识证明生成过程失败: {e}")
        logging.error(f"错误输出: {e.stderr}")
        raise RuntimeError(f"零知识证明生成失败: {e.stderr}")
        
    except subprocess.TimeoutExpired as e:
        logging.error(f"零知识证明生成超时: {e}")
        raise RuntimeError("零知识证明生成超时")
        
    except Exception as e:
        logging.error(f"生成零知识证明失败: {e}")
        raise

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

    # 4) 分析数据集，为可能的零知识证明做准备（但不立即生成ptau）
    try:
        from .poweroftau_generator import PowerOfTauGenerator
        
        # 使用用户地址生成用户ID
        user_id = user_address.replace('0x', '')[:8] if user_address else 'default'
        
        # 初始化生成器并分析数据集
        generator = PowerOfTauGenerator()
        total_pixels = generator.calculate_dataset_pixels(dataset_folder)
        optimal_config = generator.get_optimal_constraints(total_pixels)
        
        logging.info(f"数据集分析完成: {total_pixels} 像素，最优约束: 2^{optimal_config['power']} = {optimal_config['constraint_size']}")
        
        # 保存配置信息供后续使用（当检测到水印时）
        ptau_info = {
            "total_pixels": total_pixels,
            "optimal_config": optimal_config,
            "user_id": user_id,
            "dataset_folder": dataset_folder  # 保存数据集路径供后续使用
        }
        
    except Exception as e:
        logging.error(f"数据集分析失败: {e}")
        error_msg = f"数据集分析失败: {str(e)}"
        print(error_msg)
        raise RuntimeError(error_msg)

    # 5) 调用 checkForWatermark.py 查看是否有水印
    #    如果返回 1 => 有水印 => 生成零知识证明
    #    如果返回 0 => 无水印 => 直接继续铸造
    try:
        # 指定输入目录为刚解压的dataset文件夹
        wm_cmd = ["python", "features/checkForWatermark.py", "--input", dataset_folder, "--verbose"]
        logging.info(f"执行水印检测命令: {wm_cmd}")
        # 添加120秒的超时控制
        wm_result = subprocess.run(wm_cmd, capture_output=True, text=True, check=True, timeout=120)
        wm_output = wm_result.stdout.strip()
        logging.info(f"水印检测脚本输出: {wm_output}")

        # 检查输出的第一行是否为 0 或 1
        result_line = wm_output.split('\n')[0] if '\n' in wm_output else wm_output
        
        if result_line == "1":
            logging.warning("检测到水印，涉嫌侵权！")
            
            # 立即告知用户侵权，拒绝铸造NFT
            violation_msg = "检测到您的数据集包含已有水印，涉嫌侵权行为。无法进行NFT铸造。"
            background_msg = "我们正在后台生成零知识证明来证明您的数据集确实包含水印，相关证明将发送给您。"
            
            logging.warning(violation_msg)
            logging.info(background_msg)
            print(f"{violation_msg}\n{background_msg}")
            
            # 启动后台任务生成零知识证明
            try:
                # 在后台生成零知识证明（这里先不阻塞，返回状态让用户知道）
                logging.info("开始后台生成Powers of Tau和零知识证明")
                
                # 准备Powers of Tau初始文件，等待用户贡献
                zk_proof_result = prepare_poweroftau_for_user_contribution(dataset_folder, ptau_info)
                logging.info(f"零知识证明生成成功: {zk_proof_result}")
                
                # 返回侵权状态和零知识证明结果
                return {
                    "status": "copyright_violation",
                    "message": violation_msg,
                    "background_message": background_msg,
                    "zk_proof_result": zk_proof_result,
                    "ptau_info": ptau_info,
                    "requires_user_contribution": True,  # 新增：标识需要用户在浏览器中完成贡献
                    "user_id": user_id,
                    "constraint_power": ptau_info["optimal_config"]["power"]
                }
                
            except Exception as zk_e:
                logging.error(f"零知识证明生成失败: {zk_e}")
                error_msg = f"检测到侵权行为。零知识证明生成过程中出现错误: {str(zk_e)}"
                print(error_msg)
                
                # 即使零知识证明生成失败，也要返回侵权状态
                return {
                    "status": "copyright_violation", 
                    "message": violation_msg,
                    "error": error_msg,
                    "ptau_info": ptau_info,
                    "requires_user_contribution": False  # 出错时不需要用户贡献
                }
                
        elif result_line == "0":
            logging.info("未检测到水印，数据集合规。需要用户转账3 ETH后才能进行NFT铸造。")
            
            # 返回需要转账的状态，不直接启动铸造脚本
            return {
                "status": "no_watermark_transfer_required",
                "message": "数据集检测通过，未发现水印。请转账3 ETH以完成NFT铸造。",
                "transfer_required": True,
                "ptau_info": ptau_info,
                "metadata_url": metadata_url,
                "user_address": user_address
            }
        else:
            logging.warning(f"水印检测脚本返回未知值: {result_line}")
            error_msg = "水印检测结果不明，暂不进行铸造。"
            print(error_msg)
            raise ValueError(error_msg)  # 同样抛出异常

    except subprocess.TimeoutExpired as e:
        logging.error(f"水印检测脚本执行超时: {e}")
        error_msg = "水印检测超时，请稍后重试或联系管理员。"
        print(error_msg)
        raise TimeoutError(error_msg)  # 超时异常

    except subprocess.CalledProcessError as e:
        logging.error(f"水印检测脚本执行失败: {e}")
        error_msg = f"水印检测失败，无法判断是否能铸造: {e}"
        print(error_msg)
        raise RuntimeError(error_msg)  # 执行错误异常


# 独立的函数用于在转账确认后启动铸造脚本
def start_nft_minting(metadata_url: str, user_address: str, ptau_info: dict = None):
    """
    在转账确认后启动NFT铸造脚本
    """
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
        
        # 创建状态跟踪文件，统一保存在status目录下
        project_root = os.path.dirname(os.path.dirname(__file__))  # my_agent_project 目录
        status_dir = os.path.join(project_root, "status")
        os.makedirs(status_dir, exist_ok=True)
        status_file_path = os.path.join(status_dir, f"mint_status_{session_id}.json")
        status_data = {
            "session_id": session_id,
            "timestamp": timestamp,
            "metadata_url": metadata_url,
            "user_address": user_address,
            "status": "started",
            "start_time": time.time(),
            "ptau_info": ptau_info or {}  # 添加ptau信息
        }
        
        with open(status_file_path, "w") as status_file:
            json.dump(status_data, status_file)
        
        # 打开日志文件以追加模式写入
        with open(log_file_path, "a") as log_file:
            log_file.write(f"\n\n--- 新铸造请求 {metadata_url} {user_address} (会话ID: {session_id}) ---\n")
            if ptau_info:
                log_file.write(f"Powers of Tau配置: {ptau_info.get('optimal_config', {})}\n")
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
            if ptau_info:
                logging.info(f"Powers of Tau配置: {ptau_info.get('optimal_config', {})}")
        
        print("NFT铸造请求已提交（后台处理中）。")
        
        # 返回状态信息
        return {
            "status": "processing",
            "message": "NFT铸造请求已提交，正在后台处理",
            "session_id": session_id,
            "ptau_info": ptau_info or {}
        }
    except Exception as error:
        logging.error(f"提交铸造脚本失败: {error}")
        print("提交铸造脚本失败。")
        raise