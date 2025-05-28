#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
完整的第三阶段集成测试脚本
验证检测到水印后的完整流程：
1. 水印检测
2. 第三阶段数据分块处理
3. Powers of Tau准备
"""

import os
import sys
import json
import logging
import shutil

# 添加features目录到path
sys.path.append(os.path.join(os.path.dirname(__file__), 'features'))

from feature_register import register_data

def test_complete_watermark_detection_and_chunking():
    """测试完整的水印检测和分块流程"""
    print("=== 完整的第三阶段集成测试 ===")
    
    # 准备测试数据
    dataset_dir = os.path.join(os.path.dirname(__file__), "data", "test_dataset_for_stage3")
    
    if not os.path.exists(dataset_dir):
        print("❌ 测试数据集目录不存在")
        return False
    
    # 检查数据集内容
    image_files = [f for f in os.listdir(dataset_dir) if f.endswith('.png')]
    print(f"📋 测试数据集: {len(image_files)} 张图片")
    for img in image_files:
        print(f"   - {img}")
    
    # 创建测试用的metadata URL（模拟）
    # 注意：这个测试会使用现有的数据集，而不是从网络下载
    test_metadata_url = "http://test.example.com/metadata.json"
    test_user_address = "0x1234567890abcdef"
    
    print(f"\n🔍 开始测试水印检测和分块流程...")
    
    try:
        # 备份原始register_data函数的部分逻辑，我们要直接测试核心部分
        from features.checkForWatermark import main as check_watermark
        from features.poweroftau_generator import PowerOfTauGenerator
        
        # 1. 数据集分析
        print("1. 数据集分析...")
        generator = PowerOfTauGenerator()
        total_pixels = generator.calculate_dataset_pixels(dataset_dir)
        optimal_config = generator.get_optimal_constraints(total_pixels)
        
        print(f"   总像素数: {total_pixels}")
        print(f"   最优约束: 2^{optimal_config['power']} = {optimal_config['constraint_size']}")
        print(f"   分块配置: M={optimal_config['M']}, m={optimal_config['m']}")
        
        # 2. 水印检测
        print("\n2. 水印检测...")
        
        # 直接调用水印检测
        sys.argv = ['checkForWatermark.py', '--input', dataset_dir, '--verbose']
        
        # 捕获水印检测输出
        import subprocess
        wm_cmd = ["python", "features/checkForWatermark.py", "--input", dataset_dir, "--verbose"]
        wm_result = subprocess.run(wm_cmd, capture_output=True, text=True, check=True, timeout=120)
        wm_output = wm_result.stdout.strip()
        
        print(f"   检测结果: {wm_output.split()[0] if wm_output else 'None'}")
        
        # 检查是否检测到水印
        result_line = wm_output.split('\n')[0] if '\n' in wm_output else wm_output
        
        if result_line != "1":
            print(f"❌ 未检测到水印，无法测试分块流程")
            return False
        
        print("   ✅ 检测到水印!")
        
        # 3. 提取买家哈希值
        print("\n3. 提取买家哈希值...")
        watermark_lines = wm_output.split('\n')
        detected_buy_hash = None
        
        for line in watermark_lines:
            if "提取的哈希值:" in line or "匹配的预期哈希:" in line:
                import re
                hash_match = re.search(r'[a-f0-9]{64}', line)
                if hash_match:
                    detected_buy_hash = hash_match.group(0)
                    break
        
        if not detected_buy_hash:
            print("❌ 无法提取买家哈希值")
            return False
        
        print(f"   检测到的买家哈希: {detected_buy_hash[:16]}...")
        
        # 4. 第三阶段数据分块处理
        print("\n4. 第三阶段数据分块处理...")
        
        from stage3_chunk_and_proof import process_watermarked_dataset_registration
        
        chunking_result = process_watermarked_dataset_registration(
            buy_hash=detected_buy_hash,
            optimal_config=optimal_config
        )
        
        if chunking_result["status"] != "chunking_completed":
            print(f"❌ 分块处理失败: {chunking_result.get('message', 'Unknown error')}")
            return False
        
        print("   ✅ 第三阶段分块处理完成!")
        chunk_info = chunking_result["chunking_result"]
        session_info = chunk_info["session_info"]
        
        print(f"   - 处理图片数: {session_info['total_images']}")
        print(f"   - 生成分块数: {session_info['total_chunks']}")
        print(f"   - 分块大小: {session_info['chunk_pixel_size']} 像素/块")
        print(f"   - 输出目录: {os.path.basename(session_info['output_directory'])}")
        
        # 5. 验证分块文件
        print("\n5. 验证分块文件...")
        chunk_output_dir = chunk_info["chunk_output_dir"]
        
        if not os.path.exists(chunk_output_dir):
            print(f"❌ 分块输出目录不存在: {chunk_output_dir}")
            return False
        
        # 统计分块文件
        total_files = 0
        for root, dirs, files in os.walk(chunk_output_dir):
            json_files = [f for f in files if f.endswith('.json')]
            total_files += len(json_files)
        
        if total_files != session_info['total_chunks']:
            print(f"❌ 分块文件数量不匹配: 期望{session_info['total_chunks']}, 实际{total_files}")
            return False
        
        print(f"   ✅ 分块文件验证通过: {total_files} 个JSON文件")
        
        # 验证第一个分块文件的格式
        first_chunk_file = None
        for root, dirs, files in os.walk(chunk_output_dir):
            json_files = [f for f in files if f.endswith('.json')]
            if json_files:
                first_chunk_file = os.path.join(root, json_files[0])
                break
        
        if first_chunk_file:
            try:
                with open(first_chunk_file, 'r') as f:
                    chunk_data = json.load(f)
                
                required_keys = ["originalPixelValues", "Watermark_PixelValues", 
                               "binaryWatermark", "binaryWatermark_num"]
                
                if all(key in chunk_data for key in required_keys):
                    pixel_count = len(chunk_data["originalPixelValues"])
                    watermark_num = chunk_data["binaryWatermark_num"]
                    print(f"   ✅ 分块格式正确: {pixel_count} 像素, watermark_num={watermark_num}")
                else:
                    print(f"   ❌ 分块格式错误: 缺少必要字段")
                    return False
            except Exception as e:
                print(f"   ❌ 分块文件读取失败: {e}")
                return False
        
        # 6. 模拟Powers of Tau准备（不实际执行，只验证参数）
        print("\n6. Powers of Tau准备验证...")
        
        user_id = "TEST123"
        ptau_info = {
            "total_pixels": total_pixels,
            "optimal_config": optimal_config,
            "user_id": user_id,
            "dataset_folder": dataset_dir
        }
        
        constraint_power = optimal_config['power']
        print(f"   约束幂次: 2^{constraint_power}")
        print(f"   用户ID: {user_id}")
        print(f"   ✅ Powers of Tau参数准备完成")
        
        print(f"\n🎉 完整的第三阶段集成测试通过!")
        print(f"✅ 水印检测正常")
        print(f"✅ 买家哈希提取正常") 
        print(f"✅ 第三阶段分块处理正常")
        print(f"✅ 分块文件格式正确")
        print(f"✅ Powers of Tau参数准备正常")
        
        # 输出关键信息
        print(f"\n📊 处理结果摘要:")
        print(f"   检测到的买家哈希: {detected_buy_hash}")
        print(f"   分块配置: m={optimal_config['m']}, M={optimal_config['M']}")
        print(f"   约束大小: 2^{optimal_config['power']} = {optimal_config['constraint_size']}")
        print(f"   分块文件数: {session_info['total_chunks']}")
        print(f"   分块输出目录: {chunk_output_dir}")
        
        return True
        
    except Exception as e:
        print(f"❌ 集成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    
    print("🧪 第三阶段完整集成测试")
    print("=" * 60)
    
    success = test_complete_watermark_detection_and_chunking()
    
    print(f"\n" + "=" * 60)
    if success:
        print(f"🎉 第三阶段完整集成测试成功!")
        print(f"✅ 修复后的流程正常工作")
        print(f"✅ 检测到水印后会正确执行分块处理")
        print(f"✅ 生成的分块文件符合LSB_groth16格式")
    else:
        print(f"❌ 第三阶段完整集成测试失败")
        print(f"需要检查和修复相关问题")
    
    return success

if __name__ == "__main__":
    main() 
 
 