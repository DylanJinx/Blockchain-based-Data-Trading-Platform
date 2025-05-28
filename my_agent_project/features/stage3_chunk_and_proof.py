#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
第三阶段：数据分块和零知识证明生成
在登记数据集时，如果检测到水印，使用已计算的最优约束参数(X,M,m)对ZK输入数据进行分块
"""

import os
import sys
import json
import logging
import numpy as np
import shutil
from typing import Dict, List, Any, Optional

# 添加features目录到path
sys.path.append(os.path.join(os.path.dirname(__file__)))

from addWatermark import find_zk_input_for_buy_hash

class Stage3ChunkProcessor:
    """第三阶段数据分块处理器"""
    
    def __init__(self, data_dir=None):
        """
        初始化分块处理器
        
        Args:
            data_dir: 数据目录，默认为../data
        """
        if data_dir is None:
            self.data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
        else:
            self.data_dir = data_dir
        
        self.zk_inputs_dir = os.path.join(self.data_dir, "zk_inputs")
        self.chunked_inputs_dir = os.path.join(self.data_dir, "chunked_inputs")
        
        # 确保目录存在
        os.makedirs(self.chunked_inputs_dir, exist_ok=True)
        
        logging.info(f"Stage3ChunkProcessor初始化完成，数据目录: {self.data_dir}")
    
    def chunk_zk_input_data(self, buy_hash: str, chunk_pixel_size: int, 
                           output_session_dir: str = None) -> Dict[str, Any]:
        """
        根据chunk_pixel_size对ZK输入数据进行分块
        学习LSB_groth16/generate_input.py的分块逻辑
        
        Args:
            buy_hash: 买家哈希值
            chunk_pixel_size: 每块的像素数量 (即参数m)
            output_session_dir: 输出会话目录（如果为None则自动创建）
        
        Returns:
            分块结果信息
        """
        try:
            logging.info(f"开始分块处理，buy_hash: {buy_hash[:16]}..., chunk_size: {chunk_pixel_size}")
            
            # 1. 查找对应的ZK输入文件
            zk_input_result = find_zk_input_for_buy_hash(buy_hash, self.data_dir)
            if not zk_input_result:
                raise ValueError(f"未找到buy_hash对应的ZK输入文件: {buy_hash[:16]}...")
            
            zk_input_files = zk_input_result['zk_input_files']
            logging.info(f"找到 {len(zk_input_files)} 个ZK输入文件")
            
            # 2. 创建输出目录
            if output_session_dir is None:
                output_session_dir = os.path.join(
                    self.chunked_inputs_dir, 
                    f"session_{buy_hash[:16]}"
                )
            
            os.makedirs(output_session_dir, exist_ok=True)
            
            chunk_output_dir = os.path.join(output_session_dir, f"chunk_pixel_{chunk_pixel_size}")
            os.makedirs(chunk_output_dir, exist_ok=True)
            
            chunked_files = []
            processing_summary = []
            
            # 3. 处理每个ZK输入文件（每张图片）
            for img_idx, file_info in enumerate(zk_input_files):
                zk_file_path = file_info['file_path']
                filename = file_info['filename']
                
                logging.info(f"处理第 {img_idx + 1} 张图片: {filename}")
                
                # 加载ZK输入数据
                with open(zk_file_path, 'r', encoding='utf-8') as f:
                    zk_data = json.load(f)
                
                metadata = zk_data['metadata']
                pixel_data = zk_data['pixel_data']
                
                # 获取像素数据（已经是列优先排列）
                ori_pixels = np.array(pixel_data['original_pixels'])
                wm_pixels = np.array(pixel_data['watermarked_pixels'])
                binary_watermark = pixel_data['binary_watermark']
                
                total_pixels = metadata['total_pixels']
                image_dimensions = metadata['image_dimensions']
                
                logging.info(f"  图片尺寸: {image_dimensions}, 总像素: {total_pixels}")
                
                # 4. 按照LSB_groth16/generate_input.py的逻辑进行分块
                chunked_files_for_image = self._chunk_single_image(
                    ori_pixels, wm_pixels, binary_watermark,
                    total_pixels, chunk_pixel_size,
                    chunk_output_dir, img_idx + 1
                )
                
                chunked_files.extend(chunked_files_for_image)
                
                processing_summary.append({
                    "image_index": img_idx + 1,
                    "original_file": filename,
                    "total_pixels": total_pixels,
                    "image_dimensions": image_dimensions,
                    "chunks_created": len(chunked_files_for_image)
                    # 移除chunk_files详细列表，减少输出冗余
                })
                
                logging.info(f"  ✅ 完成分块，生成 {len(chunked_files_for_image)} 个分块文件")
            
            # 5. 生成会话信息文件
            session_info = {
                "buy_hash": buy_hash,
                "chunk_pixel_size": chunk_pixel_size,
                "total_images": len(zk_input_files),
                "total_chunks": len(chunked_files),
                "output_directory": chunk_output_dir,
                "processing_summary": processing_summary,
                "chunked_files_count": len(chunked_files),  # 只保存数量，不保存详细列表
                "chunked_files_dir": chunk_output_dir,  # 保存目录路径
                "timestamp": time.time(),
                "format_version": "1.0"
            }
            
            session_info_file = os.path.join(output_session_dir, "session_info.json")
            with open(session_info_file, 'w', encoding='utf-8') as f:
                json.dump(session_info, f, indent=2, ensure_ascii=False)
            
            logging.info(f"✅ 分块处理完成:")
            logging.info(f"  - 处理图片数: {len(zk_input_files)}")
            logging.info(f"  - 生成分块数: {len(chunked_files)}")
            logging.info(f"  - 输出目录: {chunk_output_dir}")
            logging.info(f"  - 会话信息: {session_info_file}")
            
            return {
                "success": True,
                "session_info": session_info,
                "session_info_file": session_info_file,
                "chunk_output_dir": chunk_output_dir,
                "total_chunks": len(chunked_files)
            }
        
        except Exception as e:
            logging.error(f"分块处理失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _chunk_single_image(self, ori_pixels: np.ndarray, wm_pixels: np.ndarray, 
                           binary_watermark: List[int], total_pixels: int, 
                           chunk_pixel_size: int, output_dir: str, image_index: int) -> List[str]:
        """
        对单张图片进行分块处理
        完全按照LSB_groth16/generate_input.py的逻辑
        
        Args:
            ori_pixels: 原始像素数组 (列优先排列)
            wm_pixels: 水印像素数组 (列优先排列)
            binary_watermark: 二进制水印数组
            total_pixels: 总像素数
            chunk_pixel_size: 分块大小
            output_dir: 输出目录
            image_index: 图片索引
        
        Returns:
            分块文件路径列表
        """
        chunk_files = []
        
        # 计算填充像素数（如果最后一块不够chunk_pixel_size）
        zero_pixels = chunk_pixel_size - (total_pixels % chunk_pixel_size) if (total_pixels % chunk_pixel_size != 0) else 0
        
        # 计算扩展后的水印大小，并补充足够的0
        extended_watermark_size = total_pixels * 3 + zero_pixels * 3
        extended_watermark = binary_watermark + [0] * (extended_watermark_size - len(binary_watermark))
        
        # 计算分块数
        chunks = (total_pixels + chunk_pixel_size - 1) // chunk_pixel_size
        
        logging.info(f"    分块计算: 总像素={total_pixels}, 分块大小={chunk_pixel_size}, 分块数={chunks}, 填充像素={zero_pixels}")
        
        # 为当前图片创建子目录
        image_output_dir = os.path.join(output_dir, f'input_{image_index}')
        os.makedirs(image_output_dir, exist_ok=True)
        
        for chunk_idx in range(chunks):
            start_idx = chunk_idx * chunk_pixel_size
            end_idx = min((chunk_idx + 1) * chunk_pixel_size, total_pixels)
            
            logging.debug(f"    处理分块 {chunk_idx + 1}/{chunks}: 像素范围 {start_idx}-{end_idx}")
            
            # 分块后，如果最后一块不足chunk_pixel_size，就需要补零
            if end_idx - start_idx < chunk_pixel_size:
                fill_size = chunk_pixel_size - (end_idx - start_idx)
                ori_fill = np.zeros((fill_size, 3), dtype=int)
                wm_fill = np.zeros((fill_size, 3), dtype=int)
                ori_block_pixels = np.vstack([ori_pixels[start_idx:end_idx], ori_fill])
                wm_block_pixels = np.vstack([wm_pixels[start_idx:end_idx], wm_fill])
            else:
                ori_block_pixels = ori_pixels[start_idx:end_idx]
                wm_block_pixels = wm_pixels[start_idx:end_idx]
            
            # 特别处理最后一个分块的水印数据
            if chunk_idx == chunks - 1:
                end_extend_idx = end_idx * 3 + zero_pixels * 3
                current_watermark = extended_watermark[start_idx * 3 : end_extend_idx]
            else:
                current_watermark = extended_watermark[start_idx * 3 : end_idx * 3]
            
            # 生成LSB_groth16格式的JSON数据
            json_data = {
                "originalPixelValues": ori_block_pixels.tolist(),
                "Watermark_PixelValues": wm_block_pixels.tolist(),
                "binaryWatermark": current_watermark,
                "binaryWatermark_num": "513"
            }
            
            # 保存分块文件
            output_filename = os.path.join(image_output_dir, f'input_{image_index}_{chunk_idx + 1}.json')
            with open(output_filename, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=4)
            
            chunk_files.append(output_filename)
            logging.debug(f"    ✅ 保存分块文件: {os.path.basename(output_filename)}")
        
        logging.info(f"    ✅ 图片 {image_index} 分块完成，生成 {len(chunk_files)} 个文件")
        return chunk_files

def process_watermarked_dataset_registration(buy_hash: str, optimal_config: Dict[str, Any], user_address: str = None) -> Dict[str, Any]:
    """
    在数据集登记时检测到水印后的处理流程
    使用登记时已计算的最优约束参数进行分块
    
    Args:
        buy_hash: 检测到的买家哈希值
        optimal_config: 登记时计算的最优约束配置，包含X、M、m参数
        user_address: 用户地址（用于生成唯一的用户ID）
    
    Returns:
        处理结果
    """
    try:
        logging.info("=== 第三阶段：检测到水印数据集，开始分块处理 ===")
        logging.info(f"Buy hash: {buy_hash[:16]}...")
        logging.info(f"User address: {user_address}")
        logging.info(f"最优约束配置: {optimal_config}")
        
        # 提取关键参数
        chunk_pixel_size = optimal_config['m']  # 每块像素数
        constraint_power = optimal_config['power']  # X (幂次)
        num_chunks_expected = optimal_config['M']  # 分块数
        
        logging.info(f"分块参数: m={chunk_pixel_size}, X=2^{constraint_power}, M={num_chunks_expected}")
        
        # 创建分块处理器
        processor = Stage3ChunkProcessor()
        
        # 执行分块处理
        result = processor.chunk_zk_input_data(
            buy_hash=buy_hash,
            chunk_pixel_size=chunk_pixel_size
        )
        
        if result['success']:
            # 添加约束配置信息到结果中
            result['optimal_config'] = optimal_config
            result['ready_for_proof_generation'] = True
            
            logging.info("✅ 第三阶段分块处理完成！")
            
            # 🚀 正确的流程：分块完成后，立即生成Powers of Tau初始文件
            # 而不是立即创建LSB实验目录！LSB实验目录应该等Powers of Tau完成后再创建
            
            # 获取分块信息
            chunk_pixel_size = optimal_config.get('m', 29)
            constraint_power = optimal_config.get('power', 16)
            total_chunks = result.get('total_chunks', 0)
            
            logging.info(f"✅ 第三阶段数据分块处理完成")
            logging.info(f"分块结果: {total_chunks} 个分块文件已生成")
            logging.info(f"准备Powers of Tau初始文件，等待用户在浏览器中贡献")
            
            # 生成Powers of Tau初始文件，准备用户贡献
            try:
                from features.poweroftau_generator import PowerOfTauGenerator
                generator = PowerOfTauGenerator()
                
                # 🔧 Bug修复：使用用户地址生成唯一的用户ID，而不是买家哈希
                # 这样每个不同的用户都会有不同的用户ID
                if user_address:
                    user_id = user_address.replace('0x', '')[:8].upper()
                    user_id_source = "用户地址"
                else:
                    # 如果没有用户地址，回退到买家哈希（兼容性）
                    user_id = buy_hash[:8].upper()
                    user_id_source = "买家哈希"
                    
                logging.info(f"生成的用户ID: {user_id} (来源: {user_id_source})")
                
                # 生成Powers of Tau初始文件
                ptau_result = generator.generate_initial_ptau_for_user_contribution(
                    constraint_power=constraint_power,
                    user_id=user_id
                )
                
                if ptau_result.get("status") == "success":
                    logging.info(f"✅ Powers of Tau初始文件生成成功: {ptau_result.get('initial_ptau_path')}")
                    
                    # 创建分块完成状态文件，供Powers of Tau完成后使用
                    current_dir = os.path.dirname(os.path.abspath(__file__))
                    project_root = os.path.dirname(os.path.dirname(current_dir))
                    lsb_dir = os.path.join(project_root, "LSB_groth16")
                    
                    stage3_status_file = os.path.join(lsb_dir, f"stage3_completed_{user_id}.json")
                    stage3_status = {
                        "buyer_hash": buy_hash,
                        "buyer_hash_16": buy_hash[:16],
                        "chunk_pixel_size": chunk_pixel_size,
                        "constraint_power": constraint_power,
                        "total_chunks": total_chunks,
                        "optimal_config": optimal_config,
                        "chunked_data_dir": result.get('chunk_output_dir'),
                        "stage3_completion_time": time.time(),
                        "user_id": user_id,
                        "user_address": user_address,  # 🔧 保存用户地址供后续使用
                        "user_id_source": user_id_source,  # 记录用户ID来源
                        "status": "stage3_completed_waiting_ptau",
                        "ready_for_stage4": False  # 等Powers of Tau完成后设为True
                    }
                    
                    with open(stage3_status_file, 'w') as f:
                        json.dump(stage3_status, f, indent=2)
                    
                    logging.info(f"✅ 阶段3状态文件已保存: {stage3_status_file}")
                    
                    return {
                        "status": "copyright_violation",
                        "message": "检测到侵权行为，需要您贡献随机性以生成零知识证明",
                        "background_message": "系统检测到该数据集包含水印，表明可能是从其他地方购买后转售。为了生成零知识证明，需要您在浏览器中贡献一些随机性。",
                        "requires_user_contribution": True,
                        "user_id": user_id,
                        "constraint_power": constraint_power,
                        "ptau_info": {
                            "initial_ptau_path": ptau_result.get("initial_ptau_path"),
                            "constraint_power": constraint_power,
                            "total_chunks": total_chunks,
                            "chunk_pixel_size": chunk_pixel_size
                        },
                        "zk_proof_result": {
                            "stage": "stage3_chunking_completed",
                            "chunks_generated": total_chunks,
                            "next_step": "powers_of_tau_contribution"
                        }
                    }
                else:
                    logging.error(f"❌ Powers of Tau初始文件生成失败: {ptau_result.get('error')}")
                    return {
                        "status": "stage3_failed",
                        "message": f"Powers of Tau初始化失败: {ptau_result.get('error')}",
                        "error": ptau_result.get('error')
                    }
                    
            except Exception as ptau_e:
                logging.error(f"❌ Powers of Tau生成失败: {ptau_e}")
                return {
                    "status": "stage3_failed", 
                    "message": f"Powers of Tau生成失败: {str(ptau_e)}",
                    "error": str(ptau_e)
                }
        else:
            logging.error(f"分块处理失败: {result['error']}")
            return {
                "status": "chunking_failed",
                "message": f"分块处理失败: {result['error']}",
                "error": result['error']
            }
    
    except Exception as e:
        logging.error(f"第三阶段处理失败: {str(e)}")
        return {
            "status": "stage3_failed", 
            "message": f"第三阶段处理失败: {str(e)}",
            "error": str(e)
        }

# 为了兼容性，导入time模块
import time

if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    
    # 示例参数（实际使用时从登记阶段获取）
    test_buy_hash = "4b9f3139de796443209eefd90bf43deff2d5bd4902346e604022bcd825f28136e"
    test_optimal_config = {
        "power": 19,
        "constraint_size": 524288, 
        "M": 4,
        "m": 7140,
        "total_time": 120.0
    }
    
    print("=== 第三阶段测试 ===")
    result = process_watermarked_dataset_registration(test_buy_hash, test_optimal_config)
    print(json.dumps(result, indent=2, ensure_ascii=False)) 