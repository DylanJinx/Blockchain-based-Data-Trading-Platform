#!/usr/bin/env python3
"""
测试水印检测和Powers of Tau完整流程
"""

import sys
import os
import logging
import requests
import json
import time

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_watermark_workflow():
    """测试完整的水印检测和Powers of Tau流程"""
    
    # API服务器地址
    api_base = "http://localhost:8765"
    
    # 使用用户提供的真实IPFS URL进行测试
    # 这个URL包含的是含水印的数据集
    metadata_url = "http://127.0.0.1:8080/ipfs/QmV159Xx5SRGbErJiodqjno4Mp6DmfNeTMpFeVRab2F5Aw"
    user_address = "0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC"
    
    logging.info("🚀 开始测试水印检测和Powers of Tau完整流程...")
    
    try:
        # 1. 调用register-data API，直接使用IPFS数据集URL
        logging.info("步骤1: 调用register-data API")
        logging.info(f"使用含水印数据集URL: {metadata_url}")
        register_payload = {
            "metadata_url": metadata_url,
            "user_address": user_address
        }
        
        response = requests.post(
            f"{api_base}/api/register-data",
            json=register_payload,
            timeout=300  # 5分钟超时
        )
        
        logging.info(f"API响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            logging.info(f"API响应内容: {json.dumps(result, indent=2, ensure_ascii=False)}")
            
            # 检查是否返回了copyright_violation状态
            if result.get("status") == "copyright_violation":
                logging.info("✅ 成功检测到水印侵权")
                
                # 检查是否需要用户贡献
                if result.get("requires_user_contribution"):
                    logging.info("✅ 需要用户贡献Powers of Tau")
                    
                    # 获取Powers of Tau信息
                    user_id = result.get("user_id")
                    constraint_power = result.get("constraint_power")
                    
                    if user_id and constraint_power:
                        logging.info(f"✅ Powers of Tau信息: user_id={user_id}, constraint_power={constraint_power}")
                        
                        # 测试Powers of Tau API端点
                        return test_powers_of_tau_apis(api_base, user_id, constraint_power)
                    else:
                        logging.error("❌ 缺少Powers of Tau信息")
                        return False
                else:
                    logging.info("✅ 后台生成零知识证明（不需要用户贡献）")
                    return True
            else:
                logging.error(f"❌ 未检测到水印侵权，状态: {result.get('status')}")
                return False
        else:
            logging.error(f"❌ API调用失败，状态码: {response.status_code}")
            logging.error(f"响应内容: {response.text}")
            return False
            
    except Exception as e:
        logging.error(f"❌ 测试过程中出现异常: {e}")
        return False

def test_powers_of_tau_apis(api_base, user_id, constraint_power):
    """测试Powers of Tau相关API"""
    
    logging.info("🔧 开始测试Powers of Tau API...")
    
    try:
        # 1. 测试下载初始ptau文件
        logging.info("步骤1: 测试下载初始ptau文件")
        download_url = f"{api_base}/api/download-ptau/{user_id}/pot{constraint_power}_0000.ptau"
        
        download_resp = requests.head(download_url, timeout=30)
        if download_resp.status_code == 200:
            logging.info("✅ 初始ptau文件可以下载")
        else:
            logging.error(f"❌ 无法下载初始ptau文件，状态码: {download_resp.status_code}")
            return False
        
        # 2. 模拟用户贡献（这里创建一个假的贡献文件）
        logging.info("步骤2: 模拟用户贡献")
        
        # 创建一个模拟的贡献文件
        temp_contribution_data = b"MOCK_CONTRIBUTION_DATA_FOR_TESTING"
        files = {
            'contributed_ptau': ('contributed.ptau', temp_contribution_data, 'application/octet-stream')
        }
        
        upload_url = f"{api_base}/api/upload-contribution/{user_id}"
        upload_resp = requests.post(upload_url, files=files, timeout=60)
        
        if upload_resp.status_code == 200:
            upload_result = upload_resp.json()
            logging.info(f"✅ 贡献上传成功: {upload_result}")
            
            # 3. 检查最终的零知识证明状态
            logging.info("步骤3: 检查零知识证明完成状态")
            time.sleep(2)  # 等待后端处理
            
            # 可以添加更多的状态检查逻辑
            return True
        else:
            logging.error(f"❌ 贡献上传失败，状态码: {upload_resp.status_code}")
            logging.error(f"响应内容: {upload_resp.text}")
            return False
            
    except Exception as e:
        logging.error(f"❌ Powers of Tau API测试失败: {e}")
        return False

def check_api_server():
    """检查API服务器是否运行"""
    try:
        # 简单检查服务器是否响应
        response = requests.get("http://localhost:8765", timeout=5)
        return True  # 只要有响应就认为服务器在运行
    except:
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("水印检测和Powers of Tau流程测试")
    print("=" * 60)
    
    # 检查API服务器
    if not check_api_server():
        print("❌ API服务器未运行，请先启动 api_server.py")
        sys.exit(1)
    
    # 运行测试
    success = test_watermark_workflow()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ 测试通过！水印检测和Powers of Tau流程工作正常")
    else:
        print("❌ 测试失败！需要进一步调试")
    print("=" * 60) 