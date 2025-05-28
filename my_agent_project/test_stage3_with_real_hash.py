#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试Stage 3分块处理，使用实际存在的买家哈希
"""

import sys
import os
import logging
import json

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 添加features目录到path
sys.path.append('features')

from stage3_chunk_and_proof import process_watermarked_dataset_registration

def test_stage3_with_real_hash():
    """使用实际存在的买家哈希测试Stage 3分块处理"""
    
    # 使用实际存在的买家哈希 a158e72bdc06739d
    buy_hash = "a158e72bdc06739d4b9f3139de796443209eefd90bf43deff2d5bd4902346e604022bcd825f28136e"
    
    # 使用与Powers of Tau相同的约束配置
    optimal_config = {
        'power': 16,  # 2^16 = 65536，与已生成的pot16_final.ptau匹配
        'constraint_size': 65536,
        'M': 29,  # 假设分块数
        'm': 29,  # 每块像素数（与测试的29像素匹配）
        'total_time': 120.0
    }
    
    print("=== 测试Stage 3分块处理（使用实际买家哈希）===")
    print(f"买家哈希: {buy_hash[:16]}...")
    print(f"约束配置: {optimal_config}")
    
    try:
        # 执行Stage 3分块处理
        result = process_watermarked_dataset_registration(buy_hash, optimal_config)
        
        print("\n=== Stage 3处理结果 ===")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        if result.get("status") == "chunking_completed":
            print("\n✅ Stage 3分块处理成功！")
            
            # 检查LSB_experiments目录是否生成
            import os
            lsb_experiments_dir = "/Users/dylan/Code_Projects/Python_Projects/image_similarity/LSB_groth16/LSB_experiments"
            buyer_hash_16 = buy_hash[:16]
            buyer_experiment_dir = os.path.join(lsb_experiments_dir, buyer_hash_16)
            
            print(f"检查实验目录: {buyer_experiment_dir}")
            if os.path.exists(buyer_experiment_dir):
                print("✅ 买家实验目录已创建")
                contents = os.listdir(buyer_experiment_dir)
                print(f"目录内容: {contents}")
            else:
                print("❌ 买家实验目录未创建")
                
        else:
            print(f"❌ Stage 3处理失败: {result.get('message', '未知错误')}")
            
    except Exception as e:
        print(f"❌ 测试过程出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_stage3_with_real_hash() 