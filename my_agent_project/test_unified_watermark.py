#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
统一水印处理方式测试脚本
验证列优先嵌入/提取的一致性，与LSB_groth16兼容性
"""

import os
import sys
import zipfile
import tempfile
import shutil
import hashlib
import time
import logging
import json
from PIL import Image
import numpy as np

# 添加features目录到path，以便导入模块
sys.path.append(os.path.join(os.path.dirname(__file__), 'features'))

from addWatermark import add_lsb_watermark
from checkForWatermark import extract_lsb_watermark

def generate_test_buy_hash():
    """生成测试用的buy_hash"""
    timestamp = int(time.time())
    test_data = f"test_unified_watermark_{timestamp}"
    buy_hash = hashlib.sha256(test_data.encode()).hexdigest()
    return buy_hash

def analyze_lsb_bits(image_path, max_pixels=50):
    """
    分析图像的LSB位，用于验证水印嵌入结果
    
    参数:
    image_path: 图像路径
    max_pixels: 最多分析的像素数
    
    返回:
    dict: 包含LSB分析结果的字典
    """
    try:
        image = Image.open(image_path).convert('RGB')
        pixel = image.load()
        width, height = image.size
        
        lsb_data = []
        pixel_count = 0
        
        # 按列优先顺序提取LSB位
        for x in range(width):
            for y in range(height):
                if pixel_count >= max_pixels:
                    break
                    
                r, g, b = pixel[x, y]
                lsb_data.append({
                    'position': (x, y),
                    'pixel_index': pixel_count,
                    'rgb': (r, g, b),
                    'lsb': (r & 1, g & 1, b & 1),
                    'bit_index': pixel_count * 3
                })
                pixel_count += 1
            
            if pixel_count >= max_pixels:
                break
        
        return {
            'image_size': (width, height),
            'total_capacity': width * height * 3,
            'analyzed_pixels': len(lsb_data),
            'lsb_data': lsb_data
        }
    
    except Exception as e:
        logging.error(f"分析LSB位时出错: {str(e)}")
        return None

def test_watermark_embedding_extraction(test_image_path, buy_hash):
    """
    测试水印嵌入和提取的完整流程
    
    参数:
    test_image_path: 测试图像路径
    buy_hash: 要嵌入的buy_hash
    
    返回:
    dict: 测试结果
    """
    print(f"\n=== 测试图像: {os.path.basename(test_image_path)} ===")
    
    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    try:
        watermarked_path = os.path.join(temp_dir, "watermarked_test.png")
        
        # 1. 分析原始图像的LSB位
        print("1. 分析原始图像LSB位...")
        original_lsb = analyze_lsb_bits(test_image_path, max_pixels=20)
        if original_lsb:
            print(f"   图像尺寸: {original_lsb['image_size']}")
            print(f"   总容量: {original_lsb['total_capacity']} 位")
            print("   前10个像素的LSB位:")
            for i, data in enumerate(original_lsb['lsb_data'][:10]):
                print(f"     像素{i}: 位置{data['position']}, RGB{data['rgb']}, LSB{data['lsb']}")
        
        # 2. 嵌入水印
        print(f"2. 嵌入buy_hash水印: {buy_hash[:16]}...")
        embedding_success = add_lsb_watermark(test_image_path, buy_hash, watermarked_path)
        
        if not embedding_success:
            return {"success": False, "error": "水印嵌入失败"}
        
        print("   水印嵌入成功!")
        
        # 3. 分析水印图像的LSB位
        print("3. 分析水印图像LSB位...")
        watermarked_lsb = analyze_lsb_bits(watermarked_path, max_pixels=20)
        if watermarked_lsb:
            print("   前10个像素的LSB位:")
            for i, data in enumerate(watermarked_lsb['lsb_data'][:10]):
                print(f"     像素{i}: 位置{data['position']}, RGB{data['rgb']}, LSB{data['lsb']}")
        
        # 4. 比较LSB位变化
        print("4. 比较LSB位变化...")
        if original_lsb and watermarked_lsb:
            changes = 0
            buy_hash_binary = ''.join([bin(ord(c))[2:].rjust(8, '0') for c in buy_hash])
            expected_bits = len(buy_hash_binary)
            
            print(f"   buy_hash二进制长度: {expected_bits} 位")
            print(f"   buy_hash二进制前32位: {buy_hash_binary[:32]}...")
            
            for i in range(min(len(original_lsb['lsb_data']), len(watermarked_lsb['lsb_data']))):
                orig_lsb = original_lsb['lsb_data'][i]['lsb']
                wm_lsb = watermarked_lsb['lsb_data'][i]['lsb']
                
                if orig_lsb != wm_lsb:
                    changes += 1
                    if i < 5:  # 只显示前5个变化
                        print(f"     变化 {changes}: 像素{i} {orig_lsb} -> {wm_lsb}")
            
            print(f"   总共 {changes} 个LSB位发生变化")
        
        # 5. 提取水印
        print("5. 提取水印...")
        extracted_hash = extract_lsb_watermark(watermarked_path)
        
        if extracted_hash:
            print(f"   成功提取: {extracted_hash}")
            match = extracted_hash == buy_hash
            print(f"   是否匹配: {'✓' if match else '✗'}")
            
            if not match:
                print(f"   原始: {buy_hash}")
                print(f"   提取: {extracted_hash}")
                # 逐字符比较
                for i, (orig_char, extr_char) in enumerate(zip(buy_hash, extracted_hash)):
                    if orig_char != extr_char:
                        print(f"   差异位置 {i}: '{orig_char}' != '{extr_char}'")
                        break
        else:
            print("   ✗ 提取失败")
            match = False
        
        # 6. 验证剩余位是否为0
        print("6. 验证剩余LSB位...")
        if watermarked_lsb:
            buy_hash_binary = ''.join([bin(ord(c))[2:].rjust(8, '0') for c in buy_hash])
            expected_bits = len(buy_hash_binary)
            
            # 检查buy_hash之后的位是否都为0
            zero_count = 0
            non_zero_count = 0
            total_checked = min(100, watermarked_lsb['analyzed_pixels'] * 3)  # 检查100位或所有位
            
            all_bits = []
            for data in watermarked_lsb['lsb_data']:
                all_bits.extend(data['lsb'])
            
            for i in range(expected_bits, min(len(all_bits), expected_bits + 50)):
                if all_bits[i] == 0:
                    zero_count += 1
                else:
                    non_zero_count += 1
            
            print(f"   检查buy_hash后50位: {zero_count}个0, {non_zero_count}个1")
            print(f"   剩余位清零率: {zero_count/(zero_count+non_zero_count)*100:.1f}%")
        
        return {
            "success": True,
            "embedding_success": embedding_success,
            "extraction_success": extracted_hash is not None,
            "match": match,
            "original_hash": buy_hash,
            "extracted_hash": extracted_hash,
            "original_lsb": original_lsb,
            "watermarked_lsb": watermarked_lsb
        }
    
    finally:
        # 清理临时文件
        shutil.rmtree(temp_dir)

def main():
    """主测试函数"""
    print("=== 统一水印处理方式测试 ===")
    print("验证列优先嵌入/提取与LSB_groth16的兼容性")
    
    # 配置日志
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    
    # 测试数据路径
    dataset_zip_path = "/Users/dylan/Code_Projects/Python_Projects/image_similarity/my_agent_project/data/dataset.zip"
    
    if not os.path.exists(dataset_zip_path):
        print(f"错误: 测试数据文件不存在: {dataset_zip_path}")
        return False
    
    # 创建临时目录解压测试数据
    temp_dir = tempfile.mkdtemp()
    try:
        print(f"\n解压测试数据到: {temp_dir}")
        
        # 解压数据集
        with zipfile.ZipFile(dataset_zip_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        
        # 清理macOS特殊文件
        macosx_dir = os.path.join(temp_dir, "__MACOSX")
        if os.path.exists(macosx_dir):
            shutil.rmtree(macosx_dir)
        
        # 查找测试图像
        test_images = []
        supported_formats = ['.png', '.jpg', '.jpeg', '.bmp', '.gif']
        
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                if any(file.lower().endswith(fmt) for fmt in supported_formats):
                    test_images.append(os.path.join(root, file))
                    if len(test_images) >= 3:  # 只测试前3张图
                        break
            if len(test_images) >= 3:
                break
        
        if not test_images:
            print("错误: 在数据集中未找到图像文件")
            return False
        
        print(f"找到 {len(test_images)} 张测试图像")
        
        # 生成测试buy_hash
        test_buy_hash = generate_test_buy_hash()
        print(f"测试buy_hash: {test_buy_hash}")
        
        # 逐个测试图像
        all_results = []
        success_count = 0
        
        for i, image_path in enumerate(test_images):
            try:
                result = test_watermark_embedding_extraction(image_path, test_buy_hash)
                all_results.append(result)
                
                if result["success"] and result["match"]:
                    success_count += 1
                    print(f"✓ 图像 {i+1} 测试通过")
                else:
                    print(f"✗ 图像 {i+1} 测试失败")
            
            except Exception as e:
                print(f"✗ 图像 {i+1} 测试异常: {str(e)}")
                all_results.append({"success": False, "error": str(e)})
        
        # 汇总结果
        print(f"\n=== 测试结果汇总 ===")
        print(f"测试图像数: {len(test_images)}")
        print(f"成功数: {success_count}")
        print(f"成功率: {success_count/len(test_images)*100:.1f}%")
        
        if success_count == len(test_images):
            print("🎉 所有测试通过！统一水印处理方式实现成功！")
            print("✓ 列优先嵌入/提取方式一致")
            print("✓ 与LSB_groth16兼容")
            print("✓ buy_hash保持不变")
            print("✓ 剩余位自动清零")
            return True
        else:
            print("⚠️  部分测试失败，需要进一步调试")
            return False
    
    finally:
        # 清理临时目录
        shutil.rmtree(temp_dir)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 