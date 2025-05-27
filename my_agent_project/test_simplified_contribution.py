#!/usr/bin/env python3

import requests
import json
import time

def test_simplified_contribution():
    """
    测试简化的Powers of Tau贡献端点
    """
    
    # 测试参数
    user_id = "testuser123"
    constraint_power = 10  # 使用较小的约束大小进行测试
    
    # 模拟前端收集的随机性数据
    test_entropy = json.dumps({
        "userInput": "这是一个测试的随机输入字符串，包含一些中文和数字123456",
        "mouseMovements": [
            {"x": 100, "y": 200, "timestamp": 1000},
            {"x": 150, "y": 250, "timestamp": 1500},
            {"x": 200, "y": 300, "timestamp": 2000}
        ],
        "keyboardEvents": [
            {"key": "a", "timestamp": 3000, "keyCode": 65},
            {"key": "b", "timestamp": 3500, "keyCode": 66}
        ],
        "timestamp": time.time(),
        "userAgent": "test-browser",
        "screenInfo": {"width": 1920, "height": 1080},
        "randomValues": [0.123, 0.456, 0.789]
    })
    
    # API端点
    api_url = "http://localhost:8765/api/contribute-with-entropy"
    
    print(f"测试简化的Powers of Tau贡献功能")
    print(f"  用户ID: {user_id}")
    print(f"  约束大小: 2^{constraint_power} = {2**constraint_power}")
    print(f"  随机性数据长度: {len(test_entropy)} 字符")
    print(f"  API URL: {api_url}")
    
    # 发送请求
    try:
        print(f"\n发送贡献请求...")
        
        payload = {
            "user_id": user_id,
            "constraint_power": constraint_power,
            "entropy": test_entropy
        }
        
        start_time = time.time()
        response = requests.post(api_url, json=payload, timeout=300)  # 5分钟超时
        elapsed_time = time.time() - start_time
        
        print(f"HTTP状态码: {response.status_code}")
        print(f"请求耗时: {elapsed_time:.2f} 秒")
        print(f"响应内容:")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
        
        # 分析响应
        if response.status_code == 200:
            data = response.json()
            status = data.get("status")
            
            if status == "success":
                print(f"\n✅ Powers of Tau贡献成功！")
                print(f"✅ 最终ptau文件: {data.get('final_ptau_path', 'N/A')}")
                print(f"✅ 使用的随机性长度: {data.get('entropy_used', 'N/A')}")
                print(f"✅ 贡献哈希前缀: {data.get('contribution_hash', 'N/A')}")
            else:
                print(f"⚠️  意外状态: {status}")
        else:
            print(f"❌ 请求失败，状态码: {response.status_code}")
            
    except requests.exceptions.Timeout:
        print(f"❌ 请求超时（超过5分钟）")
    except requests.exceptions.RequestException as e:
        print(f"❌ 请求异常: {e}")
    except Exception as e:
        print(f"❌ 其他错误: {e}")

if __name__ == "__main__":
    print("=== 测试简化的Powers of Tau贡献功能 ===")
    test_simplified_contribution() 