# my_agent_project/config.py

import os
import sys
import logging
import openai

# =============== 配置日志 ===============
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# =============== 读取环境变量 ===============
API_KEY = os.getenv("OPENAI_API_KEY")
if not API_KEY:
    logging.error("未检测到 OPENAI_API_KEY，请先在环境中设置该变量后再运行脚本。")
    sys.exit(1)

# 设置 OpenAI API Key
openai.api_key = API_KEY

# =============== 模型名称 ===============
MODEL_NAME = "gpt-4"

# =============== 其他全局常量 ===============
# 指向 XRID/ 文件夹下的结果 CSV
RESULT_CSV = "XRID/test_predictions_finetuned.csv"
