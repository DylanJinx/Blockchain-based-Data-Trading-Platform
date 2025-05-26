#!/usr/bin/env python3
"""
直接测试水印检测和Powers of Tau流程
绕过元数据URL解析，直接使用现有的含水印数据集
"""

import sys
import os
import logging
import json

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入register_data函数
from features.feature_register import register_data

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_watermark_detection_direct():
    """直接测试水印检测功能"""
    
    logging.info("🚀 开始直接测试水印检测和Powers of Tau流程...")
    
    # 检查是否有包含水印的数据集
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    watermark_zip = os.path.join(data_dir, "dataset_watermark.zip")
    
    if not os.path.exists(watermark_zip):
        logging.error(f"❌ 找不到测试数据集: {watermark_zip}")
        return False
    
    logging.info(f"✅ 找到测试数据集: {watermark_zip}")
    
    # 创建临时的测试元数据JSON，直接指向本地文件
    # 这样可以绕过IPFS下载步骤
    test_metadata = {
        "name": "测试水印数据集",
        "description": "包含水印的测试数据集，用于验证Powers of Tau流程",
        "zip_cid": "local_test_dataset_watermark",  # 使用特殊标识
        "image_count": 100,
        "creation_date": "2025-05-26",
        "creator": "测试用户",
        "tags": ["测试", "水印", "数据集"]
    }
    
    # 保存临时元数据文件
    temp_metadata_file = "temp_test_metadata.json"
    with open(temp_metadata_file, 'w', encoding='utf-8') as f:
        json.dump(test_metadata, f, ensure_ascii=False, indent=2)
    
    logging.info(f"✅ 创建临时元数据文件: {temp_metadata_file}")
    
    user_address = "0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC"
    
    try:
        # 调用register_data函数
        logging.info("步骤1: 调用register_data函数进行水印检测")
        
        # 使用file://协议来访问本地文件
        metadata_url = f"file://{os.path.abspath(temp_metadata_file)}"
        logging.info(f"使用元数据URL: {metadata_url}")
        
        result = register_data(metadata_url, user_address)
        
        # 分析结果
        if result is None:
            logging.error("❌ register_data返回了None，可能是由于元数据解析失败")
            return False
        
        if isinstance(result, dict):
            logging.info(f"✅ register_data返回结果: {json.dumps(result, indent=2, ensure_ascii=False)}")
            
            # 检查是否检测到侵权
            if result.get("status") == "copyright_violation":
                logging.info("✅ 成功检测到水印侵权！")
                
                # 检查是否需要用户贡献
                if result.get("requires_user_contribution"):
                    logging.info("✅ 需要用户贡献Powers of Tau")
                    
                    user_id = result.get("user_id")
                    constraint_power = result.get("constraint_power")
                    
                    if user_id and constraint_power:
                        logging.info(f"✅ Powers of Tau信息正确: user_id={user_id}, constraint_power={constraint_power}")
                        return True
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
            logging.error(f"❌ register_data返回了意外的结果类型: {type(result)}")
            return False
            
    except Exception as e:
        logging.error(f"❌ 测试过程中出现异常: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # 清理临时文件
        if os.path.exists(temp_metadata_file):
            os.remove(temp_metadata_file)
            logging.info(f"✅ 清理临时文件: {temp_metadata_file}")

if __name__ == "__main__":
    print("=" * 60)
    print("直接水印检测和Powers of Tau流程测试")
    print("=" * 60)
    
    # 运行测试
    success = test_watermark_detection_direct()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ 测试通过！水印检测和Powers of Tau流程工作正常")
    else:
        print("❌ 测试失败！需要进一步调试")
    print("=" * 60) 