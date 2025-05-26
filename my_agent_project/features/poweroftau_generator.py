#!/usr/bin/env python3
"""
Power of Tau 生成器模块
用于为数据集登记功能生成零知识证明所需的 Powers of Tau 文件
"""

import os
import sys
import json
import subprocess
import time
import shutil
import logging
from typing import Dict, Any, Tuple, Optional
from PIL import Image

class PowerOfTauGenerator:
    """Power of Tau生成器类"""
    
    def __init__(self, project_root: str = None):
        """
        初始化Power of Tau生成器
        
        Args:
            project_root: 项目根目录路径
        """
        if project_root is None:
            # 从当前文件位置推断项目根目录
            current_dir = os.path.dirname(os.path.abspath(__file__))
            self.project_root = os.path.dirname(os.path.dirname(current_dir))
        else:
            self.project_root = project_root
            
        # 设置各个目录路径
        self.abcd_dir = os.path.join(self.project_root, "ABCD_total_time")
        self.lsb_dir = os.path.join(self.project_root, "LSB_groth16")
        self.single_analysis_script = os.path.join(self.abcd_dir, "code", "single_image_analysis.py")
        
        # 创建临时工作目录
        self.temp_dir = os.path.join(self.project_root, "temp_ptau")
        os.makedirs(self.temp_dir, exist_ok=True)
        
        logging.info(f"PowerOfTauGenerator 初始化完成，项目根目录: {self.project_root}")
    
    def calculate_dataset_pixels(self, dataset_path: str) -> int:
        """
        计算数据集中所有图片的总像素数
        
        Args:
            dataset_path: 数据集目录路径
            
        Returns:
            总像素数
        """
        total_pixels = 0
        image_count = 0
        
        try:
            # 支持的图片格式
            supported_formats = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.gif'}
            
            for root, dirs, files in os.walk(dataset_path):
                for file in files:
                    file_ext = os.path.splitext(file)[1].lower()
                    if file_ext in supported_formats:
                        image_path = os.path.join(root, file)
                        try:
                            with Image.open(image_path) as img:
                                width, height = img.size
                                pixels = width * height
                                total_pixels += pixels
                                image_count += 1
                                logging.debug(f"图片 {file}: {width}x{height} = {pixels} 像素")
                        except Exception as e:
                            logging.warning(f"无法处理图片 {image_path}: {e}")
                            
            logging.info(f"数据集分析完成: 共 {image_count} 张图片，总像素数: {total_pixels}")
            return total_pixels
            
        except Exception as e:
            logging.error(f"计算数据集像素数失败: {e}")
            raise
    
    def get_optimal_constraints(self, total_pixels: int) -> Dict[str, Any]:
        """
        计算最优约束配置（使用真正的adaptive_block_algorithm.py）
        
        Args:
            total_pixels: 总像素数
            
        Returns:
            包含最优约束配置的字典
        """
        try:
            logging.info(f"开始计算 {total_pixels} 像素的最优约束配置")
            
            # 导入真正的算法
            sys.path.append(os.path.join(self.project_root, "ABCD_total_time", "code"))
            from adaptive_block_algorithm import AdaptiveBlockAlgorithm
            
            # 运行真正的算法
            algorithm = AdaptiveBlockAlgorithm()
            optimal, results, constraint_groups = algorithm.run_analysis(
                total_pixels, use_d_total=True, save_results=False
            )
            
            if optimal:
                config = {
                    'power': optimal['power'],
                    'constraint_size': optimal['X'],  # optimal['X'] 就是约束大小
                    'M': optimal['M'],
                    'm': optimal['m'],
                    'total_time': optimal['total_time']
                }
                logging.info(f"计算得到的最优配置: {config}")
                return config
            else:
                # 如果算法失败，使用安全的默认配置
                logging.warning("adaptive_block_algorithm未返回结果，使用默认配置")
                return self._get_fallback_config(total_pixels)
                
        except Exception as e:
            logging.error(f"使用adaptive_block_algorithm计算失败: {e}")
            logging.info("回退到简化计算方法")
            return self._get_fallback_config(total_pixels)
    
    def _get_fallback_config(self, total_pixels: int) -> Dict[str, Any]:
        """
        当主算法失败时的备用约束计算
        
        Args:
            total_pixels: 总像素数
            
        Returns:
            备用约束配置
        """
        # 基于经验的简化计算
        if total_pixels <= 100000:
            power = 18  # 2^18 = 262144
        elif total_pixels <= 500000:
            power = 19  # 2^19 = 524288 
        elif total_pixels <= 1000000:
            power = 20  # 2^20 = 1048576
        elif total_pixels <= 2000000:
            power = 21  # 2^21 = 2097152
        else:
            power = 22  # 2^22 = 4194304
        
        constraint_size = 2 ** power
        # 简单估算M和m
        c = 2250  # 每像素约束数
        m = constraint_size // c  # 每块最大像素数
        M = (total_pixels + m - 1) // m  # 分块数
        
        config = {
            'power': power,
            'constraint_size': constraint_size,
            'M': M,
            'm': m,
            'total_time': 0.0
        }
        
        logging.info(f"使用备用配置: {config}")
        return config
    
    def generate_powers_of_tau(self, constraint_power: int, user_id: str) -> str:
        """
        生成Powers of Tau文件
        
        Args:
            constraint_power: 约束大小的幂次 (如12表示2^12=4096约束)
            user_id: 用户标识符
            
        Returns:
            最终生成的ptau文件路径
        """
        try:
            logging.info(f"开始为用户 {user_id} 生成 Powers of Tau (约束: 2^{constraint_power})")
            
            # 创建用户专用的工作目录
            user_temp_dir = os.path.join(self.temp_dir, f"user_{user_id}")
            os.makedirs(user_temp_dir, exist_ok=True)
            
            # 定义各个阶段的文件名
            initial_ptau = os.path.join(user_temp_dir, f"pot{constraint_power}_0000.ptau")
            contributed_ptau = os.path.join(user_temp_dir, f"pot{constraint_power}_0001.ptau")
            beacon_ptau = os.path.join(user_temp_dir, f"pot{constraint_power}_beacon.ptau")
            final_ptau = os.path.join(user_temp_dir, f"pot{constraint_power}_final.ptau")
            
            # 1. 初始化Powers of Tau
            logging.info("步骤1: 初始化Powers of Tau")
            self._run_snarkjs_command([
                "powersoftau", "new", "bn128", str(constraint_power), initial_ptau, "-v"
            ])
            
            # 2. 准备用户贡献文件（这里先创建一个空的贡献文件，等待用户在浏览器端完成贡献）
            logging.info("步骤2: 准备用户贡献文件")
            # 返回初始ptau文件路径，让前端下载进行贡献
            return initial_ptau
            
        except Exception as e:
            logging.error(f"生成Powers of Tau失败: {e}")
            raise
    
    def complete_powers_of_tau_ceremony(self, user_contributed_ptau: str, user_id: str, constraint_power: int) -> str:
        """
        完成Powers of Tau仪式的后续步骤
        
        Args:
            user_contributed_ptau: 用户贡献后的ptau文件路径
            user_id: 用户标识符
            constraint_power: 约束大小的幂次
            
        Returns:
            最终ptau文件路径
        """
        try:
            logging.info(f"完成用户 {user_id} 的 Powers of Tau 仪式")
            
            # 用户工作目录
            user_temp_dir = os.path.join(self.temp_dir, f"user_{user_id}")
            
            # 定义文件名
            beacon_ptau = os.path.join(user_temp_dir, f"pot{constraint_power}_beacon.ptau")
            final_ptau = os.path.join(user_temp_dir, f"pot{constraint_power}_final.ptau")
            final_destination = os.path.join(self.lsb_dir, f"pot{constraint_power}_final.ptau")
            
            # 3. 验证用户贡献
            logging.info("步骤3: 验证用户贡献")
            self._run_snarkjs_command([
                "powersoftau", "verify", user_contributed_ptau
            ])
            
            # 4. 引入随机化信标
            logging.info("步骤4: 引入随机化信标")
            # 使用当前时间戳作为随机信标
            beacon_hash = hex(int(time.time()))[2:]  # 去掉0x前缀
            self._run_snarkjs_command([
                "powersoftau", "beacon", user_contributed_ptau, beacon_ptau, beacon_hash, "10", "-v"
            ])
            
            # 5. 生成最终的final.ptau
            logging.info("步骤5: 生成最终的final.ptau")
            self._run_snarkjs_command([
                "powersoftau", "prepare", "phase2", beacon_ptau, final_ptau, "-v"
            ])
            
            # 6. 验证final.ptau
            logging.info("步骤6: 验证final.ptau")
            self._run_snarkjs_command([
                "powersoftau", "verify", final_ptau
            ])
            
            # 7. 将最终文件复制到LSB_groth16文件夹
            logging.info("步骤7: 复制最终文件到LSB_groth16文件夹")
            os.makedirs(self.lsb_dir, exist_ok=True)
            shutil.copy2(final_ptau, final_destination)
            
            logging.info(f"Powers of Tau生成完成: {final_destination}")
            return final_destination
            
        except Exception as e:
            logging.error(f"完成Powers of Tau仪式失败: {e}")
            raise
    
    def _run_snarkjs_command(self, args: list) -> subprocess.CompletedProcess:
        """
        运行snarkjs命令
        
        Args:
            args: snarkjs命令参数列表
            
        Returns:
            subprocess执行结果
        """
        cmd = ["snarkjs"] + args
        logging.info(f"执行snarkjs命令: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=1200  # 20分钟超时
            )
            
            if result.stdout:
                logging.debug(f"snarkjs输出: {result.stdout}")
            
            return result
            
        except subprocess.CalledProcessError as e:
            logging.error(f"snarkjs命令执行失败: {e}")
            logging.error(f"错误输出: {e.stderr}")
            raise
        except subprocess.TimeoutExpired as e:
            logging.error(f"snarkjs命令执行超时: {e}")
            raise
    
    def _run_snarkjs_command_with_input(self, args: list, user_input: str = None) -> subprocess.CompletedProcess:
        """
        运行需要用户输入的snarkjs命令
        
        Args:
            args: snarkjs命令参数列表
            user_input: 用户输入的文本（用于贡献等需要熵值的操作）
            
        Returns:
            subprocess执行结果
        """
        cmd = ["snarkjs"] + args
        logging.info(f"执行snarkjs命令（带输入）: {' '.join(cmd)}")
        
        try:
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # 如果提供了用户输入，发送给进程
            if user_input:
                stdout, stderr = process.communicate(input=user_input, timeout=1200)
            else:
                stdout, stderr = process.communicate(timeout=1200)
            
            if process.returncode != 0:
                logging.error(f"snarkjs命令执行失败，返回码: {process.returncode}")
                logging.error(f"错误输出: {stderr}")
                raise subprocess.CalledProcessError(process.returncode, cmd, stdout, stderr)
            
            if stdout:
                logging.debug(f"snarkjs输出: {stdout}")
            
            return subprocess.CompletedProcess(cmd, process.returncode, stdout, stderr)
            
        except subprocess.TimeoutExpired as e:
            logging.error(f"snarkjs命令执行超时: {e}")
            process.kill()
            raise
        except Exception as e:
            logging.error(f"snarkjs命令执行异常: {e}")
            raise
    
    def contribute_with_entropy(self, initial_ptau_path: str, contributed_ptau_path: str, entropy: str = None, name: str = "contribution") -> str:
        """
        使用指定的熵值进行Powers of Tau贡献
        
        Args:
            initial_ptau_path: 初始ptau文件路径
            contributed_ptau_path: 贡献后的ptau文件路径
            entropy: 熵值字符串，如果为None则自动生成
            name: 贡献者名称
            
        Returns:
            贡献后的ptau文件路径
        """
        try:
            if entropy is None:
                # 自动生成熵值
                import secrets
                import string
                entropy = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))
                
            logging.info(f"开始Powers of Tau贡献，熵值长度: {len(entropy)}")
            
            # 执行贡献命令
            self._run_snarkjs_command_with_input([
                "powersoftau", "contribute", initial_ptau_path, contributed_ptau_path, 
                f"--name={name}", "-v"
            ], user_input=f"{entropy}\n")
            
            logging.info(f"Powers of Tau贡献完成: {contributed_ptau_path}")
            return contributed_ptau_path
            
        except Exception as e:
            logging.error(f"Powers of Tau贡献失败: {e}")
            raise
    
    def cleanup_temp_files(self, user_id: str = None):
        """
        清理临时文件
        
        Args:
            user_id: 用户标识符，如果为None则清理所有临时文件
        """
        try:
            if user_id:
                user_temp_dir = os.path.join(self.temp_dir, f"user_{user_id}")
                if os.path.exists(user_temp_dir):
                    shutil.rmtree(user_temp_dir)
                    logging.info(f"已清理用户 {user_id} 的临时文件")
            else:
                if os.path.exists(self.temp_dir):
                    shutil.rmtree(self.temp_dir)
                    logging.info("已清理所有临时文件")
        except Exception as e:
            logging.warning(f"清理临时文件失败: {e}")
    
    def generate_initial_ptau_for_user_contribution(self, constraint_power: int, user_id: str) -> Dict[str, str]:
        """
        为用户贡献生成初始Powers of Tau文件
        这个方法只执行初始化步骤，返回文件路径供用户下载进行贡献
        
        Args:
            constraint_power: 约束大小的幂次
            user_id: 用户标识符
            
        Returns:
            包含初始ptau文件路径等信息的字典
        """
        try:
            logging.info(f"为用户 {user_id} 生成初始 Powers of Tau (约束: 2^{constraint_power})")
            
            # 创建用户专用的工作目录
            user_temp_dir = os.path.join(self.temp_dir, f"user_{user_id}")
            os.makedirs(user_temp_dir, exist_ok=True)
            
            # 定义文件路径
            initial_ptau = os.path.join(user_temp_dir, f"pot{constraint_power}_0000.ptau")
            
            # 1. 初始化Powers of Tau
            logging.info("步骤1: 初始化Powers of Tau")
            self._run_snarkjs_command([
                "powersoftau", "new", "bn128", str(constraint_power), initial_ptau, "-v"
            ])
            
            logging.info(f"初始Powers of Tau文件生成完成: {initial_ptau}")
            
            return {
                "initial_ptau_path": initial_ptau,
                "user_temp_dir": user_temp_dir,
                "constraint_power": constraint_power,
                "user_id": user_id,
                "download_filename": f"pot{constraint_power}_0000.ptau"
            }
            
        except Exception as e:
            logging.error(f"生成初始Powers of Tau失败: {e}")
            raise
    
    def complete_ptau_ceremony_from_user_contribution(self, contributed_ptau_path: str, user_id: str, constraint_power: int) -> str:
        """
        从用户贡献的ptau文件完成Powers of Tau仪式
        
        Args:
            contributed_ptau_path: 用户贡献后上传的ptau文件路径
            user_id: 用户标识符
            constraint_power: 约束大小的幂次
            
        Returns:
            最终ptau文件路径
        """
        try:
            logging.info(f"从用户贡献完成 Powers of Tau 仪式 (用户: {user_id})")
            
            # 用户工作目录
            user_temp_dir = os.path.join(self.temp_dir, f"user_{user_id}")
            
            # 3. 验证用户贡献
            logging.info("步骤3: 验证用户贡献")
            self._run_snarkjs_command([
                "powersoftau", "verify", contributed_ptau_path
            ])
            
            # 定义后续文件名
            beacon_ptau = os.path.join(user_temp_dir, f"pot{constraint_power}_beacon.ptau")
            final_ptau = os.path.join(user_temp_dir, f"pot{constraint_power}_final.ptau")
            final_destination = os.path.join(self.lsb_dir, f"pot{constraint_power}_final.ptau")
            
            # 4. 引入随机化信标
            logging.info("步骤4: 引入随机化信标")
            beacon_hash = hex(int(time.time()))[2:]  # 使用当前时间戳作为随机信标
            self._run_snarkjs_command([
                "powersoftau", "beacon", contributed_ptau_path, beacon_ptau, beacon_hash, "10", "-v"
            ])
            
            # 5. 生成最终的final.ptau
            logging.info("步骤5: 生成最终的final.ptau")
            self._run_snarkjs_command([
                "powersoftau", "prepare", "phase2", beacon_ptau, final_ptau, "-v"
            ])
            
            # 6. 验证final.ptau
            logging.info("步骤6: 验证final.ptau")
            self._run_snarkjs_command([
                "powersoftau", "verify", final_ptau
            ])
            
            # 7. 将最终文件复制到LSB_groth16文件夹
            logging.info("步骤7: 复制最终文件到LSB_groth16文件夹")
            os.makedirs(self.lsb_dir, exist_ok=True)
            shutil.copy2(final_ptau, final_destination)
            
            logging.info(f"Powers of Tau生成完成: {final_destination}")
            return final_destination
            
        except Exception as e:
            logging.error(f"完成Powers of Tau仪式失败: {e}")
            raise

def generate_ptau_for_dataset(dataset_path: str, user_id: str) -> Dict[str, Any]:
    """
    为数据集生成Powers of Tau的主函数
    
    Args:
        dataset_path: 数据集路径
        user_id: 用户标识符
        
    Returns:
        包含生成信息的字典
    """
    generator = PowerOfTauGenerator()
    
    try:
        # 1. 计算数据集总像素数
        total_pixels = generator.calculate_dataset_pixels(dataset_path)
        
        # 2. 获取最优约束配置
        optimal_config = generator.get_optimal_constraints(total_pixels)
        
        # 3. 生成初始Powers of Tau文件
        initial_ptau_path = generator.generate_powers_of_tau(
            optimal_config['power'], 
            user_id
        )
        
        return {
            "status": "success",
            "total_pixels": total_pixels,
            "optimal_config": optimal_config,
            "initial_ptau_path": initial_ptau_path,
            "message": "Powers of Tau初始化完成，等待用户贡献"
        }
        
    except Exception as e:
        logging.error(f"为数据集生成Powers of Tau失败: {e}")
        return {
            "status": "error",
            "message": str(e)
        }

if __name__ == "__main__":
    # 测试代码
    import argparse
    
    parser = argparse.ArgumentParser(description='Powers of Tau生成器')
    parser.add_argument('--dataset', required=True, help='数据集路径')
    parser.add_argument('--user-id', required=True, help='用户ID')
    
    args = parser.parse_args()
    
    # 设置日志
    logging.basicConfig(level=logging.INFO)
    
    result = generate_ptau_for_dataset(args.dataset, args.user_id)
    print(json.dumps(result, indent=2, ensure_ascii=False)) 