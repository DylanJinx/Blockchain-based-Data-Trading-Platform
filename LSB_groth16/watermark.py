#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import glob
from PIL import Image

# 你的秘密信息（可以自行修改或保持不变）
mySecret = "832384048dc3c8e95128d4659dbc86bab5701203deff1d150a98c76548c3aa3e"
# 转为二进制字符串（'0'/'1'）
mySecretBinary = ''.join([bin(ord(c))[2:].rjust(8, '0') for c in mySecret])

# 原图、目标文件夹
root_ori_folder = './ori_pic'
root_wm_folder  = './watermark_pic'

def convert_jpeg_to_png(ori_folder):
    """
    将 ori_folder 下所有 .jpg/.jpeg 文件转换为 .png (RGB)格式，
    转换后会在同一目录生成同名 .png 文件，并删除原始的 .jpeg/.jpg 文件。
    """
    for file in os.listdir(ori_folder):
        f_lower = file.lower()
        if f_lower.endswith('.jpg') or f_lower.endswith('.jpeg'):
            old_path = os.path.join(ori_folder, file)
            # 读取并转成RGB
            img = Image.open(old_path).convert('RGB')
            new_name = os.path.splitext(file)[0] + '.png'
            new_path = os.path.join(ori_folder, new_name)
            img.save(new_path, format='PNG')
            print(f"[转换] {file} --> {new_name}")
            
            # 删除原始 .jpg 或 .jpeg 文件
            os.remove(old_path)
            print(f"[删除] 删除原始文件: {file}")

def embed_watermark(source_path, target_path, secret_binary):
    """
    对 source_path 指定的 PNG 图像在 RGB 三个通道的 LSB 位嵌入 secret_binary。
    保存结果到 target_path (PNG)。
    这里的遍历顺序是 for x in range(width): for y in range(height):
    这与 generate_input.py 中使用 reshape(-1, 3, order='F') 的方式相吻合。
    """
    # 加载 PNG 图片
    image = Image.open(source_path).convert('RGB')
    pixel = image.load()
    width, height = image.size

    # 计算容量
    total_capacity = width * height * 3  # 每个像素3个通道
    # 如果 secret_binary 不够，可以在后面填0
    if len(secret_binary) < total_capacity:
        padded_secret = secret_binary + '0' * (total_capacity - len(secret_binary))
    else:
        # 如果水印比容量大，则截断（或可自行选择其他策略）
        padded_secret = secret_binary[:total_capacity]

    index = 0
    # 注意：按照 x -> y 的嵌入顺序，正好对应 np.reshape(-1,3,order='F')
    for x in range(width):
        for y in range(height):
            r, g, b = pixel[x, y]
            # 嵌入到 r 通道LSB
            r = (r & 0xFE) | int(padded_secret[index])
            index += 1
            # 嵌入到 g 通道LSB
            g = (g & 0xFE) | int(padded_secret[index])
            index += 1
            # 嵌入到 b 通道LSB
            b = (b & 0xFE) | int(padded_secret[index])
            index += 1

            pixel[x, y] = (r, g, b)

    # 保存
    image.save(target_path, format='PNG')
    print(f"[水印嵌入] {source_path} --> {target_path}")

def main():
    # 第一步：先转换 ori_pic/ 中的所有 .jpg/.jpeg 至 .png，并删除原始 .jpeg 文件
    convert_jpeg_to_png(root_ori_folder)

    # 第二步：再对 ori_pic/ 中现有的 .png 文件依次嵌入水印
    # 并输出到 watermark_pic/ 中
    if not os.path.exists(root_wm_folder):
        os.makedirs(root_wm_folder)

    png_files = glob.glob(os.path.join(root_ori_folder, '*.png'))
    print(f"\n[信息] 在 {root_ori_folder} 中找到 {len(png_files)} 个 PNG 文件，开始水印嵌入...\n")

    for png_path in png_files:
        filename = os.path.basename(png_path)           # xxx.png
        target_path = os.path.join(root_wm_folder, filename)
        embed_watermark(png_path, target_path, mySecretBinary)

    print("\n[完成] 所有 PNG 图像均已嵌入水印并输出到 watermark_pic/。")

if __name__ == '__main__':
    main()
