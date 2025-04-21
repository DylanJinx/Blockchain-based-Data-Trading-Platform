# XRID.py
import os
import argparse
import six_transformations
import feature_extraction
import predict_and_finetune

os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"

def main():
    parser = argparse.ArgumentParser(description='XRID Pipeline')

    # 情况1：只传 --transform_dir
    parser.add_argument('--transform_dir', type=str, default=None,
                        help='Directory containing the images to perform six transformations.')
    # 情况2：同时传 --original_dir 和 --suspicion_dir
    parser.add_argument('--original_dir', type=str, default=None,
                        help='Directory containing the original dataset for suspicion comparison.')
    parser.add_argument('--suspicion_dir', type=str, default=None,
                        help='Directory containing the suspicious dataset.')
    parser.add_argument('--predict_and_finetune', action='store_true',
                        help='Run the predict_and_finetune.py script')

    args = parser.parse_args()

    if args.predict_and_finetune:
        print("[Step] Running predict_and_finetune.py ...")
        predict_and_finetune.main()  
        return

    # ========== 情况1: 如果提供了 transform_dir，则执行图像增强 ==========
    if args.transform_dir:
        transform_folder = args.transform_dir
        if not os.path.isdir(transform_folder):
            raise ValueError(f"[Error] 图像增强阶段：目录不存在 -> {transform_folder}")
        print(f"[Step] 开始对 {transform_folder} 中的图像进行六种变换...")
        six_transformations.apply_transformations(transform_folder)
        print("[Done] 六种变换处理完成。\n")
        # 不做特征对比，也不做怀疑数据集比较
        return

    # ========== 情况2: 若同时提供 original_dir + suspicion_dir，则对比原图与怀疑集 ==========
    if args.original_dir and args.suspicion_dir:
        if not os.path.isdir(args.original_dir):
            raise ValueError(f"[Error] original_dir 不存在: {args.original_dir}")
        if not os.path.isdir(args.suspicion_dir):
            raise ValueError(f"[Error] suspicion_dir 不存在: {args.suspicion_dir}")

        print(f"[Step] 正在比较 {args.original_dir} 与 {args.suspicion_dir} ...")
        feature_extraction.run_feature_comparison(
            dataset_dir=args.original_dir,  # 这里将 original_dir 视为 dataset_dir
            suspicion_dir=args.suspicion_dir
        )
        print("[Done] 已完成对比怀疑数据集。")
        return
    
    # ========== 如果仅提供 original_dir (而无 suspicion_dir)，则跑“情况1”相似度对比(多子文件夹) ==========
    if args.original_dir:
        if not os.path.isdir(args.original_dir):
            raise ValueError(f"[Error] 特征提取阶段：目录不存在 -> {args.original_dir}")
        print(f"[Step] 对 {args.original_dir} 执行特征提取与相似度计算(情况1)...")
        feature_extraction.run_feature_comparison(args.original_dir)
        print("[Done] 特征提取与相似度对比阶段完成。")
        return

    # 如果都没命中，则给点提示
    print("[Info] 你既没有传 --transform_dir，也没传 ( --original_dir + --suspicion_dir )，"
          "也没用 --predict_and_finetune，故无事可做。")

if __name__ == "__main__":
    main()
