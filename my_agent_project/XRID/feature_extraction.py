import os
import torch
import numpy as np
import pandas as pd
from PIL import Image
from skimage.metrics import structural_similarity as ssim
from torchvision import transforms
import ot
from sklearn.utils import shuffle

from transformers import (
    ViTModel, 
    ViTImageProcessor,
    AutoImageProcessor,
    AutoModel, 
    Blip2Processor,
    Blip2Model
)

########################
#   1. 模型加载
########################

def load_vit_model(device):
    vit_model = ViTModel.from_pretrained("google/vit-base-patch16-224").to(device)
    vit_model.eval()
    vit_preprocess = ViTImageProcessor.from_pretrained("google/vit-base-patch16-224")
    return vit_model, vit_preprocess

def load_dino_model(device):
    dino_preprocessor = AutoImageProcessor.from_pretrained("facebook/dinov2-base")
    dino_model = AutoModel.from_pretrained("facebook/dinov2-base").to(device)
    dino_model.eval()
    return dino_model, dino_preprocessor

def load_blip2_model(device):
    blip2_processor = Blip2Processor.from_pretrained("Salesforce/blip2-flan-t5-xl")
    blip2_model = Blip2Model.from_pretrained("Salesforce/blip2-flan-t5-xl").to(device)
    blip2_model.eval()
    return blip2_model, blip2_processor

########################
#   2. 特征提取
########################

def extract_feature_vit(model, preprocess, img_path, device):
    try:
        pil_image = Image.open(img_path).convert("RGB")
    except:
        return None
    inputs = preprocess(images=pil_image, return_tensors="pt").to(device)
    with torch.no_grad():
        outputs = model(**inputs)
    cls_emb = outputs.last_hidden_state[:, 0, :]
    cls_emb = cls_emb / cls_emb.norm(dim=-1, keepdim=True)
    return cls_emb.squeeze(0).cpu().numpy()

def extract_feature_dino(model, preprocess, img_path, device):
    try:
        pil_image = Image.open(img_path).convert("RGB")
    except:
        return None
    inputs = preprocess(images=pil_image, return_tensors="pt").to(device)
    with torch.no_grad():
        outputs = model(**inputs)
    cls_emb = outputs.last_hidden_state[:, 0, :]
    cls_emb = cls_emb / cls_emb.norm(dim=-1, keepdim=True)
    return cls_emb.squeeze(0).cpu().numpy()

def extract_feature_blip2(model, preprocess, img_path, device):
    try:
        pil_image = Image.open(img_path).convert("RGB")
    except:
        return None
    inputs = preprocess(pil_image, return_tensors="pt").to(device)
    with torch.no_grad():
        vision_outputs = model.vision_model(**inputs)
    cls_emb = vision_outputs.last_hidden_state[:, 0, :]
    cls_emb = cls_emb / cls_emb.norm(dim=-1, keepdim=True)
    return cls_emb.squeeze(0).cpu().numpy()

########################
#   3. 指标计算
########################

def calculate_ssim(img_path1, img_path2):
    try:
        img1 = Image.open(img_path1).convert("RGB").resize((224, 224))
        img2 = Image.open(img_path2).convert("RGB").resize((224, 224))
        img1_np = np.array(img1)
        img2_np = np.array(img2)
        ssim_val = ssim(img1_np, img2_np, channel_axis=2)
        return ssim_val
    except:
        return None

def gaussian_kernel(x, y, sigma=1.0):
    x = x[:, np.newaxis, :]
    y = y[np.newaxis, :, :]
    return np.exp(-np.sum((x - y)**2, axis=2) / (2 * sigma**2))

def calculate_mmd(features1, features2, sigma=1.0):
    K = gaussian_kernel(features1, features1, sigma)
    L = gaussian_kernel(features2, features2, sigma)
    P = gaussian_kernel(features1, features2, sigma)
    return K.mean() + L.mean() - 2 * P.mean()

def calculate_wasserstein_distance(features1, features2):
    try:
        features1 = (features1 - features1.mean(axis=0)) / (features1.std(axis=0) + 1e-8)
        features2 = (features2 - features2.mean(axis=0)) / (features2.std(axis=0) + 1e-8)
        cost_matrix = ot.dist(features1, features2, metric='euclidean')
        a = np.ones((features1.shape[0],)) / features1.shape[0]
        b = np.ones((features2.shape[0],)) / features2.shape[0]
        w_dist = ot.emd2(a, b, cost_matrix)
        return w_dist
    except:
        return None

def calculate_average_cosine_similarity(features1, features2):
    norm1 = features1 / np.linalg.norm(features1, axis=1, keepdims=True)
    norm2 = features2 / np.linalg.norm(features2, axis=1, keepdims=True)
    sim_matrix = np.dot(norm1, norm2.T)
    return sim_matrix.mean()

########################
#   4. 先特征匹配，再算SSIM
########################

def compute_average_ssim_by_best_match(
    orig_folder,
    transform_folder,
    dino_model,
    dino_preprocess,
    device
):
    """
    1) 提取orig_folder中每张图的DINO特征 -> orig_feats
    2) 提取transform_folder中每张图的DINO特征 -> tamp_feats
    3) 构造相似度矩阵 sim_matrix = tamp_feats x orig_feats^T
    4) 对每个变换图找最匹配原图，计算像素级SSIM
    5) 返回平均SSIM
    """
    orig_files = [
        f for f in os.listdir(orig_folder)
        if f.lower().endswith(('.jpg','.jpeg','.png','.bmp','.gif'))
    ]
    transform_files = [
        f for f in os.listdir(transform_folder)
        if f.lower().endswith(('.jpg','.jpeg','.png','.bmp','.gif'))
    ]
    if not orig_files or not transform_files:
        return 0.0

    # 提取原图特征
    orig_data = []
    for f in orig_files:
        feat = extract_feature_dino(dino_model, dino_preprocess, os.path.join(orig_folder, f), device)
        if feat is not None:
            orig_data.append((f, feat))
    if not orig_data:
        return 0.0

    # 提取变换图特征
    transform_data = []
    for f in transform_files:
        feat = extract_feature_dino(dino_model, dino_preprocess, os.path.join(transform_folder, f), device)
        if feat is not None:
            transform_data.append((f, feat))
    if not transform_data:
        return 0.0

    orig_names, orig_feats = zip(*orig_data)
    transform_names, transform_feats = zip(*transform_data)
    orig_feats = np.stack(orig_feats, axis=0)
    transform_feats = np.stack(transform_feats, axis=0)

    # 计算相似度矩阵 (dot前最好特征已归一化)
    sim_matrix = np.dot(transform_feats, orig_feats.T)

    ssim_vals = []
    for i in range(len(transform_names)):
        row = sim_matrix[i]
        best_idx = np.argmax(row)
        t_path = os.path.join(transform_folder, transform_names[i])
        o_path = os.path.join(orig_folder, orig_names[best_idx])
        val = calculate_ssim(o_path, t_path)
        if val is not None:
            ssim_vals.append(val)

    if ssim_vals:
        return float(np.mean(ssim_vals))
    else:
        return 0.0

########################
#   5. 后处理：添加 Label、删除列、打乱 -> 另存 train.csv
########################

def create_train_csv(comparison_csv_path):
    """
    生成 train.csv 的后处理函数：
    1) 给数据打 Label (Comparison Type里含"Positive"为1, "Non-Resale"为0)
    2) 删除不需要的列
    3) 打乱并输出 train.csv
    """
    if not os.path.isfile(comparison_csv_path):
        print(f"[Warning] CSV 文件不存在: {comparison_csv_path}")
        return

    df = pd.read_csv(comparison_csv_path)

    def assign_label(comp_type: str) -> int:
        lower_type = str(comp_type).lower()
        if "positive" in lower_type:
            return 1
        elif "non-resale" in lower_type:
            return 0
        else:
            return 0

    if 'Comparison Type' in df.columns:
        df['Label'] = df['Comparison Type'].apply(assign_label)
    else:
        df['Label'] = 0

    # 删除指定列
    for col in ['Comparison Type', 'Transformation Type', 'Step']:
        if col in df.columns:
            df.drop(columns=col, inplace=True)

    df = shuffle(df, random_state=42)

    # 与 dataset_dir 同级目录
    parent_dir = os.path.dirname(comparison_csv_path)
    train_csv_path = os.path.join(parent_dir, "train.csv")
    df.to_csv(train_csv_path, index=False)
    print(f"[Info] 已生成 train.csv -> {train_csv_path}")



########################
#   6. 主函数
########################

def run_feature_comparison(dataset_dir, suspicion_dir=None):
    """
    根据是否传入 suspicion_dir 来区分两种情况：
    
    1) 如果 suspicion_dir is None：
       - 遍历 dataset_dir 下的 original/ 与各变换子文件夹，
         计算 5 个特征，存到 comparison_results.csv
       - 若有 negative_results.csv，则拼接
       - 生成 train.csv（打 label, 删列, 打乱）
       
    2) 如果 suspicion_dir 不为空：
       - 将 dataset_dir 视为“原始数据集所在目录” (里面应有原图),
         对比 suspicion_dir 下的图片
       - 输出 test.csv，其中只有 5 个字段：
            Average_SSIM_DINO,
            MMD_ViT,
            MMD_BLIP2,
            Wasserstein_Distance_BLIP2,
            Average_Cosine_Similarity_BLIP2
       - 不再生成 comparison_results.csv、train.csv 等
    """
    device = torch.device("cuda" if torch.cuda.is_available() 
                          else "mps" if torch.backends.mps.is_available()
                          else "cpu")
    print(f"[feature_extraction] Running on device={device}")

    print("[Step] 加载模型 (DINO, ViT, BLIP2)...")
    dino_model, dino_preprocess = load_dino_model(device)
    vit_model, vit_preprocess = load_vit_model(device)
    blip2_model, blip2_preprocess = load_blip2_model(device)

    # -------------------
    # 情况2: 若 suspicion_dir 不为空，就对比 dataset_dir/original 与 suspicion_dir
    # -------------------
    if suspicion_dir is not None:
        if not os.path.isdir(os.path.join(dataset_dir)):
            print(f"[Error] 原始数据集目录不存在: {dataset_dir}")
            return
        if not os.path.isdir(suspicion_dir):
            print(f"[Error] 怀疑数据集目录不存在: {suspicion_dir}")
            return

        # 原始图片目录
        orig_dir = os.path.join(dataset_dir, 'original')  # 这里你可以要求 dataset_dir 直接就是 "imagenet-tench/original"

        # 提取特征并计算五个指标
        # （这里给你一个简单示例，若要“先特征匹配再SSIM”，可参考 compute_average_ssim_by_best_match）
        # -------------------------------------------------------------------
        print(f"[Info] 对比: {orig_dir} vs {suspicion_dir}")

        # 取所有文件
        orig_files = [
            f for f in os.listdir(orig_dir)
            if f.lower().endswith(('.jpg','.jpeg','.png','.bmp','.gif'))
        ]
        susp_files = [
            f for f in os.listdir(suspicion_dir)
            if f.lower().endswith(('.jpg','.jpeg','.png','.bmp','.gif'))
        ]
        if not orig_files or not susp_files:
            print("[Warning] 原图或怀疑数据集为空，跳过。")
            return

        # 计算 SSIM
        avg_ssim_dino = compute_average_ssim_by_best_match(
            orig_folder=orig_dir,
            transform_folder=suspicion_dir,
            dino_model=dino_model,
            dino_preprocess=dino_preprocess,
            device=device
        )
        # 计算 MMD (ViT, BLIP2)
        #   你可以把extract_feature_vit, extract_feature_blip2写法同 run_feature_comparison中 “for f in ...”
        #   这里只是简略示例
        vit_orig_feats, vit_susp_feats = [], []
        blip2_orig_feats, blip2_susp_feats = [], []

        for f in orig_files:
            path = os.path.join(orig_dir, f)
            feat_v = extract_feature_vit(vit_model, vit_preprocess, path, device)
            feat_b = extract_feature_blip2(blip2_model, blip2_preprocess, path, device)
            if feat_v is not None:
                vit_orig_feats.append(feat_v)
            if feat_b is not None:
                blip2_orig_feats.append(feat_b)

        for f in susp_files:
            path = os.path.join(suspicion_dir, f)
            feat_v = extract_feature_vit(vit_model, vit_preprocess, path, device)
            feat_b = extract_feature_blip2(blip2_model, blip2_preprocess, path, device)
            if feat_v is not None:
                vit_susp_feats.append(feat_v)
            if feat_b is not None:
                blip2_susp_feats.append(feat_b)

        mmd_vit = calculate_mmd(np.array(vit_orig_feats), np.array(vit_susp_feats)) \
                  if vit_orig_feats and vit_susp_feats else 0.0
        
        if blip2_orig_feats and blip2_susp_feats:
            arr_o = np.array(blip2_orig_feats)
            arr_s = np.array(blip2_susp_feats)
            mmd_blip2 = calculate_mmd(arr_o, arr_s)
            w_dist = calculate_wasserstein_distance(arr_o, arr_s)
            w_dist_blip2 = w_dist if w_dist is not None else 0.0
            avg_cos_blip2 = calculate_average_cosine_similarity(arr_o, arr_s)
        else:
            mmd_blip2 = 0.0
            w_dist_blip2 = 0.0
            avg_cos_blip2 = 0.0

        # 汇总
        result_dict = {
            "Average_SSIM_DINO": avg_ssim_dino,
            "MMD_ViT": mmd_vit,
            "MMD_BLIP2": mmd_blip2,
            "Wasserstein_Distance_BLIP2": w_dist_blip2,
            "Average_Cosine_Similarity_BLIP2": avg_cos_blip2
        }

        df = pd.DataFrame([result_dict])
        test_csv_path = os.path.join(os.path.dirname(dataset_dir), "test.csv")
        df.to_csv(test_csv_path, index=False)
        print(f"[Done] 已生成 test.csv -> {test_csv_path}")

        return

    # -------------------
    # 情况1: 如果没给 suspicion_dir，就执行原先多变换+comparison_results.csv 的逻辑
    # -------------------

    # 检查 original/
    orig_dir = os.path.join(dataset_dir, 'original')
    if not os.path.isdir(orig_dir):
        print(f"[Error] original/ 目录不存在: {orig_dir}")
        return

    # 找变换类型
    transform_types = [
        d for d in os.listdir(dataset_dir)
        if os.path.isdir(os.path.join(dataset_dir, d)) and d != 'original'
    ]

    results = []
    for ttype in transform_types:
        ttype_path = os.path.join(dataset_dir, ttype)
        steps = [
            d for d in os.listdir(ttype_path)
            if os.path.isdir(os.path.join(ttype_path, d))
        ]
        for step in steps:
            print(f"\n[Compare] transform={ttype}, step={step}")
            step_dir = os.path.join(ttype_path, step)

            # 1) Average_SSIM_DINO (先DINO特征匹配，再像素SSIM)
            avg_ssim_dino = compute_average_ssim_by_best_match(
                orig_folder=orig_dir,
                transform_folder=step_dir,
                dino_model=dino_model,
                dino_preprocess=dino_preprocess,
                device=device
            )

            # 2) ViT -> MMD
            vit_orig_feats, vit_tamp_feats = [], []
            orig_files = [
                f for f in os.listdir(orig_dir)
                if f.lower().endswith(('.jpg','.jpeg','.png','.bmp','.gif'))
            ]
            for f in orig_files:
                path = os.path.join(orig_dir, f)
                feat = extract_feature_vit(vit_model, vit_preprocess, path, device)
                if feat is not None:
                    vit_orig_feats.append(feat)

            tamp_files = [
                f for f in os.listdir(step_dir)
                if f.lower().endswith(('.jpg','.jpeg','.png','.bmp','.gif'))
            ]
            for f in tamp_files:
                path = os.path.join(step_dir, f)
                feat = extract_feature_vit(vit_model, vit_preprocess, path, device)
                if feat is not None:
                    vit_tamp_feats.append(feat)

            if not vit_orig_feats or not vit_tamp_feats:
                mmd_vit = 0.0
            else:
                mmd_vit = calculate_mmd(np.array(vit_orig_feats), np.array(vit_tamp_feats))

            # 3) BLIP2 -> MMD, W-dist, Cos
            blip2_orig_feats, blip2_tamp_feats = [], []
            for f in orig_files:
                path = os.path.join(orig_dir, f)
                feat = extract_feature_blip2(blip2_model, blip2_preprocess, path, device)
                if feat is not None:
                    blip2_orig_feats.append(feat)

            for f in tamp_files:
                path = os.path.join(step_dir, f)
                feat = extract_feature_blip2(blip2_model, blip2_preprocess, path, device)
                if feat is not None:
                    blip2_tamp_feats.append(feat)

            if not blip2_orig_feats or not blip2_tamp_feats:
                mmd_blip2 = 0.0
                w_dist_blip2 = 0.0
                avg_cos_blip2 = 0.0
            else:
                arr_o = np.array(blip2_orig_feats)
                arr_t = np.array(blip2_tamp_feats)
                mmd_blip2 = calculate_mmd(arr_o, arr_t)
                w_dist = calculate_wasserstein_distance(arr_o, arr_t)
                w_dist_blip2 = w_dist if w_dist is not None else 0.0
                avg_cos_blip2 = calculate_average_cosine_similarity(arr_o, arr_t)

            row = {
                "Comparison Type": "Positive Sample",
                "Transformation Type": ttype,
                "Step": step,
                "Average_SSIM_DINO": avg_ssim_dino,
                "MMD_ViT": mmd_vit,
                "MMD_BLIP2": mmd_blip2,
                "Wasserstein_Distance_BLIP2": w_dist_blip2,
                "Average_Cosine_Similarity_BLIP2": avg_cos_blip2
            }
            results.append(row)

    # 生成 comparison_results.csv
    parent_dir = os.path.dirname(dataset_dir)
    comparison_csv_path = os.path.join(parent_dir, "comparison_results.csv")
    df = pd.DataFrame(results, columns=[
        "Comparison Type",
        "Transformation Type",
        "Step",
        "Average_SSIM_DINO",
        "MMD_ViT",
        "MMD_BLIP2",
        "Wasserstein_Distance_BLIP2",
        "Average_Cosine_Similarity_BLIP2"
    ])
    df.to_csv(comparison_csv_path, index=False)
    print(f"\n[Info] 对比结果已保存 -> {comparison_csv_path}")

    # 先定义一份“comparison_results.csv”的列顺序
    column_order = [
        "Comparison Type",
        "Transformation Type",
        "Step",
        "Average_SSIM_DINO",
        "MMD_ViT",
        "MMD_BLIP2",
        "Wasserstein_Distance_BLIP2",
        "Average_Cosine_Similarity_BLIP2"
    ]

    # 如果有 negative_results.csv，把它(除表头)按正确顺序追加到 comparison_results.csv
    negative_csv_path = os.path.join(parent_dir, "negative_results.csv")
    if os.path.isfile(negative_csv_path):
        print("[Info] 发现 negative_results.csv，开始追加...")

        # 1) 读取 negative_results.csv
        neg_df = pd.read_csv(negative_csv_path)

        # 2) 让列顺序与 comparison_results.csv 一致
        neg_df = neg_df[column_order]

        # 3) 以追加模式写入 comparison_results.csv，不写入表头 (header=False)
        with open(comparison_csv_path, 'a', encoding='utf-8') as outf:
            neg_df.to_csv(outf, index=False, header=False)

        print("[Info] 已追加 negative_results.csv (重排列顺序，不含表头)")


    # 生成 train.csv
    create_train_csv(comparison_csv_path)
    print("[Done] 已额外生成 train.csv。")