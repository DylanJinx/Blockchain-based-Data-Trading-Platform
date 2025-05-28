import subprocess
import time
import json
import os

# 确保目标文件夹存在
zkey_folder = 'zkey'
time_json_folder = 'time_json'
os.makedirs(zkey_folder, exist_ok=True)
os.makedirs(time_json_folder, exist_ok=True)  # 确保存放时间记录的文件夹存在

# 时间记录字典
time_records = {}

# 1. 生成没有贡献的key
start_time = time.time()
subprocess.run("snarkjs groth16 setup LSB.r1cs ptau/pothownumberptau_final.ptau zkey/LSB_000.zkey", shell=True)
time_records['setup_time'] = time.time() - start_time

# 2. 参与二阶段仪式
start_time = time.time()
input_value = "south_china_normal_university"
contribute_command = f"echo {input_value} | snarkjs zkey contribute zkey/LSB_000.zkey zkey/LSB_001.zkey --name=\"First Contributor Name\" -v"
subprocess.run(contribute_command, shell=True)
time_records['contribute_time'] = time.time() - start_time

# 3. 验证
start_time = time.time()
subprocess.run("snarkjs zkey verify LSB.r1cs ptau/pothownumberptau_final.ptau zkey/LSB_001.zkey", shell=True)
time_records['verify_time'] = time.time() - start_time

# 4. 引入随机beacon值
start_time = time.time()
subprocess.run("snarkjs zkey beacon zkey/LSB_001.zkey zkey/LSB_final.zkey 1cbf6603d6ff9ba4e1d15d0fd83be3a80bca470b6a43a7f9055204e860298f99 10 -n=\"Final Beacon phase2\"", shell=True)
time_records['beacon_time'] = time.time() - start_time

# 5. 验证最终的zkey
start_time = time.time()
subprocess.run("snarkjs zkey verify LSB.r1cs ptau/pothownumberptau_final.ptau zkey/LSB_final.zkey", shell=True)
time_records['final_verify_time'] = time.time() - start_time

# 导出验证键
start_time = time.time()
subprocess.run("snarkjs zkey export verificationkey zkey/LSB_final.zkey verification_key.json", shell=True)
time_records['export_verification_key_time'] = time.time() - start_time

# 保存时间记录到JSON文件
json_path = os.path.join(time_json_folder, "C_zkey_time.json")
with open(json_path, 'w') as json_file:
    json.dump(time_records, json_file, indent=4)

print("All tasks completed and time records are saved in zkey_time.json.")
