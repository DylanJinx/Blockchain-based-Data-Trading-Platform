import subprocess
import os

# 文件夹编号列表
# 已经跑完的分块 = [22, 24, 25, 27, 30, 33, 39, 48, 58, 59, 67, 78, 94, 116, 117, 156, 233, 236, 315, 466, 476, 630, 932, 974]
folder_numbers = [1785, 1948, 3570, 4284, 7140, 10710]
# 文件名列表
file_names = ['B_witness.py', 'C_zkey_time.py', 'D_proof_public.py']
# file_names = ['B_witness.py', 'C_zkey_time.py', 'D_proof_public.py', 'E_verify_proof_public.py']

for number in folder_numbers:
    # 设置每个文件夹的基础路径
    base_path = f"LSB_{number}/LSB"
    os.chdir(base_path)  # 更改当前工作目录到相应的文件夹
    success = True
    
    try:
        # 在对应的文件夹环境下运行 circom 命令
        subprocess.run(['circom', 'LSB.circom', '--r1cs', '--wasm', '--sym'], check=True)
        print(f"circom 命令在 {base_path} 中成功执行")
    except subprocess.CalledProcessError as e:
        print(f"circom 命令在 {base_path} 中执行失败，错误信息：{e}")
        success = False
    
    if success:  # 仅在 circom 命令成功后继续
        for file_name in file_names:
            path = file_name
            try:
                # 运行Python脚本
                subprocess.run(['python', path], check=True)
                print(f"已成功运行：{os.path.join(base_path, file_name)}")
            except subprocess.CalledProcessError as e:
                print(f"运行失败：{os.path.join(base_path, file_name)}，错误信息：{e}")
                success = False
                break  # 如果一个文件运行失败，跳出内层循环
        if not success:
            print(f"由于在文件夹LSB_{number}中发生错误，跳过此文件夹的剩余文件。")
    
    os.chdir('../../')  # 恢复到原始目录，为下一次迭代做准备