#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
第四阶段零知识证明生成测试脚本

测试目标：
1. 使用分块好的数据在LSB_experiments/{buy_hash前16字符}中创建实验
2. 运行完整的零知识证明生成流程
3. 验证 B_witness.py, C_zkey_time.py, D_proof_public.py, E_verify_public.py 执行结果
"""

import os
import sys
import logging

# 添加features目录到path
sys.path.append(os.path.join(os.path.dirname(__file__), 'features'))

from stage4_proof_generation import Stage4ProofGenerator

def test_stage4_with_existing_chunked_data():
    """使用已有的分块数据测试第四阶段"""
    
    print("=== 第四阶段零知识证明生成测试 ===")
    
    # 使用已知的分块数据
    test_buy_hash = "a158e72bdc06739d4b9f3139de796443209eefd90bf43deff2d5bd4902346e604022bcd825f28136e"
    test_chunked_data_dir = "/Users/dylan/Code_Projects/Python_Projects/image_similarity/my_agent_project/data/chunked_inputs/session_a158e72bdc06739d/chunk_pixel_29"
    test_chunk_pixel_size = 29
    test_constraint_power = 16  # 改为16，因为用户只有pot16_final.ptau
    
    print(f"📋 测试参数:")
    print(f"   买家哈希: {test_buy_hash[:16]}...")
    print(f"   分块数据目录: {test_chunked_data_dir}")
    print(f"   分块像素大小: {test_chunk_pixel_size}")
    print(f"   约束功率: 2^{test_constraint_power}")
    
    # 检查分块数据是否存在
    if not os.path.exists(test_chunked_data_dir):
        print(f"❌ 分块数据目录不存在: {test_chunked_data_dir}")
        print("请先运行第三阶段分块处理")
        return False
    
    # 统计分块文件
    total_json_files = 0
    for root, dirs, files in os.walk(test_chunked_data_dir):
        total_json_files += len([f for f in files if f.endswith('.json')])
    
    print(f"📁 找到 {total_json_files} 个分块JSON文件")
    
    if total_json_files == 0:
        print("❌ 没有找到分块JSON文件")
        return False
    
    try:
        # 创建第四阶段证明生成器
        print("🚀 初始化第四阶段证明生成器...")
        generator = Stage4ProofGenerator()
        
        # 只执行前几个步骤，暂时不运行完整的证明生成流程（耗时较长）
        print("📋 执行第四阶段前期准备步骤...")
        
        # 1. 创建实验目录
        experiment_name = test_buy_hash[:16]
        experiment_dir = os.path.join(generator.experiments_base, experiment_name)
        
        print(f"🗂️  创建实验目录: {experiment_dir}")
        generator._create_experiment_directory(experiment_dir)
        
        # 2. 复制分块数据
        print(f"📂 复制分块数据...")
        generator._copy_chunked_data(test_chunked_data_dir, experiment_dir, test_chunk_pixel_size)
        
        # 3. 设置ptau文件
        print(f"⚙️  设置ptau文件...")
        generator._setup_ptau_file(experiment_dir, test_constraint_power)
        
        # 4. 更新配置文件
        print(f"🔧 更新配置文件...")
        generator._update_configuration_files(experiment_dir, test_chunk_pixel_size, test_constraint_power)
        
        # 5. 编译电路
        print(f"🔨 编译电路...")
        generator._compile_circuit(experiment_dir)
        
        print("✅ 第四阶段前期准备完成！")
        print(f"💡 实验目录创建于: {experiment_dir}")
        
        # 验证关键文件是否存在
        lsb_dir = os.path.join(experiment_dir, "LSB")
        verification_checks = [
            ("LSB.circom", os.path.join(lsb_dir, "LSB.circom")),
            ("LSB.r1cs", os.path.join(lsb_dir, "LSB.r1cs")),
            ("LSB.wasm", os.path.join(lsb_dir, "LSB_js", "LSB.wasm")),
            ("B_witness.py", os.path.join(lsb_dir, "B_witness.py")),
            ("C_zkey_time.py", os.path.join(lsb_dir, "C_zkey_time.py")),
            ("D_proof_public.py", os.path.join(lsb_dir, "D_proof_public.py")),
            ("E_verify_proof_public.py", os.path.join(lsb_dir, "E_verify_proof_public.py")),
            (f"ptau文件", os.path.join(lsb_dir, "ptau", f"pot{test_constraint_power}_final.ptau")),
            (f"输入数据目录", os.path.join(lsb_dir, f"input_json_chunk_pixel_{test_chunk_pixel_size}"))
        ]
        
        print("\n🔍 验证关键文件:")
        all_files_exist = True
        for desc, filepath in verification_checks:
            exists = os.path.exists(filepath)
            status = "✅" if exists else "❌"
            print(f"   {status} {desc}: {os.path.basename(filepath)}")
            if not exists:
                all_files_exist = False
        
        if all_files_exist:
            print("\n🎉 所有关键文件准备完成！")
            print("\n📝 下一步可以手动执行以下步骤来生成零知识证明:")
            print(f"   cd {lsb_dir}")
            print("   python B_witness.py")
            print("   python C_zkey_time.py") 
            print("   python D_proof_public.py")
            print("   python E_verify_proof_public.py")
            
            return True
        else:
            print("\n❌ 部分关键文件缺失，请检查配置")
            return False
            
    except Exception as e:
        print(f"❌ 第四阶段测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_quick_proof_generation():
    """快速测试一个小规模的证明生成（如果数据允许）"""
    
    print("\n" + "="*50)
    print("🚀 尝试快速证明生成测试")
    print("="*50)
    
    # 使用更小的分块数据进行快速测试
    test_buy_hash = "a158e72bdc06739d4b9f3139de796443209eefd90bf43deff2d5bd4902346e604022bcd825f28136e"
    test_chunked_data_dir = "/Users/dylan/Code_Projects/Python_Projects/image_similarity/my_agent_project/data/chunked_inputs/session_a158e72bdc06739d/chunk_pixel_29"
    test_chunk_pixel_size = 29
    test_constraint_power = 16  # 改为16，因为用户只有pot16_final.ptau
    
    # 检查是否只有少量分块文件可以快速测试
    if not os.path.exists(test_chunked_data_dir):
        print("❌ 测试数据不存在，跳过快速测试")
        return False
    
    # 统计文件数量
    total_files = 0
    for root, dirs, files in os.walk(test_chunked_data_dir):
        total_files += len([f for f in files if f.endswith('.json')])
    
    print(f"📁 分块文件数量: {total_files}")
    
    if total_files > 100:
        print("⚠️  文件数量较多，跳过完整证明生成测试（避免耗时过长）")
        print("💡 如需完整测试，请使用较小的数据集或手动执行")
        return False
    
    try:
        generator = Stage4ProofGenerator()
        
        print("🔄 开始完整的零知识证明生成流程...")
        
        result = generator.generate_proof_for_watermark(
            buy_hash=test_buy_hash,
            chunked_data_dir=test_chunked_data_dir,
            chunk_pixel_size=test_chunk_pixel_size,
            constraint_power=test_constraint_power
        )
        
        if result["status"] == "success":
            print("✅ 快速证明生成测试成功！")
            print(f"📁 实验目录: {result['experiment_dir']}")
            print("📊 执行结果:")
            for step, details in result["proof_results"].items():
                print(f"   {step}: {details['duration']:.2f}秒")
            
            verification = result["verification_results"]
            print(f"🔍 验证结果:")
            print(f"   证明文件: {verification['proof_files_generated']}")
            print(f"   公开输入文件: {verification['public_files_generated']}")
            print(f"   验证耗时: {verification['duration']:.2f}秒")
            
            return True
        else:
            print(f"❌ 快速证明生成失败: {result['error']}")
            return False
            
    except Exception as e:
        print(f"❌ 快速测试异常: {str(e)}")
        return False

if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    
    print("开始第四阶段零知识证明生成测试")
    print("="*60)
    
    # 测试第四阶段前期准备
    success = test_stage4_with_existing_chunked_data()
    
    if success:
        # 如果前期准备成功，尝试快速测试
        user_input = input("\n是否尝试完整的零知识证明生成？(y/N): ").strip().lower()
        if user_input == 'y':
            test_quick_proof_generation()
        else:
            print("💡 跳过完整证明生成，您可以手动进入实验目录执行各个步骤")
    
    print("\n🏁 第四阶段测试完成") 