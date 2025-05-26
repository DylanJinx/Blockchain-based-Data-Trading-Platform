#!/usr/bin/env python3
"""
验证水印检测和Powers of Tau流程修复的测试脚本
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

def test_watermark_copyright_violation_flow():
    """测试水印检测导致的侵权流程"""
    
    # API服务器地址
    api_base = "http://localhost:8765"
    
    # 测试数据 - 使用一个包含水印的元数据URL
    metadata_url = "https://ipfs.io/ipfs/QmTestHashWithWatermark"
    user_address = "0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC"
    
    logging.info("开始测试水印检测和Powers of Tau流程...")
    
    try:
        # 1. 调用register-data API
        logging.info("步骤1: 调用register-data API")
        register_payload = {
            "metadata_url": metadata_url,
            "user_address": user_address
        }
        
        response = requests.post(
            f"{api_base}/api/register-data",
            json=register_payload,
            timeout=30
        )
        
        logging.info(f"API响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            logging.info(f"API响应内容: {json.dumps(result, indent=2, ensure_ascii=False)}")
            
            # 验证响应状态
            if result.get("status") == "copyright_violation":
                logging.info("✅ 成功检测到侵权状态")
                
                # 验证必要字段
                required_fields = ["message", "requires_user_contribution", "user_id", "constraint_power"]
                missing_fields = [field for field in required_fields if field not in result]
                
                if missing_fields:
                    logging.error(f"❌ 缺少必要字段: {missing_fields}")
                    return False
                
                logging.info(f"✅ 用户ID: {result['user_id']}")
                logging.info(f"✅ 约束幂次: {result['constraint_power']}")
                logging.info(f"✅ 需要用户贡献: {result['requires_user_contribution']}")
                
                if result.get("requires_user_contribution"):
                    logging.info("✅ Powers of Tau流程已正确启动，等待用户贡献")
                    return True
                else:
                    logging.warning("⚠️ 未要求用户贡献，可能存在问题")
                    return False
                    
            elif result.get("status") == "waiting_for_transfer":
                logging.error("❌ 错误：应该检测到水印但返回了等待转账状态")
                return False
            else:
                logging.error(f"❌ 未知状态: {result.get('status')}")
                return False
                
        else:
            logging.error(f"❌ API调用失败，状态码: {response.status_code}")
            logging.error(f"响应内容: {response.text}")
            return False
            
    except Exception as e:
        logging.error(f"❌ 测试过程中出现异常: {e}")
        return False

def test_no_watermark_normal_flow():
    """测试无水印的正常登记流程"""
    
    # API服务器地址
    api_base = "http://localhost:8765"
    
    # 测试数据 - 使用一个不含水印的元数据URL
    metadata_url = "https://ipfs.io/ipfs/QmTestHashNoWatermark"
    user_address = "0x70997970C51812dc3A010C7d01b50e0d17dc79C8"
    
    logging.info("开始测试无水印的正常登记流程...")
    
    try:
        # 调用register-data API
        logging.info("步骤1: 调用register-data API")
        register_payload = {
            "metadata_url": metadata_url,
            "user_address": user_address
        }
        
        response = requests.post(
            f"{api_base}/api/register-data",
            json=register_payload,
            timeout=30
        )
        
        logging.info(f"API响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            logging.info(f"API响应内容: {json.dumps(result, indent=2, ensure_ascii=False)}")
            
            # 验证响应状态
            if result.get("status") == "waiting_for_transfer":
                logging.info("✅ 成功进入正常登记流程，等待转账")
                logging.info(f"✅ 代理地址: {result.get('agent_address')}")
                logging.info(f"✅ 需要转账: {result.get('required_eth')} ETH")
                return True
            elif result.get("status") == "copyright_violation":
                logging.error("❌ 错误：不应检测到水印但返回了侵权状态")
                return False
            else:
                logging.error(f"❌ 未知状态: {result.get('status')}")
                return False
                
        else:
            logging.error(f"❌ API调用失败，状态码: {response.status_code}")
            logging.error(f"响应内容: {response.text}")
            return False
            
    except Exception as e:
        logging.error(f"❌ 测试过程中出现异常: {e}")
        return False

def main():
    """主测试函数"""
    logging.info("=== 开始验证水印检测和Powers of Tau流程修复 ===")
    
    # 等待API服务器启动
    api_base = "http://localhost:8765"
    max_retries = 5
    for i in range(max_retries):
        try:
            response = requests.get(f"{api_base}/api/get-listed-nfts", timeout=5)
            if response.status_code in [200, 500]:  # 500也表示服务器在运行
                logging.info("✅ API服务器已启动")
                break
        except:
            logging.info(f"等待API服务器启动... ({i+1}/{max_retries})")
            time.sleep(2)
    else:
        logging.error("❌ 无法连接到API服务器，请确保api_server.py正在运行")
        return False
    
    # 运行测试
    test_results = []
    
    # 测试1: 水印侵权流程
    logging.info("\n" + "="*50)
    logging.info("测试1: 水印侵权检测流程")
    logging.info("="*50)
    result1 = test_watermark_copyright_violation_flow()
    test_results.append(("水印侵权流程", result1))
    
    # 测试2: 正常登记流程
    logging.info("\n" + "="*50)
    logging.info("测试2: 无水印正常登记流程")
    logging.info("="*50)
    result2 = test_no_watermark_normal_flow()
    test_results.append(("正常登记流程", result2))
    
    # 打印总结
    logging.info("\n" + "="*50)
    logging.info("测试结果总结")
    logging.info("="*50)
    
    all_passed = True
    for test_name, result in test_results:
        status = "✅ 通过" if result else "❌ 失败"
        logging.info(f"{test_name}: {status}")
        if not result:
            all_passed = False
    
    if all_passed:
        logging.info("\n🎉 所有测试通过！修复验证成功！")
        return True
    else:
        logging.error("\n💥 部分测试失败，需要进一步检查")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 