#!/usr/bin/env python3
"""
自适应分块算法 - 完整实现
整合ABCD四个步骤的拟合公式，自动选择最优约束
"""

import numpy as np
import math
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib

# 设置中文字体
matplotlib.use("Agg")
plt.rcParams['font.sans-serif'] = ['Songti SC', 'STHeiti', 'SimHei', 'SimSun', 'FangSong', 'Arial Unicode MS'] 
plt.rcParams['axes.unicode_minus'] = False

class AdaptiveBlockAlgorithm:
    """自适应分块算法类"""
    
    def __init__(self):
        # 常数设置
        self.c = 2250  # 每像素约束数 (1125 * 2)
        
        # A步骤拟合参数
        self.A_cut = 2**15
        self.A_alpha_s = 1.625375
        self.A_beta_s = 2.574410e-03
        self.A_alpha_l = -113.042472
        self.A_beta_l = 1.611649e-04
        
        # B步骤拟合参数
        self.B_alpha = -3.744890
        self.B_beta1 = 0.949187
        self.B_beta2 = -0.001573
        
        # C步骤拟合参数  
        self.C_a = 112.955779
        self.C_b = 0.442681
        self.C_c = -6.382411
        self.C_d = 3.213201e-05
        self.C_e = -2.177809e-05
        
        # D步骤拟合参数（两个可选模型）
        # D_time模型
        self.D_time_a = -15.193138
        self.D_time_b = -0.026156
        self.D_time_c = 0.948947
        self.D_time_d = 0.001730
        
        # D_total_time模型
        self.D_total_a = -6.336975
        self.D_total_b = -0.009190
        self.D_total_c = 0.548115
        self.D_total_d = 0.016493
    
    def predict_A_time(self, X):
        """预测A步骤时间（分段函数）"""
        if X <= self.A_cut:
            return self.A_alpha_s + self.A_beta_s * X
        else:
            return self.A_alpha_l + self.A_beta_l * X * math.log2(X)
    
    def predict_B_time(self, pixel, chunks):
        """预测B步骤时间"""
        ln_B_time = (self.B_alpha + 
                     self.B_beta1 * np.log(pixel) + 
                     self.B_beta2 * np.log(chunks))
        return np.exp(ln_B_time)
    
    def predict_C_time(self, pixel, chunks, X):
        """预测C步骤时间"""
        return (self.C_a + 
                self.C_b * pixel + 
                self.C_c * np.log(chunks) + 
                self.C_d * X + 
                self.C_e * (pixel ** 2))
    
    def predict_D_time_single(self, pixel, X):
        """预测D步骤单次时间"""
        log2_X = math.log2(X)
        return (self.D_time_a + 
                self.D_time_b * pixel + 
                self.D_time_c * log2_X + 
                self.D_time_d * pixel * log2_X)
    
    def predict_D_total_time(self, pixel, chunks):
        """预测D步骤总时间"""
        return (self.D_total_a + 
                self.D_total_b * pixel + 
                self.D_total_c * chunks + 
                self.D_total_d * pixel * chunks)
    
    def calculate_constraint_groups(self, total_pixels):
        """
        计算给定总像素数下每个2^i约束的(M,m)组合
        
        Args:
            total_pixels: 总像素数N
            
        Returns:
            constraint_groups: 字典，键为约束X值，值为(M,m)组合列表
        """
        print(f"=== 分析图像分辨率: {total_pixels} 像素 ===")
        print(f"每像素约束数: {self.c}")
        print()
        
        constraint_groups = {}
        
        # 测试不同的分块数M（从1到total_pixels）
        for M in range(1, min(total_pixels + 1, 10000)):  # 限制最大分块数避免计算过久
            # 计算每块像素数（向上取整）
            m = math.ceil(total_pixels / M)
            
            # 计算约束数
            constraints = m * self.c
            
            # 找到最近的2的幂
            power = math.ceil(math.log2(constraints))
            X = 2 ** power
            
            # 只考虑2^16到2^25的约束范围
            if 16 <= power <= 25:
                if X not in constraint_groups:
                    constraint_groups[X] = []
                
                constraint_groups[X].append({
                    'M': M,
                    'm': m,
                    'power': power,
                    'constraints': constraints,
                    'actual_total_pixels': M * m
                })
        
        # 对每个约束下的组合按像素数降序排序（FFT台阶效应，像素数大的时间短）
        for X in constraint_groups:
            constraint_groups[X].sort(key=lambda x: x['m'], reverse=True)
        
        return constraint_groups
    
    def evaluate_performance(self, total_pixels, constraint_groups, use_d_total=True):
        """
        评估每个约束下的性能
        
        Args:
            total_pixels: 总像素数
            constraint_groups: 约束组合字典
            use_d_total: 是否使用D_total_time模型（否则使用D_time模型）
            
        Returns:
            results: 性能评估结果列表
        """
        results = []
        
        print(f"=== 性能评估（使用{'D_total_time' if use_d_total else 'D_time'}模型） ===")
        print(f"{'约束':>10} {'分块数M':>8} {'像素数m':>8} {'A_time':>8} {'B_time':>8} {'C_time':>8} {'D_time':>8} {'总时间':>10}")
        print("-" * 80)
        
        for X in sorted(constraint_groups.keys()):
            # 根据FFT台阶效应，选择该约束下像素数最大的组合
            best_group = constraint_groups[X][0]  # 已按m降序排序
            
            M = best_group['M']
            m = best_group['m']
            
            # 计算ABCD各步骤时间
            A_time = self.predict_A_time(X)
            B_time = self.predict_B_time(m, M) * M  # B步骤需要处理M个块
            C_time = self.predict_C_time(m, M, X)
            
            if use_d_total:
                D_time = self.predict_D_total_time(m, M)
            else:
                D_single = self.predict_D_time_single(m, X)
                D_time = D_single * M
            
            # 计算总时间
            total_time = A_time + B_time + C_time + D_time
            
            result = {
                'X': X,
                'power': best_group['power'],
                'M': M,
                'm': m,
                'A_time': A_time,
                'B_time': B_time,
                'C_time': C_time,
                'D_time': D_time,
                'total_time': total_time,
                'constraint_groups_count': len(constraint_groups[X])
            }
            
            results.append(result)
            
            print(f"2^{result['power']:>2} {M:>8} {m:>8} {A_time:>8.1f} {B_time:>8.1f} {C_time:>8.1f} {D_time:>8.1f} {total_time:>10.1f}")
        
        return results
    
    def find_optimal_constraint(self, results):
        """找到最优约束"""
        if not results:
            return None
        
        # 按总时间排序
        results_sorted = sorted(results, key=lambda x: x['total_time'])
        optimal = results_sorted[0]
        
        print(f"\n=== 最优约束分析 ===")
        print(f"最优约束: 2^{optimal['power']} = {optimal['X']}")
        print(f"最优分块数M: {optimal['M']}")
        print(f"最优单块像素数m: {optimal['m']}")
        print(f"最短总时间: {optimal['total_time']:.2f} 秒")
        print()
        print(f"时间构成:")
        print(f"  A步骤: {optimal['A_time']:.2f} 秒 ({optimal['A_time']/optimal['total_time']*100:.1f}%)")
        print(f"  B步骤: {optimal['B_time']:.2f} 秒 ({optimal['B_time']/optimal['total_time']*100:.1f}%)")
        print(f"  C步骤: {optimal['C_time']:.2f} 秒 ({optimal['C_time']/optimal['total_time']*100:.1f}%)")
        print(f"  D步骤: {optimal['D_time']:.2f} 秒 ({optimal['D_time']/optimal['total_time']*100:.1f}%)")
        
        return optimal
    
    def print_detailed_analysis(self, total_pixels, constraint_groups):
        """打印详细的约束组合分析"""
        print(f"\n=== 详细约束组合分析 ===")
        
        for X in sorted(constraint_groups.keys()):
            power = int(math.log2(X))
            groups = constraint_groups[X]
            
            print(f"\n约束 2^{power} = {X}:")
            print(f"  共有 {len(groups)} 个(M,m)组合")
            print(f"  {'分块数M':>8} {'像素数m':>8} {'实际总像素':>10} {'约束数':>10}")
            
            # 显示前5个组合（像素数最大的）
            for i, group in enumerate(groups[:5]):
                print(f"  {group['M']:>8} {group['m']:>8} {group['actual_total_pixels']:>10} {group['constraints']:>10}")
            
            if len(groups) > 5:
                print(f"  ... 还有 {len(groups)-5} 个组合")
    
    def plot_analysis(self, results, total_pixels):
        """绘制分析图表"""
        if not results:
            return
        
        # 提取数据
        powers = [r['power'] for r in results]
        A_times = [r['A_time'] for r in results]
        B_times = [r['B_time'] for r in results]
        C_times = [r['C_time'] for r in results]
        D_times = [r['D_time'] for r in results]
        total_times = [r['total_time'] for r in results]
        
        plt.figure(figsize=(16, 12))
        
        # 总时间对比
        plt.subplot(2, 3, 1)
        plt.plot(powers, total_times, 'o-', linewidth=2, markersize=8)
        min_idx = np.argmin(total_times)
        plt.scatter([powers[min_idx]], [total_times[min_idx]], color='red', s=100, zorder=5)
        plt.xlabel('FFT约束幂次')
        plt.ylabel('总时间 (秒)')
        plt.title(f'总执行时间\n最优: 2^{powers[min_idx]}')
        plt.grid(True, alpha=0.3)
        
        # ABCD步骤时间分布
        plt.subplot(2, 3, 2)
        plt.plot(powers, A_times, 'o-', label='A步骤', linewidth=2, markersize=6)
        plt.plot(powers, B_times, 's-', label='B步骤', linewidth=2, markersize=6)
        plt.plot(powers, C_times, '^-', label='C步骤', linewidth=2, markersize=6)
        plt.plot(powers, D_times, 'd-', label='D步骤', linewidth=2, markersize=6)
        plt.xlabel('FFT约束幂次')
        plt.ylabel('时间 (秒)')
        plt.title('各步骤执行时间')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # 时间构成堆叠图
        plt.subplot(2, 3, 3)
        plt.bar(powers, A_times, label='A步骤', alpha=0.8)
        plt.bar(powers, B_times, bottom=A_times, label='B步骤', alpha=0.8)
        
        C_bottom = [a+b for a,b in zip(A_times, B_times)]
        plt.bar(powers, C_times, bottom=C_bottom, label='C步骤', alpha=0.8)
        
        D_bottom = [a+b+c for a,b,c in zip(A_times, B_times, C_times)]
        plt.bar(powers, D_times, bottom=D_bottom, label='D步骤', alpha=0.8)
        
        plt.xlabel('FFT约束幂次')
        plt.ylabel('时间 (秒)')
        plt.title('时间构成分析')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # 分块数和像素数变化
        M_values = [r['M'] for r in results]
        m_values = [r['m'] for r in results]
        
        plt.subplot(2, 3, 4)
        plt.semilogy(powers, M_values, 'o-', linewidth=2, markersize=8, color='blue')
        plt.xlabel('FFT约束幂次')
        plt.ylabel('分块数M (log scale)')
        plt.title('最优分块数变化')
        plt.grid(True, alpha=0.3)
        
        plt.subplot(2, 3, 5)
        plt.semilogy(powers, m_values, 's-', linewidth=2, markersize=8, color='green')
        plt.xlabel('FFT约束幂次')
        plt.ylabel('单块像素数m (log scale)')
        plt.title('最优单块像素数变化')
        plt.grid(True, alpha=0.3)
        
        # 效率分析
        plt.subplot(2, 3, 6)
        efficiency = [total_pixels / t for t in total_times]
        plt.plot(powers, efficiency, 'o-', linewidth=2, markersize=8, color='red')
        max_idx = np.argmax(efficiency)
        plt.scatter([powers[max_idx]], [efficiency[max_idx]], color='blue', s=100, zorder=5)
        plt.xlabel('FFT约束幂次')
        plt.ylabel('处理效率 (像素/秒)')
        plt.title(f'处理效率分析\n最高效率: 2^{powers[max_idx]}')
        plt.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('../figures/adaptive_block_analysis.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def save_results(self, total_pixels, results, constraint_groups, optimal):
        """保存分析结果"""
        # 保存性能评估结果
        results_df = pd.DataFrame(results)
        results_df.to_csv('../results/performance_evaluation.csv', index=False)
        
        # 保存约束组合详情
        constraint_details = []
        for X, groups in constraint_groups.items():
            power = int(math.log2(X))
            for group in groups:
                constraint_details.append({
                    'X': X,
                    'power': power,
                    'M': group['M'],
                    'm': group['m'],
                    'constraints': group['constraints'],
                    'actual_total_pixels': group['actual_total_pixels']
                })
        
        constraint_df = pd.DataFrame(constraint_details)
        constraint_df.to_csv('../results/constraint_combinations.csv', index=False)
        
        # 保存最优结果摘要
        summary = {
            'total_pixels': total_pixels,
            'optimal_X': optimal['X'],
            'optimal_power': optimal['power'],
            'optimal_M': optimal['M'],
            'optimal_m': optimal['m'],
            'optimal_total_time': optimal['total_time'],
            'A_time': optimal['A_time'],
            'B_time': optimal['B_time'],
            'C_time': optimal['C_time'],
            'D_time': optimal['D_time']
        }
        
        summary_df = pd.DataFrame([summary])
        summary_df.to_csv('../results/optimal_summary.csv', index=False)
        
        print(f"\n结果已保存到:")
        print(f"  - results/performance_evaluation.csv")
        print(f"  - results/constraint_combinations.csv")
        print(f"  - results/optimal_summary.csv")
        print(f"  - figures/adaptive_block_analysis.png")
    
    def run_analysis(self, total_pixels, use_d_total=True, save_results=True):
        """运行完整的自适应分块分析"""
        print("=" * 80)
        print("自适应分块算法 - 最优约束选择")
        print("=" * 80)
        
        # 1. 计算约束组合
        constraint_groups = self.calculate_constraint_groups(total_pixels)
        
        # 2. 打印详细分析
        self.print_detailed_analysis(total_pixels, constraint_groups)
        
        # 3. 性能评估
        results = self.evaluate_performance(total_pixels, constraint_groups, use_d_total)
        
        # 4. 找到最优约束
        optimal = self.find_optimal_constraint(results)
        
        # 5. 生成图表
        if results:
            self.plot_analysis(results, total_pixels)
        
        # 6. 保存结果
        if save_results and optimal:
            self.save_results(total_pixels, results, constraint_groups, optimal)
        
        return optimal, results, constraint_groups

def main():
    """主函数：测试不同分辨率的图像"""
    algorithm = AdaptiveBlockAlgorithm()
    
    # 测试案例
    test_cases = [
        {'name': 'image21420', 'pixels': 21420},
        {'name': 'image96480', 'pixels': 96480},
        {'name': 'image193000', 'pixels': 193000},
        {'name': '超大图像示例', 'pixels': 500000},
    ]
    
    for case in test_cases:
        print(f"\n{'='*100}")
        print(f"测试案例: {case['name']} ({case['pixels']} 像素)")
        print(f"{'='*100}")
        
        optimal, results, constraint_groups = algorithm.run_analysis(case['pixels'])
        
        print(f"\n{'='*60}")
        print(f"案例 {case['name']} 分析完成")
        print(f"{'='*60}")

if __name__ == '__main__':
    main() 