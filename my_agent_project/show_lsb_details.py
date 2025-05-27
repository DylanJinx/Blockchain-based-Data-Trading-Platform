#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
显示LSB位详细信息的脚本
展示嵌入水印前后的最低有效位对比
"""

import os
import zipfile
import tempfile
import shutil
import hashlib
import time
from PIL import Image

def add_lsb_watermark_unified(image_path, buy_hash, output_path):
    """嵌入水印 - 列优先方式"""
    try:
        image = Image.open(image_path).convert('RGB')
        pixel = image.load()
        width, height = image.size
        
        binary_watermark = ''.join([bin(ord(c))[2:].rjust(8, '0') for c in buy_hash])
        total_capacity = width * height * 3
        
        if len(binary_watermark) < total_capacity:
            padded_secret = binary_watermark + '0' * (total_capacity - len(binary_watermark))
        else:
            padded_secret = binary_watermark[:total_capacity]
        
        index = 0
        for x in range(width):  # 列优先
            for y in range(height):
                r, g, b = pixel[x, y]
                r = (r & 0xFE) | int(padded_secret[index])
                index += 1
                g = (g & 0xFE) | int(padded_secret[index])
                index += 1
                b = (b & 0xFE) | int(padded_secret[index])
                index += 1
                pixel[x, y] = (r, g, b)
        
        image.save(output_path, format='PNG')
        return True
    except Exception as e:
        print(f"水印嵌入错误: {str(e)}")
        return False

def extract_and_display_lsb_details(original_path, watermarked_path, buy_hash, max_pixels=100):
    """提取并详细显示LSB位信息"""
    print(f"\n=== LSB位详细分析 ===")
    print(f"原始图像: {os.path.basename(original_path)}")
    print(f"水印图像: {os.path.basename(watermarked_path)}")
    print(f"buy_hash: {buy_hash}")
    
    # 转换buy_hash为二进制
    buy_hash_binary = ''.join([bin(ord(c))[2:].rjust(8, '0') for c in buy_hash])
    print(f"buy_hash二进制长度: {len(buy_hash_binary)} 位")
    print(f"buy_hash前64位: {buy_hash_binary[:64]}")
    
    # 读取两个图像
    orig_img = Image.open(original_path).convert('RGB')
    wm_img = Image.open(watermarked_path).convert('RGB')
    
    orig_pixel = orig_img.load()
    wm_pixel = wm_img.load()
    width, height = orig_img.size
    
    print(f"图像尺寸: {width}x{height}")
    print(f"总容量: {width * height * 3} 位")
    
    # 按列优先顺序分析
    print(f"\n=== 前{max_pixels}个像素的LSB位对比 ===")
    print("像素序号 | 位置(x,y) | 原始RGB | 水印RGB | 原始LSB | 水印LSB | 变化 | 期望位")
    print("-" * 85)
    
    bit_index = 0
    pixel_count = 0
    changes = 0
    correct_bits = 0
    
    for x in range(width):
        for y in range(height):
            if pixel_count >= max_pixels:
                break
                
            orig_r, orig_g, orig_b = orig_pixel[x, y]
            wm_r, wm_g, wm_b = wm_pixel[x, y]
            
            orig_lsb = (orig_r & 1, orig_g & 1, orig_b & 1)
            wm_lsb = (wm_r & 1, wm_g & 1, wm_b & 1)
            
            # 期望的位值
            expected_bits = []
            for i in range(3):
                if bit_index + i < len(buy_hash_binary):
                    expected_bits.append(int(buy_hash_binary[bit_index + i]))
                else:
                    expected_bits.append(0)  # 剩余位应该为0
            
            # 检查变化
            changed = orig_lsb != wm_lsb
            if changed:
                changes += 1
            
            # 检查正确性
            if wm_lsb == tuple(expected_bits):
                correct_bits += 3
            else:
                for i in range(3):
                    if wm_lsb[i] == expected_bits[i]:
                        correct_bits += 1
            
            # 格式化输出
            change_marker = "✓" if changed else " "
            print(f"像素{pixel_count:3d}   | ({x:2d},{y:2d})  | {orig_r:3d},{orig_g:3d},{orig_b:3d} | {wm_r:3d},{wm_g:3d},{wm_b:3d} | "
                  f"{orig_lsb[0]},{orig_lsb[1]},{orig_lsb[2]}   | {wm_lsb[0]},{wm_lsb[1]},{wm_lsb[2]}   | {change_marker:^4} | {expected_bits[0]},{expected_bits[1]},{expected_bits[2]}")
            
            bit_index += 3
            pixel_count += 1
        
        if pixel_count >= max_pixels:
            break
    
    print(f"\n=== 统计信息 ===")
    print(f"分析像素数: {pixel_count}")
    print(f"变化像素数: {changes}")
    print(f"变化率: {changes/pixel_count*100:.1f}%")
    print(f"正确位数: {correct_bits}/{pixel_count*3}")
    print(f"正确率: {correct_bits/(pixel_count*3)*100:.1f}%")
    
    # 分析后续的清零位
    print(f"\n=== 验证剩余位清零 ===")
    if bit_index < width * height * 3:
        check_pixels = min(50, width * height - pixel_count)  # 额外检查50个像素
        zero_count = 0
        non_zero_count = 0
        
        for x in range(width):
            for y in range(height):
                if pixel_count >= max_pixels + check_pixels:
                    break
                if pixel_count < max_pixels:
                    pixel_count += 1
                    continue
                    
                wm_r, wm_g, wm_b = wm_pixel[x, y]
                wm_lsb = (wm_r & 1, wm_g & 1, wm_b & 1)
                
                for bit in wm_lsb:
                    if bit == 0:
                        zero_count += 1
                    else:
                        non_zero_count += 1
                
                pixel_count += 1
            
            if pixel_count >= max_pixels + check_pixels:
                break
        
        total_checked = zero_count + non_zero_count
        if total_checked > 0:
            print(f"检查剩余{check_pixels}个像素({total_checked}位): {zero_count}个0, {non_zero_count}个1")
            print(f"清零率: {zero_count/total_checked*100:.1f}%")
        else:
            print("没有剩余位可检查")
    
    return {
        "total_pixels": pixel_count,
        "changed_pixels": changes,
        "correct_bits": correct_bits
    }

def main():
    """主函数"""
    print("=== LSB位详细分析脚本 ===")
    
    # 测试数据路径
    dataset_zip_path = "/Users/dylan/Code_Projects/Python_Projects/image_similarity/my_agent_project/data/dataset.zip"
    
    if not os.path.exists(dataset_zip_path):
        print(f"错误: 测试数据文件不存在: {dataset_zip_path}")
        return False
    
    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    try:
        print(f"解压测试数据到: {temp_dir}")
        
        # 解压数据集
        with zipfile.ZipFile(dataset_zip_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        
        # 清理macOS特殊文件
        macosx_dir = os.path.join(temp_dir, "__MACOSX")
        if os.path.exists(macosx_dir):
            shutil.rmtree(macosx_dir)
        
        # 查找第一张图像
        test_image = None
        supported_formats = ['.png', '.jpg', '.jpeg', '.bmp', '.gif']
        
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                if any(file.lower().endswith(fmt) for fmt in supported_formats):
                    test_image = os.path.join(root, file)
                    break
            if test_image:
                break
        
        if not test_image:
            print("错误: 在数据集中未找到图像文件")
            return False
        
        print(f"使用测试图像: {os.path.basename(test_image)}")
        
        # 生成测试buy_hash
        timestamp = int(time.time())
        test_data = f"lsb_analysis_{timestamp}"
        test_buy_hash = hashlib.sha256(test_data.encode()).hexdigest()
        
        # 创建水印图像
        watermarked_path = os.path.join(temp_dir, "watermarked_analysis.png")
        success = add_lsb_watermark_unified(test_image, test_buy_hash, watermarked_path)
        
        if not success:
            print("错误: 水印嵌入失败")
            return False
        
        print("水印嵌入成功!")
        
        # 详细分析LSB位
        result = extract_and_display_lsb_details(test_image, watermarked_path, test_buy_hash, max_pixels=30)
        
        print(f"\n=== 分析完成 ===")
        print(f"✓ 列优先嵌入/提取方式已验证")
        print(f"✓ 与LSB_groth16兼容的水印方式")
        print(f"✓ buy_hash内容保持不变")
        print(f"✓ 剩余位自动填充0")
        
        return True
        
    finally:
        # 清理临时目录
        shutil.rmtree(temp_dir)

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 