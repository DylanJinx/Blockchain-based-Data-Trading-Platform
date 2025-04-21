import os
import pandas as pd
import joblib

from xgboost import XGBClassifier
from sklearn.preprocessing import StandardScaler

# -------------------------------
# 1) 使用已训练好的模型 + 标准化器，对 test.csv 做预测
# -------------------------------
def predict_on_test_csv(
    model_path: str,
    scaler_path: str,
    test_csv_path: str,
    feature_cols: list,
    output_csv_path: str = None
):
    """
    使用已有的 XGBoost 模型和 scaler，对没有 Label 的 test.csv 进行推理，
    并将预测标签 (0/1) 和预测概率附加到结果中。
    """
    # 1.1 加载模型 & scaler
    model = joblib.load(model_path)   # xgboost模型
    scaler = joblib.load(scaler_path) # 标准化器

    # 1.2 读取 test.csv (没有 Label)
    df_test = pd.read_csv(test_csv_path)

    # 1.3 提取特征并标准化
    X_test = df_test[feature_cols].values
    X_test_scaled = scaler.transform(X_test)

    # 1.4 预测
    y_pred = model.predict(X_test_scaled)                 # 0/1
    y_pred_proba = model.predict_proba(X_test_scaled)     # shape=(n,2), [:,1] 是预测为1的概率

    # 1.5 将结果写回 df_test
    df_test["Predicted_Label"] = y_pred
    df_test["Prob_of_1"] = y_pred_proba[:, 1]

    # 1.6 如果指定了 output_csv_path，则保存
    if output_csv_path:
        df_test.to_csv(output_csv_path, index=False)
        print(f"[Info] 预测结果已保存至: {output_csv_path}")
    else:
        print("[Info] 预测结果(前5行):")
        print(df_test.head())

    return df_test


# -------------------------------
# 2) 微调初步模型 (在带 Label 的 train.csv 上) 并再次预测 test.csv
# -------------------------------
def finetune_and_predict(
    base_model_path: str,
    scaler_path: str,
    train_csv_path: str,
    test_csv_path: str,
    feature_cols: list,
    finetune_model_path: str = "models/xgb_finetune.joblib",
    output_csv_path: str = None
):
    """
    先用带 Label 的 train.csv 微调初步模型，然后对 test.csv 做预测，保存结果。
    """
    # 2.1 加载初步模型 & scaler
    base_model = joblib.load(base_model_path)  # xgboost模型
    scaler = joblib.load(scaler_path)          # 标准化器

    # 2.2 加载 train.csv (包含 Label 列)
    df_train = pd.read_csv(train_csv_path)
    X_train = df_train[feature_cols].values
    y_train = df_train["Label"].values
    X_train_scaled = scaler.transform(X_train)

    # 2.3 在 train.csv 上“微调”（这里是简易的重新fit）
    print("[Info] 开始微调...")
    #   复制初步模型的参数，生成一个新XGBClassifier，然后fit
    base_params = base_model.get_params()
    finetuned_model = XGBClassifier(**base_params)
    finetuned_model.fit(X_train_scaled, y_train)
    print("[Info] 微调完成。")

    # 2.4 将微调后的模型保存
    os.makedirs(os.path.dirname(finetune_model_path), exist_ok=True)
    joblib.dump(finetuned_model, finetune_model_path)
    print(f"[Info] 微调后模型已保存 -> {finetune_model_path}")

    # 2.5 再对 test.csv 做预测（同样 test.csv 没有 Label）
    df_test = pd.read_csv(test_csv_path)
    X_test = df_test[feature_cols].values
    X_test_scaled = scaler.transform(X_test)
    y_pred = finetuned_model.predict(X_test_scaled)
    y_pred_proba = finetuned_model.predict_proba(X_test_scaled)

    df_test["Predicted_Label"] = y_pred
    df_test["Prob_of_1"] = y_pred_proba[:, 1]

    if output_csv_path:
        df_test.to_csv(output_csv_path, index=False)
        print(f"[Info] 使用微调模型预测的结果已保存 -> {output_csv_path}")
    else:
        print("[Info] 微调后预测结果(前5行):")
        print(df_test.head())

    return finetuned_model, df_test


# -------------------------------
# 3) 主函数入口
# -------------------------------
def main():
    # 3.1 配置路径 (根据你的真实情况修改)
    model_path = "models/xgb_init_cifar.joblib"   # 初步模型
    scaler_path = "models/scaler_cifar.joblib"    # 标准化器

    train_csv_path = "./train.csv"  # 包含Label
    test_csv_path = "./test.csv"    # 不包含Label

    # 3.2 定义 5 个特征列 (与CSV中的列保持一致)
    feature_cols = [
        "Average_SSIM_DINO",
        "MMD_ViT",
        "MMD_BLIP2",
        "Wasserstein_Distance_BLIP2",
        "Average_Cosine_Similarity_BLIP2"
    ]

    # 3.3 第一步：使用初步模型，预测 test.csv 的标签
    print("=== (1) 使用初步模型预测 test.csv ===")
    _ = predict_on_test_csv(
        model_path=model_path,
        scaler_path=scaler_path,
        test_csv_path=test_csv_path,
        feature_cols=feature_cols,
        output_csv_path="test_predictions_initial.csv"  # 可以改成你想输出的文件名
    )

    # 3.4 第二步：用 train.csv (带 Label) 微调，然后再预测 test.csv
    print("\n=== (2) 微调并再次预测 test.csv ===")
    finetune_and_predict(
        base_model_path=model_path,
        scaler_path=scaler_path,
        train_csv_path=train_csv_path,
        test_csv_path=test_csv_path,
        feature_cols=feature_cols,
        finetune_model_path="models/xgb_finetune.joblib",
        output_csv_path="test_predictions_finetuned.csv"
    )