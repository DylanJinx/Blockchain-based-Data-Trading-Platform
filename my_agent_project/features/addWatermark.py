import os
import shutil
import zipfile
import logging
import json
import hashlib
import time
from PIL import Image
import numpy as np
from web3 import Web3

def add_lsb_watermark(image_path, buy_hash, output_path):
    """
    将buy_hash水印信息嵌入到图像的最低有效位(LSB)
    
    参数:
    image_path: 原始图像路径
    buy_hash: 要嵌入的buy_hash值 (字符串)
    output_path: 输出图像路径
    
    返回:
    bool: 成功返回True，失败返回False
    """
    try:
        # 加载图像
        image = Image.open(image_path)
        
        # 检查是否是PNG/JPG格式
        if image.format not in ['PNG', 'JPEG', 'JPG']:
            # 如果不是，转换为RGB模式确保能够处理
            image = image.convert('RGB')
        
        # 将图像转换为numpy数组以便处理
        pixels = np.array(image)
        
        # 将buy_hash转换为二进制字符串
        binary_watermark = ''.join([bin(ord(c))[2:].rjust(8, '0') for c in buy_hash])
        watermark_length = len(binary_watermark)
        
        # 展平数组以便逐位嵌入
        pixels_flat = pixels.reshape(-1)
        
        if len(pixels_flat) < watermark_length:
            logging.error(f"图像 {os.path.basename(image_path)} 太小，无法嵌入完整的水印")
            return False
        
        # 嵌入水印信息
        for i in range(watermark_length):
            # 将最低位清零并替换为水印位
            pixels_flat[i] = (pixels_flat[i] & ~1) | int(binary_watermark[i])
        
        # 将剩余像素值的最低位设为0（从水印长度开始到图像结束）
        for i in range(watermark_length, len(pixels_flat)):
            pixels_flat[i] = pixels_flat[i] & ~1  # 清零最低位
        
        # 重构图像
        watermarked_pixels = pixels_flat.reshape(pixels.shape)
        watermarked_image = Image.fromarray(watermarked_pixels)
        
        # 保存水印图像
        watermarked_image.save(output_path)
        return True
    
    except Exception as e:
        logging.error(f"为图像 {os.path.basename(image_path)} 添加水印时出错: {str(e)}")
        return False

def generate_watermark_from_contract(token_id, buyer_address, sale_hash=None):
    """
    基于合约数据生成水印信息
    
    参数:
    token_id: NFT的tokenId
    buyer_address: 买家的以太坊地址
    sale_hash: 如果已知，直接使用该SaleHash值，否则从合约获取
    
    返回:
    tuple: (水印JSON字符串, buy_hash字符串)
    """
    timestamp = int(time.time())
    
    # 如果未提供sale_hash，尝试从合约获取
    if not sale_hash:
        try:
            # 初始化Web3连接
            w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))
            
            # 读取合约信息
            deploy_info_path = os.path.join(os.path.dirname(__file__), "..", "..", "python_call_contract", "deploy_address.json")
            with open(deploy_info_path, "r") as f:
                deploy_info = json.load(f)
            
            data_registration_addr = deploy_info["DataRegistration"]
            
            # 加载ABI
            abi_path = os.path.join(os.path.dirname(__file__), "..", "..", "BDTP_contract", "out", "DataRegistration.sol", "DataRegistration.json")
            with open(abi_path, "r") as f:
                artifact = json.load(f)
                data_registration_abi = artifact["abi"]
            
            # 初始化合约
            contract = w3.eth.contract(address=data_registration_addr, abi=data_registration_abi)
            
            # 调用getTokenIdToSaleHash获取SaleHash
            sale_hash = contract.functions.getTokenIdToSaleHash(token_id).call()
            
            # 将bytes32转换为16进制字符串
            sale_hash = sale_hash.hex()
            logging.info(f"从合约获取SaleHash: {sale_hash}")
        except Exception as e:
            logging.error(f"从合约获取SaleHash失败: {str(e)}")
            # 如果无法获取，使用一个基于tokenId的模拟值
            sale_hash = hashlib.sha256(f"fallback_sale_hash_{token_id}".encode()).hexdigest()
            logging.warning(f"使用后备SaleHash: {sale_hash}")
    
    # 计算buyHash = H(SaleHash, Buyer_address, timestamp)
    buy_hash_input = f"{sale_hash}{buyer_address.lower()}{timestamp}"
    buy_hash = hashlib.sha256(buy_hash_input.encode()).hexdigest()
    
    # 构建水印信息JSON对象
    watermark_data = {
        "token_id": token_id,
        "buyer_address": buyer_address,
        "sale_hash": sale_hash,
        "timestamp": timestamp,
        "buy_hash": buy_hash
    }
    
    # 添加校验和
    data_str = json.dumps(watermark_data, sort_keys=True)
    checksum = hashlib.sha256(data_str.encode()).hexdigest()[:8]
    watermark_data["checksum"] = checksum
    
    return json.dumps(watermark_data), buy_hash

def process_image_folder(input_folder, output_folder, buy_hash):
    """
    处理文件夹中的所有图像，添加水印
    
    参数:
    input_folder: 输入文件夹路径
    output_folder: 输出文件夹路径
    buy_hash: 要嵌入的buy_hash值
    
    返回:
    int: 成功处理的图像数量
    """
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    processed_count = 0
    supported_formats = ['.png', '.jpg', '.jpeg', '.bmp', '.gif']
    
    for root, dirs, files in os.walk(input_folder):
        for file in files:
            # 检查文件扩展名
            if any(file.lower().endswith(fmt) for fmt in supported_formats):
                input_path = os.path.join(root, file)
                # 计算相对路径，以便在输出目录中创建相同的结构
                rel_path = os.path.relpath(input_path, input_folder)
                output_path = os.path.join(output_folder, rel_path)
                
                # 确保输出目录存在
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                
                # 添加水印
                if add_lsb_watermark(input_path, buy_hash, output_path):
                    processed_count += 1
                    logging.info(f"成功为 {rel_path} 添加水印")
            else:
                # 对于非图像文件，直接复制
                input_path = os.path.join(root, file)
                rel_path = os.path.relpath(input_path, input_folder)
                output_path = os.path.join(output_folder, rel_path)
                
                # 确保输出目录存在
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                
                shutil.copy2(input_path, output_path)
    
    return processed_count

def main(token_id=None, buyer_address=None, sale_hash=None):
    """
    主函数，处理整个水印流程
    
    参数:
    token_id: NFT的tokenId (可选)
    buyer_address: 买家的以太坊地址 (可选)
    sale_hash: 从合约获取的SaleHash (可选)
    """
    # 配置日志
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    
    DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
    
    # 定义文件路径
    dataset_zip_path = os.path.join(DATA_DIR, "dataset.zip")              # data/dataset.zip
    dataset_folder = os.path.join(DATA_DIR, "dataset")                    # data/dataset/
    watermark_folder = os.path.join(DATA_DIR, "dataset_watermark")        # data/dataset_watermark/
    watermark_zip_path = os.path.join(DATA_DIR, "dataset_watermark.zip")  # data/dataset_watermark.zip
    watermark_info_path = os.path.join(DATA_DIR, "watermark_info.json")   # 保存水印信息
    
    # 检查输入文件是否存在
    if not os.path.isfile(dataset_zip_path):
        logging.error(f"{dataset_zip_path} 文件不存在，无法执行水印流程。")
        return False
    
    # 清理旧文件
    if os.path.exists(dataset_folder):
        shutil.rmtree(dataset_folder)
    if os.path.exists(watermark_folder):
        shutil.rmtree(watermark_folder)
    if os.path.isfile(watermark_zip_path):
        os.remove(watermark_zip_path)
    
    # 1) 解压 dataset.zip 到 dataset/
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
    
    # 2) 生成水印信息
    watermark_info = None
    if token_id and buyer_address:
        # 如果提供了token_id和buyer_address，使用合约信息生成水印
        watermark_info, buy_hash = generate_watermark_from_contract(token_id, buyer_address, sale_hash)
        logging.info(f"已生成基于合约的水印信息，使用buy_hash: {buy_hash}")
    else:
        # 否则生成一个基本的水印信息（用于测试）
        timestamp = int(time.time())
        buy_hash = hashlib.sha256(f"test_{timestamp}".encode()).hexdigest()
        logging.info(f"已生成测试buy_hash: {buy_hash}")
        
        # 创建一个简单的测试水印信息
        test_watermark = {
            "timestamp": timestamp,
            "note": f"This is a test watermark created at {timestamp}",
            "buy_hash": buy_hash,
            "checksum": hashlib.sha256(f"test_{timestamp}".encode()).hexdigest()[:8]
        }
        watermark_info = json.dumps(test_watermark)
    
    # 3) 处理文件夹中的所有图像，添加水印
    processed_count = process_image_folder(dataset_folder, watermark_folder, buy_hash)
    logging.info(f"已为 {processed_count} 个文件添加水印")
    
    # 4) 保存水印信息到文件，供以后检测使用 - 修改为追加模式
    watermark_record = {
        "buy_hash": buy_hash,
        "watermark_info": watermark_info,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "token_id": token_id,
        "buyer_address": buyer_address,
        "processed_files": processed_count
    }
    
    # 检查文件是否存在，如果存在则加载现有数据
    if os.path.exists(watermark_info_path):
        try:
            with open(watermark_info_path, 'r') as f:
                existing_data = json.load(f)
                
            # 如果现有数据是旧格式（单个记录），转换为新格式（多个记录）
            if "buy_hash" in existing_data and "records" not in existing_data:
                # 旧格式，转换为新格式
                new_data = {
                    "records": [existing_data],
                    "last_updated": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "total_records": 1
                }
                existing_data = new_data
            elif "records" not in existing_data:
                # 如果没有records字段，创建新的结构
                existing_data = {
                    "records": [],
                    "last_updated": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "total_records": 0
                }
        except (json.JSONDecodeError, FileNotFoundError):
            # 文件损坏或不存在，创建新的数据结构
            existing_data = {
                "records": [],
                "last_updated": time.strftime("%Y-%m-%d %H:%M:%S"),
                "total_records": 0
            }
    else:
        # 文件不存在，创建新的数据结构
        existing_data = {
            "records": [],
            "last_updated": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_records": 0
        }
    
    # 添加新的水印记录
    existing_data["records"].append(watermark_record)
    existing_data["last_updated"] = time.strftime("%Y-%m-%d %H:%M:%S")
    existing_data["total_records"] = len(existing_data["records"])
    
    # 保存更新后的数据
    with open(watermark_info_path, 'w') as f:
        json.dump(existing_data, f, indent=4)
    
    logging.info(f"已保存水印信息到: {watermark_info_path}，当前共有 {existing_data['total_records']} 条记录")
    
    # 5) 压缩 dataset_watermark => dataset_watermark.zip
    with zipfile.ZipFile(watermark_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(watermark_folder):
            for file in files:
                fullpath = os.path.join(root, file)
                arcname = os.path.relpath(fullpath, watermark_folder)
                zipf.write(fullpath, arcname)
    
    logging.info(f"已生成水印压缩包: {watermark_zip_path}")
    return True

if __name__ == "__main__":
    import sys
    
    # 从命令行获取参数
    token_id = None
    buyer_address = None
    sale_hash = None
    
    if len(sys.argv) > 1:
        token_id = int(sys.argv[1])
    if len(sys.argv) > 2:
        buyer_address = sys.argv[2]
    if len(sys.argv) > 3:
        sale_hash = sys.argv[3]
    
    main(token_id, buyer_address, sale_hash)