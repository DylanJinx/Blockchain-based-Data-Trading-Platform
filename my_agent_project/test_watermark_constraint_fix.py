#!/usr/bin/env python3

import requests
import json
import time
import os
import shutil

def create_test_dataset_with_matching_watermark():
    """创建一个包含匹配水印的测试数据集"""
    # 首先复制现有的数据集
    source_dir = "/Users/dylan/Code_Projects/Python_Projects/image_similarity/my_agent_project/features/../data/dataset"
    test_dir = "/Users/dylan/Code_Projects/Python_Projects/image_similarity/my_agent_project/features/../data/test_watermark_dataset"
    
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
    
    shutil.copytree(source_dir, test_dir)
    
    # 修改watermark_info.json，让它包含我们数据集中的一个哈希值
    watermark_info_path = os.path.join(test_dir, "watermark_info.json")
    
    # 使用数据集中存在的哈希值
    matching_hash = "72f490a068a8b13e6c059cbde984d91561f51404fa9de4a15a6b8bdea85f04a3"
    
    watermark_info = {
        "buy_hash": matching_hash
    }
    
    with open(watermark_info_path, "w") as f:
        json.dump(watermark_info, f)
    
    print(f"创建了测试数据集: {test_dir}")
    print(f"设置匹配哈希: {matching_hash}")
    
    return test_dir

def test_watermark_constraint_calculation():
    """
    测试水印检测流程中的约束计算问题
    """
    
    # 创建包含匹配水印的测试数据集
    test_dataset_dir = create_test_dataset_with_matching_watermark()
    
    # 先直接测试水印检测
    print(f"\n=== 先测试水印检测脚本 ===")
    try:
        import subprocess
        cmd = ["python", "checkForWatermark.py", "--input", test_dataset_dir, "--verbose"]
        result = subprocess.run(cmd, cwd="features", capture_output=True, text=True)
        print(f"水印检测输出: {result.stdout}")
        print(f"退出码: {result.returncode}")
    except Exception as e:
        print(f"水印检测测试失败: {e}")
    
    # 现在测试API
    metadata_url = "http://127.0.0.1:8080/ipfs/QmV159Xx5SRGbErJiodqjno4Mp6DmfNeTMpFeVRab2F5Aw"
    user_address = "0x15d34AAf54267DB7D7c367839AAf71A00a2C6A65"
    
    # API端点
    api_url = "http://localhost:8765/api/register-data"
    
    print(f"\n=== 测试API水印检测流程中的约束计算 ===")
    print(f"  Metadata URL: {metadata_url}")
    print(f"  User Address: {user_address}")
    print(f"  API URL: {api_url}")
    
    # 发送请求
    try:
        print(f"\n发送登记请求...")
        
        payload = {
            "metadata_url": metadata_url,
            "user_address": user_address
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
            
            if status == "copyright_violation":
                print(f"\n✅ 检测到水印，返回了正确的侵权状态")
                print(f"✅ 约束幂次: {data.get('constraint_power', 'N/A')}")
                
                # 检查约束是否合理（应该是19而不是20）
                constraint_power = data.get("constraint_power")
                if constraint_power == 19:
                    print(f"✅ 约束计算正确：2^{constraint_power} = {2**constraint_power}")
                elif constraint_power == 20:
                    print(f"❌ 约束计算仍有问题：强制使用了2^{constraint_power} = {2**constraint_power}")
                    print(f"   预期应该是2^19 = {2**19}")
                else:
                    print(f"⚠️  约束幂次为 {constraint_power}，需要验证是否合理")
                    
                # 检查ptau_info
                ptau_info = data.get("ptau_info", {})
                if ptau_info:
                    optimal_config = ptau_info.get("optimal_config", {})
                    if optimal_config:
                        power = optimal_config.get("power")
                        constraint_size = optimal_config.get("constraint_size")
                        print(f"✅ ptau_info中的配置: 2^{power} = {constraint_size}")
                        
                        if power == 19:
                            print(f"✅ ptau_info中的约束计算正确")
                        elif power == 20:
                            print(f"❌ ptau_info中的约束计算仍有问题")
                        
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
    finally:
        # 清理测试数据集
        if os.path.exists(test_dataset_dir):
            shutil.rmtree(test_dataset_dir)
            print(f"\n已清理测试数据集: {test_dataset_dir}")

if __name__ == "__main__":
    print("=== 测试水印检测流程中的约束计算问题 ===")
    test_watermark_constraint_calculation() 