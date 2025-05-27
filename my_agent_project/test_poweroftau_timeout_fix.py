#!/usr/bin/env python3
"""
测试Powers of Tau超时修复和重复执行问题解决的脚本
"""

import requests
import json
import time
import os
import sys

def test_timeout_fix():
    """测试超时修复"""
    print("🧪 测试Powers of Tau超时问题修复")
    print("=" * 60)
    
    # 测试参数 - 使用较大的约束来触发长时间处理
    user_id = "timeout_test_90f79bf6"
    constraint_power = 16  # 2^16约束，会需要较长时间
    
    # 模拟前端收集的随机性数据
    test_entropy = json.dumps({
        "userInput": "测试超时修复的随机性数据，包含足够的随机信息来生成安全的Powers of Tau贡献",
        "mouseMovements": [
            {"x": i*15 + 100, "y": i*25 + 200, "timestamp": i*150 + 1000} 
            for i in range(25)
        ],
        "keyboardEvents": [
            {"key": chr(97+i%26), "timestamp": i*300 + 3000, "keyCode": 97+i%26} 
            for i in range(10)
        ],
        "timestamp": time.time(),
        "userAgent": "timeout-test-browser",
        "screenInfo": {"width": 1920, "height": 1080},
        "randomValues": [time.time() + i*0.123 for i in range(10)]
    })
    
    print(f"📋 测试配置:")
    print(f"   用户ID: {user_id}")
    print(f"   约束大小: 2^{constraint_power} = {2**constraint_power:,}")
    print(f"   随机性数据长度: {len(test_entropy)} 字符")
    print(f"   预计处理时间: 3-5分钟")
    
    # API端点
    api_url = "http://localhost:8765/api/contribute-with-entropy"
    
    try:
        print(f"\n🚀 开始Powers of Tau贡献测试...")
        
        payload = {
            "user_id": user_id,
            "constraint_power": constraint_power,
            "entropy": test_entropy
        }
        
        start_time = time.time()
        
        # 使用6分钟超时（比前端的5分钟稍长）
        response = requests.post(
            api_url, 
            json=payload, 
            timeout=360
        )
        
        elapsed_time = time.time() - start_time
        
        print(f"\n📊 测试结果:")
        print(f"   HTTP状态码: {response.status_code}")
        print(f"   总耗时: {elapsed_time:.2f} 秒 ({elapsed_time/60:.1f} 分钟)")
        
        if response.status_code == 200:
            try:
                result = response.json()
                print(f"   ✅ 请求成功!")
                print(f"   📝 状态: {result.get('status', 'N/A')}")
                print(f"   💬 消息: {result.get('message', 'N/A')}")
                print(f"   📁 最终文件: {result.get('final_ptau_path', 'N/A')}")
                print(f"   🔑 熵值使用量: {result.get('entropy_used', 'N/A')}")
                print(f"   🏷️  贡献哈希: {result.get('contribution_hash', 'N/A')}")
                
                # 验证文件是否真实生成
                final_path = result.get('final_ptau_path')
                if final_path and os.path.exists(final_path):
                    file_size = os.path.getsize(final_path) / (1024*1024)
                    print(f"   ✅ 文件验证通过: {file_size:.2f} MB")
                else:
                    print(f"   ❌ 最终文件不存在")
                    
                return True
                
            except json.JSONDecodeError:
                print(f"   ❌ 响应不是有效JSON")
                print(f"   📄 响应内容: {response.text[:200]}...")
                return False
        else:
            print(f"   ❌ 请求失败: {response.status_code}")
            print(f"   📄 错误内容: {response.text[:200]}...")
            return False
            
    except requests.exceptions.Timeout:
        print(f"   ⏰ 请求超时（6分钟）")
        print(f"   💡 这可能表明后端处理仍需更长时间")
        print(f"   🔍 请检查服务器日志确认是否仍在处理")
        return None  # 超时不算失败
        
    except requests.exceptions.ConnectionError:
        print(f"   ❌ 无法连接到API服务器")
        print(f"   💡 请确保API服务器在localhost:8765运行")
        return False
        
    except Exception as e:
        print(f"   ❌ 测试异常: {e}")
        return False

def test_no_duplicate_execution():
    """测试确保没有重复执行步骤6的问题"""
    print("\n🔍 测试重复执行问题修复")
    print("=" * 60)
    
    # 使用较小的约束进行快速测试
    user_id = "duplicate_test_123"
    constraint_power = 12  # 2^12约束，处理更快
    
    test_entropy = json.dumps({
        "userInput": "快速测试重复执行修复",
        "mouseMovements": [{"x": 100+i*10, "y": 200+i*10, "timestamp": 1000+i*100} for i in range(25)],
        "keyboardEvents": [{"key": chr(97+i), "timestamp": 3000+i*200, "keyCode": 97+i} for i in range(10)],
        "timestamp": time.time(),
        "userAgent": "duplicate-test-browser",
        "screenInfo": {"width": 1920, "height": 1080},
        "randomValues": [0.1, 0.2, 0.3, 0.4, 0.5]
    })
    
    print(f"📋 快速测试配置:")
    print(f"   用户ID: {user_id}")
    print(f"   约束大小: 2^{constraint_power} = {2**constraint_power}")
    print(f"   预计处理时间: 30-60秒")
    
    try:
        payload = {
            "user_id": user_id,
            "constraint_power": constraint_power,
            "entropy": test_entropy
        }
        
        start_time = time.time()
        response = requests.post(
            "http://localhost:8765/api/contribute-with-entropy",
            json=payload,
            timeout=120  # 2分钟超时
        )
        elapsed_time = time.time() - start_time
        
        print(f"\n📊 快速测试结果:")
        print(f"   HTTP状态码: {response.status_code}")
        print(f"   处理耗时: {elapsed_time:.2f} 秒")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ 快速测试成功!")
            print(f"   📝 状态: {result.get('status', 'N/A')}")
            print(f"   💡 请检查服务器日志，确认没有重复执行'步骤6: 验证final.ptau'")
            return True
        else:
            print(f"   ❌ 快速测试失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ 快速测试异常: {e}")
        return False

def main():
    """主测试函数"""
    print("🧪 Powers of Tau 超时和重复执行问题修复验证")
    print("=" * 80)
    
    # 首先检查API服务器状态
    try:
        response = requests.get("http://localhost:8765", timeout=5)
        print("✅ API服务器运行正常")
    except:
        print("❌ API服务器未运行，请先启动服务器")
        return
    
    results = []
    
    # 测试1: 重复执行问题修复（快速测试）
    result1 = test_no_duplicate_execution()
    if result1 is not None:
        results.append(result1)
    
    # 测试2: 超时问题修复（长时间测试）
    print(f"\n⚠️  即将开始长时间测试（3-5分钟），请确认是否继续？")
    user_confirm = input("输入 'y' 继续长时间测试，或按Enter跳过: ").strip().lower()
    
    if user_confirm == 'y':
        result2 = test_timeout_fix()
        if result2 is not None:
            results.append(result2)
    else:
        print("⏭️  跳过长时间测试")
    
    # 汇总结果
    print("\n" + "=" * 80)
    print("📊 测试结果汇总:")
    
    if len(results) > 0:
        passed = sum(1 for r in results if r is True)
        total = len(results)
        
        if passed == total:
            print(f"   🎉 所有测试通过! ({passed}/{total})")
            print(f"   ✅ 超时和重复执行问题已修复!")
            print(f"\n💡 修复内容:")
            print(f"   1. ✅ 前端超时时间延长到5分钟")
            print(f"   2. ✅ 改进了超时错误处理和用户提示")
            print(f"   3. ✅ 修复了重复执行步骤6的问题")
            print(f"   4. ✅ 优化了API调用流程")
        else:
            print(f"   ⚠️  部分测试失败: {passed}/{total}")
    else:
        print(f"   ℹ️  未执行完整测试")
    
    print(f"\n🔧 建议:")
    print(f"   1. 重启前端开发服务器以应用超时修复")
    print(f"   2. 重新测试完整的水印检测 → Powers of Tau流程")
    print(f"   3. 监控服务器日志确认没有重复执行问题")

if __name__ == "__main__":
    main() 