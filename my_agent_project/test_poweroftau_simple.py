#!/usr/bin/env python3
"""
简化的Powers of Tau测试脚本
使用小约束（2^12）快速验证6个步骤的功能
"""

import sys
import os
import logging

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_simple_poweroftau():
    """简化的Powers of Tau测试"""
    try:
        from features.poweroftau_generator import PowerOfTauGenerator
        
        print("🧪 开始简化Powers of Tau测试（2^12约束）")
        
        generator = PowerOfTauGenerator()
        constraint_power = 12  # 2^12 = 4096约束，快速测试
        user_id = "simple_test"
        
        print(f"   约束大小: 2^{constraint_power} = {2**constraint_power}")
        
        # 步骤1: 生成初始ptau
        print(f"\n🔧 步骤1: 初始化Powers of Tau")
        initial_info = generator.generate_initial_ptau_for_user_contribution(constraint_power, user_id)
        initial_ptau = initial_info["initial_ptau_path"]
        
        print(f"   ✅ 初始ptau: {initial_ptau}")
        print(f"   📁 大小: {os.path.getsize(initial_ptau) / (1024*1024):.1f} MB")
        
        # 步骤2: 模拟用户贡献（快速版本）
        print(f"\n👤 步骤2: 模拟用户贡献")
        user_temp_dir = initial_info["user_temp_dir"]
        contributed_ptau = os.path.join(user_temp_dir, f"pot{constraint_power}_0001.ptau")
        
        # 使用新的贡献方法（自动生成熵值）
        generator.contribute_with_entropy(
            initial_ptau, 
            contributed_ptau, 
            entropy="test_entropy_for_simple_test_123456789",
            name="simple_test"
        )
        
        print(f"   ✅ 贡献完成: {contributed_ptau}")
        print(f"   📁 大小: {os.path.getsize(contributed_ptau) / (1024*1024):.1f} MB")
        
        # 步骤3-6: 完成仪式
        print(f"\n🏁 步骤3-6: 完成Powers of Tau仪式")
        final_ptau = generator.complete_ptau_ceremony_from_user_contribution(
            contributed_ptau, user_id, constraint_power
        )
        
        print(f"   ✅ 最终ptau: {final_ptau}")
        print(f"   📁 大小: {os.path.getsize(final_ptau) / (1024*1024):.1f} MB")
        
        # 验证LSB_groth16目录
        lsb_file = os.path.join(generator.lsb_dir, f"pot{constraint_power}_final.ptau")
        if os.path.exists(lsb_file):
            print(f"   ✅ 已复制到LSB_groth16: {lsb_file}")
        else:
            print(f"   ❌ LSB_groth16复制失败")
            
        # 清理
        generator.cleanup_temp_files(user_id)
        print(f"   🧹 临时文件已清理")
        
        print(f"\n🎉 Powers of Tau 6步流程测试成功！")
        return True
        
    except Exception as e:
        logging.error(f"测试失败: {e}")
        print(f"💥 测试失败: {e}")
        return False

def test_constraint_calculation():
    """测试约束计算"""
    try:
        from features.poweroftau_generator import PowerOfTauGenerator
        
        print(f"\n📊 测试约束计算")
        generator = PowerOfTauGenerator()
        
        # 测试不同像素数的约束计算
        test_cases = [30000, 100000, 500000, 921600, 1000000]
        
        for pixels in test_cases:
            config = generator.get_optimal_constraints(pixels)
            print(f"   {pixels:>7} 像素 → 2^{config['power']} = {config['constraint_size']:>7} 约束 (M={config['M']}, m={config['m']})")
            
        print(f"   ✅ 约束计算测试完成")
        return True
        
    except Exception as e:
        logging.error(f"约束计算测试失败: {e}")
        print(f"💥 约束计算测试失败: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("🧪 简化Powers of Tau测试")
    print("=" * 50)
    
    # 测试约束计算
    success1 = test_constraint_calculation()
    
    # 测试Powers of Tau流程
    success2 = test_simple_poweroftau()
    
    if success1 and success2:
        print(f"\n🎊 所有测试通过！Powers of Tau功能正常")
    else:
        print(f"\n💥 部分测试失败")
        
    sys.exit(0 if success1 and success2 else 1) 