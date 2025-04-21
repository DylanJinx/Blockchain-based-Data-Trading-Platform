import os
import pandas as pd
from feature_extraction import (
    extract_feature_dino, extract_feature_vit, extract_feature_blip2,
    calculate_ssim, calculate_mmd, calculate_wasserstein_distance, calculate_average_cosine_similarity
)
from transformers import AutoImageProcessor, AutoModel
import torch

def run_suspicion_comparison(original_dir, suspicion_dir, device):
    """
    比较原始数据集和怀疑数据集，计算并输出五个特征
    """
    # 加载模型
    dino_model = AutoModel.from_pretrained("facebook/dinov2-base").to(device)
    dino_preprocess = AutoImageProcessor.from_pretrained("facebook/dinov2-base")
    vit_model = AutoModel.from_pretrained("google/vit-base-patch16-224").to(device)
    vit_preprocess = AutoImageProcessor.from_pretrained("google/vit-base-patch16-224")
    blip2_model = AutoModel.from_pretrained("Salesforce/blip2-flan-t5-xl").to(device)
    blip2_preprocess = AutoImageProcessor.from_pretrained("Salesforce/blip2-flan-t5-xl")

    # 获取文件列表
    orig_files = [
        f for f in os.listdir(original_dir)
        if f.lower().endswith(('.jpg','.jpeg','.png','.bmp','.gif'))
    ]
    suspicion_files = [
        f for f in os.listdir(suspicion_dir)
        if f.lower().endswith(('.jpg','.jpeg','.png','.bmp','.gif'))
    ]

    # 提取特征
    orig_feats = [extract_feature_dino(dino_model, dino_preprocess, os.path.join(original_dir, f), device) for f in orig_files]
    suspicion_feats = [extract_feature_dino(dino_model, dino_preprocess, os.path.join(suspicion_dir, f), device) for f in suspicion_files]

    # 计算 MMD 和 Cosine Similarity
    mmd_vit = calculate_mmd(orig_feats, suspicion_feats)  # ViT的MMD计算
    mmd_blip2 = calculate_mmd(orig_feats, suspicion_feats)  # BLIP2的MMD计算
    w_dist_blip2 = calculate_wasserstein_distance(orig_feats, suspicion_feats)  # Wasserstein Distance
    avg_cos_blip2 = calculate_average_cosine_similarity(orig_feats, suspicion_feats)  # Cosine Similarity

    # 计算 SSIM
    ssim_vals = []
    for orig_file, suspicion_file in zip(orig_files, suspicion_files):
        orig_path = os.path.join(original_dir, orig_file)
        suspicion_path = os.path.join(suspicion_dir, suspicion_file)
        ssim_vals.append(calculate_ssim(orig_path, suspicion_path))

    avg_ssim_dino = sum(ssim_vals) / len(ssim_vals) if ssim_vals else 0.0

    # 保存结果到 CSV
    results = {
        "Average_SSIM_DINO": avg_ssim_dino,
        "MMD_VIT": mmd_vit,
        "MMD_BLIP2": mmd_blip2,
        "Wasserstein_Distance_BLIP2": w_dist_blip2,
        "Average_Cosine_Similarity_BLIP2": avg_cos_blip2
    }

    df = pd.DataFrame([results])

    # 保存为 test.csv
    output_csv = "test.csv"
    df.to_csv(output_csv, index=False)
    print(f"[Info] 对比结果已保存到: {output_csv}")


if __name__ == "__main__":
    # 获取设备
    device = torch.device("cuda" if torch.cuda.is_available() 
                          else "mps" if torch.backends.mps.is_available()
                          else "cpu")

    # 设置原图和怀疑图的目录
    original_dir = "imagenet-tench/original"
    suspicion_dir = "imagenet-suspicion"

    # 运行对比
    run_suspicion_comparison(original_dir, suspicion_dir, device)