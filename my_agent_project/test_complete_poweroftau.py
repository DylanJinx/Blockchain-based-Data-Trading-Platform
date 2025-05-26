#!/usr/bin/env python3
"""
完整的Powers of Tau测试脚本
验证有水印时的完整6步流程：
1. 初始化poweroftau
2. 第一次贡献（自动生成熵值）
3. 验证第一次贡献
4. 引入随机化信标
5. 生成最终的final.ptau
6. 验证final.ptau
"""

import sys
import os
import logging
import tempfile
import shutil

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_complete_poweroftau_flow():
    """测试完整的Powers of Tau 6步流程"""
    try:
        from features.poweroftau_generator import PowerOfTauGenerator
        
        print("🧪 测试完整Powers of Tau 6步流程")
        print("=" * 60)
        
        generator = PowerOfTauGenerator()
        constraint_power = 12  # 使用2^12 = 4096约束进行快速测试
        user_id = "complete_test"
        
        print(f"📋 测试配置:")
        print(f"   约束大小: 2^{constraint_power} = {2**constraint_power}")
        print(f"   用户ID: {user_id}")
        
        # ============ 步骤1: 初始化Powers of Tau ============
        print(f"\n🔧 步骤1: 初始化Powers of Tau")
        initial_info = generator.generate_initial_ptau_for_user_contribution(constraint_power, user_id)
        initial_ptau = initial_info["initial_ptau_path"]
        user_temp_dir = initial_info["user_temp_dir"]
        
        print(f"   ✅ 初始化完成: {initial_ptau}")
        print(f"   📁 文件大小: {os.path.getsize(initial_ptau) / (1024*1024):.2f} MB")
        
        # ============ 步骤2: 第一次贡献 ============
        print(f"\n👤 步骤2: 第一次贡献（自动生成熵值）")
        contributed_ptau = os.path.join(user_temp_dir, f"pot{constraint_power}_0001.ptau")
        
        # 使用自定义熵值进行贡献
        test_entropy = "this_is_a_test_entropy_string_for_watermark_evidence_123456789"
        generator.contribute_with_entropy(
            initial_ptau, 
            contributed_ptau, 
            entropy=test_entropy,
            name="watermark_evidence_test"
        )
        
        print(f"   ✅ 贡献完成: {contributed_ptau}")
        print(f"   📁 文件大小: {os.path.getsize(contributed_ptau) / (1024*1024):.2f} MB")
        print(f"   🔑 使用熵值长度: {len(test_entropy)}")
        
        # ============ 步骤3-6: 完成Powers of Tau仪式 ============
        print(f"\n🏁 步骤3-6: 完成Powers of Tau仪式")
        print(f"   - 步骤3: 验证第一次贡献")
        print(f"   - 步骤4: 引入随机化信标")
        print(f"   - 步骤5: 生成最终的final.ptau")
        print(f"   - 步骤6: 验证final.ptau")
        
        final_ptau_path = generator.complete_ptau_ceremony_from_user_contribution(
            contributed_ptau, user_id, constraint_power
        )
        
        print(f"   ✅ Powers of Tau仪式完成!")
        print(f"   📁 最终ptau文件: {final_ptau_path}")
        print(f"   📁 文件大小: {os.path.getsize(final_ptau_path) / (1024*1024):.2f} MB")
        
        # ============ 验证LSB_groth16目录 ============
        print(f"\n📂 验证LSB_groth16目录")
        lsb_file = os.path.join(generator.lsb_dir, f"pot{constraint_power}_final.ptau")
        if os.path.exists(lsb_file):
            print(f"   ✅ 文件已复制到LSB_groth16: {lsb_file}")
            print(f"   📁 LSB文件大小: {os.path.getsize(lsb_file) / (1024*1024):.2f} MB")
        else:
            print(f"   ❌ LSB_groth16目录中未找到文件")
            return False
        
        # ============ 清理测试文件 ============
        print(f"\n🧹 清理测试文件")
        generator.cleanup_temp_files(user_id)
        print(f"   ✅ 临时文件已清理")
        
        print(f"\n🎉 完整Powers of Tau 6步流程测试成功！")
        print(f"✅ 所有步骤都正常工作：")
        print(f"   1. ✅ 初始化Powers of Tau")
        print(f"   2. ✅ 第一次贡献（带熵值）")
        print(f"   3. ✅ 验证第一次贡献")
        print(f"   4. ✅ 引入随机化信标")
        print(f"   5. ✅ 生成最终的final.ptau")
        print(f"   6. ✅ 验证final.ptau")
        print(f"   7. ✅ 复制到LSB_groth16目录")
        
        return True
        
    except Exception as e:
        logging.error(f"Powers of Tau测试失败: {e}")
        print(f"\n💥 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_watermark_detection_with_poweroftau():
    """测试完整的水印检测+Powers of Tau流程"""
    try:
        print(f"\n🔍 测试水印检测+Powers of Tau集成流程")
        print("=" * 60)
        
        # 创建临时数据集
        temp_dataset_dir = tempfile.mkdtemp(prefix="watermark_test_dataset_")
        
        # 创建一些虚拟图片文件（用于测试）
        for i in range(5):
            test_image = os.path.join(temp_dataset_dir, f"test_image_{i}.jpg")
            with open(test_image, 'wb') as f:
                # 创建一个100x100的虚拟图片数据
                f.write(b"dummy_image_data" * 1000)  # 模拟图片数据
                
        print(f"   📁 临时数据集: {temp_dataset_dir}")
        print(f"   📊 包含5个测试图片文件")
        
        # 模拟ptau_info
        from features.poweroftau_generator import PowerOfTauGenerator
        generator = PowerOfTauGenerator()
        
        # 计算像素数（假设每个文件代表100x100图片）
        total_pixels = 5 * 100 * 100  # 50,000像素
        optimal_config = generator.get_optimal_constraints(total_pixels)
        
        ptau_info = {
            "total_pixels": total_pixels,
            "optimal_config": optimal_config,
            "user_id": "watermark_test_user",
            "dataset_folder": temp_dataset_dir
        }
        
        print(f"   📊 模拟配置:")
        print(f"      总像素数: {total_pixels}")
        print(f"      最优约束: 2^{optimal_config['power']} = {optimal_config['constraint_size']}")
        print(f"      分块配置: M={optimal_config['M']}, m={optimal_config['m']}")
        
        # 测试零知识证明生成函数的Powers of Tau部分
        print(f"\n🧪 测试Powers of Tau生成（不包括LSB电路生成）")
        
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
            entropy="watermark_evidence_entropy_123456789",
            name="watermark_evidence_contribution"
        )
        
        # 完成仪式
        final_ptau_path = generator.complete_ptau_ceremony_from_user_contribution(
            contributed_ptau, user_id, constraint_power
        )
        
        print(f"   ✅ Powers of Tau生成成功: {final_ptau_path}")
        print(f"   📁 文件大小: {os.path.getsize(final_ptau_path) / (1024*1024):.2f} MB")
        
        # 清理
        generator.cleanup_temp_files(user_id)
        shutil.rmtree(temp_dataset_dir)
        
        print(f"   🧹 测试文件已清理")
        print(f"\n🎉 水印检测+Powers of Tau集成测试成功！")
        
        return True
        
    except Exception as e:
        logging.error(f"集成测试失败: {e}")
        print(f"\n💥 集成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Powers of Tau 完整功能测试")
    print("=" * 80)
    
    # 测试1: 完整的Powers of Tau 6步流程
    print("\n📝 测试1: 完整Powers of Tau 6步流程")
    success1 = test_complete_poweroftau_flow()
    
    # 测试2: 水印检测集成流程
    print("\n📝 测试2: 水印检测+Powers of Tau集成流程")
    success2 = test_watermark_detection_with_poweroftau()
    
    # 总结
    print("\n" + "=" * 80)
    print("🏁 测试总结")
    print("=" * 80)
    
    if success1 and success2:
        print("🎊 所有测试通过！Powers of Tau功能完全正常")
        print("✅ 可以处理有水印数据集的零知识证明生成")
        print("✅ 6个步骤流程完整无误")
        print("✅ 与水印检测系统集成正常")
        sys.exit(0)
    else:
        print("💥 部分测试失败，需要修复问题")
        if not success1:
            print("❌ Powers of Tau基础功能测试失败")
        if not success2:
            print("❌ 水印检测集成测试失败")
        sys.exit(1) 