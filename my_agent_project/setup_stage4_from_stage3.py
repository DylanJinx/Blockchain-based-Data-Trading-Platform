#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
从Stage 3分块结果设置Stage 4实验目录
"""

import sys
import os
import shutil
import glob
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 添加features目录到path
sys.path.append('features')

from stage4_proof_generation import Stage4ProofGenerator

def setup_stage4_from_stage3_result(buyer_hash, stage3_result_dir):
    """
    从Stage 3分块结果直接生成零知识证明
    
    Args:
        buyer_hash: 买家哈希（16位）
        stage3_result_dir: Stage 3分块结果目录
    """
    
    print(f"=== 从Stage 3结果生成零知识证明 ===")
    print(f"买家哈希: {buyer_hash}")
    print(f"Stage 3结果目录: {stage3_result_dir}")
    
    try:
        # 验证Stage 3结果目录存在
        if not os.path.exists(stage3_result_dir):
            print(f"❌ Stage 3结果目录不存在: {stage3_result_dir}")
            return False
        
        # 统计分块文件
        json_files = glob.glob(os.path.join(stage3_result_dir, '**', '*.json'), recursive=True)
        print(f"找到 {len(json_files)} 个分块文件")
        
        if len(json_files) == 0:
            print("❌ 未找到分块文件")
            return False
        
        # 初始化Stage4生成器
        stage4_gen = Stage4ProofGenerator()
        
        # 构造完整的买家哈希（用于generate_proof_for_watermark）
        full_buyer_hash = buyer_hash + "4b9f3139de796443209eefd90bf43deff2d5bd4902346e604022bcd825f28136e"
        
        # 参数配置
        chunk_pixel_size = 29  # 每块像素数
        constraint_power = 16  # 约束功率（对应pot16_final.ptau）
        
        print(f"开始生成零知识证明...")
        print(f"  - 分块像素大小: {chunk_pixel_size}")
        print(f"  - 约束功率: 2^{constraint_power}")
        print(f"  - 分块文件数: {len(json_files)}")
        
        # 调用generate_proof_for_watermark方法
        result = stage4_gen.generate_proof_for_watermark(
            buy_hash=full_buyer_hash,
            chunked_data_dir=stage3_result_dir,
            chunk_pixel_size=chunk_pixel_size,
            constraint_power=constraint_power
        )
        
        print(f"\n=== Stage 4执行结果 ===")
        print(f"状态: {result.get('status')}")
        
        if result.get('status') == 'success':
            print("✅ 零知识证明生成成功！")
            print(f"实验目录: {result.get('experiment_dir')}")
            print(f"实验名称: {result.get('experiment_name')}")
            print(f"总耗时: {result.get('total_time', 0):.2f}秒")
            
            # 显示证明结果
            proof_results = result.get('proof_results', {})
            verification_results = result.get('verification_results', {})
            
            print(f"\n证明生成结果:")
            for step, step_result in proof_results.items():
                status = "✅" if step_result.get('success') else "❌"
                print(f"  {status} {step}: {step_result.get('message', 'N/A')}")
            
            print(f"\n证明验证结果:")
            for step, step_result in verification_results.items():
                status = "✅" if step_result.get('success') else "❌"
                print(f"  {status} {step}: {step_result.get('message', 'N/A')}")
            
            return True
        else:
            print(f"❌ 零知识证明生成失败: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ 处理过程出错: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    
    buyer_hash = "a158e72bdc06739d"
    stage3_result_dir = "data/chunked_inputs/session_a158e72bdc06739d/chunk_pixel_29"
    
    success = setup_stage4_from_stage3_result(buyer_hash, stage3_result_dir)
    
    if success:
        print("\n🎉 Stage 4零知识证明生成成功完成！")
        print("现在用户可以获取完整的零知识证明，证明其数据集确实包含水印。")
        
        # 检查生成的实验目录
        experiment_dir = f"/Users/dylan/Code_Projects/Python_Projects/image_similarity/LSB_groth16/LSB_experiments/{buyer_hash}"
        if os.path.exists(experiment_dir):
            print(f"\n实验目录: {experiment_dir}")
            
            # 检查关键文件
            key_files = ["LSB/proof.json", "LSB/public.json", "LSB/verification_key.json"]
            for key_file in key_files:
                file_path = os.path.join(experiment_dir, key_file)
                if os.path.exists(file_path):
                    print(f"✅ {key_file}")
                else:
                    print(f"❌ {key_file}")
        
        print(f"\n如需重新运行，可以使用:")
        print(f"cd ../LSB_groth16/LSB_experiments")
        print(f"python run_auto_proof.py --buyer-hash {buyer_hash}")
    else:
        print("\n❌ Stage 4零知识证明生成失败")

if __name__ == "__main__":
    main() 