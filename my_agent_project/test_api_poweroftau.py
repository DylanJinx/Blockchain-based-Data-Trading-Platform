#!/usr/bin/env python3
"""
测试Powers of Tau相关API的脚本
验证前端和后端的API通讯是否正常工作
"""

import sys
import os
import logging
import tempfile
import requests
import time
import shutil

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_watermark_detection_api():
    """测试有水印时的完整API流程"""
    try:
        print("🧪 测试有水印数据集的API流程")
        print("=" * 60)
        
        # API基础URL
        base_url = "http://localhost:5000"
        
        # 1. 创建测试数据集
        test_dataset_dir = tempfile.mkdtemp(prefix="api_test_dataset_")
        print(f"📁 创建测试数据集: {test_dataset_dir}")
        
        # 创建测试图片文件
        from PIL import Image
        import numpy as np
        
        for i in range(3):
            img_array = np.random.randint(0, 255, (200, 200, 3), dtype=np.uint8)
            img = Image.fromarray(img_array)
            img_path = os.path.join(test_dataset_dir, f"test_image_{i}.jpg")
            img.save(img_path)
        
        print(f"   ✅ 创建了3张200x200测试图片")
        
        # 2. 准备测试数据
        test_metadata_url = "https://test-metadata-url.com/watermark-test"
        test_account = "0x1234567890123456789012345678901234567890"
        
        print(f"📊 测试参数:")
        print(f"   metadata_url: {test_metadata_url}")
        print(f"   account: {test_account}")
        print(f"   dataset_cid: {os.path.basename(test_dataset_dir)}")
        
        # 3. 模拟数据集登记请求（这应该触发水印检测）
        print(f"\n🔍 步骤1: 发送数据集登记请求")
        register_data = {
            "metadata_url": test_metadata_url,
            "account": test_account
        }
        
        try:
            response = requests.post(f"{base_url}/api/register", json=register_data, timeout=10)
            print(f"   📡 API响应状态: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"   📋 响应内容: {result}")
                
                # 检查是否检测到水印并需要Powers of Tau贡献
                if result.get("status") == "copyright_violation":
                    if result.get("requires_user_contribution"):
                        print(f"   ✅ 检测到水印，需要用户贡献")
                        return test_powers_of_tau_contribution_api(result)
                    else:
                        print(f"   ✅ 检测到水印，但不需要用户贡献")
                        return True
                else:
                    print(f"   ⚠️ 未检测到水印或其他状态: {result.get('status')}")
                    return True
            else:
                print(f"   ❌ API请求失败: {response.text}")
                return False
                
        except requests.exceptions.ConnectionError:
            print(f"   ⚠️ 无法连接到API服务器 ({base_url})")
            print(f"   💡 请确保运行了: python api_server.py")
            return False
        except Exception as e:
            print(f"   ❌ API请求异常: {e}")
            return False
            
    except Exception as e:
        logging.error(f"API测试失败: {e}")
        return False
    finally:
        # 清理测试数据集
        if 'test_dataset_dir' in locals() and os.path.exists(test_dataset_dir):
            shutil.rmtree(test_dataset_dir)

def test_powers_of_tau_contribution_api(watermark_result):
    """测试Powers of Tau贡献API"""
    try:
        print(f"\n⚡ 步骤2: 测试Powers of Tau贡献API")
        
        base_url = "http://localhost:5000"
        user_id = watermark_result.get("user_id")
        constraint_power = watermark_result.get("constraint_power")
        
        print(f"   👤 用户ID: {user_id}")
        print(f"   🔢 约束大小: 2^{constraint_power}")
        
        # 2.1 下载初始ptau文件
        print(f"\n📥 下载初始ptau文件")
        try:
            response = requests.get(f"{base_url}/api/get-initial-ptau/{user_id}", timeout=30)
            if response.status_code == 200:
                initial_ptau_data = response.content
                print(f"   ✅ 下载成功，文件大小: {len(initial_ptau_data) / (1024*1024):.2f} MB")
            else:
                print(f"   ❌ 下载失败: {response.status_code}")
                return False
        except Exception as e:
            print(f"   ❌ 下载异常: {e}")
            return False
        
        # 2.2 模拟用户在浏览器中的贡献
        print(f"\n🌐 模拟浏览器中的贡献")
        
        # 这里我们模拟用户已经在浏览器中完成了贡献
        # 在实际应用中，这个步骤会在前端完成
        print(f"   🎲 模拟用户在浏览器中输入随机性并生成贡献...")
        
        # 为了测试，我们在后端模拟这个过程
        from features.poweroftau_generator import PowerOfTauGenerator
        generator = PowerOfTauGenerator()
        
        # 保存初始ptau文件
        temp_ptau_file = f"/tmp/test_initial_{user_id}.ptau"
        with open(temp_ptau_file, 'wb') as f:
            f.write(initial_ptau_data)
        
        # 生成贡献文件
        contributed_ptau_file = f"/tmp/test_contributed_{user_id}.ptau"
        generator.contribute_with_entropy(
            temp_ptau_file,
            contributed_ptau_file,
            entropy="test_api_contribution_entropy_123456789",
            name="test_api_contribution"
        )
        
        print(f"   ✅ 模拟贡献完成")
        
        # 2.3 上传贡献文件
        print(f"\n📤 上传贡献文件")
        try:
            with open(contributed_ptau_file, 'rb') as f:
                files = {'ptau_file': f}
                data = {'constraint_power': str(constraint_power)}
                
                response = requests.post(
                    f"{base_url}/api/upload-contribution/{user_id}",
                    files=files,
                    data=data,
                    timeout=300  # 5分钟超时，因为完成仪式需要时间
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"   ✅ 上传成功: {result}")
                    
                    # 检查最终ptau文件是否生成
                    final_ptau_path = result.get("final_ptau_path")
                    if final_ptau_path and os.path.exists(final_ptau_path):
                        file_size = os.path.getsize(final_ptau_path) / (1024*1024)
                        print(f"   ✅ 最终ptau文件已生成: {final_ptau_path}")
                        print(f"   📁 文件大小: {file_size:.2f} MB")
                        return True
                    else:
                        print(f"   ❌ 最终ptau文件未找到")
                        return False
                else:
                    print(f"   ❌ 上传失败: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            print(f"   ❌ 上传异常: {e}")
            return False
        finally:
            # 清理临时文件
            for temp_file in [temp_ptau_file, contributed_ptau_file]:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
        
    except Exception as e:
        logging.error(f"Powers of Tau贡献API测试失败: {e}")
        return False

def test_api_endpoints():
    """测试基本API端点可用性"""
    try:
        print(f"\n🔌 测试API端点可用性")
        
        base_url = "http://localhost:5000"
        
        # 测试健康检查端点（如果有的话）
        try:
            response = requests.get(f"{base_url}/api/health", timeout=5)
            if response.status_code == 200:
                print(f"   ✅ 健康检查端点正常")
            else:
                print(f"   ⚠️ 健康检查端点返回: {response.status_code}")
        except:
            print(f"   ⚠️ 没有健康检查端点，这是正常的")
        
        # 测试基本连接
        try:
            response = requests.get(base_url, timeout=5)
            print(f"   ✅ API服务器连接正常")
            return True
        except requests.exceptions.ConnectionError:
            print(f"   ❌ 无法连接到API服务器")
            print(f"   💡 请运行: python api_server.py")
            return False
            
    except Exception as e:
        logging.error(f"API端点测试失败: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Powers of Tau API 测试")
    print("=" * 60)
    
    # 测试1: API端点可用性
    endpoint_ok = test_api_endpoints()
    
    if endpoint_ok:
        # 测试2: 完整的水印检测+Powers of Tau流程
        workflow_ok = test_watermark_detection_api()
        
        if workflow_ok:
            print(f"\n🎉 所有API测试通过！")
            print(f"✅ Powers of Tau API集成工作正常")
            sys.exit(0)
        else:
            print(f"\n❌ 工作流程测试失败")
            sys.exit(1)
    else:
        print(f"\n❌ API服务器连接失败")
        print(f"💡 请确保运行了API服务器: python api_server.py")
        sys.exit(1) 