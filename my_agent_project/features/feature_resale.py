import os
import sys
import csv
import subprocess
from config import logging, RESULT_CSV

# 在环境变量中写入 export PYTORCH_ENABLE_MPS_FALLBACK=1
os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"

current_dir = os.path.dirname(os.path.abspath(__file__))  # 当前文件所在目录 (my_agent_project/features)
RESULT_CSV = os.path.join(current_dir, "..", "XRID", "test_predictions_finetuned.csv")

def run_xrid_commands(original_dataset, suspicious_dataset):
    """
    按顺序执行 XRID/XRID.py 的四个命令:
     - python XRID.py --transform_dir ./<original_dataset>
     - python XRID.py --original_dir ./<original_dataset>
     - python XRID.py --original_dir ./<original_dataset> --suspicion_dir ./<suspicious_dataset>
     - python XRID.py --predict_and_finetune
     
    其中:
      1) 我们将原本的 "XRID.py" 改为 "XRID/XRID.py"
      2) 通过 cwd="XRID" 在 XRID/ 文件夹内执行命令
         => 脚本内再去访问 "./imagenet-suspicion" 时才找得到
    """
    commands = [
        ["python", "XRID.py", "--transform_dir", f"./{original_dataset}"],
        ["python", "XRID.py", "--original_dir", f"./{original_dataset}"],
        ["python", "XRID.py", "--original_dir", f"./{original_dataset}", "--suspicion_dir", f"./{suspicious_dataset}"],
        ["python", "XRID.py", "--predict_and_finetune"]
    ]

    for cmd in commands:
        cmd_str = " ".join(cmd)
        logging.info(f"开始执行命令: {cmd_str}, cwd=XRID")
        try:
            # 在 XRID 文件夹内执行
            cwd_path = os.path.join("..", "my_agent_project", "XRID") 
            subprocess.run(cmd, check=True, cwd=cwd_path)
            logging.info(f"命令执行成功: {cmd_str}")
        except subprocess.CalledProcessError as e:
            logging.error(f"命令执行失败: {cmd_str}, 退出码: {e.returncode}")
            sys.exit(e.returncode)


def interpret_results(original_dataset, suspicious_dataset):
    """
    读取结果文件 (XRID/test_predictions_finetuned.csv) 并根据 Predicted_Label 的值进行解读:
     - 1 => 确实存在转售行为
     - 0 => 不存在转售行为
    """
    if not os.path.isfile(RESULT_CSV):
        logging.error(f"未找到结果文件: {RESULT_CSV}")
        print("分析结果文件缺失，无法判断是否存在转售行为。")
        return

    try:
        with open(RESULT_CSV, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            prediction_label = None
            for row in reader:
                if "Predicted_Label" in row:
                    prediction_label = row["Predicted_Label"].strip()
                    break  # 只取第一行

        if prediction_label is None:
            logging.error("CSV中没有找到 'Predicted_Label' 字段")
            print("CSV文件格式错误，未能确定结果。")
            return

        if prediction_label == "1":
            print(f"数据集 {original_dataset} 与 {suspicious_dataset} 确实存在转售行为。")
            return "1"
        elif prediction_label == "0":
            print(f"数据集 {original_dataset} 与 {suspicious_dataset} 不存在转售行为。")
            return "0"
        else:
            print("无法确认是否存在转售行为，检测结果非预期。")
            return None

    except Exception as e:
        logging.error(f"读取结果文件时发生错误: {e}")
        print("读取结果文件时发生错误。无法确认是否存在转售行为。")
