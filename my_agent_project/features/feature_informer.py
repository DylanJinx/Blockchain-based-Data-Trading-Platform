import subprocess
import logging

def report_nft(token_id_a: int, token_id_b: int, jinx_address: str):
    """
    第七功能 - 完整举报&检测
    调用:
      python function_7_informer.py report <tokenIdA> <tokenIdB> <jinxAddr>
    """
    logging.info(f"[report_nft] tokenA={token_id_a}, tokenB={token_id_b}, jinx={jinx_address}")

    cmd = [
        "python",
        "../python_call_contract/function_7_informer.py",
        "report",
        str(token_id_a),
        str(token_id_b),
        jinx_address
    ]
    print(f"开始举报并检测: tokenA={token_id_a}, tokenB={token_id_b}, jinx={jinx_address}")
    try:
        subprocess.run(cmd, cwd="../python_call_contract", check=True)
        print("举报 + 转售检测流程执行完毕。")
    except subprocess.CalledProcessError as e:
        logging.error(f"report_nft 执行失败: {e}")
        print("流程出现异常，无法完成。")
