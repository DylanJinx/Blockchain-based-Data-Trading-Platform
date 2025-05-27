#!/usr/bin/env python3

import os
import sys
import json
import shutil
import tempfile
import zipfile
from PIL import Image
import numpy as np

# 添加当前目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from features.addWatermark import main as add_watermark_main
from features.checkForWatermark import main as check_watermark_main
import subprocess

def create_test_dataset():
    """创建测试数据集"""
    # 创建临时测试目录
    test_dir = tempfile.mkdtemp(prefix="watermark_test_")
    print(f"创建测试目录: {test_dir}")
    
    # 创建一些测试图像
    dataset_dir = os.path.join(test_dir, "test_dataset")
    os.makedirs(dataset_dir, exist_ok=True)
    
    for i in range(5):
        # 创建一个简单的测试图像
        image = Image.new('RGB', (100, 100), color=(i*50, 100, 150))
        image.save(os.path.join(dataset_dir, f"test_image_{i}.png"))
    
    # 压缩为zip文件
    zip_path = os.path.join(test_dir, "dataset.zip")
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for root, dirs, files in os.walk(dataset_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, dataset_dir)
                zipf.write(file_path, arcname)
    
    return test_dir, zip_path

def test_multiple_watermark_records():
    """测试多个水印记录的保存和检测"""
    print("=== 测试多个水印记录功能 ===\n")
    
    # 创建测试数据集
    test_dir, zip_path = create_test_dataset()
    
    try:
        # 保存原始工作目录
        original_cwd = os.getcwd()
        
        # 设置测试环境
        data_dir = os.path.join(test_dir, "data")
        os.makedirs(data_dir, exist_ok=True)
        
        # 复制数据集到data目录
        shutil.copy2(zip_path, os.path.join(data_dir, "dataset.zip"))
        
        # 模拟三次不同的购买行为
        buyers = [
            {"token_id": 1, "buyer_address": "0x1234567890123456789012345678901234567890"},
            {"token_id": 2, "buyer_address": "0xabcdefabcdefabcdefabcdefabcdefabcdefabcd"},
            {"token_id": 3, "buyer_address": "0x9876543210987654321098765432109876543210"}
        ]
        
        print("1. 模拟多次购买，添加水印...")
        watermark_info_path = os.path.join(data_dir, "watermark_info.json")
        
        for i, buyer in enumerate(buyers):
            print(f"\n--- 第 {i+1} 次购买 ---")
            print(f"Token ID: {buyer['token_id']}, 买家: {buyer['buyer_address']}")
            
            # 切换到测试目录
            os.chdir(test_dir)
            
            # 调用水印添加功能
            sys.argv = ["addWatermark.py", str(buyer['token_id']), buyer['buyer_address']]
            add_watermark_main(buyer['token_id'], buyer['buyer_address'])
            
            # 检查水印信息文件
            if os.path.exists(watermark_info_path):
                with open(watermark_info_path, 'r') as f:
                    info = json.load(f)
                
                if "records" in info:
                    print(f"✓ 当前记录数: {info['total_records']}")
                    print(f"✓ 最新买家: {info['records'][-1]['buyer_address']}")
                    print(f"✓ 最新buy_hash: {info['records'][-1]['buy_hash'][:16]}...")
                else:
                    print(f"✓ 单条记录格式 (买家: {info.get('buyer_address', 'Unknown')})")
        
        print(f"\n2. 检查最终的水印信息文件...")
        if os.path.exists(watermark_info_path):
            with open(watermark_info_path, 'r') as f:
                final_info = json.load(f)
            
            print(f"文件内容预览:")
            print(json.dumps(final_info, indent=2, ensure_ascii=False)[:500] + "...")
            
            if "records" in final_info:
                print(f"✓ 总记录数: {final_info['total_records']}")
                print(f"✓ 所有买家地址:")
                for i, record in enumerate(final_info['records']):
                    print(f"  {i+1}. {record['buyer_address']} (buy_hash: {record['buy_hash'][:16]}...)")
            else:
                print("! 仍然是旧格式，只有一条记录")
        
        print(f"\n3. 测试水印检测功能...")
        
        # 切换到测试目录进行检测
        os.chdir(test_dir)
        
        # 运行水印检测
        dataset_watermark_path = os.path.join(data_dir, "dataset_watermark.zip")
        if os.path.exists(dataset_watermark_path):
            # 使用subprocess运行检测脚本
            check_cmd = [
                "python", 
                os.path.join(original_cwd, "features", "checkForWatermark.py"),
                "--input", dataset_watermark_path,
                "--verbose"
            ]
            
            print(f"执行检测命令: {' '.join(check_cmd)}")
            
            result = subprocess.run(check_cmd, capture_output=True, text=True, cwd=test_dir)
            print(f"检测结果: {result.returncode}")
            print(f"输出:\n{result.stdout}")
            
            if result.stderr:
                print(f"错误输出:\n{result.stderr}")
                
            # 分析结果
            if result.stdout.strip().startswith("1"):
                print("✓ 成功检测到水印匹配！")
            else:
                print("✗ 未检测到水印匹配")
        else:
            print("! 未找到dataset_watermark.zip文件")
        
        print(f"\n4. 验证水印记录的完整性...")
        
        # 重新读取文件确认
        if os.path.exists(watermark_info_path):
            with open(watermark_info_path, 'r') as f:
                verification_info = json.load(f)
            
            if "records" in verification_info:
                expected_count = len(buyers)
                actual_count = verification_info['total_records']
                
                if actual_count == expected_count:
                    print(f"✓ 记录数量正确: {actual_count}/{expected_count}")
                    
                    # 检查每个买家的记录是否都存在
                    recorded_addresses = [record['buyer_address'] for record in verification_info['records']]
                    expected_addresses = [buyer['buyer_address'] for buyer in buyers]
                    
                    all_present = all(addr in recorded_addresses for addr in expected_addresses)
                    if all_present:
                        print("✓ 所有买家记录都已保存")
                    else:
                        print("✗ 部分买家记录缺失")
                        print(f"期望: {expected_addresses}")
                        print(f"实际: {recorded_addresses}")
                else:
                    print(f"✗ 记录数量不匹配: {actual_count}/{expected_count}")
            else:
                print("✗ 文件格式不正确，缺少records字段")
        
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 恢复原始工作目录
        os.chdir(original_cwd)
        
        # 清理测试目录
        try:
            shutil.rmtree(test_dir)
            print(f"\n已清理测试目录: {test_dir}")
        except Exception as e:
            print(f"清理测试目录失败: {e}")

if __name__ == "__main__":
    test_multiple_watermark_records() 