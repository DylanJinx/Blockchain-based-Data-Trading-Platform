#!/usr/bin/env python3
"""
完整的水印检测+Powers of Tau工作流程测试
模拟用户数据集包含水印时的完整流程：
1. 数据集分析
2. 水印检测（模拟检测到水印）
3. 生成初始Powers of Tau
4. 模拟用户贡献
5. 完成Powers of Tau仪式
6. 生成零知识证明文件
"""

import sys
import os
import logging
import tempfile
import shutil
import time

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def create_test_dataset():
    """创建测试数据集"""
    try:
        # 创建临时目录和测试图片
        test_dir = tempfile.mkdtemp(prefix="watermark_test_")
        logging.info(f"创建测试数据集: {test_dir}")
        
        # 创建一些测试图片文件（空文件，只用于测试像素计算）
        from PIL import Image
        import numpy as np
        
        for i in range(3):
            # 创建100x100的随机图片
            img_array = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
            img = Image.fromarray(img_array)
            img.save(os.path.join(test_dir, f"test_image_{i}.jpg"))
        
        logging.info(f"测试数据集创建完成: {test_dir}, 包含3张100x100图片")
        return test_dir
        
    except Exception as e:
        logging.error(f"创建测试数据集失败: {e}")
        raise

def test_complete_watermark_workflow():
    """测试完整的水印+Powers of Tau工作流程"""
    test_dataset = None
    
    try:
        from features.poweroftau_generator import PowerOfTauGenerator
        from features.feature_register import prepare_poweroftau_for_user_contribution
        
        print("🧪 测试完整水印检测+Powers of Tau工作流程")
        print("=" * 60)
        
        # 1. 创建测试数据集
        print("📁 步骤1: 创建测试数据集")
        test_dataset = create_test_dataset()
        
        # 2. 初始化PowerOfTauGenerator并分析数据集
        print("📊 步骤2: 分析数据集并计算约束配置")
        generator = PowerOfTauGenerator()
        user_id = "watermark_test_user"
        
        total_pixels = generator.calculate_dataset_pixels(test_dataset)
        optimal_config = generator.get_optimal_constraints(total_pixels)
        
        print(f"   📋 数据集分析结果:")
        print(f"   - 总像素数: {total_pixels:,}")
        print(f"   - 最优约束: 2^{optimal_config['power']} = {optimal_config['constraint_size']:,}")
        print(f"   - 分块数M: {optimal_config['M']}")
        print(f"   - 单块像素数m: {optimal_config['m']}")
        
        # 3. 模拟水印检测（假设检测到水印）
        print("\n🔍 步骤3: 模拟水印检测（假设检测到水印）")
        
        # 准备ptau_info
        ptau_info = {
            "total_pixels": total_pixels,
            "optimal_config": optimal_config,
            "user_id": user_id,
            "dataset_folder": test_dataset
        }
        
        print("   ⚠️  模拟检测到水印，开始Powers of Tau流程")
        
        # 4. 准备Powers of Tau初始文件
        print("\n⚡ 步骤4: 准备Powers of Tau初始文件")
        initial_result = prepare_poweroftau_for_user_contribution(test_dataset, ptau_info)
        
        print(f"   ✅ 初始文件准备完成:")
        print(f"   - 状态: {initial_result['status']}")
        print(f"   - 约束大小: 2^{initial_result['constraint_power']}")
        print(f"   - 用户ID: {initial_result['user_id']}")
        
        # 5. 模拟用户在浏览器中的贡献
        print("\n🌐 步骤5: 模拟用户在浏览器中的贡献")
        
        initial_ptau_path = initial_result['initial_ptau_info']['initial_ptau_path']
        constraint_power = initial_result['constraint_power']
        
        # 创建贡献文件路径
        user_temp_dir = os.path.dirname(initial_ptau_path)
        contributed_ptau_path = os.path.join(user_temp_dir, f"pot{constraint_power}_0001.ptau")
        
        # 模拟用户贡献（这在实际应用中由浏览器完成）
        print("   🎲 生成模拟用户贡献...")
        generator.contribute_with_entropy(
            initial_ptau_path,
            contributed_ptau_path,
            entropy="test_watermark_workflow_entropy_12345",
            name="watermark_test_contribution"
        )
        
        print(f"   ✅ 用户贡献完成: {contributed_ptau_path}")
        
        # 6. 完成Powers of Tau仪式
        print("\n🏁 步骤6: 完成Powers of Tau仪式")
        final_ptau_path = generator.complete_ptau_ceremony_from_user_contribution(
            contributed_ptau_path, user_id, constraint_power
        )
        
        print(f"   ✅ Powers of Tau仪式完成: {final_ptau_path}")
        
        # 7. 验证最终文件
        print("\n✅ 步骤7: 验证最终文件")
        if os.path.exists(final_ptau_path):
            file_size = os.path.getsize(final_ptau_path) / (1024 * 1024)  # MB
            print(f"   📁 最终ptau文件: {final_ptau_path}")
            print(f"   📏 文件大小: {file_size:.2f} MB")
        else:
            raise RuntimeError("最终ptau文件不存在")
        
        # 8. 清理用户临时文件
        print("\n🧹 步骤8: 清理临时文件")
        generator.cleanup_temp_files(user_id)
        print("   ✅ 临时文件清理完成")
        
        print("\n🎉 完整工作流程测试成功！")
        print("\n📋 测试总结:")
        print(f"   - 数据集像素: {total_pixels:,}")
        print(f"   - 约束配置: 2^{constraint_power} = {2**constraint_power:,}")
        print(f"   - 最终ptau: {os.path.basename(final_ptau_path)}")
        print(f"   - 工作流程: 数据分析 → 水印检测 → Powers of Tau → 零知识证明准备")
        
        return True
        
    except Exception as e:
        logging.error(f"工作流程测试失败: {e}")
        print(f"\n❌ 测试失败: {e}")
        return False
        
    finally:
        # 清理测试数据集
        if test_dataset and os.path.exists(test_dataset):
            try:
                shutil.rmtree(test_dataset)
                logging.info(f"已清理测试数据集: {test_dataset}")
            except Exception as e:
                logging.warning(f"清理测试数据集失败: {e}")

if __name__ == "__main__":
    success = test_complete_watermark_workflow()
    sys.exit(0 if success else 1) 