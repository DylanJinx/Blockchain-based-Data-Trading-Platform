#!/usr/bin/env python3
"""
测试约束计算修复
验证PowerOfTauGenerator是否能正确计算921600像素的最优约束
"""

import sys
import os
import logging

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_constraint_calculation():
    """测试约束计算功能"""
    try:
        from features.poweroftau_generator import PowerOfTauGenerator
        
        # 初始化生成器
        generator = PowerOfTauGenerator()
        
        # 测试921600像素的约束计算
        total_pixels = 921600
        logging.info(f"测试像素数: {total_pixels}")
        
        # 计算最优约束
        optimal_config = generator.get_optimal_constraints(total_pixels)
        
        print(f"\n=== 约束计算结果 ===")
        print(f"总像素数: {total_pixels}")
        print(f"最优约束: 2^{optimal_config['power']} = {optimal_config['constraint_size']}")
        print(f"分块数M: {optimal_config['M']}")
        print(f"单块像素数m: {optimal_config['m']}")
        print(f"预估总时间: {optimal_config['total_time']:.2f} 秒")
        
        # 验证是否与single_image_analysis.py的结果一致
        expected_power = 19  # 根据之前的测试，921600像素应该是2^19
        if optimal_config['power'] == expected_power:
            print(f"✅ 约束计算正确！与single_image_analysis.py结果一致")
            return True
        else:
            print(f"❌ 约束计算可能有误。期望: 2^{expected_power}, 实际: 2^{optimal_config['power']}")
            return False
            
    except Exception as e:
        logging.error(f"测试失败: {e}")
        print(f"❌ 测试失败: {e}")
        return False

if __name__ == "__main__":
    print("开始测试约束计算修复...")
    success = test_constraint_calculation()
    
    if success:
        print("\n🎉 测试通过！约束计算修复成功")
    else:
        print("\n💥 测试失败，需要进一步修复")
    
    sys.exit(0 if success else 1) 