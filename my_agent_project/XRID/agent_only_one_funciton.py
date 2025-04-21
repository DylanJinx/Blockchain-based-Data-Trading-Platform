import os
import openai
import subprocess
import logging
import csv
import json
import sys

# 配置带时间戳的日志
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def parse_datasets_from_input(user_query: str) -> tuple:
    """使用GPT-4解析用户输入，返回数据集名称元组"""
    system_message = {
        "role": "system",
        "content": (
            "你是一个智能助手，负责从用户的请求中提取两个数据集名称。"
            "请只输出一个 JSON 对象，不要使用任何三反引号或 Markdown 代码块。"
            "输出格式形如："
            "{\"original_dataset\": \"xxx\", \"suspicious_dataset\": \"yyy\"}"
            "不要输出任何其他文本。"
        )
    }
    user_message = {"role": "user", "content": user_query}

    try:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logging.error("未设置OpenAI API密钥")
            sys.exit(1)
        openai.api_key = api_key

        logging.info("正在调用GPT-4解析数据集名称...")
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[system_message, user_message]
        )
        reply_content = response['choices'][0]['message']['content']
        logging.info(f"GPT-4返回内容: {reply_content}")

        datasets = json.loads(reply_content.strip())
        datasetA = datasets.get("original_dataset") or datasets.get("dataset1") or datasets.get("A")
        datasetB = datasets.get("suspicious_dataset") or datasets.get("dataset2") or datasets.get("B")
        if not datasetA or not datasetB:
            logging.error("解析数据集名称失败")
            sys.exit(1)
        logging.info(f"解析结果 -> A: {datasetA}, B: {datasetB}")
        return datasetA, datasetB

    except Exception as e:
        logging.error(f"GPT-4 API调用或解析失败: {e}")
        sys.exit(1)

def run_command(cmd_args: list):
    """执行子进程命令"""
    cmd_str = " ".join(cmd_args)
    logging.info(f"正在执行命令: {cmd_str}")
    try:
        subprocess.run(cmd_args, check=True)
        logging.info(f"命令执行成功: {cmd_str}")
    except subprocess.CalledProcessError as e:
        logging.error(f"命令执行失败（错误码{e.returncode}）: {cmd_str}")
        sys.exit(e.returncode)

def main():
    # 获取用户输入
    if len(sys.argv) > 1:
        user_query = " ".join(sys.argv[1:])
    else:
        user_query = input("请输入查询语句: ").strip()
    if not user_query:
        logging.error("未提供输入")
        sys.exit(1)

    # 解析数据集名称
    datasetA, datasetB = parse_datasets_from_input(user_query)

    # 执行XRID命令序列
    run_command(["python", "XRID.py", "--transform_dir", f"./{datasetA}"])
    run_command(["python", "XRID.py", "--original_dir", f"./{datasetA}"])
    run_command(["python", "XRID.py", "--original_dir", f"./{datasetA}", "--suspicion_dir", f"./{datasetB}"])
    run_command(["python", "XRID.py", "--predict_and_finetune"])

    # 读取预测结果
    result_file = "test_predictions_finetuned.csv"
    logging.info(f"正在读取结果文件{result_file}...")
    try:
        with open(result_file, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            prediction_label = None
            for row in reader:
                if "Predicted_Label" in row:
                    prediction_label = row["Predicted_Label"].strip()
                    break
        if prediction_label is None:
            logging.error(f"未找到Predicted_Label列")
            sys.exit(1)
    except FileNotFoundError:
        logging.error(f"结果文件{result_file}不存在")
        sys.exit(1)
    except Exception as e:
        logging.error(f"读取文件错误: {e}")
        sys.exit(1)

    # 输出结论
    logging.info(f"预测标签值: {prediction_label}")
    if prediction_label == "1":
        print(f"数据集 {datasetA} 和数据集 {datasetB} 确实存在转售行为")
    elif prediction_label == "0":
        print(f"数据集 {datasetA} 和数据集 {datasetB} 不存在转售行为")
    else:
        print("无法确定转售行为（结果异常）")
        logging.warning(f"异常标签值: {prediction_label}")

if __name__ == "__main__":
    main()