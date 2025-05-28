#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
自动化零知识证明生成脚本

功能：
1. 自动检测买家哈希文件夹（如 a158e72bdc06739d/）
2. 依次执行 circom 编译 → B → C → D → E 步骤
3. 记录执行时间和结果
4. 支持指定特定买家哈希或自动检测
"""

import subprocess
import os
import time
import sys
import argparse
from pathlib import Path

def run_command(command, cwd=None, timeout=3600):
    """
    执行命令并返回结果
    
    Args:
        command: 命令列表
        cwd: 工作目录
        timeout: 超时时间（秒）
    
    Returns:
        (success, duration, output, error)
    """
    start_time = time.time()
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True,
            timeout=timeout
        )
        duration = time.time() - start_time
        return True, duration, result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        duration = time.time() - start_time
        return False, duration, e.stdout, e.stderr
    except subprocess.TimeoutExpired as e:
        duration = time.time() - start_time
        return False, duration, "", f"命令超时（{timeout}秒）"

def find_buyer_hash_directories():
    """
    查找所有买家哈希目录（16个字符的十六进制）
    
    Returns:
        买家哈希目录列表
    """
    current_dir = Path(".")
    buyer_dirs = []
    
    for item in current_dir.iterdir():
        if item.is_dir() and len(item.name) == 16:
            # 检查是否为十六进制字符串
            try:
                int(item.name, 16)
                buyer_dirs.append(item.name)
            except ValueError:
                continue
    
    return sorted(buyer_dirs)

def run_proof_generation(buyer_hash, include_verify=True):
    """
    为指定买家哈希运行完整的零知识证明生成流程
    
    Args:
        buyer_hash: 买家哈希（16个字符）
        include_verify: 是否包含验证步骤
    
    Returns:
        执行结果字典
    """
    print(f"\n{'='*60}")
    print(f"开始为买家哈希 {buyer_hash} 生成零知识证明")
    print(f"{'='*60}")
    
    # 检查目录是否存在
    buyer_dir = Path(buyer_hash)
    lsb_dir = buyer_dir / "LSB"
    
    if not buyer_dir.exists():
        return {
            "buyer_hash": buyer_hash,
            "success": False,
            "error": f"买家目录不存在: {buyer_hash}",
            "steps": {}
        }
    
    if not lsb_dir.exists():
        return {
            "buyer_hash": buyer_hash,
            "success": False,
            "error": f"LSB目录不存在: {lsb_dir}",
            "steps": {}
        }
    
    # 执行步骤
    steps = [
        ("A_circom_compile", ["circom", "LSB.circom", "--r1cs", "--wasm", "--sym"], 300),
        ("B_witness", ["python", "B_witness.py"], 1800),
        ("C_zkey", ["python", "C_zkey_time.py"], 3600),
        ("D_proof", ["python", "D_proof_public.py"], 3600),
    ]
    
    if include_verify:
        steps.append(("E_verify", ["python", "E_verify_proof_public.py"], 1800))
    
    results = {
        "buyer_hash": buyer_hash,
        "success": True,
        "total_time": 0,
        "steps": {},
        "error": None
    }
    
    overall_start = time.time()
    
    for step_name, command, timeout in steps:
        print(f"\n🔄 执行步骤: {step_name}")
        print(f"   命令: {' '.join(command)}")
        print(f"   目录: {lsb_dir}")
        
        success, duration, stdout, stderr = run_command(
            command, 
            cwd=str(lsb_dir), 
            timeout=timeout
        )
        
        results["steps"][step_name] = {
            "success": success,
            "duration": duration,
            "command": ' '.join(command),
            "stdout": stdout[:500] + "..." if len(stdout) > 500 else stdout,
            "stderr": stderr[:500] + "..." if len(stderr) > 500 else stderr
        }
        
        if success:
            print(f"   ✅ 成功，耗时: {duration:.2f}秒")
        else:
            print(f"   ❌ 失败，耗时: {duration:.2f}秒")
            print(f"   错误: {stderr[:200]}...")
            results["success"] = False
            results["error"] = f"步骤 {step_name} 失败: {stderr[:200]}"
            break
    
    results["total_time"] = time.time() - overall_start
    
    if results["success"]:
        print(f"\n🎉 买家哈希 {buyer_hash} 的零知识证明生成成功！")
        print(f"⏱️  总耗时: {results['total_time']:.2f}秒")
        
        # 统计生成的文件
        proof_dir = lsb_dir / "proof_json"
        public_dir = lsb_dir / "public_json"
        
        proof_count = 0
        public_count = 0
        
        if proof_dir.exists():
            proof_count = len(list(proof_dir.rglob("*.json")))
        
        if public_dir.exists():
            public_count = len(list(public_dir.rglob("*.json")))
        
        print(f"📁 生成文件统计:")
        print(f"   - 证明文件: {proof_count} 个")
        print(f"   - 公开输入文件: {public_count} 个")
        
    else:
        print(f"\n❌ 买家哈希 {buyer_hash} 的零知识证明生成失败")
        print(f"🔍 错误信息: {results['error']}")
    
    return results

def main():
    parser = argparse.ArgumentParser(description="自动化零知识证明生成")
    parser.add_argument(
        "--buyer-hash", 
        type=str, 
        help="指定买家哈希（16个字符）"
    )
    parser.add_argument(
        "--no-verify", 
        action="store_true", 
        help="跳过验证步骤（只执行BCD）"
    )
    parser.add_argument(
        "--list", 
        action="store_true", 
        help="列出所有可用的买家哈希目录"
    )
    
    args = parser.parse_args()
    
    print("🚀 自动化零知识证明生成工具")
    print(f"📍 工作目录: {os.getcwd()}")
    
    # 如果只是列出目录
    if args.list:
        buyer_dirs = find_buyer_hash_directories()
        if buyer_dirs:
            print(f"\n📋 找到 {len(buyer_dirs)} 个买家哈希目录:")
            for buyer_hash in buyer_dirs:
                print(f"   - {buyer_hash}")
        else:
            print("\n📋 没有找到买家哈希目录")
        return
    
    # 确定要处理的买家哈希
    if args.buyer_hash:
        if len(args.buyer_hash) != 16:
            print(f"❌ 买家哈希必须是16个字符，当前: {len(args.buyer_hash)}")
            return
        buyer_hashes = [args.buyer_hash]
    else:
        # 自动检测
        buyer_hashes = find_buyer_hash_directories()
        if not buyer_hashes:
            print("❌ 没有找到买家哈希目录，请确保目录存在")
            print("💡 使用 --list 查看可用目录，或使用 --buyer-hash 指定")
            return
        
        print(f"\n📋 自动检测到 {len(buyer_hashes)} 个买家哈希目录:")
        for bh in buyer_hashes:
            print(f"   - {bh}")
        
        if len(buyer_hashes) > 1:
            response = input(f"\n❓ 是否处理所有 {len(buyer_hashes)} 个目录？(y/N): ").strip().lower()
            if response != 'y':
                print("🔄 已取消执行")
                return
    
    # 执行零知识证明生成
    include_verify = not args.no_verify
    all_results = []
    
    for buyer_hash in buyer_hashes:
        result = run_proof_generation(buyer_hash, include_verify)
        all_results.append(result)
        
        # 如果有多个目录，询问是否继续
        if len(buyer_hashes) > 1 and buyer_hash != buyer_hashes[-1]:
            if not result["success"]:
                response = input(f"\n❓ 买家哈希 {buyer_hash} 失败，是否继续下一个？(y/N): ").strip().lower()
                if response != 'y':
                    break
    
    # 总结报告
    print(f"\n{'='*60}")
    print("📊 执行总结")
    print(f"{'='*60}")
    
    success_count = sum(1 for r in all_results if r["success"])
    total_count = len(all_results)
    
    print(f"✅ 成功: {success_count}/{total_count}")
    
    if success_count < total_count:
        print(f"❌ 失败的买家哈希:")
        for result in all_results:
            if not result["success"]:
                print(f"   - {result['buyer_hash']}: {result['error']}")
    
    print(f"\n🏁 自动化零知识证明生成完成")

if __name__ == "__main__":
    main() 