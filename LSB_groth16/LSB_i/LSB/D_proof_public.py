import subprocess
import time
import json
from pathlib import Path

def log_error(message):
    """将错误消息写入日志文件"""
    with open('error_log.txt', 'a', encoding='utf-8') as f:
        f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")

def run_snarkjs_prove(zkey_file, witness_file, proof_file, public_file):
    command = f'snarkjs groth16 prove {zkey_file} {witness_file} {proof_file} {public_file}'
    start_time = time.time()
    try:
        result = subprocess.run(command, check=True, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # print(f"Command Output: {result.stdout.decode()}")  # 打印标准输出内容，用于调试
    except subprocess.CalledProcessError as e:
        error_message = f"Error executing command: {command}\nError Message: {e.stderr.decode()}"
        print(error_message)  # 打印错误信息
        log_error(error_message)  # 写入日志文件
        return None
    end_time = time.time()
    return end_time - start_time

def main():
    zkey_file = 'zkey/LSB_final.zkey'
    witness_folder = Path('wtns')
    proof_folder = Path('proof_json')
    public_folder = Path('public_json')
    times = []
    total_time = 0

    for witness_subfolder in witness_folder.glob('wtns_*'):
        i = witness_subfolder.name.split('_')[1]  # 解析图片编号

        image_proof_folder = proof_folder / f'proof_{i}'
        image_proof_folder.mkdir(parents=True, exist_ok=True)  # 创建proof文件夹

        image_public_folder = public_folder / f'public_{i}'
        image_public_folder.mkdir(parents=True, exist_ok=True)  # 创建public文件夹

        witness_files = list(witness_subfolder.glob('witness_*.wtns'))
        for witness_file in witness_files:
            filename_parts = witness_file.stem.split('_')
            j = filename_parts[2]

            proof_file = image_proof_folder / f'proof_{i}_{j}.json'
            public_file = image_public_folder / f'public_{i}_{j}.json'

            time_taken = run_snarkjs_prove(zkey_file, witness_file, proof_file, public_file)
            if time_taken is not None:
                times.append({'witness': f'witness_{i}_{j}.wtns', 'time': time_taken})
                total_time += time_taken

    results = {
        'total_time': total_time,
        'individual_times': times
    }

    with open('time_json/D_proof&public_time.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=4)

if __name__ == '__main__':
    main()
