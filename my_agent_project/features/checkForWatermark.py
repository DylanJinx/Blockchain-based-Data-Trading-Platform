import os
import zipfile
import json
import logging
import tempfile
import shutil
import hashlib
import argparse
from PIL import Image
import numpy as np
import time
import sys
import re

def extract_lsb_watermark(image_path, expected_length=512):
    """
    从图像的最低有效位(LSB)中提取水印信息
    
    参数:
    image_path: 图像路径
    expected_length: 预期的水印二进制长度（十六进制hash的64个字符 × 8位/字符 = 512位）
    
    返回:
    str: 提取的buy_hash字符串，如果无法提取则返回None
    """
    try:
        # 加载图像
        image = Image.open(image_path)
        pixels = np.array(image)
        
        # 展平像素数组
        pixels_flat = pixels.reshape(-1)
        
        # 提取最低有效位，但只提取我们期望的哈希长度
        bits = []
        for i in range(min(expected_length, len(pixels_flat))):
            bits.append(str(pixels_flat[i] & 1))
        
        bit_string = ''.join(bits)
        
        # 每8位转换为一个字符
        chars = []
        for i in range(0, len(bit_string), 8):
            if i + 8 <= len(bit_string):  # 确保有完整的8位
                byte = bit_string[i:i+8]
                char_code = int(byte, 2)
                chars.append(chr(char_code))
        
        extracted_text = ''.join(chars)
        
        # 检查是否符合十六进制字符串格式（应该是64个十六进制字符）
        if re.match(r'^[0-9a-f]{64}$', extracted_text):
            return extracted_text
        
        # 如果不是64位的十六进制字符，尝试提取可能的部分哈希
        hex_part = re.search(r'([0-9a-f]{20,64})', extracted_text)
        if hex_part:
            return hex_part.group(1)
            
        return None
    
    except Exception as e:
        logging.error(f"提取水印时出错 ({os.path.basename(image_path)}): {str(e)}")
        return None

def validate_watermark(extracted_hash, expected_hashes=None):
    """
    验证提取的水印是否为有效的哈希值
    
    参数:
    extracted_hash: 提取的哈希字符串
    expected_hashes: 预期的哈希值列表 (可选)
    
    返回:
    tuple: (是否有效, 哈希字符串, 匹配的预期哈希)
    """
    # 检查是否是有效的十六进制字符串
    if not extracted_hash:
        return False, None, None
        
    if not re.match(r'^[0-9a-f]{64}$', extracted_hash):
        return False, extracted_hash, None
    
    # 如果提供了预期哈希列表，检查是否有匹配
    matched_hash = None
    if expected_hashes:
        for expected_hash in expected_hashes:
            if extracted_hash == expected_hash:
                matched_hash = expected_hash
                break
    
    # 如果提供了预期哈希但没有匹配，仍然返回True（格式有效）但标记未匹配
    return True, extracted_hash, matched_hash

def scan_folder_for_watermark(folder_path, expected_hashes=None, limit=None):
    """
    扫描文件夹，检查图像中的水印
    
    参数:
    folder_path: 要扫描的文件夹路径
    expected_hashes: 预期的buy_hash列表 (可选)
    limit: 最多扫描的文件数量，None表示扫描所有文件
    
    返回:
    tuple: (是否检测到水印, 检测到的水印信息, 验证结果)
    """
    supported_formats = ['.png', '.jpg', '.jpeg', '.bmp', '.gif']
    watermark_found = False
    detected_watermarks = []
    verification_results = []
    
    scanned_count = 0
    
    # 遍历文件夹中的所有图像文件
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if limit is not None and scanned_count >= limit:
                break
                
            if any(file.lower().endswith(fmt) for fmt in supported_formats):
                image_path = os.path.join(root, file)
                
                # 提取水印
                extracted_hash = extract_lsb_watermark(image_path)
                
                if extracted_hash:
                    valid, hash_value, matched_hash = validate_watermark(extracted_hash, expected_hashes)
                    
                    if valid:
                        detected_watermarks.append(hash_value)
                        
                        if matched_hash:
                            watermark_found = True  # 只要有一个匹配，就设置为True
                            verification_results.append({
                                "file": os.path.basename(image_path),
                                "is_valid": True,
                                "is_matched": True,
                                "message": "检测到匹配的buy_hash水印",
                                "extracted_hash": hash_value,
                                "matched_with": matched_hash
                            })
                            logging.info(f"在文件 {os.path.basename(image_path)} 中检测到匹配的水印: {hash_value}")
                        else:
                            verification_results.append({
                                "file": os.path.basename(image_path),
                                "is_valid": True,
                                "is_matched": False,
                                "message": "检测到有效但未知的buy_hash水印",
                                "extracted_hash": hash_value
                            })
                            logging.info(f"在文件 {os.path.basename(image_path)} 中检测到未知水印: {hash_value}")
                    else:
                        verification_results.append({
                            "file": os.path.basename(image_path),
                            "is_valid": False, 
                            "is_matched": False,
                            "message": "检测到格式不正确的水印",
                            "extracted_hash": hash_value
                        })
                        logging.info(f"在文件 {os.path.basename(image_path)} 中检测到无效水印: {hash_value}")
                
                scanned_count += 1
        
        if limit is not None and scanned_count >= limit:
            break
    
    # 计算验证通过率和匹配率
    valid_count = sum(1 for result in verification_results if result["is_valid"])
    matched_count = sum(1 for result in verification_results if result.get("is_matched", False))
    
    verification_rate = valid_count / len(verification_results) if verification_results else 0
    matching_rate = matched_count / len(verification_results) if verification_results else 0
    
    return watermark_found, detected_watermarks, {
        "verification_results": verification_results,
        "verification_rate": verification_rate,
        "matching_rate": matching_rate,
        "scanned_files": scanned_count
    }

def main():
    parser = argparse.ArgumentParser(description='检测图像数据集中的水印')
    parser.add_argument('--input', '-i', help='输入文件或文件夹路径')
    parser.add_argument('--hash', '-H', help='预期的buy_hash值')  # 改为-H避免冲突
    parser.add_argument('--limit', '-l', type=int, default=None, help='最多扫描的文件数量，默认扫描所有文件')
    parser.add_argument('--verbose', '-v', action='store_true', help='显示详细日志')
    
    args = parser.parse_args()
    
    # 配置日志级别
    log_level = logging.INFO if args.verbose else logging.WARNING
    logging.basicConfig(level=log_level, format="%(asctime)s - %(levelname)s - %(message)s")
    
    # 定义默认路径
    DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
    
    input_path = args.input if args.input else os.path.join(DATA_DIR, "dataset_watermark.zip")
    
    # 存储所有可能的预期hash值
    expected_hashes = []
    
    # 如果命令行提供了hash，添加到预期列表
    if args.hash:
        expected_hashes.append(args.hash)
    
    # 从watermark_info.json加载已知的buy_hash列表
    watermark_info_path = os.path.join(DATA_DIR, "watermark_info.json")
    if os.path.exists(watermark_info_path):
        try:
            with open(watermark_info_path, 'r') as f:
                info = json.load(f)
                
            # 处理新格式（多个记录）
            if "records" in info and isinstance(info["records"], list):
                for record in info["records"]:
                    if "buy_hash" in record and record["buy_hash"] not in expected_hashes:
                        expected_hashes.append(record["buy_hash"])
                        logging.info(f"从records加载buy_hash: {record['buy_hash']} (买家: {record.get('buyer_address', 'Unknown')}, 时间: {record.get('timestamp', 'Unknown')})")
                
                logging.info(f"从新格式watermark_info.json加载了 {len(info['records'])} 条水印记录")
                
            # 处理旧格式（单个记录）- 向后兼容
            elif "buy_hash" in info and info["buy_hash"] not in expected_hashes:
                expected_hashes.append(info["buy_hash"])
                logging.info(f"从旧格式watermark_info.json加载buy_hash: {info['buy_hash']}")
                
            # 处理其他可能的格式
            if "buy_hashes" in info and isinstance(info["buy_hashes"], list):
                for hash_value in info["buy_hashes"]:
                    if hash_value not in expected_hashes:
                        expected_hashes.append(hash_value)
                        logging.info(f"从buy_hashes列表加载buy_hash: {hash_value}")
                        
            # 处理可能存在的历史记录
            if "history" in info and isinstance(info["history"], list):
                for entry in info["history"]:
                    if "buy_hash" in entry and entry["buy_hash"] not in expected_hashes:
                        expected_hashes.append(entry["buy_hash"])
                        logging.info(f"从历史记录加载buy_hash: {entry['buy_hash']}")
                        
        except Exception as e:
            logging.warning(f"无法从{watermark_info_path}加载预期的buy_hash: {str(e)}")
    
    logging.info(f"总共加载了 {len(expected_hashes)} 个预期的buy_hash值用于匹配")
    
    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    try:
        # 处理不同类型的输入
        scan_dir = temp_dir
        
        if os.path.isfile(input_path) and input_path.endswith('.zip'):
            # 如果是zip文件，先解压
            with zipfile.ZipFile(input_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            # 处理可能的macOS特殊文件夹
            macosx_dir = os.path.join(temp_dir, "__MACOSX")
            if os.path.exists(macosx_dir):
                shutil.rmtree(macosx_dir)
                
            # 处理子文件夹
            subdirs = [d for d in os.listdir(temp_dir) 
                       if os.path.isdir(os.path.join(temp_dir, d)) and not d.startswith('__MACOSX')]
            
            if len(subdirs) == 1:
                scan_dir = os.path.join(temp_dir, subdirs[0])
        
        elif os.path.isdir(input_path):
            # 如果是目录，直接使用
            scan_dir = input_path
        
        # 扫描文件夹
        watermark_found, detected_watermarks, verification_info = scan_folder_for_watermark(
            scan_dir, 
            expected_hashes, 
            args.limit
        )
        
        # 输出检测结果：只要有一个图片检测出匹配的水印，就输出1
        result = "1" if watermark_found else "0"
        print(result)
        
        # 详细输出
        if args.verbose:
            results = verification_info["verification_results"]
            valid_count = sum(1 for r in results if r["is_valid"])
            matched_count = sum(1 for r in results if r.get("is_matched", False))
            
            print(f"\n扫描结果概述:")
            print(f"扫描文件数: {verification_info['scanned_files']}")
            print(f"检测到水印数: {len(detected_watermarks)}")
            print(f"有效水印数: {valid_count}")
            print(f"匹配水印数: {matched_count}")
            
            if watermark_found:
                print(f"\n检测到匹配的水印信息:")
                
                # 打印匹配的水印详情
                for i, result in enumerate([r for r in results if r.get("is_matched", False)]):
                    print(f"\n匹配水印 {i+1} (文件: {result['file']}):")
                    print(f"  提取的哈希值: {result['extracted_hash']}")
                    print(f"  匹配的预期哈希: {result['matched_with']}")
            else:
                print("\n未检测到匹配的水印")
    
    finally:
        # 清理临时目录
        shutil.rmtree(temp_dir)

if __name__ == "__main__":
    main()