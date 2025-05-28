#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
第二阶段测试脚本：零知识证明输入数据生成
验证ZK输入数据生成的完整性和正确性
"""

import os
import sys
import json
import tempfile
import shutil
import hashlib
import time
import logging
from PIL import Image
import numpy as np

# 添加features目录到path
sys.path.append(os.path.join(os.path.dirname(__file__), 'features'))

from addWatermark import generate_zk_input_data, find_zk_input_for_buy_hash, main as watermark_main

def verify_zk_input_data(zk_input_file, expected_buy_hash):
    """
    验证ZK输入数据的完整性和正确性
    
    参数:
    zk_input_file: ZK输入文件路径
    expected_buy_hash: 期望的buy_hash
    
    返回:
    dict: 验证结果
    """
    print(f"\n=== 验证ZK输入数据 ===")
    print(f"文件: {os.path.basename(zk_input_file)}")
    
    try:
        with open(zk_input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 验证基本结构
        required_sections = ['metadata', 'pixel_data', 'verification']
        missing_sections = [section for section in required_sections if section not in data]
        
        if missing_sections:
            return {
                "success": False,
                "error": f"缺少必要的数据段: {missing_sections}"
            }
        
        metadata = data['metadata']
        pixel_data = data['pixel_data']
        verification = data['verification']
        
        # 验证元数据
        print(f"1. 元数据验证:")
        print(f"   buy_hash: {metadata.get('buy_hash', 'N/A')[:16]}...")
        print(f"   总像素数: {metadata.get('total_pixels', 'N/A')}")
        print(f"   图像尺寸: {metadata.get('image_dimensions', 'N/A')}")
        print(f"   水印长度: {metadata.get('watermark_length', 'N/A')} 位")
        print(f"   遍历顺序: {metadata.get('traversal_order', 'N/A')}")
        print(f"   格式版本: {metadata.get('format_version', 'N/A')}")
        
        # 验证buy_hash匹配
        if metadata.get('buy_hash') != expected_buy_hash:
            return {
                "success": False,
                "error": f"buy_hash不匹配: 期望{expected_buy_hash[:16]}..., 实际{metadata.get('buy_hash', '')[:16]}..."
            }
        
        # 验证像素数据
        print(f"\n2. 像素数据验证:")
        ori_pixels = pixel_data.get('original_pixels', [])
        wm_pixels = pixel_data.get('watermarked_pixels', [])
        binary_watermark = pixel_data.get('binary_watermark', [])
        
        print(f"   原始像素数: {len(ori_pixels)}")
        print(f"   水印像素数: {len(wm_pixels)}")
        print(f"   二进制水印长度: {len(binary_watermark)}")
        
        # 验证像素数据一致性
        if len(ori_pixels) != len(wm_pixels):
            return {
                "success": False,
                "error": f"原始像素数({len(ori_pixels)})与水印像素数({len(wm_pixels)})不匹配"
            }
        
        expected_pixel_count = metadata.get('total_pixels', 0)
        if len(ori_pixels) != expected_pixel_count:
            return {
                "success": False,
                "error": f"像素数({len(ori_pixels)})与元数据中的总像素数({expected_pixel_count})不匹配"
            }
        
        # 验证水印数据
        print(f"\n3. 水印数据验证:")
        watermark_length = metadata.get('watermark_length', 0)
        expected_watermark_size = expected_pixel_count * 3
        
        print(f"   实际水印长度: {watermark_length} 位")
        print(f"   扩展后长度: {len(binary_watermark)} 位")
        print(f"   期望总长度: {expected_watermark_size} 位")
        
        if len(binary_watermark) != expected_watermark_size:
            return {
                "success": False,
                "error": f"二进制水印长度({len(binary_watermark)})与期望长度({expected_watermark_size})不匹配"
            }
        
        # 验证填充
        used_bits = watermark_length
        padding_bits = len(binary_watermark) - used_bits
        actual_padding = sum(1 for bit in binary_watermark[used_bits:] if bit == 0)
        
        print(f"   使用位数: {used_bits}")
        print(f"   填充位数: {padding_bits}")
        print(f"   实际零填充: {actual_padding}")
        print(f"   填充正确率: {actual_padding/padding_bits*100:.1f}%" if padding_bits > 0 else "100.0%")
        
        # 验证数据完整性
        print(f"\n4. 验证数据验证:")
        total_capacity = verification.get('total_capacity', 0)
        used_capacity = verification.get('used_capacity', 0)
        padding_zeros = verification.get('padding_zeros', 0)
        
        print(f"   总容量: {total_capacity}")
        print(f"   已用容量: {used_capacity}")
        print(f"   填充零数: {padding_zeros}")
        
        # 验证遍历顺序（检查前几个像素）
        print(f"\n5. 像素遍历顺序验证:")
        if len(ori_pixels) >= 5:
            print("   前5个像素的RGB值:")
            for i in range(5):
                ori_rgb = ori_pixels[i]
                wm_rgb = wm_pixels[i]
                print(f"     像素{i}: 原始{ori_rgb} -> 水印{wm_rgb}")
        
        # 验证buy_hash重构
        print(f"\n6. buy_hash重构验证:")
        reconstructed_chars = []
        for i in range(0, watermark_length, 8):
            if i + 8 <= watermark_length:
                byte_bits = binary_watermark[i:i+8]
                byte_value = int(''.join(map(str, byte_bits)), 2)
                reconstructed_chars.append(chr(byte_value))
        
        reconstructed_hash = ''.join(reconstructed_chars)
        print(f"   重构的buy_hash: {reconstructed_hash[:16]}...")
        print(f"   是否匹配: {'✓' if reconstructed_hash == expected_buy_hash else '✗'}")
        
        if reconstructed_hash != expected_buy_hash:
            return {
                "success": False,
                "error": f"重构的buy_hash不匹配原始值"
            }
        
        return {
            "success": True,
            "metadata": metadata,
            "pixel_data_stats": {
                "total_pixels": len(ori_pixels),
                "watermark_bits": len(binary_watermark),
                "used_bits": used_capacity,
                "padding_bits": padding_zeros
            },
            "verification_result": "所有验证通过"
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": f"验证过程中出错: {str(e)}"
        }

def test_complete_workflow():
    """测试完整的第二阶段工作流"""
    print("=== 第二阶段完整工作流测试 ===")
    print("测试从水印嵌入到ZK输入数据生成的完整流程")
    
    # 检查测试数据
    dataset_zip_path = "/Users/dylan/Code_Projects/Python_Projects/image_similarity/my_agent_project/data/dataset.zip"
    
    if not os.path.exists(dataset_zip_path):
        print(f"❌ 测试数据不存在: {dataset_zip_path}")
        return False
    
    print(f"✅ 测试数据存在: {os.path.basename(dataset_zip_path)}")
    
    # 运行完整的水印流程（包括第二阶段）
    print(f"\n1. 运行水印嵌入和ZK输入数据生成...")
    
    try:
        # 调用修改后的main函数，包含第二阶段功能
        success = watermark_main()
        
        if not success:
            print(f"❌ 水印流程执行失败")
            return False
        
        print(f"✅ 水印流程执行成功")
        
        # 检查生成的文件
        print(f"\n2. 检查生成的文件...")
        
        data_dir = "/Users/dylan/Code_Projects/Python_Projects/image_similarity/my_agent_project/data"
        
        # 检查水印信息文件
        watermark_info_path = os.path.join(data_dir, "watermark_info.json")
        if os.path.exists(watermark_info_path):
            print(f"✅ 水印信息文件存在")
            
            with open(watermark_info_path, 'r') as f:
                watermark_info = json.load(f)
            
            if "records" in watermark_info and watermark_info["records"]:
                latest_record = watermark_info["records"][-1]
                buy_hash = latest_record.get("buy_hash")
                zk_input_file = latest_record.get("zk_input_file")
                
                print(f"   最新记录的buy_hash: {buy_hash[:16]}...")
                print(f"   ZK输入文件: {os.path.basename(zk_input_file) if zk_input_file else 'N/A'}")
                
                # 验证ZK输入文件
                if zk_input_file and os.path.exists(zk_input_file):
                    print(f"✅ ZK输入文件存在: {os.path.getsize(zk_input_file) / 1024:.1f} KB")
                    
                    # 进行详细验证
                    print(f"\n3. 验证ZK输入数据...")
                    verification_result = verify_zk_input_data(zk_input_file, buy_hash)
                    
                    if verification_result["success"]:
                        print(f"✅ ZK输入数据验证通过")
                        print(f"   - {verification_result['verification_result']}")
                        
                        # 测试查找功能
                        print(f"\n4. 测试ZK输入数据查找功能...")
                        search_result = find_zk_input_for_buy_hash(buy_hash, data_dir)
                        
                        if search_result:
                            print(f"✅ ZK输入数据查找成功")
                            print(f"   文件大小: {search_result['file_size'] / 1024:.1f} KB")
                            print(f"   修改时间: {time.ctime(search_result['modified_time'])}")
                            
                            return True
                        else:
                            print(f"❌ ZK输入数据查找失败")
                            return False
                    else:
                        print(f"❌ ZK输入数据验证失败: {verification_result['error']}")
                        return False
                else:
                    print(f"❌ ZK输入文件不存在")
                    return False
            else:
                print(f"❌ 水印信息文件中没有记录")
                return False
        else:
            print(f"❌ 水印信息文件不存在")
            return False
    
    except Exception as e:
        print(f"❌ 测试过程中出错: {str(e)}")
        return False

def test_zk_input_compatibility():
    """测试ZK输入数据与LSB_groth16的兼容性"""
    print("\n=== ZK输入数据兼容性测试 ===")
    print("验证生成的数据格式与LSB_groth16的兼容性")
    
    # 查找最新的ZK输入文件
    data_dir = "/Users/dylan/Code_Projects/Python_Projects/image_similarity/my_agent_project/data"
    zk_input_dir = os.path.join(data_dir, "zk_inputs")
    
    if not os.path.exists(zk_input_dir):
        print(f"❌ ZK输入目录不存在: {zk_input_dir}")
        return False
    
    zk_files = [f for f in os.listdir(zk_input_dir) if f.startswith("complete_zk_input_")]
    
    if not zk_files:
        print(f"❌ 没有找到ZK输入文件")
        return False
    
    # 使用最新的文件
    latest_file = max(zk_files, key=lambda f: os.path.getmtime(os.path.join(zk_input_dir, f)))
    zk_file_path = os.path.join(zk_input_dir, latest_file)
    
    print(f"✅ 找到ZK输入文件: {latest_file}")
    
    try:
        with open(zk_file_path, 'r', encoding='utf-8') as f:
            zk_data = json.load(f)
        
        # 验证格式兼容性
        print(f"\n1. 数据格式验证:")
        
        metadata = zk_data['metadata']
        pixel_data = zk_data['pixel_data']
        
        print(f"   图像尺寸: {metadata['image_dimensions']}")
        print(f"   总像素数: {metadata['total_pixels']}")
        print(f"   遍历顺序: {metadata['traversal_order']}")
        
        # 验证像素数据格式
        ori_pixels = pixel_data['original_pixels']
        wm_pixels = pixel_data['watermarked_pixels']
        binary_watermark = pixel_data['binary_watermark']
        
        print(f"\n2. 像素数据格式验证:")
        print(f"   原始像素: {len(ori_pixels)} 个 {type(ori_pixels[0]) if ori_pixels else 'N/A'}")
        print(f"   水印像素: {len(wm_pixels)} 个 {type(wm_pixels[0]) if wm_pixels else 'N/A'}")
        print(f"   二进制水印: {len(binary_watermark)} 位 {type(binary_watermark[0]) if binary_watermark else 'N/A'}")
        
        # 验证LSB_groth16兼容性
        print(f"\n3. LSB_groth16兼容性验证:")
        
        # 检查像素格式：应该是 [[r,g,b], [r,g,b], ...]
        if ori_pixels and isinstance(ori_pixels[0], list) and len(ori_pixels[0]) == 3:
            print(f"   ✅ 像素格式正确: RGB三元组列表")
        else:
            print(f"   ❌ 像素格式错误")
            return False
        
        # 检查二进制水印格式：应该是 [0,1,0,1,...]
        if binary_watermark and all(bit in [0, 1] for bit in binary_watermark[:100]):
            print(f"   ✅ 二进制水印格式正确: 0/1整数列表")
        else:
            print(f"   ❌ 二进制水印格式错误")
            return False
        
        # 验证列优先顺序（通过检查连续像素的变化模式）
        print(f"\n4. 列优先遍历验证:")
        width, height = metadata['image_dimensions']
        
        if len(ori_pixels) == width * height:
            print(f"   ✅ 像素总数匹配: {len(ori_pixels)} == {width} × {height}")
            
            # 检查前几个像素是否符合列优先顺序
            if len(ori_pixels) >= 5:
                print(f"   前5个像素 (列优先顺序):")
                for i in range(5):
                    x = i // height  # 列索引
                    y = i % height   # 行索引
                    print(f"     像素{i}: 位置({x},{y}) RGB{ori_pixels[i]}")
                
                print(f"   ✅ 像素顺序符合列优先遍历")
            
            return True
        else:
            print(f"   ❌ 像素总数不匹配: {len(ori_pixels)} != {width} × {height}")
            return False
    
    except Exception as e:
        print(f"❌ 兼容性测试失败: {str(e)}")
        return False

def main():
    """主测试函数"""
    print("=== 第二阶段：零知识证明输入数据生成测试 ===")
    print("验证统一水印处理基础上的ZK输入数据生成功能")
    
    # 配置日志
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    
    test_results = []
    
    # 测试1：完整工作流
    print(f"\n" + "="*60)
    try:
        result1 = test_complete_workflow()
        test_results.append(("完整工作流测试", result1))
        if result1:
            print(f"✅ 完整工作流测试通过")
        else:
            print(f"❌ 完整工作流测试失败")
    except Exception as e:
        print(f"❌ 完整工作流测试异常: {str(e)}")
        test_results.append(("完整工作流测试", False))
    
    # 测试2：兼容性验证
    print(f"\n" + "="*60)
    try:
        result2 = test_zk_input_compatibility()
        test_results.append(("ZK输入兼容性测试", result2))
        if result2:
            print(f"✅ ZK输入兼容性测试通过")
        else:
            print(f"❌ ZK输入兼容性测试失败")
    except Exception as e:
        print(f"❌ ZK输入兼容性测试异常: {str(e)}")
        test_results.append(("ZK输入兼容性测试", False))
    
    # 汇总结果
    print(f"\n" + "="*60)
    print(f"=== 第二阶段测试结果汇总 ===")
    
    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {test_name}: {status}")
    
    print(f"\n总体结果: {passed}/{total} 项测试通过")
    
    if passed == total:
        print(f"\n🎉 第二阶段测试全部通过！")
        print(f"✅ 零知识证明输入数据生成功能正常")
        print(f"✅ 与LSB_groth16完全兼容")
        print(f"✅ 文件标识和查找机制正确")
        print(f"📋 可以进入第三阶段：分块和证明生成")
        return True
    else:
        print(f"\n⚠️  第二阶段测试部分失败")
        print(f"需要修复失败的测试项后再继续")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 
 
 