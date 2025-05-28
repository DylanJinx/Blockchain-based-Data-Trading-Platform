import json
import time
from pathlib import Path
import subprocess

def generate_wtns(input_json, output_wtns, wasm_file):
    # 构建命令字符串，注意Windows中路径的格式
    command = f'node LSB_js/generate_witness.js {wasm_file} {input_json} {output_wtns}'
    # 执行命令
    subprocess.run(command, check=True, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def main():
    input_dir = Path('input_json_chunk_pixel_29')  # 使用了具体的像素分块设置
    output_dir = Path('wtns')
    wasm_file = 'LSB_js/LSB.wasm'
    times = []
    errors = []

    output_dir.mkdir(exist_ok=True)  # 如果wtns文件夹不存在，则创建

    start_time = time.time()

    image_folders = [x for x in input_dir.iterdir() if x.is_dir()]  # 遍历所有图片的文件夹
    
    for image_folder in image_folders:
        image_id = image_folder.name.split('_')[1]  # 解析图片编号
        image_output_dir = output_dir / f'wtns_{image_id}'
        image_output_dir.mkdir(exist_ok=True)  # 为每个图片创建wtns文件夹
        
        input_files = list(image_folder.glob('input_*.json'))
        for input_file in input_files:
            parts = input_file.stem.split('_')
            i = parts[1]  # 图片编号
            j = parts[2]  # 块编号
            output_file = image_output_dir / f'witness_{i}_{j}.wtns'
            
            try:
                generate_start = time.time()
                generate_wtns(input_file, output_file, wasm_file)
                generate_end = time.time()
                times.append({'file': f'witness_{i}_{j}.wtns', 'time': generate_end - generate_start})
            except subprocess.CalledProcessError as e:
                errors.append({'file': str(input_file), 'error': str(e)})

    end_time = time.time()

    # 记录并保存整个过程的时间
    with open('time_json/B_witness_time.json', 'w', encoding='utf-8') as f:
        json.dump({
            'total_time': end_time - start_time,
            'individual_times': times
        }, f, indent=4)

    # 如果存在错误，则保存到error.json文件中
    if errors:
        with open('error.json', 'w', encoding='utf-8') as f:
            json.dump(errors, f, indent=4)

if __name__ == '__main__':
    main()
