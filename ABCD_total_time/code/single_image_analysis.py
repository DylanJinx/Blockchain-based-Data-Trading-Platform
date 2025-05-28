#!/usr/bin/env python3
"""
单个图像自适应分块分析
快速分析特定分辨率图像的最优约束选择
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from adaptive_block_algorithm import AdaptiveBlockAlgorithm
import argparse

def analyze_single_image(total_pixels, use_d_total=True, save_results=True, detailed=True):
    """
    分析单个图像的最优约束
    
    Args:
        total_pixels: 总像素数
        use_d_total: 是否使用D_total_time模型
        save_results: 是否保存结果文件
        detailed: 是否显示详细分析
    """
    algorithm = AdaptiveBlockAlgorithm()
    
    print(f"分析图像分辨率: {total_pixels} 像素")
    print(f"使用D模型: {'D_total_time' if use_d_total else 'D_time'}")
    print()
    
    # 运行分析
    optimal, results, constraint_groups = algorithm.run_analysis(
        total_pixels, use_d_total=use_d_total, save_results=save_results
    )
    
    if not detailed:
        # 简化输出
        print(f"\n=== 简化结果 ===")
        if optimal:
            print(f"最优约束: 2^{optimal['power']} = {optimal['X']}")
            print(f"最优配置: M={optimal['M']}, m={optimal['m']}")
            print(f"总时间: {optimal['total_time']:.2f} 秒")
        
        # 显示所有约束的总时间对比
        if results:
            print(f"\n所有约束时间对比:")
            for result in results:
                print(f"  2^{result['power']:>2}: {result['total_time']:>8.1f} 秒")
    
    return optimal, results, constraint_groups

def main():
    """命令行接口"""
    parser = argparse.ArgumentParser(description='单个图像自适应分块分析')
    parser.add_argument('pixels', type=int, help='图像总像素数')
    parser.add_argument('--d-model', choices=['total', 'single'], default='total',
                        help='D步骤模型选择: total(D_total_time) 或 single(D_time)')
    parser.add_argument('--no-save', action='store_true', help='不保存结果文件')
    parser.add_argument('--simple', action='store_true', help='简化输出')
    
    args = parser.parse_args()
    
    use_d_total = (args.d_model == 'total')
    save_results = not args.no_save
    detailed = not args.simple
    
    analyze_single_image(args.pixels, use_d_total, save_results, detailed)

if __name__ == '__main__':
    if len(sys.argv) == 1:
        # 如果没有命令行参数，使用交互模式
        print("=== 交互式单图像分析 ===")
        try:
            pixels = int(input("请输入图像总像素数: "))
            model_choice = input("选择D步骤模型 (1: D_total_time, 2: D_time) [1]: ").strip()
            use_d_total = (model_choice != '2')
            
            analyze_single_image(pixels, use_d_total=use_d_total)
        except (ValueError, KeyboardInterrupt):
            print("输入错误或用户取消")
    else:
        main() 