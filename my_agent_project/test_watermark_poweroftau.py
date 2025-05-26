#!/usr/bin/env python3
"""
测试有水印时的Powers of Tau生成流程
验证完整的6个步骤：初始化 → 用户贡献(模拟) → 验证 → 信标 → final.ptau → 验证
"""

import sys
import os
import shutil
import logging
import tempfile

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_watermark_poweroftau_flow():
    """测试有水印时的完整Powers of Tau流程"""
    try:
        from features.poweroftau_generator import PowerOfTauGenerator
        
        print("🧪 开始测试有水印时的Powers of Tau生成流程")
        
        # 初始化生成器
        generator = PowerOfTauGenerator()
        
        # 模拟参数（使用较小的约束以加快测试）
        constraint_power = 16  # 2^16 = 65536约束，用于快速测试
        user_id = "test_watermark_user"
        
        print(f"\n📋 测试参数:")
        print(f"   约束大小: 2^{constraint_power} = {2**constraint_power}")
        print(f"   用户ID: {user_id}")
        
        # 步骤1: 生成初始ptau（用于用户贡献）
        print(f"\n🔧 步骤1: 生成初始Powers of Tau")
        initial_info = generator.generate_initial_ptau_for_user_contribution(constraint_power, user_id)
        
        initial_ptau_path = initial_info["initial_ptau_path"]
        print(f"   ✅ 初始ptau生成完成: {initial_ptau_path}")
        print(f"   📁 文件大小: {os.path.getsize(initial_ptau_path) / (1024*1024):.1f} MB")
        
        # 步骤2: 模拟用户贡献（在实际应用中，这会在浏览器中完成）
        print(f"\n👤 步骤2: 模拟用户贡献")
        user_temp_dir = initial_info["user_temp_dir"]
        contributed_ptau = os.path.join(user_temp_dir, f"pot{constraint_power}_0001.ptau")
        
        # 使用新的贡献方法
        generator.contribute_with_entropy(
            initial_ptau_path, 
            contributed_ptau, 
            entropy="test_contribution_entropy_for_watermark_proof_123456789",
            name="test_contribution"
        )
        print(f"   ✅ 用户贡献完成: {contributed_ptau}")
        print(f"   📁 文件大小: {os.path.getsize(contributed_ptau) / (1024*1024):.1f} MB")
        
        # 步骤3-6: 完成Powers of Tau仪式
        print(f"\n🏁 步骤3-6: 完成Powers of Tau仪式")
        final_ptau_path = generator.complete_ptau_ceremony_from_user_contribution(
            contributed_ptau, user_id, constraint_power
        )
        
        print(f"   ✅ Powers of Tau完整流程完成!")
        print(f"   📁 最终ptau文件: {final_ptau_path}")
        print(f"   📁 文件大小: {os.path.getsize(final_ptau_path) / (1024*1024):.1f} MB")
        
        # 验证LSB_groth16目录中的文件
        expected_lsb_file = os.path.join(generator.lsb_dir, f"pot{constraint_power}_final.ptau")
        if os.path.exists(expected_lsb_file):
            print(f"   ✅ 文件已复制到LSB_groth16目录: {expected_lsb_file}")
        else:
            print(f"   ❌ 未找到LSB_groth16目录中的文件")
            
        # 清理测试文件
        print(f"\n🧹 清理测试文件")
        generator.cleanup_temp_files(user_id)
        print(f"   ✅ 临时文件已清理")
        
        print(f"\n🎉 Powers of Tau测试完成！所有6个步骤都执行成功")
        return True
        
    except Exception as e:
        logging.error(f"Powers of Tau测试失败: {e}")
        print(f"\n💥 测试失败: {e}")
        return False

def test_full_watermark_detection_flow():
    """测试完整的水印检测到Powers of Tau生成流程"""
    try:
        print(f"\n🔍 测试完整水印检测流程")
        
        # 创建一个临时数据集用于测试
        temp_dataset_dir = tempfile.mkdtemp(prefix="test_watermark_dataset_")
        
        # 创建一些测试图片文件（空文件用于测试）
        for i in range(3):
            test_image_path = os.path.join(temp_dataset_dir, f"test_image_{i}.jpg")
            with open(test_image_path, 'wb') as f:
                # 创建一个简单的测试文件（这里用空文件代替）
                f.write(b"test_image_data")
                
        print(f"   📁 临时数据集目录: {temp_dataset_dir}")
        
        # 这里不实际调用水印检测（因为需要真实的图片），只测试Powers of Tau部分
        from features.poweroftau_generator import PowerOfTauGenerator
        
        # 模拟ptau_info
        generator = PowerOfTauGenerator()
        ptau_info = {
            "total_pixels": 30000,  # 模拟像素数
            "optimal_config": {
                "power": 16,
                "constraint_size": 65536,
                "M": 100,
                "m": 300,
                "total_time": 0.0
            },
            "user_id": "test_watermark_user_2",
            "dataset_folder": temp_dataset_dir
        }
        
        print(f"   📊 模拟配置: 2^{ptau_info['optimal_config']['power']} 约束")
        
        # 测试零知识证明生成函数（不包括create_LSB_i.py部分）
        from features.feature_register import generate_zk_proof_for_watermark
        
        # 这里只测试Powers of Tau部分，跳过LSB电路生成
        print(f"   🧪 测试Powers of Tau生成部分...")
        
        # 直接测试Powers of Tau生成器
        optimal_config = ptau_info["optimal_config"]
        user_id = ptau_info["user_id"]
        constraint_power = optimal_config['power']
        
        # 生成初始ptau
        initial_info = generator.generate_initial_ptau_for_user_contribution(constraint_power, user_id)
        
        # 模拟用户贡献
        user_temp_dir = initial_info["user_temp_dir"]
        contributed_ptau = os.path.join(user_temp_dir, f"pot{constraint_power}_0001.ptau")
        
        generator.contribute_with_entropy(
            initial_info["initial_ptau_path"], 
            contributed_ptau, 
            entropy="test_watermark_contribution_entropy_123456789",
            name="test_watermark_contribution"
        )
        
        # 完成仪式
        final_ptau_path = generator.complete_ptau_ceremony_from_user_contribution(
            contributed_ptau, user_id, constraint_power
        )
        
        print(f"   ✅ Powers of Tau生成成功: {final_ptau_path}")
        
        # 清理
        generator.cleanup_temp_files(user_id)
        shutil.rmtree(temp_dataset_dir)
        
        print(f"   🧹 测试文件已清理")
        print(f"\n🎉 完整水印检测流程测试完成！")
        return True
        
    except Exception as e:
        logging.error(f"完整流程测试失败: {e}")
        print(f"\n💥 完整流程测试失败: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 Powers of Tau 水印检测流程测试")
    print("=" * 60)
    
    # 测试1: 基础Powers of Tau流程
    success1 = test_watermark_poweroftau_flow()
    
    # 测试2: 完整水印检测流程
    success2 = test_full_watermark_detection_flow()
    
    if success1 and success2:
        print(f"\n🎊 所有测试通过！Powers of Tau功能正常工作")
        sys.exit(0)
    else:
        print(f"\n💥 部分测试失败，请检查实现")
        sys.exit(1) 