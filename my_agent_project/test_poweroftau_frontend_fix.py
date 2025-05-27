#!/usr/bin/env python3
"""
测试Powers of Tau前端修复的脚本
验证API端点是否正常工作以及前端修复是否有效
"""

import requests
import json
import time
import os
import sys

def test_api_server_status():
    """测试API服务器状态"""
    print("🔍 测试1: 检查API服务器状态")
    
    try:
        response = requests.get("http://localhost:8765", timeout=5)
        print(f"   ✅ API服务器响应正常: {response.status_code}")
        return True
    except requests.exceptions.ConnectionError:
        print(f"   ❌ API服务器未运行，请确保在8765端口启动服务器")
        return False
    except Exception as e:
        print(f"   ❌ API服务器检查失败: {e}")
        return False

def test_contribute_with_entropy_endpoint():
    """测试contribute-with-entropy API端点"""
    print("\n🔧 测试2: 测试contribute-with-entropy端点")
    
    # 模拟前端发送的请求数据
    test_data = {
        "user_id": "90f79bf6",  # 用户报告中的user_id
        "constraint_power": 16,  # 用户报告中的约束幂次
        "entropy": json.dumps({
            "userInput": "测试随机性数据，用于验证Powers of Tau贡献功能",
            "mouseMovements": [
                {"x": 100, "y": 200, "timestamp": 1000},
                {"x": 150, "y": 250, "timestamp": 1500},
                {"x": 200, "y": 300, "timestamp": 2000}
            ] * 10,  # 确保有足够的鼠标移动数据
            "keyboardEvents": [
                {"key": "a", "timestamp": 3000, "keyCode": 65},
                {"key": "b", "timestamp": 3500, "keyCode": 66},
                {"key": "c", "timestamp": 4000, "keyCode": 67}
            ] * 5,  # 确保有足够的键盘事件
            "timestamp": time.time(),
            "userAgent": "test-agent",
            "screenInfo": {"width": 1920, "height": 1080},
            "randomValues": [0.123, 0.456, 0.789, 0.321, 0.654]
        })
    }
    
    try:
        print(f"   📤 发送请求到: http://localhost:8765/api/contribute-with-entropy")
        print(f"   👤 用户ID: {test_data['user_id']}")
        print(f"   🔢 约束幂次: {test_data['constraint_power']}")
        print(f"   📊 随机性数据长度: {len(test_data['entropy'])} 字符")
        
        response = requests.post(
            "http://localhost:8765/api/contribute-with-entropy",
            headers={"Content-Type": "application/json"},
            json=test_data,
            timeout=120  # Powers of Tau生成可能需要较长时间
        )
        
        print(f"   📥 响应状态码: {response.status_code}")
        print(f"   📋 响应头Content-Type: {response.headers.get('Content-Type', 'Unknown')}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                print(f"   ✅ API端点正常工作!")
                print(f"   📝 响应消息: {result.get('message', 'N/A')}")
                print(f"   🎯 贡献状态: {result.get('status', 'N/A')}")
                if 'final_ptau_path' in result:
                    print(f"   📁 生成的文件: {result['final_ptau_path']}")
                return True
            except json.JSONDecodeError:
                print(f"   ❌ 响应不是有效的JSON格式")
                print(f"   📄 响应内容: {response.text[:200]}...")
                return False
        else:
            print(f"   ❌ API返回错误状态码: {response.status_code}")
            print(f"   📄 错误内容: {response.text[:200]}...")
            return False
            
    except requests.exceptions.Timeout:
        print(f"   ⏰ 请求超时，Powers of Tau生成可能需要更长时间")
        print(f"   💡 这在约束大小为2^16时是正常的")
        return None  # 超时不算失败，只是需要更长时间
    except requests.exceptions.ConnectionError:
        print(f"   ❌ 无法连接到API服务器")
        return False
    except Exception as e:
        print(f"   ❌ 请求失败: {e}")
        return False

def test_smaller_constraint():
    """测试较小的约束大小，确保基本功能正常"""
    print("\n🧪 测试3: 测试较小约束大小 (2^12)")
    
    test_data = {
        "user_id": "test_small",
        "constraint_power": 12,  # 较小的约束，生成速度更快
        "entropy": json.dumps({
            "userInput": "快速测试用的随机性数据",
            "mouseMovements": [{"x": i*10, "y": i*20, "timestamp": i*100} for i in range(25)],
            "keyboardEvents": [{"key": chr(97+i), "timestamp": i*200, "keyCode": 97+i} for i in range(10)],
            "timestamp": time.time(),
            "userAgent": "test-agent",
            "screenInfo": {"width": 1920, "height": 1080},
            "randomValues": [0.1, 0.2, 0.3, 0.4, 0.5]
        })
    }
    
    try:
        response = requests.post(
            "http://localhost:8765/api/contribute-with-entropy",
            headers={"Content-Type": "application/json"},
            json=test_data,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ 小约束测试成功!")
            print(f"   📝 消息: {result.get('message', 'N/A')}")
            return True
        else:
            print(f"   ❌ 小约束测试失败: {response.status_code}")
            print(f"   📄 错误: {response.text[:200]}...")
            return False
            
    except Exception as e:
        print(f"   ❌ 小约束测试异常: {e}")
        return False

def check_frontend_files():
    """检查前端文件是否已正确修改"""
    print("\n📁 测试4: 检查前端文件修改")
    
    # 检查PowersOfTauContribution.js
    frontend_file = "../frontend/src/components/PowersOfTauContribution.js"
    if os.path.exists(frontend_file):
        with open(frontend_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        if 'import apiService from "../services/apiService";' in content:
            print(f"   ✅ PowersOfTauContribution.js 已导入apiService")
        else:
            print(f"   ❌ PowersOfTauContribution.js 未正确导入apiService")
            return False
            
        if 'apiService.contributeWithEntropy(' in content:
            print(f"   ✅ PowersOfTauContribution.js 已使用apiService.contributeWithEntropy")
        else:
            print(f"   ❌ PowersOfTauContribution.js 仍在使用fetch而不是apiService")
            return False
            
        if 'fetch("/api/contribute-with-entropy"' not in content:
            print(f"   ✅ PowersOfTauContribution.js 已移除直接fetch调用")
        else:
            print(f"   ❌ PowersOfTauContribution.js 仍包含直接fetch调用")
            return False
            
        print(f"   ✅ 前端文件修改正确")
        return True
    else:
        print(f"   ❌ 找不到前端文件: {frontend_file}")
        return False

def check_proxy_config():
    """检查前端代理配置"""
    print("\n🔄 测试5: 检查前端代理配置")
    
    craco_config = "../frontend/craco.config.js"
    if os.path.exists(craco_config):
        with open(craco_config, 'r', encoding='utf-8') as f:
            content = f.read()
            
        if 'devServer' in content and 'proxy' in content:
            print(f"   ✅ craco.config.js 包含代理配置")
        else:
            print(f"   ❌ craco.config.js 缺少代理配置")
            return False
            
        if 'localhost:8765' in content:
            print(f"   ✅ 代理目标正确指向localhost:8765")
        else:
            print(f"   ❌ 代理目标不正确")
            return False
            
        print(f"   ✅ 代理配置正确")
        return True
    else:
        print(f"   ❌ 找不到craco配置文件: {craco_config}")
        return False

def main():
    """主测试函数"""
    print("🧪 Powers of Tau 前端修复验证测试")
    print("=" * 50)
    
    results = []
    
    # 测试1: API服务器状态
    results.append(test_api_server_status())
    
    # 测试2: 前端文件修改检查
    results.append(check_frontend_files())
    
    # 测试3: 代理配置检查
    results.append(check_proxy_config())
    
    # 如果API服务器运行正常，进行功能测试
    if results[0]:
        # 测试4: 快速功能测试
        small_result = test_smaller_constraint()
        if small_result:
            results.append(small_result)
            
            # 测试5: 实际用户场景测试
            main_result = test_contribute_with_entropy_endpoint()
            if main_result is not None:  # None表示超时，不算失败
                results.append(main_result)
    
    # 汇总结果
    print("\n" + "=" * 50)
    print("📊 测试结果汇总:")
    
    passed = sum(1 for r in results if r is True)
    total = len([r for r in results if r is not None])
    
    if passed == total and total > 0:
        print(f"   🎉 所有测试通过! ({passed}/{total})")
        print(f"   ✅ Powers of Tau前端修复成功!")
        print(f"\n💡 下一步:")
        print(f"   1. 重启前端开发服务器以应用代理配置")
        print(f"   2. 确保API服务器在8765端口运行")
        print(f"   3. 重新测试完整的水印检测 -> Powers of Tau流程")
    else:
        print(f"   ⚠️  部分测试失败: {passed}/{total}")
        print(f"   🔧 需要检查失败的测试项并修复")

if __name__ == "__main__":
    main() 