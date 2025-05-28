#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
证明文件打包生成器
在零知识证明生成完成后，自动打包verification_key.json, proof_json/, public_json/, E_verify_proof_public.py
"""

import os
import zipfile
import shutil
import logging
import json
import time
from typing import Dict, Any, Optional

class ProofPackageGenerator:
    """证明文件打包生成器"""
    
    def __init__(self, base_dir: str = None):
        """
        初始化打包生成器
        
        Args:
            base_dir: 基础目录，默认为LSB_groth16
        """
        if base_dir is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(current_dir))
            self.base_dir = os.path.join(project_root, "LSB_groth16")
        else:
            self.base_dir = base_dir
        
        self.experiments_dir = os.path.join(self.base_dir, "LSB_experiments")
        self.packages_dir = os.path.join(self.base_dir, "proof_packages")
        
        # 确保包目录存在
        os.makedirs(self.packages_dir, exist_ok=True)
        
        logging.info(f"ProofPackageGenerator初始化完成，基础目录: {self.base_dir}")
    
    def create_proof_package(self, user_address: str, experiment_dir: str, 
                           buy_hash: str = None) -> Dict[str, Any]:
        """
        为指定用户创建证明文件包
        
        Args:
            user_address: 用户地址（用于命名）
            experiment_dir: 实验目录路径
            buy_hash: 买家哈希值（可选，用于记录）
        
        Returns:
            打包结果信息
        """
        try:
            if not user_address:
                raise ValueError("用户地址不能为空")
            
            lsb_dir = os.path.join(experiment_dir, "LSB")
            
            # 验证实验目录存在
            if not os.path.exists(experiment_dir):
                raise FileNotFoundError(f"实验目录不存在: {experiment_dir}")
            
            if not os.path.exists(lsb_dir):
                raise FileNotFoundError(f"LSB目录不存在: {lsb_dir}")
            
            logging.info(f"开始为用户 {user_address} 创建证明包...")
            logging.info(f"实验目录: {experiment_dir}")
            
            # 检查必需的文件和目录
            required_items = [
                ("verification_key.json", os.path.join(lsb_dir, "verification_key.json")),
                ("proof_json目录", os.path.join(lsb_dir, "proof_json")),
                ("public_json目录", os.path.join(lsb_dir, "public_json")),
                ("E_verify_proof_public.py", os.path.join(lsb_dir, "E_verify_proof_public.py"))
            ]
            
            missing_items = []
            for name, path in required_items:
                if not os.path.exists(path):
                    missing_items.append(name)
            
            if missing_items:
                raise FileNotFoundError(f"缺少必需文件: {', '.join(missing_items)}")
            
            # 创建用户特定的包名称
            # 使用用户地址（去掉0x）+ 时间戳确保唯一性
            clean_address = user_address.replace('0x', '').lower()
            timestamp = int(time.time())
            package_name = f"proof_{clean_address}_{timestamp}"
            package_zip = f"{package_name}.zip"
            package_path = os.path.join(self.packages_dir, package_zip)
            
            logging.info(f"创建证明包: {package_zip}")
            
            # 创建ZIP压缩包
            with zipfile.ZipFile(package_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # 添加verification_key.json
                verification_key_path = os.path.join(lsb_dir, "verification_key.json")
                zipf.write(verification_key_path, "verification_key.json")
                logging.info("✅ 已添加 verification_key.json")
                
                # 添加proof_json目录
                proof_json_dir = os.path.join(lsb_dir, "proof_json")
                proof_count = self._add_directory_to_zip(zipf, proof_json_dir, "proof_json")
                logging.info(f"✅ 已添加 proof_json 目录 ({proof_count} 个文件)")
                
                # 添加public_json目录
                public_json_dir = os.path.join(lsb_dir, "public_json")
                public_count = self._add_directory_to_zip(zipf, public_json_dir, "public_json")
                logging.info(f"✅ 已添加 public_json 目录 ({public_count} 个文件)")
                
                # 添加E_verify_proof_public.py
                verify_script_path = os.path.join(lsb_dir, "E_verify_proof_public.py")
                zipf.write(verify_script_path, "E_verify_proof_public.py")
                logging.info("✅ 已添加 E_verify_proof_public.py")
                
                # 添加使用说明文件
                readme_content = self._generate_readme_content(user_address, buy_hash, proof_count, public_count)
                zipf.writestr("README.md", readme_content)
                logging.info("✅ 已添加 README.md 使用说明")
                
                # 添加包信息文件
                package_info = {
                    "user_address": user_address,
                    "buy_hash": buy_hash,
                    "experiment_dir": experiment_dir,
                    "package_creation_time": time.time(),
                    "package_creation_time_str": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "proof_files_count": proof_count,
                    "public_files_count": public_count,
                    "package_name": package_name,
                    "format_version": "1.0"
                }
                zipf.writestr("package_info.json", json.dumps(package_info, indent=2, ensure_ascii=False))
                logging.info("✅ 已添加 package_info.json 包信息")
            
            # 获取包文件大小
            package_size = os.path.getsize(package_path)
            package_size_mb = package_size / (1024 * 1024)
            
            logging.info(f"✅ 证明包创建完成:")
            logging.info(f"   包名称: {package_zip}")
            logging.info(f"   包大小: {package_size_mb:.2f} MB")
            logging.info(f"   包路径: {package_path}")
            logging.info(f"   证明文件数: {proof_count}")
            logging.info(f"   公开输入文件数: {public_count}")
            
            return {
                "status": "success",
                "package_name": package_zip,
                "package_path": package_path,
                "package_size": package_size,
                "package_size_mb": package_size_mb,
                "proof_files_count": proof_count,
                "public_files_count": public_count,
                "user_address": user_address,
                "buy_hash": buy_hash,
                "package_info": package_info
            }
            
        except Exception as e:
            logging.error(f"创建证明包失败: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "user_address": user_address,
                "experiment_dir": experiment_dir
            }
    
    def _add_directory_to_zip(self, zipf: zipfile.ZipFile, source_dir: str, archive_dir: str) -> int:
        """
        将整个目录添加到ZIP文件中
        
        Args:
            zipf: ZIP文件对象
            source_dir: 源目录路径
            archive_dir: 在ZIP中的目录名
        
        Returns:
            添加的文件数量
        """
        file_count = 0
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                file_path = os.path.join(root, file)
                # 计算在ZIP中的相对路径
                relative_path = os.path.relpath(file_path, source_dir)
                archive_path = os.path.join(archive_dir, relative_path).replace('\\', '/')
                zipf.write(file_path, archive_path)
                file_count += 1
        return file_count
    
    def _generate_readme_content(self, user_address: str, buy_hash: str, 
                                proof_count: int, public_count: int) -> str:
        """生成README.md内容"""
        buy_hash_display = buy_hash[:16] + "..." if buy_hash else "未知"
        
        content = f"""# 零知识证明文件包

## 包信息
- **用户地址**: `{user_address}`
- **证明文件数量**: {proof_count}
- **公开输入文件数量**: {public_count}
- **生成时间**: {time.strftime("%Y-%m-%d %H:%M:%S")}

## 文件说明

### 1. verification_key.json
验证密钥文件，用于验证零知识证明的有效性。

### 2. proof_json/ 目录
包含所有生成的零知识证明文件：
- `proof_1/` - 第1张图片的证明文件
- `proof_2/` - 第2张图片的证明文件
- ...
- 每个子目录包含该图片各个分块的证明文件

### 3. public_json/ 目录
包含所有公开输入文件：
- `public_1/` - 第1张图片的公开输入
- `public_2/` - 第2张图片的公开输入
- ...
- 每个子目录包含该图片各个分块的公开输入文件

### 4. E_verify_proof_public.py
验证脚本，用于验证所有证明的有效性。

## 使用方法

1. **解压文件包**:
   ```bash
   unzip proof_*.zip
   cd proof_*
   ```

2. **安装依赖** (需要Node.js和snarkjs):
   ```bash
   npm install -g snarkjs
   ```

3. **验证证明**:
   ```bash
   python E_verify_proof_public.py
   ```

4. **手动验证单个证明** (可选):
   ```bash
   snarkjs groth16 verify verification_key.json public_json/public_1/public_1_1.json proof_json/proof_1/proof_1_1.json
   ```

## 证明含义

这些零知识证明证明了您提交的数据集确实包含了从原始创作者处购买时嵌入的数字水印。

- ✅ **证明有效** = 您的数据集包含指定的数字水印
- ❌ **证明无效** = 数据集可能被篡改或不包含相应水印

## 技术细节

- **零知识证明系统**: Groth16
- **电路**: LSB数字水印验证电路
- **证明对象**: 每个图片分块的LSB位验证
- **安全性**: 基于椭圆曲线密码学，计算安全


"""
        return content
    
    def list_available_packages(self, user_address: str = None) -> list:
        """列出可用的证明包"""
        if not os.path.exists(self.packages_dir):
            return []
        
        packages = []
        for filename in os.listdir(self.packages_dir):
            if filename.endswith('.zip') and filename.startswith('proof_'):
                package_path = os.path.join(self.packages_dir, filename)
                
                # 如果指定了用户地址，只返回该用户的包
                if user_address:
                    clean_address = user_address.replace('0x', '').lower()
                    if not filename.startswith(f'proof_{clean_address}_'):
                        continue
                
                try:
                    # 尝试读取包信息
                    with zipfile.ZipFile(package_path, 'r') as zipf:
                        if 'package_info.json' in zipf.namelist():
                            package_info_content = zipf.read('package_info.json').decode('utf-8')
                            package_info = json.loads(package_info_content)
                        else:
                            # 旧格式包，从文件名解析信息
                            package_info = {
                                "package_name": filename[:-4],  # 去掉.zip
                                "user_address": "unknown",
                                "package_creation_time_str": "unknown"
                            }
                    
                    packages.append({
                        "filename": filename,
                        "filepath": package_path,
                        "size": os.path.getsize(package_path),
                        "size_mb": os.path.getsize(package_path) / (1024 * 1024),
                        "mtime": os.path.getmtime(package_path),
                        "package_info": package_info
                    })
                    
                except Exception as e:
                    logging.warning(f"读取包信息失败 {filename}: {e}")
                    continue
        
        # 按创建时间排序（最新的在前）
        packages.sort(key=lambda x: x['mtime'], reverse=True)
        return packages
    
    def cleanup_old_packages(self, days_old: int = 7) -> int:
        """清理旧的证明包文件"""
        if not os.path.exists(self.packages_dir):
            return 0
        
        current_time = time.time()
        cutoff_time = current_time - (days_old * 24 * 60 * 60)
        
        cleaned_count = 0
        for filename in os.listdir(self.packages_dir):
            if filename.endswith('.zip') and filename.startswith('proof_'):
                file_path = os.path.join(self.packages_dir, filename)
                if os.path.getmtime(file_path) < cutoff_time:
                    try:
                        os.remove(file_path)
                        cleaned_count += 1
                        logging.info(f"已清理旧证明包: {filename}")
                    except Exception as e:
                        logging.warning(f"清理文件失败 {filename}: {e}")
        
        return cleaned_count


# 辅助函数，用于在stage4完成后自动调用
def auto_package_proof_on_completion(user_address: str, experiment_dir: str, 
                                   buy_hash: str = None) -> Dict[str, Any]:
    """
    在stage4完成后自动创建证明包
    
    Args:
        user_address: 用户地址
        experiment_dir: 实验目录
        buy_hash: 买家哈希
    
    Returns:
        打包结果
    """
    try:
        generator = ProofPackageGenerator()
        result = generator.create_proof_package(
            user_address=user_address,
            experiment_dir=experiment_dir,
            buy_hash=buy_hash
        )
        
        if result["status"] == "success":
            logging.info(f"🎁 证明包自动生成完成: {result['package_name']}")
        else:
            logging.error(f"❌ 证明包自动生成失败: {result['error']}")
        
        return result
        
    except Exception as e:
        logging.error(f"自动证明打包异常: {str(e)}")
        return {
            "status": "error",
            "error": str(e)
        }


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    
    # 示例使用
    test_user_address = "0x90F79bf6EB2c4f870365E785982E1f101E93b906"
    test_experiment_dir = "/Users/dylan/Code_Projects/Python_Projects/image_similarity/LSB_groth16/LSB_experiments/d39939765e435951"
    test_buy_hash = "d39939765e435951ea3bbb5cf620368d4fd1b4562c28e41e311e9dceab436112"
    
    generator = ProofPackageGenerator()
    
    print("=== 测试证明包生成 ===")
    result = generator.create_proof_package(
        user_address=test_user_address,
        experiment_dir=test_experiment_dir,
        buy_hash=test_buy_hash
    )
    
    if result["status"] == "success":
        print(f"✅ 测试成功，生成包: {result['package_name']}")
        print(f"   大小: {result['package_size_mb']:.2f} MB")
        print(f"   路径: {result['package_path']}")
    else:
        print(f"❌ 测试失败: {result['error']}")
    
    print("\n=== 列出可用包 ===")
    packages = generator.list_available_packages(test_user_address)
    for pkg in packages:
        print(f"📦 {pkg['filename']} - {pkg['size_mb']:.2f}MB") 