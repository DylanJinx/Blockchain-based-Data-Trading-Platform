from pathlib import Path
import os

def delete_corresponding_witness_files():
    proof_folder = Path('proof_json')
    witness_folder = Path('wtns')

    # 确保文件夹存在
    if not proof_folder.exists() or not witness_folder.exists():
        print("确保所有文件夹存在")
        return

    # 遍历proof_json文件夹中所有的.json文件
    for proof_file in proof_folder.glob('proof_*.json'):
        # 获取文件名，例如 'proof_87_40.json'
        proof_filename = proof_file.stem  # Removes the suffix and returns 'proof_87_40'
        # 提取编号 '87_40'
        index_part = proof_filename.split('_')[1:]  # Splits 'proof_87_40' into ['proof', '87', '40'] and gets ['87', '40']
        index_str = '_'.join(index_part)  # Joins ['87', '40'] into '87_40'
        # 构建对应的witness文件名和完整路径
        witness_filename = f'witness_{index_str}.wtns'
        witness_file_path = witness_folder / witness_filename
        # 检查对应的witness文件是否存在，若存在则删除
        if witness_file_path.exists():
            os.remove(witness_file_path)
            print(f"Deleted: {witness_file_path}")
        else:
            print(f"No corresponding witness file found for {proof_file}")

# 调用函数
delete_corresponding_witness_files()
