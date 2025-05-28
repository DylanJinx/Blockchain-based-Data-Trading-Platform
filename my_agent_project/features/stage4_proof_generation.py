#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
第四阶段零知识证明生成模块

功能：
1. 为水印数据集生成零知识证明
2. 学习 LSB_groth16/create_LSB_i.py 的逻辑
3. 创建买家哈希对应的实验目录
4. 复制分块数据和配置文件
5. 执行完整的证明生成流程
"""

import os
import shutil
import subprocess
import time
import logging
from typing import Dict, Any, List
from pathlib import Path

# 导入证明打包生成器
try:
    # 尝试相对导入
    from .proof_package_generator import auto_package_proof_on_completion
except ImportError:
    # 如果相对导入失败，使用绝对导入
    from proof_package_generator import auto_package_proof_on_completion


class Stage4ProofGenerator:
    """第四阶段零知识证明生成器"""

    def __init__(self, lsb_groth16_base: str = None):
        """
        初始化第四阶段证明生成器
        
        Args:
            lsb_groth16_base: LSB_groth16 基础目录路径
        """
        if lsb_groth16_base is None:
            # 自动检测LSB_groth16目录
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(current_dir))
            self.lsb_groth16_base = os.path.join(project_root, "LSB_groth16")
        else:
            self.lsb_groth16_base = lsb_groth16_base
        
        self.template_dir = os.path.join(self.lsb_groth16_base, "LSB_i")
        self.experiments_base = os.path.join(self.lsb_groth16_base, "LSB_experiments")
        
        logging.info(f"LSB_groth16路径: {self.lsb_groth16_base}")
        logging.info(f"模板路径: {self.template_dir}")
        logging.info(f"实验路径: {self.experiments_base}")
        
        # 验证必要路径存在
        if not os.path.exists(self.template_dir):
            raise FileNotFoundError(f"LSB_i模板目录不存在: {self.template_dir}")
        if not os.path.exists(self.experiments_base):
            os.makedirs(self.experiments_base, exist_ok=True)

    def generate_proof_for_watermark(self, buy_hash: str, chunked_data_dir: str, 
                                   chunk_pixel_size: int, constraint_power: int,
                                   user_address: str = None) -> Dict[str, Any]:
        """
        为特定买家哈希的水印数据生成零知识证明

        Args:
            buy_hash: 买家哈希值（完整哈希）
            chunked_data_dir: 分块数据目录
            chunk_pixel_size: 分块像素大小（如29）
            constraint_power: 约束功率（如16对应2^16）
            user_address: 用户地址（用于证明包命名）

        Returns:
            证明生成结果字典
        """
        try:
            start_time = time.time()
            
            # 1. 创建实验目录
            experiment_name = buy_hash[:16]  # 使用买家哈希前16字符
            experiment_dir = os.path.join(self.experiments_base, experiment_name)
            
            logging.info(f"开始为买家哈希 {experiment_name} 生成零知识证明...")
            if user_address:
                logging.info(f"用户地址: {user_address}")
            
            self._create_experiment_directory(experiment_dir)
            
            # 2. 复制分块数据
            self._copy_chunked_data(chunked_data_dir, experiment_dir, chunk_pixel_size)
            
            # 3. 设置ptau文件
            self._setup_ptau_file(experiment_dir, constraint_power)
            
            # 4. 更新配置文件
            self._update_configuration_files(experiment_dir, chunk_pixel_size, constraint_power)
            
            # 5. 编译电路
            self._compile_circuit(experiment_dir)
            
            # 6. 执行证明生成流程
            proof_results = self._execute_proof_pipeline(experiment_dir)
            
            # 7. 验证证明
            verification_results = self._verify_proofs(experiment_dir)
            
            total_time = time.time() - start_time
            
            logging.info(f"✅ 零知识证明生成完成，总耗时: {total_time:.2f}秒")
            logging.info(f"🎉 Stage 4零知识证明生成成功完成！")
            
            # 8. 自动生成证明包（如果提供了用户地址）
            package_result = None
            if user_address:
                logging.info(f"开始为用户 {user_address} 自动生成证明包...")
                package_result = auto_package_proof_on_completion(
                    user_address=user_address,
                    experiment_dir=experiment_dir,
                    buy_hash=buy_hash
                )
                
                if package_result and package_result.get("status") == "success":
                    logging.info(f"🎁 证明包自动生成成功: {package_result['package_name']}")
                else:
                    logging.warning(f"⚠️ 证明包自动生成失败，但证明生成成功")
            else:
                logging.info("未提供用户地址，跳过自动证明包生成")
            
            return {
                "status": "success",
                "experiment_dir": experiment_dir,
                "experiment_name": experiment_name,
                "buy_hash": buy_hash,
                "chunk_pixel_size": chunk_pixel_size,
                "constraint_power": constraint_power,
                "total_time": total_time,
                "proof_results": proof_results,
                "verification_results": verification_results,
                "user_address": user_address,
                "package_result": package_result
            }
            
        except Exception as e:
            logging.error(f"❌ 零知识证明生成失败: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "buy_hash": buy_hash,
                "user_address": user_address
            }

    def _create_experiment_directory(self, experiment_dir: str):
        """创建实验目录并复制模板（如果不存在的话）"""
        if os.path.exists(experiment_dir):
            logging.info(f"实验目录已存在，将直接使用: {experiment_dir}")
            return
        
        # 复制整个LSB_i模板目录
        shutil.copytree(self.template_dir, experiment_dir)
        
        logging.info(f"✅ 模板复制完成: {self.template_dir} → {experiment_dir}")

    def _copy_chunked_data(self, chunked_data_dir: str, experiment_dir: str, chunk_pixel_size: int):
        """复制分块数据到实验目录"""
        target_input_dir = os.path.join(experiment_dir, "LSB", f"input_json_chunk_pixel_{chunk_pixel_size}")
        
        # 检查目标目录是否已经存在且包含正确的子目录结构
        if os.path.exists(target_input_dir):
            # 检查是否有input_1, input_2等子目录
            subdirs = [d for d in os.listdir(target_input_dir) 
                       if os.path.isdir(os.path.join(target_input_dir, d)) and d.startswith('input_')]
            
            if subdirs:
                # 统计子目录中的JSON文件
                total_files = 0
                for subdir in subdirs:
                    subdir_path = os.path.join(target_input_dir, subdir)
                    json_files = [f for f in os.listdir(subdir_path) if f.endswith('.json')]
                    total_files += len(json_files)
                
                if total_files > 0:
                    logging.info(f"分块数据目录已存在，包含 {len(subdirs)} 个子目录和 {total_files} 个JSON文件，跳过复制")
                    return
            else:
                # 检查是否有平铺的JSON文件（旧格式）
                existing_files = [f for f in os.listdir(target_input_dir) if f.endswith('.json')]
                if existing_files:
                    logging.info(f"分块数据目录已存在（平铺格式），包含 {len(existing_files)} 个JSON文件，跳过复制")
                    return
            
            # 如果目录存在但结构不正确，删除重建
            logging.info("分块数据目录已存在但结构不正确，将重新复制")
            shutil.rmtree(target_input_dir)
        
        # 检查源目录是否存在
        if not os.path.exists(chunked_data_dir):
            raise FileNotFoundError(f"分块数据源目录不存在: {chunked_data_dir}")
        
        # 复制整个分块数据目录
        shutil.copytree(chunked_data_dir, target_input_dir)
        
        # 统计复制的文件数量
        total_files = 0
        for root, dirs, files in os.walk(target_input_dir):
            total_files += len([f for f in files if f.endswith('.json')])
        
        logging.info(f"✅ 分块数据复制完成: {total_files} 个JSON文件")
        logging.info(f"   源目录: {chunked_data_dir}")
        logging.info(f"   目标目录: {target_input_dir}")

    def _setup_ptau_file(self, experiment_dir: str, constraint_power: int):
        """设置ptau文件"""
        ptau_filename = f"pot{constraint_power}_final.ptau"
        source_ptau = os.path.join(self.lsb_groth16_base, ptau_filename)
        target_ptau_dir = os.path.join(experiment_dir, "LSB", "ptau")
        target_ptau = os.path.join(target_ptau_dir, ptau_filename)
        
        if not os.path.exists(source_ptau):
            raise FileNotFoundError(f"找不到ptau文件: {source_ptau}")
        
        os.makedirs(target_ptau_dir, exist_ok=True)
        shutil.copy2(source_ptau, target_ptau)
        
        logging.info(f"✅ ptau文件复制完成: {ptau_filename}")

    def _update_configuration_files(self, experiment_dir: str, chunk_pixel_size: int, constraint_power: int):
        """更新配置文件：B_witness.py, C_zkey_time.py, LSB.circom"""
        lsb_dir = os.path.join(experiment_dir, "LSB")
        
        self._update_b_witness(lsb_dir, chunk_pixel_size)
        self._update_c_zkey(lsb_dir, constraint_power)
        self._update_lsb_circom(lsb_dir, chunk_pixel_size)

    def _update_b_witness(self, lsb_dir: str, chunk_pixel_size: int):
        """更新B_witness.py文件"""
        b_witness_file = os.path.join(lsb_dir, "B_witness.py")
        
        with open(b_witness_file, "r", encoding='utf-8') as f:
            content = f.read()
        
        # 替换输入目录占位符
        content = content.replace(
            "input_json_chunk_pixel_hownumberPixels", 
            f"input_json_chunk_pixel_{chunk_pixel_size}"
        )
        
        # 修复Windows路径分隔符为Unix格式（针对macOS/Linux）
        content = content.replace("LSB_js\\generate_witness.js", "LSB_js/generate_witness.js")
        content = content.replace("LSB_js\\LSB.wasm", "LSB_js/LSB.wasm")
        
        with open(b_witness_file, "w", encoding='utf-8') as f:
            f.write(content)
        
        logging.info(f"✅ B_witness.py 已更新，输入目录: input_json_chunk_pixel_{chunk_pixel_size}，路径分隔符已修复")

    def _update_c_zkey(self, lsb_dir: str, constraint_power: int):
        """更新C_zkey_time.py文件"""
        c_zkey_file = os.path.join(lsb_dir, "C_zkey_time.py")
        
        with open(c_zkey_file, "r", encoding='utf-8') as f:
            content = f.read()
        
        # 替换ptau文件占位符
        ptau_filename = f"pot{constraint_power}_final.ptau"
        content = content.replace("pothownumberptau_final.ptau", ptau_filename)
        
        with open(c_zkey_file, "w", encoding='utf-8') as f:
            f.write(content)
        
        logging.info(f"✅ C_zkey_time.py 已更新，ptau文件: {ptau_filename}")

    def _update_lsb_circom(self, lsb_dir: str, chunk_pixel_size: int):
        """更新LSB.circom文件"""
        lsb_circom_file = os.path.join(lsb_dir, "LSB.circom")
        
        with open(lsb_circom_file, "r", encoding='utf-8') as f:
            content = f.read()
        
        # 替换像素数量占位符（需要替换所有出现的位置）
        content = content.replace("hownumberPixels", str(chunk_pixel_size))
        content = content.replace("numPixelscheng3", str(chunk_pixel_size * 3))
        
        with open(lsb_circom_file, "w", encoding='utf-8') as f:
            f.write(content)
        
        logging.info(f"✅ LSB.circom 已更新，像素数: {chunk_pixel_size}，总信号数: {chunk_pixel_size * 3}")

    def _compile_circuit(self, experiment_dir: str):
        """编译电路"""
        lsb_dir = os.path.join(experiment_dir, "LSB")
        
        logging.info("开始编译电路...")
        
        # 创建必要的目录
        os.makedirs(os.path.join(lsb_dir, "LSB_js"), exist_ok=True)
        
        # 编译circom电路
        compile_cmd = ["circom", "LSB.circom", "--r1cs", "--wasm", "-o", "."]
        
        result = subprocess.run(
            compile_cmd,
            cwd=lsb_dir,
            capture_output=True,
            text=True,
            timeout=300  # 5分钟超时
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"电路编译失败: {result.stderr}")
        
        logging.info("✅ 电路编译完成")

    def _execute_proof_pipeline(self, experiment_dir: str) -> Dict[str, Any]:
        """执行证明生成流水线"""
        lsb_dir = os.path.join(experiment_dir, "LSB")
        results = {}
        
        # B步骤：生成witness文件
        logging.info("执行 B_witness.py...")
        start_time = time.time()
        
        result = subprocess.run(
            ["python", "B_witness.py"],
            cwd=lsb_dir,
            capture_output=True,
            text=True,
            timeout=1800  # 30分钟超时
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"B_witness.py 执行失败: {result.stderr}")
        
        results["B_witness"] = {
            "duration": time.time() - start_time,
            "status": "success"
        }
        logging.info(f"✅ B_witness.py 执行完成，耗时: {results['B_witness']['duration']:.2f}秒")
        
        # C步骤：生成zkey
        logging.info("执行 C_zkey_time.py...")
        start_time = time.time()
        
        result = subprocess.run(
            ["python", "C_zkey_time.py"],
            cwd=lsb_dir,
            capture_output=True,
            text=True,
            timeout=3600  # 60分钟超时
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"C_zkey_time.py 执行失败: {result.stderr}")
        
        results["C_zkey"] = {
            "duration": time.time() - start_time,
            "status": "success"
        }
        logging.info(f"✅ C_zkey_time.py 执行完成，耗时: {results['C_zkey']['duration']:.2f}秒")
        
        # D步骤：生成证明
        logging.info("执行 D_proof_public.py...")
        start_time = time.time()
        
        result = subprocess.run(
            ["python", "D_proof_public.py"],
            cwd=lsb_dir,
            capture_output=True,
            text=True,
            timeout=3600  # 60分钟超时
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"D_proof_public.py 执行失败: {result.stderr}")
        
        results["D_proof"] = {
            "duration": time.time() - start_time,
            "status": "success"
        }
        logging.info(f"✅ D_proof_public.py 执行完成，耗时: {results['D_proof']['duration']:.2f}秒")
        
        return results

    def _verify_proofs(self, experiment_dir: str) -> Dict[str, Any]:
        """验证生成的证明"""
        lsb_dir = os.path.join(experiment_dir, "LSB")
        
        logging.info("执行 E_verify_proof_public.py...")
        start_time = time.time()
        
        result = subprocess.run(
            ["python", "E_verify_proof_public.py"],
            cwd=lsb_dir,
            capture_output=True,
            text=True,
            timeout=1800  # 30分钟超时
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"E_verify_proof_public.py 执行失败: {result.stderr}")
        
        verification_result = {
            "duration": time.time() - start_time,
            "status": "success"
        }
        
        logging.info(f"✅ E_verify_proof_public.py 执行完成，耗时: {verification_result['duration']:.2f}秒")
        
        # 统计生成的证明文件
        proof_dir = os.path.join(lsb_dir, "proof_json")
        public_dir = os.path.join(lsb_dir, "public_json")
        
        proof_count = 0
        public_count = 0
        
        if os.path.exists(proof_dir):
            for root, dirs, files in os.walk(proof_dir):
                proof_count += len([f for f in files if f.endswith('.json')])
        
        if os.path.exists(public_dir):
            for root, dirs, files in os.walk(public_dir):
                public_count += len([f for f in files if f.endswith('.json')])
        
        verification_result.update({
            "proof_files_generated": proof_count,
            "public_files_generated": public_count
        })
        
        logging.info(f"证明文件统计: {proof_count} 个proof文件，{public_count} 个public文件")
        
        return verification_result


def test_stage4_proof_generation():
    """测试第四阶段证明生成"""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    
    # 测试参数 - 修改约束功率为16
    test_buy_hash = "a158e72bdc06739d4b9f3139de796443209eefd90bf43deff2d5bd4902346e604022bcd825f28136e"
    test_chunked_data_dir = "/Users/dylan/Code_Projects/Python_Projects/image_similarity/my_agent_project/data/chunked_inputs/session_a158e72bdc06739d/chunk_pixel_29"
    test_chunk_pixel_size = 29
    test_constraint_power = 16  # 改为16，因为用户只有pot16_final.ptau
    
    generator = Stage4ProofGenerator()
    
    result = generator.generate_proof_for_watermark(
        buy_hash=test_buy_hash,
        chunked_data_dir=test_chunked_data_dir,
        chunk_pixel_size=test_chunk_pixel_size,
        constraint_power=test_constraint_power
    )
    
    print(f"测试结果: {result}")
    
    return result


if __name__ == "__main__":
    test_stage4_proof_generation()
