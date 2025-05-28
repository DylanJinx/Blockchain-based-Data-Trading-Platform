#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
update_LSB_input_json.py

将 ./input_json_files/ 里的 chunk_pixel_* 目录
批量同步到 ./LSB_experiments/LSB_<size>/LSB/input_json_chunk_pixel_<size> 。

• 若目标目录已存在，脚本会先安全删除再复制，确保完全一致。
• 仅处理实验目录名形如  LSB_<数字>  的文件夹；数字即 chunk_size。
• 运行环境：Python ≥3.8
"""
import os
import shutil
from pathlib import Path

# ----------- 可根据需要修改的路径 -----------------
EXPERIMENT_BASE = Path("./LSB_experiments")     # create_LSB_i.py 生成的实验根目录
INPUT_JSON_BASE = Path("./input_json_files")    # 你刚更新完的 JSON 根目录
# -------------------------------------------------

def main() -> None:
    if not EXPERIMENT_BASE.exists():
        raise FileNotFoundError(f"实验根目录不存在: {EXPERIMENT_BASE.resolve()}")
    if not INPUT_JSON_BASE.exists():
        raise FileNotFoundError(f"JSON 根目录不存在: {INPUT_JSON_BASE.resolve()}")

    experiments = [d for d in EXPERIMENT_BASE.iterdir() if d.is_dir() and d.name.startswith("LSB_")]
    if not experiments:
        print("未找到任何 LSB_<size> 实验目录，脚本结束。")
        return

    for exp_dir in experiments:
        try:
            chunk_size = int(exp_dir.name.split("_")[1])
        except (IndexError, ValueError):
            print(f"忽略无法解析尺寸的目录: {exp_dir.name}")
            continue

        src_json_dir = INPUT_JSON_BASE / f"chunk_pixel_{chunk_size}"
        dst_json_dir = exp_dir / "LSB" / f"input_json_chunk_pixel_{chunk_size}"

        if not src_json_dir.exists():
            print(f"[跳过] 源目录缺失: {src_json_dir}")
            continue

        # 确保目标父目录存在
        dst_json_dir.parent.mkdir(parents=True, exist_ok=True)

        # 若目标目录已存在则删除（安全覆盖）
        if dst_json_dir.exists():
            shutil.rmtree(dst_json_dir)

        shutil.copytree(src_json_dir, dst_json_dir)
        print(f"[已同步] {src_json_dir}  ->  {dst_json_dir}")

    print("\n全部处理完毕！")

if __name__ == "__main__":
    main()
