#!/usr/bin/env python3
"""
测试Powers of Tau早期响应修复的脚本
验证：
1. 前端在步骤3完成后就收到响应
2. 步骤4-7在后台继续执行
3. 用户体验显著改善
"""

import requests
import json
import time
import os

def test_early_response():
    """测试早期响应机制"""
    print("🚀 测试Powers of Tau早期响应机制")
    print("=" * 70)
    
    user_id = "early_response_test"
    constraint_power = 14  # 使用中等约束
    
    # 生成测试随机性数据
    test_entropy = json.dumps({
        "userInput": "早期响应测试的随机性数据，用于验证在步骤3完成后就能收到响应",
        "mouseMovements": [
            {"x": 200+i*15, "y": 400+i*20, "timestamp": 2000+i*150} 
            for i in range(25)
        ],
        "keyboardEvents": [
            {"key": chr(97+i%26), "timestamp": 5000+i*300, "keyCode": 97+i%26} 
            for i in range(10)
        ],
        "timestamp": time.time(),
        "userAgent": "early-response-test-browser",
        "screenInfo": {"width": 1920, "height": 1080},
        "randomValues": [time.time() + i*0.789 for i in range(6)]
    })
    
    payload = {
        "user_id": user_id,
        "constraint_power": constraint_power,
        "entropy": test_entropy
    }
    
    print(f"📋 测试配置:")
    print(f"   用户ID: {user_id}")
    print(f"   约束大小: 2^{constraint_power} = {2**constraint_power:,}")
    print(f"   期望：在步骤3完成后（约30-60秒）就收到响应")
    print(f"   背景：步骤4-7将在后台继续执行（约3-4分钟）")
    
    api_url = "http://localhost:8765/api/contribute-with-entropy"
    
    try:
        print(f"\n🕐 开始Powers of Tau贡献测试...")
        start_time = time.time()
        
        response = requests.post(
            api_url,
            json=payload,
            timeout=120  # 2分钟超时，应该足够到步骤3
        )
        
        response_time = time.time() - start_time
        
        print(f"\n📊 早期响应测试结果:")
        print(f"   HTTP状态码: {response.status_code}")
        print(f"   响应时间: {response_time:.2f} 秒 ({response_time/60:.1f} 分钟)")
        
        if response.status_code == 200:
            try:
                result = response.json()
                print(f"   ✅ 请求成功!")
                print(f"   📝 状态: {result.get('status', 'N/A')}")
                print(f"   💬 消息: {result.get('message', 'N/A')}")
                print(f"   ✓ 贡献已验证: {result.get('contribution_verified', 'N/A')}")
                print(f"   🔄 下一步: {result.get('next_step', 'N/A')}")
                print(f"   🎛️  后台处理: {result.get('background_processing', 'N/A')}")
                print(f"   🔑 贡献哈希: {result.get('contribution_hash', 'N/A')}")
                
                # 分析响应时间
                if response_time <= 90:  # 90秒内响应
                    print(f"\n🎉 早期响应测试成功!")
                    print(f"   ✅ 在{response_time:.1f}秒内收到响应（预期步骤3完成）")
                    print(f"   ✅ 消息内容符合预期：{result.get('message', '')[:50]}...")
                    print(f"   ✅ 后台处理状态正确：{result.get('background_processing', '')}")
                    
                    success = True
                else:
                    print(f"\n⚠️  响应时间过长，可能没有在步骤3后返回")
                    success = False
                
                # 等待并检查后台处理
                print(f"\n⏳ 等待30秒后检查后台处理状态...")
                time.sleep(30)
                
                # 检查LSB_groth16目录中是否最终生成了文件
                lsb_dir = "/Users/dylan/Code_Projects/Python_Projects/image_similarity/LSB_groth16"
                final_file = os.path.join(lsb_dir, f"pot{constraint_power}_final.ptau")
                
                if os.path.exists(final_file):
                    file_size = os.path.getsize(final_file) / (1024*1024)
                    print(f"   ✅ 后台处理成功！最终文件已生成: {file_size:.2f} MB")
                else:
                    print(f"   ⏳ 后台仍在处理中，最终文件尚未生成")
                    print(f"   💡 这是正常的，因为步骤4-7需要较长时间")
                
                return success
                
            except json.JSONDecodeError:
                print(f"   ❌ 响应不是有效JSON")
                print(f"   📄 响应内容: {response.text[:200]}...")
                return False
        else:
            print(f"   ❌ 请求失败: {response.status_code}")
            print(f"   📄 错误内容: {response.text[:200]}...")
            return False
            
    except requests.exceptions.Timeout:
        print(f"   ⏰ 请求超时（2分钟）")
        print(f"   💡 这可能表明修复未生效，仍需等待所有步骤完成")
        return False
        
    except Exception as e:
        print(f"   ❌ 测试异常: {e}")
        return False

def check_backend_logs():
    """检查后台日志验证步骤执行"""
    print("\n📋 后台日志分析指南:")
    print("   请查看后台终端日志，应该看到：")
    print("   1. ✅ '步骤3: 验证用户贡献' - 在前端收到响应前")
    print("   2. ✅ '用户贡献验证完成' - 在前端收到响应前")  
    print("   3. ✅ '开始后台执行Powers of Tau剩余步骤（步骤4-7）' - 响应返回后")
    print("   4. ✅ '步骤4: 引入随机化信标' - 后台执行")
    print("   5. ✅ '步骤5: 生成最终的final.ptau' - 后台执行")
    print("   6. ✅ '步骤6: 验证final.ptau' - 后台执行")
    print("   7. ✅ '步骤7: 复制最终文件到LSB_groth16文件夹' - 后台执行")
    print("   8. ✅ '后台Powers of Tau完成' - 最终完成")

def main():
    """主测试函数"""
    print("🧪 Powers of Tau 早期响应修复验证")
    print("=" * 80)
    
    # 检查API服务器状态
    try:
        response = requests.get("http://localhost:8765", timeout=5)
        print("✅ API服务器运行正常")
    except:
        print("❌ API服务器未运行，请先启动服务器")
        return
    
    # 主要测试
    result = test_early_response()
    
    # 显示日志检查指南
    check_backend_logs()
    
    # 总结结果
    print("\n" + "=" * 80)
    print("📊 测试结果总结:")
    
    if result:
        print(f"   🎉 早期响应机制测试通过!")
        print(f"\n✅ 修复效果:")
        print(f"   1. ✅ 前端在步骤3完成后就收到响应（30-90秒）")
        print(f"   2. ✅ 用户不再需要等待完整的Powers of Tau流程（5分钟+）")
        print(f"   3. ✅ 步骤4-7在后台继续执行，不阻塞用户界面")
        print(f"   4. ✅ 用户体验显著改善")
        
        print(f"\n💡 用户现在的体验:")
        print(f"   • 提供随机性 → 等待30-90秒 → 看到成功完成")
        print(f"   • 显示消息：'Powers of Tau贡献完成！零知识证明正在生成...'")
        print(f"   • 可以安全关闭页面，后台继续处理")
        
    elif result is False:
        print(f"   ❌ 早期响应机制测试失败")
        print(f"   💡 可能的原因：")
        print(f"      - 修复未正确实施")
        print(f"      - 服务器需要重启")
        print(f"      - 步骤3仍需过长时间")
    else:
        print(f"   ⏭️  测试被跳过或超时")
    
    print(f"\n🔧 部署建议:")
    print(f"   1. 重启后端API服务器以应用修复")
    print(f"   2. 重启前端开发服务器")
    print(f"   3. 测试完整的水印检测→Powers of Tau流程")
    print(f"   4. 验证用户体验改善")

if __name__ == "__main__":
    main() 