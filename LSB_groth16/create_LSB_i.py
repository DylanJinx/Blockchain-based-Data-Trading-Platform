import os
import shutil
from pathlib import Path

# 为a-10e4_3-10e4区间选择的分块大小
selected_chunk_pixels = [
    21420, 10710, 7140, 4284, 3570, 1948, 1785, 974, 932, 630, 
    476, 466, 315, 236, 233, 156, 117, 116, 94, 78, 67, 
    59, 58, 48, 39, 33, 30, 27, 25, 24, 22
]

# 定义基础目录
source_folder = "./LSB_i"  # LSB模板文件夹
destination_base = "./LSB_experiments"  # 实验输出的基本目录
input_json_base = "./input_json_files"  # 生成的JSON输入文件的基础目录
ptau_folder = ""  # PTAU文件目录

# 确保目标基础目录存在
if not os.path.exists(destination_base):
    os.makedirs(destination_base)

for chunk_size in selected_chunk_pixels:
    # 创建每个分块大小的实验目录
    destination_folder = os.path.join(destination_base, f"LSB_{chunk_size}")
    
    # 检查源模板文件夹是否存在
    if not os.path.exists(source_folder):
        print(f"源模板文件夹不存在: {source_folder}")
        continue
    
    # 创建目标目录并复制模板
    if not os.path.exists(destination_folder):
        os.makedirs(destination_folder)
        # 复制模板文件夹内容到目标目录
        for item in os.listdir(source_folder):
            s = os.path.join(source_folder, item)
            d = os.path.join(destination_folder, item)
            if os.path.isdir(s):
                shutil.copytree(s, d)
            else:
                shutil.copy2(s, d)
    
    # 确保LSB子目录存在
    lsb_dir = os.path.join(destination_folder, "LSB")
    if not os.path.exists(lsb_dir):
        os.makedirs(lsb_dir)
    
    # 确保ptau目录存在
    ptau_dir = os.path.join(lsb_dir, "ptau")
    if not os.path.exists(ptau_dir):
        os.makedirs(ptau_dir)
    
    # 复制对应的JSON输入文件
    input_source_folder = os.path.join(input_json_base, f"chunk_pixel_{chunk_size}")
    input_destination_folder = os.path.join(lsb_dir, f"input_json_chunk_pixel_{chunk_size}")
    
    if os.path.exists(input_source_folder):
        if os.path.exists(input_destination_folder):
            # 如果目标目录已存在，先删除它
            shutil.rmtree(input_destination_folder)
        shutil.copytree(input_source_folder, input_destination_folder)
    else:
        print(f"输入JSON文件夹不存在: {input_source_folder}")
    
    # 计算约束数量和确定ptau文件
    constraints = chunk_size * 1125 * 2
    power = 1
    while 2**power < constraints:
        power += 1
    
    ptau_file = f"pot{power}_final.ptau"
    ptau_source = os.path.join(ptau_folder, ptau_file)
    ptau_destination = os.path.join(ptau_dir, ptau_file)
    
    if os.path.exists(ptau_source):
        shutil.copy2(ptau_source, ptau_destination)
    else:
        print(f"PTAU文件不存在: {ptau_source}")
    
    # 修改B_witness.py文件
    b_witness_file = os.path.join(lsb_dir, "B_witness.py")
    if os.path.exists(b_witness_file):
        with open(b_witness_file, "r", encoding='utf-8') as file:
            content = file.read()
        # 将占位符替换为实际的分块大小
        content = content.replace("input_json_chunk_pixel_hownumberPixels", f"input_json_chunk_pixel_{chunk_size}")
        with open(b_witness_file, "w", encoding='utf-8') as file:
            file.write(content)
    else:
        print(f"B_witness.py文件不存在: {b_witness_file}")
    
    # 修改C_zkey_time.py文件
    c_zkey_file = os.path.join(lsb_dir, "C_zkey_time.py")
    if os.path.exists(c_zkey_file):
        with open(c_zkey_file, "r", encoding='utf-8') as file:
            content = file.read()
        content = content.replace("pothownumberptau_final.ptau", ptau_file)
        with open(c_zkey_file, "w", encoding='utf-8') as file:
            file.write(content)
    else:
        print(f"C_zkey_time.py文件不存在: {c_zkey_file}")
    
    # 修改LSB.circom文件
    lsb_circom_file = os.path.join(lsb_dir, "LSB.circom")
    if os.path.exists(lsb_circom_file):
        with open(lsb_circom_file, "r", encoding='utf-8') as file:
            content = file.read()
        content = content.replace("hownumberPixels", str(chunk_size))
        content = content.replace("numPixelscheng3", str(chunk_size * 3))
        with open(lsb_circom_file, "w", encoding='utf-8') as file:
            file.write(content)
    else:
        print(f"LSB.circom文件不存在: {lsb_circom_file}")

print("处理完成，已检查所有目录和文件。")