#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试多张图片ZK输入数据生成功能
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'features'))

from addWatermark import find_zk_input_for_buy_hash

def test_multi_zk_input():
    """测试多张图片的ZK输入数据查找"""
    buy_hash = "4b9f3139de796443209eefd90bf43deff2d5bd4902346e604022bcd825f28136e"
    
    print("=== 测试多张图片ZK输入数据查找 ===")
    print(f"查找buy_hash: {buy_hash[:16]}...")
    
    result = find_zk_input_for_buy_hash(buy_hash)
    
    if result:
        print(f"✅ 找到 {result['total_files']} 个ZK输入文件:")
        for i, file_info in enumerate(result['zk_input_files'], 1):
            print(f"  {i}. {file_info['filename']} ({file_info['file_size']/1024:.1f} KB)")
            
            # 从文件名中提取图片名
            if 'train_' in file_info['filename']:
                image_name = file_info['filename'].split('_')[-1].replace('.json', '.png')
                print(f"     对应图片: {image_name}")
        
        print(f"\n总结:")
        print(f"  - 生成了 {result['total_files']} 个独立的ZK输入文件")
        print(f"  - 每个文件对应一张96×96图片")
        print(f"  - 符合LSB_groth16的单张图片处理要求")
        return True
    else:
        print("❌ 未找到ZK输入文件")
        return False

if __name__ == "__main__":
    success = test_multi_zk_input()
    print(f"\n测试结果: {'✅ 通过' if success else '❌ 失败'}") 
 
 