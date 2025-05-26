import os
import sys
import json
import re
import flask
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import openai
import subprocess
import logging
from features.feature_register import register_data, start_nft_minting
from features.feature_buy import buy_nft
from features.feature_informer import report_nft
from features.feature_resale import run_xrid_commands, interpret_results
from features.poweroftau_generator import PowerOfTauGenerator, generate_ptau_for_dataset
import requests
import time

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# 确保在环境变量中有 OPENAI_API_KEY
API_KEY = os.getenv("OPENAI_API_KEY")
if not API_KEY:
    logging.error("未检测到 OPENAI_API_KEY，请先在环境中设置该变量后再运行脚本。")
    sys.exit(1)

openai.api_key = API_KEY

# 指定要使用的OpenAI模型
MODEL_NAME = "gpt-4"

app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 存储每个用户的对话历史
conversation_history = {}

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    user_input = data.get('message', '')
    user_id = data.get('user_id', 'default_user')
    user_address = data.get('address', '')
    
    # 获取或初始化用户的对话历史
    if user_id not in conversation_history:
        system_prompt = "你是数据交易平台的客服小x，请与用户进行多轮对话。\n" + \
                       "1) 当用户说\"想要登记一个数据集(NFT)\"，并给出一个metadata_url (如 ipfs链接)，" + \
                       "   请输出: {\"feature\": \"register_data\", \"metadata_url\": \"<用户给的url>\"}\n\n" + \
                       "2) 当用户说\"上架我的 tokenId=X, 价格=Y ETH\" => 输出 {\"feature\":\"list_nft\",\"token_id\":X, \"price\":Y}\n" + \
                       "3) 当用户说\"我要下架 tokenId=X\" => 输出 {\"feature\":\"unlist_nft\",\"token_id\":X}\n" + \
                       "4) 当用户说\"我要购买 tokenId=X\" => 输出{\"feature\":\"buy_nft\",\"token_id\":X}\n" + \
                       "5) 当用户说\"我要举报 tokenId=A 和 tokenId=B 存在转售行为\" =>  输出{\"feature\":\"report_nft\", \"token_id_a\": A, \"token_id_b\": B}\n" + \
                       "6) 否则，就用客服小x的口吻友好回答，不要输出JSON。\n" + \
                       "回答语言使用中文。不要使用任何Markdown代码块。输出JSON时，就只输出JSON，不要带其他文字以及任何标点符号。"
        
        conversation_history[user_id] = [
            {
                "role": "system",
                "content": system_prompt
            }
        ]
    
    # 将用户输入添加到对话历史
    conversation_history[user_id].append({"role": "user", "content": user_input})
    
    try:
        # 调用OpenAI API
        response = openai.ChatCompletion.create(
            model=MODEL_NAME,
            messages=conversation_history[user_id],
            temperature=0.7
        )
        
        assistant_reply = response["choices"][0]["message"]["content"]
        conversation_history[user_id].append({"role": "assistant", "content": assistant_reply})
        
        # 尝试解析JSON响应
        try:
            # 清理响应，去除可能的代码块标记
            cleaned_reply = re.sub(r"```(\w+)?", "", assistant_reply)
            cleaned_reply = cleaned_reply.strip()
            data_dict = json.loads(cleaned_reply)
            
            # 根据feature字段分类处理
            feature = data_dict.get("feature")
            
            if feature == "register_data":
                metadata_url = data_dict.get("metadata_url")
                if metadata_url:
                    # 简单检查元数据URL是否可访问，但不进行水印检测
                    try:
                        # 先获取元数据，检查是否能访问
                        metadata_response = requests.get(metadata_url, timeout=5)
                        if metadata_response.status_code != 200:
                            return jsonify({
                                "reply": f"很抱歉，您提供的元数据URL ({metadata_url}) 无法访问。请检查URL是否正确。",
                            })
                        
                        try:
                            metadata = metadata_response.json()
                            dataset_cid = metadata.get('zip_cid') or metadata.get('cid')
                            
                            if not dataset_cid:
                                return jsonify({
                                    "reply": f"您提供的元数据中未找到数据集CID (zip_cid或cid字段)，请确认元数据格式正确。",
                                })
                            
                        except Exception as e:
                            logging.warning(f"解析元数据失败: {e}")
                            return jsonify({
                                "reply": f"解析元数据时出错: {str(e)}。请确认您提供的URL返回了有效的JSON数据。",
                            })
                    
                    except Exception as e:
                        logging.warning(f"预检查元数据URL出错: {e}")
                        return jsonify({
                            "reply": f"检查元数据URL时出错: {str(e)}。请确认URL是否正确。",
                        })
                    
                    # 基本检查通过，返回动作
                    return jsonify({
                        "reply": assistant_reply,
                        "action": "register_data",
                        "metadata_url": metadata_url,
                        "user_address": user_address
                    })
            
            elif feature == "list_nft":
                token_id = data_dict.get("token_id")
                price = data_dict.get("price")
                if token_id and price:
                    return jsonify({
                        "reply": assistant_reply,
                        "action": "list_nft",
                        "token_id": token_id,
                        "price": price,
                        "user_address": user_address
                    })
            
            elif feature == "unlist_nft":
                token_id = data_dict.get("token_id")
                if token_id:
                    return jsonify({
                        "reply": assistant_reply,
                        "action": "unlist_nft",
                        "token_id": token_id,
                        "user_address": user_address
                    })
            
            elif feature == "buy_nft":
                token_id = data_dict.get("token_id")
                if token_id:
                    return jsonify({
                        "reply": assistant_reply,
                        "action": "buy_nft",
                        "token_id": token_id,
                        "user_address": user_address
                    })
            
            elif feature == "report_nft":
                token_id_a = data_dict.get("token_id_a")
                token_id_b = data_dict.get("token_id_b")
                if token_id_a and token_id_b:
                    return jsonify({
                        "reply": assistant_reply,
                        "action": "report_nft",
                        "token_id_a": token_id_a,
                        "token_id_b": token_id_b,
                        "user_address": user_address
                    })
            
            # 如果有其他不认识的feature或数据不完整
            return jsonify({"reply": assistant_reply})
            
        except json.JSONDecodeError:
            # 不是JSON，直接返回回复
            return jsonify({"reply": assistant_reply})
        
    except Exception as e:
        logging.error(f"处理请求时出错: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/register-data', methods=['POST'])
def api_register_data():
    data = request.json
    metadata_url = data.get('metadata_url')
    user_address = data.get('user_address')
    
    if not metadata_url:
        return jsonify({"error": "缺少必要参数: metadata_url"}), 400
    
    if not user_address:
        return jsonify({"error": "缺少必要参数: user_address"}), 400
    
    # 验证用户地址格式
    if not user_address.startswith('0x') or len(user_address) != 42:
        return jsonify({"error": "无效的用户地址格式"}), 400
    
    try:
        # 首先检查是否已有正在处理的请求（避免重复提交）
        logging.info(f"开始登记数据集，用户地址: {user_address}, 元数据URL: {metadata_url}")
        
        # 创建日志目录（如果不存在）
        logs_dir = os.path.join(os.path.dirname(__file__), "logs")
        os.makedirs(logs_dir, exist_ok=True)
        
        # 创建会话ID和状态文件
        session_id = int(time.time())
        # 统一状态文件路径：保存在 my_agent_project/status/ 目录下
        status_dir = os.path.join(os.path.dirname(__file__), "status")
        os.makedirs(status_dir, exist_ok=True)
        status_file_path = os.path.join(status_dir, f"register_status_{session_id}.json")
        
        # 记录初始状态
        status_data = {
            "session_id": session_id,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "metadata_url": metadata_url,
            "user_address": user_address,
            "status": "initiated", 
            "start_time": time.time()
        }
        
        with open(status_file_path, "w") as f:
            json.dump(status_data, f)
            
        # 调用feature_register.py中的register_data函数
        try:
            result = register_data(metadata_url, user_address)  # 确保传递user_address参数
            
            # 检查register_data的返回值
            if isinstance(result, dict):
                # 如果返回字典，说明有特殊情况（如检测到水印）
                if result.get("status") == "copyright_violation":
                    logging.info(f"检测到侵权行为，返回Powers of Tau贡献状态")
                    return jsonify({
                        "status": "copyright_violation",
                        "message": result.get("message"),
                        "background_message": result.get("background_message"),
                        "requires_user_contribution": result.get("requires_user_contribution", False),
                        "user_id": result.get("user_id"),
                        "constraint_power": result.get("constraint_power"),
                        "ptau_info": result.get("ptau_info"),
                        "zk_proof_result": result.get("zk_proof_result")
                    })
                elif result.get("status") == "no_watermark_transfer_required":
                    # 无水印，需要转账3 ETH
                    logging.info(f"数据集未检测到水印，需要用户转账3 ETH")
                    
                    # 将必要信息保存到状态文件，供转账确认后使用
                    status_data["result_type"] = "no_watermark"
                    status_data["ptau_info"] = result.get("ptau_info", {})
                    status_data["transfer_required"] = True
                    
                    with open(status_file_path, "w") as f:
                        json.dump(status_data, f)
                    
                    return jsonify({
                        "status": "waiting_for_transfer",
                        "message": result.get("message", "请转 3 ETH 到指定地址以完成登记"),
                        "agent_address": "0x70997970C51812dc3A010C7d01b50e0d17dc79C8",
                        "required_eth": 3,
                        "session_id": session_id
                    })
                elif result.get("status") == "processing":
                    # 其他处理中状态
                    return jsonify(result)
                else:
                    # 其他未知状态，按正常流程处理
                    logging.warning(f"register_data返回了未知状态: {result}")
            
            # 如果没有返回特殊状态，继续正常的转账等待流程（这个分支现在应该不会被触发）
            logging.warning("register_data未返回预期的字典状态，使用默认转账流程")
            return jsonify({
                "status": "waiting_for_transfer",
                "message": "请转 3 ETH 到指定地址以完成登记",
                "agent_address": "0x70997970C51812dc3A010C7d01b50e0d17dc79C8",
                "required_eth": 3,
                "session_id": session_id
            })
            
        except ValueError as e:
            # 处理可能的水印检测错误
            error_message = str(e)
            logging.error(f"数据集登记失败（值错误）: {error_message}")
            
            # 更新状态文件
            status_data["status"] = "failed"
            status_data["error"] = error_message
            status_data["end_time"] = time.time()
            
            with open(status_file_path, "w") as f:
                json.dump(status_data, f)
                
            # 水印相关错误
            if "检测到水印" in error_message:
                return jsonify({
                    "status": "error",
                    "error_type": "watermark_detected",
                    "message": error_message
                }), 403  # 使用403 Forbidden状态码
            else:
                return jsonify({
                    "status": "error",
                    "message": error_message
                }), 400
                
        except TimeoutError as e:
            # 处理超时错误
            error_message = str(e)
            logging.error(f"数据集登记超时: {error_message}")
            
            # 更新状态文件
            status_data["status"] = "timeout"
            status_data["error"] = error_message
            status_data["end_time"] = time.time()
            
            with open(status_file_path, "w") as f:
                json.dump(status_data, f)
                
            return jsonify({
                "status": "timeout",
                "message": error_message
            }), 408  # 使用408 Request Timeout状态码
            
    except Exception as e:
        logging.error(f"数据集登记失败: {e}")
        
        # 尝试记录错误到状态文件（如果已创建）
        if 'status_data' in locals() and 'status_file_path' in locals():
            try:
                status_data["status"] = "failed"
                status_data["error"] = str(e)
                status_data["end_time"] = time.time()
                
                with open(status_file_path, "w") as f:
                    json.dump(status_data, f)
            except Exception as file_e:
                logging.error(f"无法更新状态文件: {file_e}")
                
        # 检查是否水印相关错误
        error_message = str(e)
        if "水印" in error_message or "watermark" in error_message.lower():
            return jsonify({
                "status": "error",
                "error_type": "watermark_related",
                "message": error_message
            }), 403  # 水印错误使用403
        
        return jsonify({
            "status": "error",
            "message": error_message
        }), 500

@app.route('/api/list-nft', methods=['POST'])
def api_list_nft():
    data = request.json
    token_id = data.get('token_id')
    price = data.get('price')
    user_address = data.get('user_address')
    
    if not token_id or not price or not user_address:
        return jsonify({"error": "缺少必要参数"}), 400
    
    try:
        # 执行function_2_list_nft.py脚本
        cmd = ["python", "../python_call_contract/function_2_list_nft.py", user_address, str(token_id), str(price)]
        result = subprocess.run(cmd, cwd="../python_call_contract", capture_output=True, text=True)
        
        return jsonify({
            "status": "success",
            "message": "NFT上架成功",
            "output": result.stdout
        })
    except Exception as e:
        logging.error(f"NFT上架失败: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/unlist-nft', methods=['POST'])
def api_unlist_nft():
    data = request.json
    token_id = data.get('token_id')
    user_address = data.get('user_address')
    
    if not token_id or not user_address:
        return jsonify({"error": "缺少必要参数"}), 400
    
    try:
        # 执行function_3_unlist_nft.py脚本
        cmd = ["python", "../python_call_contract/function_3_unlist_nft.py", user_address, str(token_id)]
        result = subprocess.run(cmd, cwd="../python_call_contract", capture_output=True, text=True)
        
        return jsonify({
            "status": "success",
            "message": "NFT下架成功",
            "output": result.stdout
        })
    except Exception as e:
        logging.error(f"NFT下架失败: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/buy-nft', methods=['POST'])
def api_buy_nft():
    data = request.json
    token_id = data.get('token_id')
    user_address = data.get('user_address')
    public_key = data.get('public_key')
    
    if not token_id or not user_address or not public_key:
        return jsonify({"error": "缺少必要参数"}), 400
    
    # 创建logs目录以保存日志
    logs_dir = os.path.join(os.path.dirname(__file__), "logs")
    os.makedirs(logs_dir, exist_ok=True)
    
    # 保存公钥文件
    public_key_path = os.path.join(os.path.dirname(__file__), "temp_public_key.pem")
    try:
        with open(public_key_path, "w") as f:
            f.write(public_key)
        
        # 记录公钥保存信息
        logging.info(f"已保存用户公钥文件: {public_key_path}, 长度: {len(public_key)} 字符")
        
        # 验证公钥文件内容
        if not public_key.startswith("-----BEGIN PUBLIC KEY-----"):
            return jsonify({"error": "公钥格式不正确，缺少开头标记"}), 400
            
        if not public_key.strip().endswith("-----END PUBLIC KEY-----"):
            return jsonify({"error": "公钥格式不正确，缺少结尾标记"}), 400
            
    except Exception as e:
        logging.error(f"保存公钥文件失败: {e}")
        return jsonify({"error": f"保存公钥文件失败: {str(e)}"}), 500
    
    try:
        # 首先获取NFT详情，确认状态和价格
        try:
            cmd = ["python", "../python_call_contract/function_4_buy_nft.py", "check", str(token_id)]
            result = subprocess.run(cmd, cwd="../python_call_contract", capture_output=True, text=True, check=True)
            check_output = result.stdout.strip()
            
            # 解析价格和上架状态
            import re
            status_match = re.search(r"ListingStatus=(\w+)", check_output)
            price_match = re.search(r"price=([\d\.]+)", check_output)
            
            if not status_match or status_match.group(1) != "Listed":
                # 删除临时公钥文件
                if os.path.exists(public_key_path):
                    os.remove(public_key_path)
                return jsonify({"error": "NFT未上架或状态异常"}), 400
            price = price_match.group(1) if price_match else "未知"
            logging.info(f"NFT {token_id} 已上架，价格为 {price} ETH")
        except Exception as e:
            logging.error(f"检查NFT状态失败: {e}")
            # 删除临时公钥文件
            if os.path.exists(public_key_path):
                os.remove(public_key_path)
            return jsonify({"error": f"检查NFT状态失败: {str(e)}"}), 500
        
        # 尝试获取SaleHash - 注意这里是新增的部分
        try:
            from features.feature_buy import get_token_sale_hash
            sale_hash = get_token_sale_hash(int(token_id))
            if sale_hash:
                logging.info(f"成功获取到NFT {token_id}的SaleHash: {sale_hash}")
            else:
                logging.warning(f"无法获取NFT {token_id}的SaleHash，将由addWatermark.py内部处理")
        except Exception as e:
            logging.error(f"获取SaleHash时出错: {e}")
            sale_hash = None
        
        # 调用feature_buy.py中的buy_nft函数
        logging.info(f"开始处理购买流程: token_id={token_id}, user_address={user_address}")
        
        # 调用feature_buy.py中的buy_nft函数
        from features.feature_buy import buy_nft
        encrypted_cid = buy_nft(int(token_id), user_address, public_key_path)
        
        # 删除临时公钥文件
        if os.path.exists(public_key_path):
            os.remove(public_key_path)
        
        # 处理各种返回情况
        if encrypted_cid == "WAIT_TIMEOUT":
            return jsonify({
                "status": "timeout",
                "message": "等待转账超时，未检测到转账交易"
            }), 408  # 使用408 Request Timeout状态码
            
        elif encrypted_cid == "MOCK_CID_FOR_ERROR" or encrypted_cid is None:
            return jsonify({
                "status": "error",
                "message": "购买处理过程中出错，请检查日志或稍后重试",
                "encrypted_cid": "ERROR_OCCURRED"
            }), 500
            
        elif encrypted_cid.startswith("MOCK_ENCRYPTED_CID_"):
            # 模拟的CID，用于测试或错误恢复
            logging.warning(f"使用模拟CID: {encrypted_cid}")
            return jsonify({
                "status": "success",
                "message": "NFT购买流程已完成（使用模拟CID）",
                "encrypted_cid": encrypted_cid
            })
        
        # 正常情况下返回加密的CID
        return jsonify({
            "status": "success",
            "message": "NFT购买成功",
            "encrypted_cid": encrypted_cid
        })
        
    except Exception as e:
        logging.error(f"NFT购买失败: {e}")
        # 删除临时公钥文件
        if os.path.exists(public_key_path):
            os.remove(public_key_path)
        return jsonify({"error": str(e)}), 500

@app.route('/api/report-nft', methods=['POST'])
def api_report_nft():
    data = request.json
    token_id_a = data.get('token_id_a')
    token_id_b = data.get('token_id_b')
    user_address = data.get('user_address')
    
    if not token_id_a or not token_id_b or not user_address:
        return jsonify({"error": "缺少必要参数"}), 400
    
    try:
        # 创建日志目录
        logs_dir = os.path.join(os.path.dirname(__file__), "logs")
        os.makedirs(logs_dir, exist_ok=True)
        
        # 创建举报日志文件
        report_log_path = os.path.join(logs_dir, f"report_{token_id_a}_{token_id_b}.log")
        
        # 设置子进程以将输出重定向到日志文件
        with open(report_log_path, "w") as log_file:
            # 记录开始时间
            log_file.write(f"开始举报检测: token_id_a={token_id_a}, token_id_b={token_id_b}, user={user_address}\n")
            log_file.write(f"时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            log_file.flush()  # 确保写入磁盘
            
            # 调用 report_nft 函数，但捕获其输出到日志文件
            cmd = [
                "python", 
                "../python_call_contract/function_7_informer.py", 
                "report", 
                str(token_id_a), 
                str(token_id_b), 
                user_address
            ]
            
            process = subprocess.Popen(
                cmd,
                stdout=log_file,
                stderr=log_file,
                cwd="../python_call_contract"
            )
            
            # 不等待进程完成，让它在后台运行
            logging.info(f"已启动举报检测进程, PID={process.pid}, 日志文件={report_log_path}")
        
        # 记录创建的日志文件路径到数据库或另一个文件中
        # 这样check_report_result可以知道在哪里查找结果
        report_index_path = os.path.join(logs_dir, "report_index.json")
        report_index = {}
        
        if os.path.exists(report_index_path):
            try:
                with open(report_index_path, "r") as f:
                    report_index = json.load(f)
            except:
                report_index = {}
        
        report_key = f"{token_id_a}_{token_id_b}_{user_address}"
        report_index[report_key] = {
            "token_id_a": token_id_a,
            "token_id_b": token_id_b, 
            "user_address": user_address,
            "log_path": report_log_path,
            "start_time": time.time()
        }
        
        with open(report_index_path, "w") as f:
            json.dump(report_index, f)
        
        return jsonify({
            "status": "success",
            "message": "举报提交成功"
        })
    except Exception as e:
        logging.error(f"举报失败: {e}")
        return jsonify({"error": str(e)}), 500

# 获取所有上架的NFT
@app.route('/api/get-listed-nfts', methods=['GET'])
def get_listed_nfts():
    try:
        # 这里需要实现从区块链获取所有上架的NFT
        # 调用合约函数获取所有上架的NFT
        cmd = ["python", "../python_call_contract/get_listed_nfts.py"]
        result = subprocess.run(cmd, cwd="../python_call_contract", capture_output=True, text=True)
        
        # 解析输出结果
        try:
            nfts = json.loads(result.stdout)
            return jsonify(nfts)
        except json.JSONDecodeError:
            # 如果输出不是有效的JSON，则返回空列表
            logging.error(f"解析listed NFTs失败: {result.stdout}")
            return jsonify([])
    except Exception as e:
        logging.error(f"获取上架NFT列表失败: {e}")
        return jsonify({"error": str(e)}), 500

# 获取单个NFT的详细信息
@app.route('/api/nft/<int:token_id>', methods=['GET'])
def get_nft_details(token_id):
    try:
        # 调用合约函数获取NFT详情
        cmd = ["python", "../python_call_contract/get_nft_details.py", str(token_id)]
        result = subprocess.run(cmd, cwd="../python_call_contract", capture_output=True, text=True)
        
        # 解析输出结果
        try:
            nft_details = json.loads(result.stdout)
            return jsonify(nft_details)
        except json.JSONDecodeError:
            logging.error(f"解析NFT详情失败: {result.stdout}")
            return jsonify({"error": "无法获取NFT详情"}), 500
    except Exception as e:
        logging.error(f"获取NFT详情失败: {e}")
        return jsonify({"error": str(e)}), 500

# 上传文件到IPFS
@app.route('/api/upload-to-ipfs', methods=['POST'])
def upload_to_ipfs():
    if 'file' not in request.files:
        return jsonify({"error": "没有文件"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "没有选择文件"}), 400
    
    # 保存上传的文件
    file_path = os.path.join(os.path.dirname(__file__), "temp_file")
    file.save(file_path)
    
    try:
        # 调用上传脚本
        cmd = ["node", "../BDTP/uploadToIPFS.js", file_path]
        logging.info(f"执行上传命令: {' '.join(cmd)}")
        result = subprocess.run(cmd, cwd="../BDTP", capture_output=True, text=True)
        
        # 删除临时文件
        os.remove(file_path)
        
        # 从输出中提取CID
        cid_match = re.search(r"CID: (\S+)", result.stdout)
        if cid_match:
            cid = cid_match.group(1)
            return jsonify({
                "status": "success",
                "cid": cid
            })
        else:
            logging.error(f"无法从输出中提取CID: {result.stdout}")
            if result.stderr:
                logging.error(f"错误输出: {result.stderr}")
            return jsonify({"error": "无法获取上传文件的CID"}), 500
    except Exception as e:
        # 删除临时文件
        if os.path.exists(file_path):
            os.remove(file_path)
        logging.error(f"上传文件到IPFS失败: {e}")
        return jsonify({"error": str(e)}), 500

# 添加新的元数据上传和加密API
@app.route('/api/create-encrypted-metadata', methods=['POST'])
def create_encrypted_metadata():
    data = request.json
    dataset_cid = data.get('dataset_cid')
    image_cid = data.get('image_cid')
    title = data.get('title')
    description = data.get('description')
    
    if not dataset_cid or not image_cid or not title or not description:
        return jsonify({"error": "缺少必要参数"}), 400
    
    try:
        # 平台公钥路径
        public_key_path = os.path.join(os.path.dirname(__file__), "..", "BDTP", "platform_public_key.pem")
        
        # 确认公钥存在
        if not os.path.exists(public_key_path):
            logging.error(f"平台公钥不存在: {public_key_path}")
            return jsonify({"error": "平台公钥不存在"}), 500
        
        # 调用加密和元数据上传脚本
        cmd = [
            "node", 
            "../BDTP/encryptAndUploadMetadata.js", 
            dataset_cid, 
            image_cid, 
            title, 
            description, 
            public_key_path
        ]
        logging.info(f"执行元数据创建命令: {' '.join(cmd)}")
        result = subprocess.run(cmd, cwd="../BDTP", capture_output=True, text=True)
        
        if result.returncode != 0:
            logging.error(f"元数据创建失败: {result.stderr}")
            return jsonify({"error": "元数据创建失败"}), 500
        
        # 从输出中提取元数据CID和URL
        metadata_cid_match = re.search(r"METADATA_CID:(\S+)", result.stdout)
        metadata_url_match = re.search(r"METADATA_URL:(\S+)", result.stdout)
        
        if metadata_cid_match and metadata_url_match:
            metadata_cid = metadata_cid_match.group(1)
            metadata_url = metadata_url_match.group(1)
            
            return jsonify({
                "status": "success",
                "metadata_cid": metadata_cid,
                "metadata_url": metadata_url
            })
        else:
            logging.error(f"无法解析元数据输出: {result.stdout}")
            return jsonify({"error": "无法获取元数据信息"}), 500
    except Exception as e:
        logging.error(f"创建加密元数据失败: {e}")
        return jsonify({"error": str(e)}), 500
    
@app.route('/api/check-register-status', methods=['POST'])
def check_register_status():
    data = request.json
    metadata_url = data.get('metadata_url')
    user_address = data.get('user_address')
    
    if not metadata_url:
        return jsonify({"error": "缺少必要参数: metadata_url"}), 400
    
    if not user_address:
        return jsonify({"error": "缺少必要参数: user_address"}), 400
    
    # 验证用户地址格式
    if not user_address.startswith('0x') or len(user_address) != 42:
        return jsonify({"error": "无效的用户地址格式"}), 400
    
    try:
        # 初始化web3连接
        from web3 import Web3, HTTPProvider
        session = requests.Session()
        session.trust_env = False
        w3 = Web3(HTTPProvider("http://127.0.0.1:8545", session=session))
        
        if not w3.is_connected():
            logging.error("无法连接到本地区块链")
            return jsonify({"error": "无法连接到区块链网络"}), 500
        
        # 转换地址为校验和格式
        user_address = w3.to_checksum_address(user_address)
        
        # 读取合约信息
        with open("../python_call_contract/deploy_address.json", "r") as f:
            deploy_info = json.load(f)
        
        # 加载NFT合约ABI
        with open("../BDTP_contract/out/DataRegistration.sol/DataRegistration.json", "r") as f:
            artifact = json.load(f)
            data_registration_abi = artifact["abi"]
            
        # 初始化合约对象
        data_registration_contract = w3.eth.contract(
            address=deploy_info["DataRegistration"],
            abi=data_registration_abi
        )
        
        # 查找用户最近的转账记录
        latest_block = w3.eth.block_number
        agent_address = "0x70997970C51812dc3A010C7d01b50e0d17dc79C8"
        required_value_wei = w3.to_wei(3, "ether")
        
        # 查找最近50个区块内的转账交易
        transfer_found = False
        tx_hash = None
        tx_block = None
        for block_num in range(max(0, latest_block - 50), latest_block + 1):
            try:
                block = w3.eth.get_block(block_num, full_transactions=True)
                for tx in block.transactions:
                    from_addr = tx["from"].lower()
                    to_addr = (tx["to"] or "").lower() if tx["to"] else ""
                    value_wei = tx["value"]
                    
                    if from_addr == user_address.lower() and to_addr == agent_address.lower() and value_wei == required_value_wei:
                        transfer_found = True
                        tx_hash = tx["hash"].hex()
                        tx_block = block_num
                        logging.info(f"找到转账交易: {tx_hash}, 区块: {block_num}")
                        break
            except Exception as e:
                logging.error(f"检查区块 {block_num} 时出错: {e}")
                continue
            
            if transfer_found:
                break
        
        # 规范化URL和CID函数
        def normalize_url(url):
            # 移除可能的尾随斜杠和查询参数
            url = url.split('?')[0].rstrip('/')
            # 移除协议部分 (http://, https://)
            if '://' in url:
                url = url.split('://', 1)[1]
            return url.lower()
        
        def extract_cid(url):
            # 提取IPFS CID (假设URL格式为 */ipfs/<CID> 或 */ipfs/<CID>/*)
            if '/ipfs/' in url:
                try:
                    cid_part = url.split('/ipfs/')[1].split('/')[0]
                    return cid_part
                except:
                    return None
            return None
        
        # 从元数据URL中提取CID
        metadata_cid = extract_cid(metadata_url)
        normalized_metadata_url = normalize_url(metadata_url)
        
        # 检查链上是否已存在具有相同元数据URL的NFT
        logging.info(f"检查链上是否存在同一URL的NFT: {metadata_url}")
        
        # 直接查询用户最近铸造的NFT
        user_nfts = []
        exact_match_nft = None
        cid_match_nft = None
        
        # 遍历所有可能的tokenId（从1到100），检查它们的所有者和URI
        for token_id in range(1, 100):
            try:
                # 检查该token是否存在及其所有者
                try:
                    owner = data_registration_contract.functions.ownerOf(token_id).call()
                except Exception:
                    # Token不存在，继续检查下一个
                    continue
                
                # 获取tokenURI
                token_uri = data_registration_contract.functions.tokenURI(token_id).call()
                
                # 记录属于该用户的NFT
                if owner.lower() == user_address.lower():
                    nft_info = {
                        "token_id": token_id,
                        "token_uri": token_uri,
                        "normalized_uri": normalize_url(token_uri),
                        "cid": extract_cid(token_uri)
                    }
                    user_nfts.append(nft_info)
                    
                    # 检查是否精确匹配当前请求的metadata_url
                    if normalize_url(token_uri) == normalized_metadata_url:
                        exact_match_nft = nft_info
                        logging.info(f"找到精确匹配的NFT: {token_id}, URI={token_uri}")
                    
                    # 检查CID是否匹配
                    elif metadata_cid and extract_cid(token_uri) == metadata_cid:
                        cid_match_nft = nft_info
                        logging.info(f"找到CID匹配的NFT: {token_id}, CID={metadata_cid}")
                
                # 检查是否有其他用户拥有具有相同元数据URL的NFT
                elif normalize_url(token_uri) == normalized_metadata_url or (metadata_cid and extract_cid(token_uri) == metadata_cid):
                    logging.warning(f"发现其他用户 {owner} 拥有相同元数据URL的NFT，tokenId={token_id}")
                    return jsonify({
                        "status": "error",
                        "message": "此元数据URL已被其他用户注册",
                        "owner": owner
                    })
                
            except Exception as e:
                logging.error(f"检查TokenID {token_id} 时出错: {str(e)}")
                continue
        
        # 检查注册流程是否在进行中
        # 查找mint_nft.log中的记录，检查是否有正在处理的请求
        pending_registration = False
        log_file_path = os.path.join(os.path.dirname(__file__), "features", "mint_nft.log")
        if os.path.exists(log_file_path):
            try:
                with open(log_file_path, "r") as log_file:
                    log_content = log_file.read()
                    
                    # 查找该元数据URL的注册记录
                    if metadata_url in log_content:
                        # 查找最近的记录，检查是否成功
                        log_lines = log_content.split('\n')
                        for line in reversed(log_lines):
                            if metadata_url in line:
                                # 如果日志中有"成功"字样但没有在链上找到NFT，说明可能有延迟
                                if "成功" in line or "success" in line.lower():
                                    pending_registration = True
                                    logging.info(f"在日志中发现成功登记记录，但尚未在链上确认: {line}")
                                    break
            except Exception as e:
                logging.error(f"读取日志文件失败: {e}")
        
        # 处理查询结果
        
        # 1. 如果找到精确匹配的NFT，返回成功
        if exact_match_nft:
            logging.info(f"已找到精确匹配的NFT，返回成功状态")
            return jsonify({
                "status": "success",
                "message": "数据集已成功登记",
                "token_id": str(exact_match_nft["token_id"]),
                "data_owner": user_address,
                "metadata_url": exact_match_nft["token_uri"],
                "tx_hash": tx_hash if tx_hash else "unknown"
            })
        
        # 2. 如果找到CID匹配的NFT，返回成功
        if cid_match_nft:
            logging.info(f"已找到CID匹配的NFT，返回成功状态")
            return jsonify({
                "status": "success", 
                "message": "数据集已成功登记（CID匹配）",
                "token_id": str(cid_match_nft["token_id"]),
                "data_owner": user_address,
                "metadata_url": cid_match_nft["token_uri"],
                "tx_hash": tx_hash if tx_hash else "unknown"
            })
        
        # 3. 如果找到了转账，并且有注册记录，但尚未在链上确认，返回处理中状态
        if transfer_found and pending_registration:
            logging.info(f"已找到转账记录和日志中的登记记录，但尚未在链上确认，返回处理中状态")
            return jsonify({
                "status": "processing",
                "message": "已检测到转账，正在铸造NFT，请稍候",
                "tx_hash": tx_hash
            })
        
        # 4. 如果找到了转账，但没有匹配的NFT，需要启动铸造流程
        if transfer_found:
            logging.info(f"已找到转账记录，但尚未找到匹配的NFT，尝试启动铸造流程")
            
            # 搜索匹配的状态文件来启动铸造流程
            status_dir = os.path.join(os.path.dirname(__file__), "status")
            status_files_found = []
            
            if os.path.exists(status_dir):
                for filename in os.listdir(status_dir):
                    if (filename.startswith("register_status_") or filename.startswith("mint_status_")) and filename.endswith(".json"):
                        status_file_path = os.path.join(status_dir, filename)
                        try:
                            with open(status_file_path, "r") as f:
                                status_data = json.load(f)
                            
                            # 检查是否匹配当前请求
                            if (status_data.get("metadata_url") == metadata_url and 
                                status_data.get("user_address", "").lower() == user_address.lower() and
                                status_data.get("result_type") == "no_watermark" and
                                status_data.get("transfer_required") == True and
                                not status_data.get("minting_started", False)):
                                
                                status_files_found.append((status_file_path, status_data))
                                
                        except Exception as e:
                            logging.error(f"读取状态文件 {filename} 失败: {e}")
                            continue
            
            # 如果找到匹配的状态文件，启动铸造流程
            if status_files_found:
                status_file_path, status_data = status_files_found[0]  # 使用第一个匹配的
                
                try:
                    logging.info(f"找到匹配的状态文件，开始启动NFT铸造流程")
                    
                    # 启动NFT铸造流程
                    ptau_info = status_data.get("ptau_info", {})
                    minting_result = start_nft_minting(metadata_url, user_address, ptau_info)
                    
                    # 更新状态文件
                    status_data["transfer_confirmed"] = True
                    status_data["transfer_tx_hash"] = tx_hash
                    status_data["minting_started"] = True
                    status_data["minting_session_id"] = minting_result.get("session_id")
                    status_data["minting_start_time"] = time.time()
                    
                    with open(status_file_path, "w") as f:
                        json.dump(status_data, f)
                    
                    logging.info(f"NFT铸造流程已启动，会话ID: {minting_result.get('session_id')}")
                    
                    return jsonify({
                        "status": "processing",
                        "message": "已检测到转账，NFT铸造流程已启动，请稍候",
                        "tx_hash": tx_hash,
                        "minting_session_id": minting_result.get("session_id")
                    })
                    
                except Exception as mint_e:
                    logging.error(f"启动NFT铸造流程失败: {mint_e}")
                    return jsonify({
                        "status": "error",
                        "message": f"检测到转账，但启动铸造流程时出错: {str(mint_e)}",
                        "tx_hash": tx_hash
                    })
            else:
                # 没有找到匹配的状态文件，可能是直接转账的情况
                logging.warning(f"检测到转账但未找到匹配的状态文件，可能需要手动处理")
                return jsonify({
                    "status": "processing",
                    "message": "已检测到转账，正在处理中，请稍候",
                    "tx_hash": tx_hash
                })
        
        # 5. 如果没有找到转账，返回等待状态
        logging.info(f"未找到转账记录，返回等待转账状态")
        return jsonify({
            "status": "waiting_for_transfer",
            "message": "请转账3 ETH到指定地址以完成登记",
            "agent_address": agent_address,
            "required_eth": 3
        })
    
    except Exception as e:
        logging.error(f"检查注册状态失败: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/check-report-status', methods=['POST'])
def check_report_status():
    """
    检查举报状态的API接口
    """
    data = request.json
    token_id_a = data.get('token_id_a')
    token_id_b = data.get('token_id_b')
    user_address = data.get('user_address')
    
    if not token_id_a or not token_id_b or not user_address:
        return jsonify({"error": "缺少必要参数"}), 400
    
    try:
        # 初始化 web3 连接
        from web3 import Web3, HTTPProvider
        web3_session = requests.Session()
        web3_session.trust_env = False
        w3 = Web3(HTTPProvider("http://127.0.0.1:8545", session=web3_session))
        
        if not w3.is_connected():
            logging.error("无法连接到本地区块链")
            return jsonify({
                "status": "error",
                "message": "无法连接到区块链网络"
            }), 500
        
        # 读取合约地址
        with open("../python_call_contract/deploy_address.json", "r") as f:
            deploy_info = json.load(f)
        
        escrow_deposit_addr = deploy_info["EscrowDeposit"]
        
        # 读取ABI
        with open("../BDTP_contract/out/EscrowDeposit.sol/EscrowDeposit.json", "r") as f:
            artifact = json.load(f)
            escrow_deposit_abi = artifact["abi"]
        
        # 初始化合约
        EscrowDeposit = w3.eth.contract(address=escrow_deposit_addr, abi=escrow_deposit_abi)
        
        # 确保用户地址是校验和格式
        user_address = w3.to_checksum_address(user_address)
        
        # 查询交易记录，检查是否已经转账
        transfer_found = False
        tx_hash = None
        agent_address = "0x70997970C51812dc3A010C7d01b50e0d17dc79C8"
        required_value_wei = w3.to_wei(2, "ether")
        
        # 查询最近的区块
        latest_block = w3.eth.block_number
        start_block = max(0, latest_block - 50)  # 最多看最近50个区块
        
        logging.info(f"检查从区块 {start_block} 到 {latest_block} 的转账情况")
        
        for block_num in range(start_block, latest_block + 1):
            try:
                block = w3.eth.get_block(block_num, full_transactions=True)
                for tx in block.transactions:
                    from_addr = tx["from"].lower()
                    to_addr = (tx["to"] or "").lower() if tx["to"] else ""
                    value_wei = tx["value"]
                    
                    if from_addr == user_address.lower() and to_addr == agent_address.lower() and value_wei == required_value_wei:
                        transfer_found = True
                        tx_hash = tx["hash"].hex()
                        logging.info(f"发现从 {from_addr} 到 {to_addr} 的转账，金额: {w3.from_wei(value_wei, 'ether')} ETH，区块: {block_num}")
                        break
                
                if transfer_found:
                    break
            except Exception as e:
                logging.error(f"检查区块 {block_num} 时出错: {e}")
                continue
        
        # 查询举报事件
        # 检查InformerDeposited事件是否已经发生
        informer_deposited = False
        deposited_token_a = None
        deposited_token_b = None
        
        # 查看是否已经有举报存款事件
        try:
            deposit_filter = EscrowDeposit.events.InformerDeposited.create_filter(
                fromBlock=start_block,
                toBlock='latest',
                argument_filters={'informer': user_address}
            )
            deposit_events = deposit_filter.get_all_entries()
            
            # 检查events中是否有匹配的token id
            for event in deposit_events:
                event_token_a = event['args']['originalTokenId']
                event_token_b = event['args']['suspicionTokenId']
                
                # 检查是否匹配当前请求的token ids (无序)
                if (event_token_a == token_id_a and event_token_b == token_id_b) or \
                   (event_token_a == token_id_b and event_token_b == token_id_a):
                    informer_deposited = True
                    deposited_token_a = event_token_a
                    deposited_token_b = event_token_b
                    logging.info(f"找到匹配的InformerDeposited事件: {event}")
                    break
            
        except Exception as e:
            logging.error(f"查询InformerDeposited事件失败: {e}")
        
        # 查找成功和失败的事件
        informer_success = False
        informer_failure = False
        
        # 查询InformerSuccess事件
        try:
            success_filter = EscrowDeposit.events.InformerSuccess.create_filter(
                fromBlock=start_block,
                toBlock='latest',
                argument_filters={'informer': user_address}
            )
            success_events = success_filter.get_all_entries()
            
            for event in success_events:
                event_token_a = event['args'].get('originalTokenId')
                event_token_b = event['args'].get('suspicionTokenId')
                
                # 检查是否匹配
                if (event_token_a == token_id_a and event_token_b == token_id_b) or \
                   (event_token_a == token_id_b and event_token_b == token_id_a):
                    informer_success = True
                    logging.info(f"找到匹配的InformerSuccess事件: {event}")
                    break
        except Exception as e:
            logging.error(f"查询InformerSuccess事件失败: {e}")
        
        # 查询InformerFailure事件
        try:
            failure_filter = EscrowDeposit.events.InformerFailure.create_filter(
                fromBlock=start_block,
                toBlock='latest',
                argument_filters={'informer': user_address}
            )
            failure_events = failure_filter.get_all_entries()
            
            for event in failure_events:
                event_token_a = event['args'].get('originalTokenId')
                event_token_b = event['args'].get('suspicionTokenId')
                
                # 检查是否匹配
                if (event_token_a == token_id_a and event_token_b == token_id_b) or \
                   (event_token_a == token_id_b and event_token_b == token_id_a):
                    informer_failure = True
                    logging.info(f"找到匹配的InformerFailure事件: {event}")
                    break
        except Exception as e:
            logging.error(f"查询InformerFailure事件失败: {e}")
        
        # 查询举报状态的事务日志
        # 可以查看是否有任何事务提到了某些特定的关键词
        xrid_log_found = False
        log_output = ""
        
        try:
            # 使用subprocess查询日志文件
            cmd = ["grep", "-i", f"tokenIdA={token_id_a}", "../python_call_contract/function_7_informer.log"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.stdout:
                xrid_log_found = True
                log_output = result.stdout
        except Exception as e:
            logging.error(f"查询日志失败: {e}")
        
        # 根据查询结果返回状态
        if informer_success:
            # 举报成功
            return jsonify({
                "status": "completed",
                "result": "proven",
                "details": "系统确认存在转售行为，您的保证金已返还，并获得了额外奖励。"
            })
        elif informer_failure:
            # 举报失败
            return jsonify({
                "status": "completed",
                "result": "rejected",
                "details": "系统未检测到转售行为，您的保证金已被没收。"
            })
        elif informer_deposited:
            # 已经提交保证金，正在处理
            # 查询XRID.py的输出日志，获取更多进度信息
            processing_message = "正在进行转售检测分析..."
            
            # 尝试检查XRID日志获取进度
            if xrid_log_found:
                if "无转售行为" in log_output:
                    return jsonify({
                        "status": "completed",
                        "result": "rejected",
                        "details": "XRID结果: 无转售行为，举报不成立，保证金已被没收。"
                    })
                elif "存在转售行为" in log_output:
                    return jsonify({
                        "status": "completed", 
                        "result": "proven",
                        "details": "XRID结果: 存在转售行为，举报成立，您已获得奖励。"
                    })
                else:
                    processing_message = "正在运行XRID算法分析数据集相似度..."
            
            return jsonify({
                "status": "processing",
                "message": processing_message
            })
        elif transfer_found:
            # 已转账，但尚未提交保证金或记录不完整
            return jsonify({
                "status": "processing",
                "message": "已检测到保证金转账，正在提交举报信息..."
            })
        else:
            # 未转账
            return jsonify({
                "status": "waiting_for_transfer",
                "message": "等待转账2 ETH作为举报保证金"
            })
            
    except Exception as e:
        logging.error(f"检查举报状态失败: {e}")
        
        return jsonify({
            "status": "error",
            "message": f"检查状态时出错: {str(e)}"
        }), 500

@app.route('/api/check-transfer', methods=['POST'])
def check_transfer():
    """
    检查用户到Agent的转账是否已经完成，如果完成则启动相应的处理流程
    """
    data = request.json
    from_address = data.get('from_address')
    to_address = data.get('to_address')
    amount_eth = data.get('amount_eth')
    session_id = data.get('session_id')  # 获取会话ID以查找状态
    
    if not from_address or not to_address or not amount_eth:
        return jsonify({"error": "缺少必要参数"}), 400
    
    try:
        # 初始化 web3 连接
        from web3 import Web3, HTTPProvider
        web3_session = requests.Session()  # 使用已导入的requests模块
        web3_session.trust_env = False
        w3 = Web3(HTTPProvider("http://127.0.0.1:8545", session=web3_session))
        
        if not w3.is_connected():
            logging.error("无法连接到本地区块链")
            return jsonify({
                "status": "error",
                "message": "无法连接到区块链网络"
            }), 500
        
        # 查询最近的转账
        transfer_found = False
        tx_hash = None
        amount_wei = w3.to_wei(amount_eth, "ether")
        
        # 查询最近的区块
        latest_block = w3.eth.block_number
        start_block = max(0, latest_block - 20)  # 最多查看最近20个区块
        
        logging.info(f"检查从区块 {start_block} 到 {latest_block} 的转账情况")
        logging.info(f"查询转账: {from_address} -> {to_address}, 金额: {amount_eth} ETH")
        
        for block_num in range(start_block, latest_block + 1):
            try:
                block = w3.eth.get_block(block_num, full_transactions=True)
                for tx in block.transactions:
                    tx_from = tx["from"].lower()
                    tx_to = (tx["to"] or "").lower() if tx["to"] else ""
                    tx_value = tx["value"]
                    
                    # 检查是否匹配
                    if tx_from == from_address.lower() and tx_to == to_address.lower() and tx_value == amount_wei:
                        transfer_found = True
                        tx_hash = tx["hash"].hex()
                        logging.info(f"发现匹配的转账, 区块: {block_num}, 交易哈希: {tx_hash}")
                        break
                
                if transfer_found:
                    break
            except Exception as e:
                logging.error(f"检查区块 {block_num} 时出错: {e}")
                continue
        
        if transfer_found:
            # 转账已确认，检查是否需要启动后续处理流程
            if session_id:
                try:
                    # 查找对应的状态文件
                    status_file_path = os.path.join(os.path.dirname(__file__), f"register_status_{session_id}.json")
                    
                    if os.path.exists(status_file_path):
                        with open(status_file_path, "r") as f:
                            status_data = json.load(f)
                        
                        # 检查是否是无水印的情况，需要启动铸造流程
                        if status_data.get("result_type") == "no_watermark" and status_data.get("transfer_required"):
                            logging.info(f"检测到转账完成，开始为会话 {session_id} 启动NFT铸造流程")
                            
                            # 启动NFT铸造流程
                            metadata_url = status_data.get("metadata_url")
                            user_address = status_data.get("user_address")
                            ptau_info = status_data.get("ptau_info", {})
                            
                            if metadata_url and user_address:
                                try:
                                    minting_result = start_nft_minting(metadata_url, user_address, ptau_info)
                                    
                                    # 更新状态文件
                                    status_data["transfer_confirmed"] = True
                                    status_data["transfer_tx_hash"] = tx_hash
                                    status_data["minting_started"] = True
                                    status_data["minting_session_id"] = minting_result.get("session_id")
                                    
                                    with open(status_file_path, "w") as f:
                                        json.dump(status_data, f)
                                    
                                    logging.info(f"NFT铸造流程已为会话 {session_id} 启动成功")
                                    
                                    return jsonify({
                                        "status": "transfer_confirmed_minting_started",
                                        "message": "转账已确认，NFT铸造流程已启动",
                                        "tx_hash": tx_hash,
                                        "minting_status": minting_result
                                    })
                                except Exception as mint_e:
                                    logging.error(f"启动NFT铸造流程失败: {mint_e}")
                                    return jsonify({
                                        "status": "transfer_found_minting_failed",
                                        "message": "转账已确认，但启动铸造流程时出错",
                                        "tx_hash": tx_hash,
                                        "error": str(mint_e)
                                    })
                            else:
                                logging.error(f"状态文件缺少必要的铸造信息")
                                return jsonify({
                                    "status": "transfer_found_missing_info",
                                    "message": "转账已确认，但缺少铸造所需信息",
                                    "tx_hash": tx_hash
                                })
                        else:
                            # 其他类型的转账确认
                            logging.info(f"转账已确认，但非无水印铸造类型: {status_data.get('result_type')}")
                except Exception as status_e:
                    logging.error(f"处理状态文件时出错: {status_e}")
            
            # 默认返回转账确认状态
            return jsonify({
                "status": "transfer_found",
                "message": "已检测到转账",
                "tx_hash": tx_hash
            })
        else:
            return jsonify({
                "status": "no_transfer",
                "message": "未检测到转账"
            })
    
    except Exception as e:
        logging.error(f"检查转账失败: {e}")
        return jsonify({
            "status": "error",
            "message": f"检查转账时出错: {str(e)}"
        }), 500
    
@app.route('/api/check-report-result', methods=['POST'])
def check_report_result():
    """
    检查举报结果的API接口 - 从日志文件读取结果
    """
    data = request.json
    token_id_a = data.get('token_id_a')
    token_id_b = data.get('token_id_b')
    user_address = data.get('user_address')
    
    if not token_id_a or not token_id_b or not user_address:
        return jsonify({"error": "缺少必要参数"}), 400
    
    try:
        # 查找对应的日志文件
        logs_dir = os.path.join(os.path.dirname(__file__), "logs")
        report_index_path = os.path.join(logs_dir, "report_index.json")
        
        if not os.path.exists(report_index_path):
            return jsonify({
                "status": "processing",
                "message": "未找到举报记录，请确认是否已提交举报"
            })
        
        with open(report_index_path, "r") as f:
            report_index = json.load(f)
        
        # 查找匹配的报告
        report_key = f"{token_id_a}_{token_id_b}_{user_address}"
        if report_key not in report_index:
            # 检查是否只是顺序不同
            report_key_alt = f"{token_id_b}_{token_id_a}_{user_address}"
            if report_key_alt in report_index:
                report_key = report_key_alt
            else:
                return jsonify({
                    "status": "processing",
                    "message": "未找到匹配的举报记录"
                })
        
        report_info = report_index[report_key]
        log_path = report_info["log_path"]
        
        if not os.path.exists(log_path):
            return jsonify({
                "status": "processing",
                "message": "检测正在准备中，日志文件尚未生成"
            })
        
        # 读取日志文件内容
        with open(log_path, "r") as f:
            log_content = f.read()
        
        # 检查日志内容判断结果
        if "无转售行为" in log_content and "保证金已被没收" in log_content:
            return jsonify({
                "status": "completed",
                "result": "rejected",
                "message": "检测未发现转售行为，举报不成立",
                "details": "XRID结果: 无转售行为，系统未检测到转售行为，您的保证金已被没收。"
            })
        elif "存在转售行为" in log_content and "获得了保证金奖励" in log_content:
            return jsonify({
                "status": "completed", 
                "result": "proven",
                "message": "检测确认存在转售行为，举报成立",
                "details": "XRID结果: 存在转售行为，系统确认存在转售行为，您的保证金已返还，并获得了额外奖励。"
            })
        elif "confiscateInformerDeposit" in log_content:
            return jsonify({
                "status": "completed",
                "result": "rejected",
                "message": "检测未发现转售行为，举报不成立",
                "details": "系统未检测到转售行为，您的保证金已被没收。"
            })
        elif "claimInformerSuccess" in log_content:
            return jsonify({
                "status": "completed",
                "result": "proven",
                "message": "检测确认存在转售行为，举报成立",
                "details": "系统确认存在转售行为，您的保证金已返还，并获得了额外奖励。"
            })
        elif "正在比较" in log_content or "特征提取" in log_content:
            return jsonify({
                "status": "processing",
                "message": "正在进行XRID算法分析",
                "progress": "正在对比数据集相似度..."
            })
        elif "开始从 IPFS 下载" in log_content or "开始下载 & 检测" in log_content:
            return jsonify({
                "status": "processing",
                "message": "正在下载数据进行检测",
                "progress": "正在下载数据集..."
            })
        elif "举报保证金提交成功" in log_content:
            return jsonify({
                "status": "processing",
                "message": "已提交举报保证金，开始检测流程",
                "progress": "准备下载数据集..."
            })
        elif "已检测到" in log_content and "ETH" in log_content:
            return jsonify({
                "status": "processing",
                "message": "已检测到转账，开始举报流程",
                "progress": "准备提交举报..."
            })
        elif "转账" in log_content and "ETH" in log_content:
            return jsonify({
                "status": "processing",
                "message": "等待转账完成",
                "progress": "请完成转账..."
            })
        
        # 检查检测是否已经很久没有进展
        start_time = report_info.get("start_time", 0)
        if time.time() - start_time > 30 * 60:  # 如果已经过了30分钟
            return jsonify({
                "status": "error",
                "message": "检测超时，请联系管理员",
                "progress": "检测过程耗时过长"
            })
        
        # 如果没有明确结果，返回处理中
        return jsonify({
            "status": "processing",
            "message": "检测正在进行中",
            "progress": "等待检测完成..."
        })
            
    except Exception as e:
        logging.error(f"检查举报结果失败: {e}")
        return jsonify({
            "status": "error",
            "message": f"检查结果时出错: {str(e)}"
        }), 500
    
@app.route('/api/check-watermark', methods=['POST'])
def check_watermark():
    """
    检查数据集是否存在水印
    """
    data = request.json
    dataset_cid = data.get('dataset_cid')
    metadata_url = data.get('metadata_url')
    
    if not dataset_cid:
        return jsonify({"error": "缺少必要参数: dataset_cid"}), 400
    
    try:
        # 创建临时目录用于下载和检查数据集
        import tempfile
        import os
        import subprocess
        import time
        
        temp_dir = tempfile.mkdtemp()
        dataset_path = os.path.join(temp_dir, "dataset.zip")
        
        # 记录检查开始时间
        start_time = time.time()
        logging.info(f"开始检查水印，数据集CID: {dataset_cid}, 元数据URL: {metadata_url}, 临时目录: {temp_dir}")
        
        # 下载数据集
        try:
            download_cmd = ["node", "../BDTP/downloadFromIPFS.js", dataset_cid, dataset_path]
            logging.info(f"执行下载命令: {download_cmd}")
            # 添加下载超时，60秒
            subprocess.run(download_cmd, cwd="../BDTP", capture_output=True, check=True, timeout=60)
            logging.info(f"下载完成，耗时: {time.time() - start_time:.2f}秒")
        except subprocess.TimeoutExpired as e:
            logging.error(f"下载数据集超时: {e}")
            return jsonify({
                "has_watermark": False,
                "error": "下载数据集超时，请稍后重试",
                "timeout": True
            }), 408
        except Exception as e:
            logging.error(f"下载数据集失败: {e}")
            return jsonify({
                "has_watermark": False,
                "error": f"无法下载数据集: {str(e)}",
                "error_occurred": True
            })
        
        # 检查水印 - 修复路径问题并添加超时
        try:
            # 注意：这里使用的是相对于 api_server.py 的路径
            watermark_cmd = ["python", "features/checkForWatermark.py", "--input", dataset_path, "-v"]
            logging.info(f"执行水印检测命令: {watermark_cmd}, 当前工作目录: {os.getcwd()}")
            
            # 添加120秒的超时控制
            result = subprocess.run(watermark_cmd, capture_output=True, text=True, timeout=120)
            output = result.stdout.strip()
            
            logging.info(f"水印检测完成，耗时: {time.time() - start_time:.2f}秒, 返回值: {result.returncode}")
            
            # 如果输出是"1"，表示检测到水印
            has_watermark = output.strip().startswith("1")
            
            # 构建详细信息
            details = {}
            if has_watermark:
                # 尝试从输出中提取更多信息
                import re
                match = re.search(r"提取的哈希值:\s*([a-f0-9]+)", output)
                if match:
                    details["extracted_hash"] = match.group(1)
                
                match = re.search(r"匹配的预期哈希:\s*([a-f0-9]+)", output)
                if match:
                    details["matched_hash"] = match.group(1)
            
            return jsonify({
                "has_watermark": has_watermark,
                "message": "检测到水印，该数据集可能是从其他地方购买并转售的" if has_watermark else "未检测到水印",
                "details": details,
                "raw_output": output,
                "execution_time": f"{time.time() - start_time:.2f}秒"
            })
            
        except subprocess.TimeoutExpired as e:
            logging.error(f"检查水印超时: {e}")
            return jsonify({
                "has_watermark": False,
                "error": "水印检测超时，可能是数据集过大或系统繁忙",
                "timeout": True,
                "execution_time": f"{time.time() - start_time:.2f}秒"
            }), 408
        except Exception as e:
            logging.error(f"检查水印失败: {e}")
            return jsonify({
                "has_watermark": False,
                "error": f"检查水印失败: {str(e)}",
                "error_occurred": True,
                "execution_time": f"{time.time() - start_time:.2f}秒"
            })
        
    except Exception as e:
        logging.error(f"水印检查过程出错: {e}")
        return jsonify({
            "has_watermark": False,
            "error": f"水印检查过程出错: {str(e)}",
            "error_occurred": True
        }), 500
    finally:
        # 清理临时文件
        import shutil
        try:
            if 'temp_dir' in locals() and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
                logging.info(f"已清理临时目录: {temp_dir}")
        except Exception as e:
            logging.warning(f"清理临时目录失败: {e}")
    
@app.route('/api/generate-ptau', methods=['POST'])
def generate_ptau():
    """生成Powers of Tau初始文件"""
    data = request.json
    dataset_path = data.get('dataset_path')
    user_address = data.get('user_address')
    
    if not dataset_path or not user_address:
        return jsonify({"error": "缺少必要参数: dataset_path 和 user_address"}), 400
    
    try:
        # 使用用户地址作为用户ID
        user_id = user_address.replace('0x', '')[:8]  # 取地址前8位作为用户ID
        
        # 生成Powers of Tau
        result = generate_ptau_for_dataset(dataset_path, user_id)
        
        if result["status"] == "success":
            return jsonify({
                "status": "success",
                "message": "Powers of Tau初始化完成",
                "total_pixels": result["total_pixels"],
                "optimal_config": result["optimal_config"],
                "user_id": user_id,
                "next_step": "user_contribution"
            })
        else:
            return jsonify(result), 500
            
    except Exception as e:
        logging.error(f"生成Powers of Tau失败: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/get-initial-ptau/<user_id>', methods=['GET'])
def get_initial_ptau(user_id):
    """获取初始ptau文件供用户下载"""
    try:
        generator = PowerOfTauGenerator()
        user_temp_dir = os.path.join(generator.temp_dir, f"user_{user_id}")
        
        # 查找初始ptau文件
        ptau_files = [f for f in os.listdir(user_temp_dir) if f.endswith('_0000.ptau')]
        
        if not ptau_files:
            return jsonify({"error": "未找到初始ptau文件"}), 404
            
        ptau_file_path = os.path.join(user_temp_dir, ptau_files[0])
        
        return send_file(
            ptau_file_path, 
            as_attachment=True, 
            download_name=ptau_files[0],
            mimetype='application/octet-stream'
        )
        
    except Exception as e:
        logging.error(f"获取初始ptau文件失败: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/upload-contribution/<user_id>', methods=['POST'])
def upload_contribution(user_id):
    """接收用户的ptau贡献文件"""
    try:
        if 'ptau_file' not in request.files:
            return jsonify({"error": "未找到ptau文件"}), 400
            
        ptau_file = request.files['ptau_file']
        constraint_power = request.form.get('constraint_power', type=int)
        
        if not constraint_power:
            return jsonify({"error": "缺少constraint_power参数"}), 400
        
        # 保存用户贡献的ptau文件
        generator = PowerOfTauGenerator()
        user_temp_dir = os.path.join(generator.temp_dir, f"user_{user_id}")
        os.makedirs(user_temp_dir, exist_ok=True)
        
        contributed_ptau_path = os.path.join(user_temp_dir, f"pot{constraint_power}_0001.ptau")
        ptau_file.save(contributed_ptau_path)
        
        # 完成Powers of Tau仪式的后续步骤
        final_ptau_path = generator.complete_ptau_ceremony_from_user_contribution(
            contributed_ptau_path, user_id, constraint_power
        )
        
        # 清理临时文件
        generator.cleanup_temp_files(user_id)
        
        return jsonify({
            "status": "success",
            "message": "Powers of Tau仪式完成",
            "final_ptau_path": final_ptau_path
        })
        
    except Exception as e:
        logging.error(f"处理用户贡献失败: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8765)