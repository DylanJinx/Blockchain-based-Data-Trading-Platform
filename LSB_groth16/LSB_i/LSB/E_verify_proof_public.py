import subprocess
import time
import json
from pathlib import Path

def run_snarkjs_verify(verification_key, public_file, proof_file):
    # 构建命令字符串
    command = f'snarkjs groth16 verify {verification_key} {public_file} {proof_file}'
    # 记录开始时间
    start_time = time.time()
    try:
        # 执行命令
        subprocess.run(command, check=True, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # 记录结束时间
        end_time = time.time()
        # 返回操作耗时
        return end_time - start_time, None
    except subprocess.CalledProcessError as e:
        # 返回错误信息和None表示操作失败
        return None, {'command': command, 'error': str(e)}

def main():
    verification_key = 'verification_key.json'
    public_folder = Path('public_json')
    proof_folder = Path('proof_json')
    times = []
    errors = []

    # 确保输出文件夹存在
    Path('time_json').mkdir(exist_ok=True)
    Path('error_json').mkdir(exist_ok=True)

    # 遍历proof_folder中所有的子文件夹
    proof_subfolders = [x for x in proof_folder.iterdir() if x.is_dir()]
    for proof_subfolder in proof_subfolders:
        i = proof_subfolder.name.split('_')[1]  # 图片编号
        proof_files = list(proof_subfolder.glob('proof_*.json'))

        for proof_file in proof_files:
            filename_parts = proof_file.stem.split('_')
            j = filename_parts[2]  # 块编号
            public_subfolder = public_folder / f'public_{i}'
            public_file = public_subfolder / f'public_{i}_{j}.json'

            # 确保对应的public文件存在
            if public_file.exists():
                # 执行snarkjs命令并记录时间
                time_taken, error = run_snarkjs_verify(verification_key, public_file, proof_file)
                if time_taken is not None:
                    times.append({'proof': f'proof_{i}_{j}.json', 'public': f'public_{i}_{j}.json', 'time': time_taken})
                else:
                    errors.append(error)

    # 计算总时间
    total_time = sum(time['time'] for time in times if time['time'] is not None)

    # 保存时间记录到文件
    with open('time_json/E_verify_proof_public_time.json', 'w', encoding='utf-8') as f:
        json.dump({
            'total_time': total_time,
            'individual_times': times
        }, f, indent=4)

    # 保存错误记录到文件
    if errors:
        with open('error_json/error_verify_proof.json', 'w', encoding='utf-8') as f:
            json.dump(errors, f, indent=4)

if __name__ == '__main__':
    main()
