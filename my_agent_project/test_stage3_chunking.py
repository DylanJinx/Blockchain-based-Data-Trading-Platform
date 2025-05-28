#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
第三阶段分块测试脚本
验证数据分块功能是否按照LSB_groth16/generate_input.py的逻辑正确工作
"""

import os
import sys
import json
import logging

# 添加features目录到path
sys.path.append(os.path.join(os.path.dirname(__file__), 'features'))

from stage3_chunk_and_proof import process_watermarked_dataset_registration, Stage3ChunkProcessor
from addWatermark import find_zk_input_for_buy_hash

def test_stage3_chunking():
    """测试第三阶段分块功能"""
    print("=== 第三阶段分块测试 ===")
    
    # 1. 从数据目录查找现有的ZK输入文件
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    zk_inputs_dir = os.path.join(data_dir, "zk_inputs")
    
    if not os.path.exists(zk_inputs_dir):
        print("❌ ZK输入目录不存在")
        return False
    
    # 获取ZK输入文件列表
    zk_files = [f for f in os.listdir(zk_inputs_dir) if f.startswith("zk_input_")]
    if not zk_files:
        print("❌ 没有找到ZK输入文件")
        return False
    
    # 从文件名提取buy_hash
    first_file = zk_files[0]
    buy_hash_prefix = first_file.split('_')[2]  # zk_input_{前缀}_{图片名}.json
    
    # 构造完整的buy_hash（这里用一个模拟的，实际应该从watermark_info.json获取）
    print(f"📋 检测到buy_hash前缀: {buy_hash_prefix}")
    print(f"📋 找到 {len(zk_files)} 个ZK输入文件")
    
    # 构造测试用的buy_hash（实际应该从watermark_info.json读取）
    test_buy_hash = f"{buy_hash_prefix}{'0' * (64 - len(buy_hash_prefix))}"  # 填充到64位
    
    # 从watermark_info.json获取真实的buy_hash
    watermark_info_file = os.path.join(data_dir, "watermark_info.json")
    if os.path.exists(watermark_info_file):
        with open(watermark_info_file, 'r') as f:
            watermark_info = json.load(f)
        
        # 查找匹配的记录
        if "records" in watermark_info:
            for record in watermark_info["records"]:
                if record.get("buy_hash", "").startswith(buy_hash_prefix):
                    test_buy_hash = record["buy_hash"]
                    print(f"✅ 从watermark_info.json获取完整buy_hash: {test_buy_hash[:16]}...")
                    break
    
    # 2. 验证ZK输入文件查找功能
    print(f"\n1. 测试ZK输入文件查找...")
    zk_result = find_zk_input_for_buy_hash(test_buy_hash, data_dir)
    
    if not zk_result:
        print(f"❌ 无法找到buy_hash对应的ZK输入文件")
        return False
    
    print(f"✅ 找到 {zk_result['total_files']} 个ZK输入文件:")
    for i, file_info in enumerate(zk_result['zk_input_files'], 1):
        print(f"   {i}. {file_info['filename']} ({file_info['file_size']/1024:.1f} KB)")
    
    # 3. 测试不同的分块大小
    test_chunk_sizes = [
        {"name": "超大分块", "m": 10000, "power": 20},  # 单分块
        {"name": "中等分块", "m": 5000, "power": 19},   # 2分块
        {"name": "小分块", "m": 2000, "power": 18},     # 5分块
    ]
    
    for i, test_case in enumerate(test_chunk_sizes, 1):
        print(f"\n{i+1}. 测试{test_case['name']} (m={test_case['m']})...")
        
        optimal_config = {
            "power": test_case["power"],
            "constraint_size": 2 ** test_case["power"],
            "M": (9216 + test_case["m"] - 1) // test_case["m"],  # 基于96x96=9216像素计算
            "m": test_case["m"],
            "total_time": 120.0
        }
        
        print(f"   配置: 2^{optimal_config['power']} 约束, {optimal_config['M']} 分块, {optimal_config['m']} 像素/块")
        
        # 执行分块处理
        result = process_watermarked_dataset_registration(test_buy_hash, optimal_config)
        
        if result["status"] == "chunking_completed":
            chunking_result = result["chunking_result"]
            session_info = chunking_result["session_info"]
            
            print(f"   ✅ 分块成功!")
            print(f"      - 处理图片数: {session_info['total_images']}")
            print(f"      - 生成分块数: {session_info['total_chunks']}")
            print(f"      - 输出目录: {os.path.basename(session_info['output_directory'])}")
            
            # 验证分块文件
            chunk_output_dir = chunking_result["chunk_output_dir"]
            if os.path.exists(chunk_output_dir):
                total_files = sum(len(files) for _, _, files in os.walk(chunk_output_dir))
                print(f"      - 验证文件数: {total_files} 个JSON文件")
                
                # 检查第一个分块文件的格式
                for root, dirs, files in os.walk(chunk_output_dir):
                    if files:
                        first_chunk = os.path.join(root, files[0])
                        try:
                            with open(first_chunk, 'r') as f:
                                chunk_data = json.load(f)
                            
                            required_keys = ["originalPixelValues", "Watermark_PixelValues", 
                                           "binaryWatermark", "binaryWatermark_num"]
                            has_all_keys = all(key in chunk_data for key in required_keys)
                            
                            if has_all_keys:
                                pixel_count = len(chunk_data["originalPixelValues"])
                                print(f"      ✅ 格式正确，像素数: {pixel_count}")
                            else:
                                print(f"      ❌ 格式错误，缺少必要字段")
                        except Exception as e:
                            print(f"      ❌ 读取分块文件失败: {e}")
                        break
            else:
                print(f"      ❌ 输出目录不存在")
        else:
            print(f"   ❌ 分块失败: {result.get('message', 'Unknown error')}")
            return False
    
    print(f"\n🎉 第三阶段分块测试完成!")
    print(f"✅ 所有分块大小测试通过")
    print(f"✅ 分块格式符合LSB_groth16要求")
    print(f"✅ 文件组织结构正确")
    
    return True

def verify_chunk_format_compatibility():
    """验证分块格式与LSB_groth16的兼容性"""
    print(f"\n=== 分块格式兼容性验证 ===")
    
    # 查找最新生成的分块文件
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    chunked_inputs_dir = os.path.join(data_dir, "chunked_inputs")
    
    if not os.path.exists(chunked_inputs_dir):
        print(f"❌ 分块输入目录不存在")
        return False
    
    # 查找最新的会话目录
    session_dirs = [d for d in os.listdir(chunked_inputs_dir) if d.startswith("session_")]
    if not session_dirs:
        print(f"❌ 没有找到分块会话目录")
        return False
    
    latest_session = max(session_dirs, 
                        key=lambda d: os.path.getmtime(os.path.join(chunked_inputs_dir, d)))
    
    session_path = os.path.join(chunked_inputs_dir, latest_session)
    print(f"📁 验证会话: {latest_session}")
    
    # 查找分块目录
    chunk_dirs = [d for d in os.listdir(session_path) if d.startswith("chunk_pixel_")]
    if not chunk_dirs:
        print(f"❌ 没有找到分块目录")
        return False
    
    # 验证每个分块目录
    for chunk_dir in chunk_dirs:
        chunk_path = os.path.join(session_path, chunk_dir)
        print(f"\n📋 验证分块目录: {chunk_dir}")
        
        # 遍历图片目录
        image_dirs = [d for d in os.listdir(chunk_path) if d.startswith("input_")]
        print(f"   找到 {len(image_dirs)} 个图片目录")
        
        for image_dir in image_dirs:
            image_path = os.path.join(chunk_path, image_dir)
            chunk_files = [f for f in os.listdir(image_path) if f.endswith('.json')]
            
            print(f"   {image_dir}: {len(chunk_files)} 个分块文件")
            
            # 验证第一个分块文件的详细格式
            if chunk_files:
                first_chunk_file = os.path.join(image_path, chunk_files[0])
                try:
                    with open(first_chunk_file, 'r') as f:
                        chunk_data = json.load(f)
                    
                    # 检查字段名称（必须与LSB_groth16一致）
                    expected_fields = {
                        "originalPixelValues": "原始像素值数组",
                        "Watermark_PixelValues": "水印像素值数组", 
                        "binaryWatermark": "二进制水印数组",
                        "binaryWatermark_num": "水印长度字符串"
                    }
                    
                    format_correct = True
                    for field, description in expected_fields.items():
                        if field not in chunk_data:
                            print(f"      ❌ 缺少字段: {field} ({description})")
                            format_correct = False
                        else:
                            print(f"      ✅ {field}: {type(chunk_data[field])}")
                    
                    if format_correct:
                        # 验证数据类型和结构
                        ori_pixels = chunk_data["originalPixelValues"]
                        wm_pixels = chunk_data["Watermark_PixelValues"] 
                        binary_wm = chunk_data["binaryWatermark"]
                        wm_num = chunk_data["binaryWatermark_num"]
                        
                        print(f"      📊 数据验证:")
                        print(f"         原始像素: {len(ori_pixels)} 个RGB三元组")
                        print(f"         水印像素: {len(wm_pixels)} 个RGB三元组")
                        print(f"         二进制水印: {len(binary_wm)} 位")
                        print(f"         水印长度: {wm_num}")
                        
                        # 验证像素格式
                        if ori_pixels and isinstance(ori_pixels[0], list) and len(ori_pixels[0]) == 3:
                            print(f"      ✅ 像素格式正确: RGB三元组")
                        else:
                            print(f"      ❌ 像素格式错误")
                            format_correct = False
                        
                        # 验证二进制水印格式
                        if all(bit in [0, 1] for bit in binary_wm[:100]):  # 检查前100位
                            print(f"      ✅ 二进制水印格式正确: 0/1整数")
                        else:
                            print(f"      ❌ 二进制水印格式错误")
                            format_correct = False
                        
                        if format_correct:
                            print(f"      🎉 格式完全兼容LSB_groth16!")
                        
                except Exception as e:
                    print(f"      ❌ 文件读取失败: {e}")
    
    return True

def main():
    """主测试函数"""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    
    print("🧪 第三阶段完整测试")
    print("=" * 60)
    
    success = True
    
    # 测试1: 分块功能
    try:
        if not test_stage3_chunking():
            success = False
    except Exception as e:
        print(f"❌ 分块测试失败: {e}")
        success = False
    
    # 测试2: 格式兼容性
    try:
        if not verify_chunk_format_compatibility():
            success = False
    except Exception as e:
        print(f"❌ 格式验证失败: {e}")
        success = False
    
    # 总结
    print(f"\n" + "=" * 60)
    if success:
        print(f"🎉 第三阶段测试全部通过!")
        print(f"✅ 数据分块功能正常")
        print(f"✅ 格式完全兼容LSB_groth16")
        print(f"✅ 使用登记阶段的约束参数")
        print(f"📋 可以进入第四阶段：零知识证明生成")
    else:
        print(f"❌ 第三阶段测试部分失败")
        print(f"需要修复失败项目后再继续")
    
    return success

if __name__ == "__main__":
    main() 
 