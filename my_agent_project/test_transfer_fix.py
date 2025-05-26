#!/usr/bin/env python3

import requests
import json
import time

def test_check_register_status():
    """
    测试check-register-status端点在检测到转账后能否启动铸造流程
    """
    
    # 使用现有状态文件中的参数
    metadata_url = "http://127.0.0.1:8080/ipfs/QmdPUNbMwE6wCatVZ4fxdoZbk12jEVhqQGBjqrR9o5WVQN"
    user_address = "0x15d34AAf54267DB7D7c367839AAf71A00a2C6A65"
    
    # API端点
    api_url = "http://localhost:8765/api/check-register-status"
    
    print(f"测试参数:")
    print(f"  Metadata URL: {metadata_url}")
    print(f"  User Address: {user_address}")
    print(f"  API URL: {api_url}")
    
    # 发送请求
    try:
        print(f"\n发送请求到 {api_url}...")
        
        payload = {
            "metadata_url": metadata_url,
            "user_address": user_address
        }
        
        response = requests.post(api_url, json=payload, timeout=30)
        
        print(f"HTTP状态码: {response.status_code}")
        print(f"响应内容:")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
        
        # 分析响应
        if response.status_code == 200:
            data = response.json()
            status = data.get("status")
            
            if status == "processing":
                print(f"\n✅ 状态正确: {status}")
                if "minting_session_id" in data:
                    print(f"✅ 铸造会话ID已返回: {data['minting_session_id']}")
                else:
                    print(f"ℹ️  没有返回铸造会话ID，可能是其他处理中状态")
            elif status == "success":
                print(f"✅ NFT已经铸造成功")
                print(f"Token ID: {data.get('token_id')}")
            else:
                print(f"⚠️  意外状态: {status}")
        else:
            print(f"❌ 请求失败，状态码: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 请求异常: {e}")
    except Exception as e:
        print(f"❌ 其他错误: {e}")

if __name__ == "__main__":
    print("=== 测试转账检测和铸造流程启动修复 ===")
    test_check_register_status() 