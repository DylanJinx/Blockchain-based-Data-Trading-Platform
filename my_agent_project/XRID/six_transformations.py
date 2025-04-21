# six_transformations.py
import os
import shutil
from PIL import Image, ImageEnhance, ImageFile
import numpy as np
import cv2
from tqdm import tqdm

# 为了避免在处理大图像时出错
ImageFile.LOAD_TRUNCATED_IMAGES = True

###########################
#      变换函数定义区
###########################

def rotate_image(image, angle):
    """旋转图像，不扩展画布，保持尺寸"""
    return image.rotate(angle, resample=Image.Resampling.BILINEAR, expand=False)

def crop_image(image, crop_percentage):
    """
    中心裁剪图像
    crop_percentage: 裁剪比例，如 10 表示裁剪 10%
    """
    width, height = image.size
    crop_width = int(width * (crop_percentage / 100.0))
    crop_height = int(height * (crop_percentage / 100.0))
    left = crop_width
    upper = crop_height
    right = width - crop_width
    lower = height - crop_height
    cropped = image.crop((left, upper, right, lower))
    # 裁剪后再缩放回原尺寸
    return cropped.resize((width, height), resample=Image.Resampling.LANCZOS)

def scale_image(image, scale_percentage):
    """
    缩放图像
    scale_percentage: 缩放比例，如 80 表示缩放至 80%
    """
    scale_factor = scale_percentage / 100.0
    width, height = image.size
    new_size = (int(width * scale_factor), int(height * scale_factor))
    scaled = image.resize(new_size, resample=Image.Resampling.LANCZOS)
    # 再缩放回原始尺寸
    return scaled.resize((width, height), resample=Image.Resampling.LANCZOS)

def adjust_color(image, adjustment_factor):
    """
    调整图像颜色
    adjustment_factor: 调整因子，如 1.5 表示颜色增强 1.5 倍
    """
    enhancer = ImageEnhance.Color(image)
    return enhancer.enhance(adjustment_factor)

def add_noise(image, noise_level):
    """
    为图像添加高斯噪声
    noise_level: 噪声强度，如 10 表示方差为 10
    """
    img_array = np.array(image).astype(np.float32)
    sigma = noise_level ** 0.5
    gauss = np.random.normal(0, sigma, img_array.shape).astype(np.float32)
    noisy_img = img_array + gauss
    noisy_img = np.clip(noisy_img, 0, 255).astype('uint8')
    return Image.fromarray(noisy_img)

def mirror_image(image, direction):
    """
    镜像图像
    direction: 'horizontal_flip' 或 'vertical_flip'
    """
    if direction == 'horizontal_flip':
        return image.transpose(Image.FLIP_LEFT_RIGHT)
    elif direction == 'vertical_flip':
        return image.transpose(Image.FLIP_TOP_BOTTOM)
    else:
        raise ValueError(f"未知的镜像方向: {direction}")

###########################
#    变换参数配置区
###########################

TRANSFORM_PARAMS = {
    'rotation': {
        'range': (-90, 90),      # 从 -90 度到 90 度
        'step': 10,              # 每次增加 10 度
        'function': rotate_image,
        'description': '每次旋转10度，范围-90度到90度'
    },
    'cropping': {
        'range': (10, 30),       # 从裁剪 10% 到 30%
        'step': 10,              # 每次增加 10%
        'function': crop_image,
        'description': '每次裁剪10%的边缘，范围10%到30%'
    },
    'scaling': {
        'range': (80, 120),      # 从缩放 80% 到 120%
        'step': 10,              # 每次增加 10%
        'function': scale_image,
        'description': '每次缩放10%，范围80%到120%'
    },
    'color_adjustment': {
        'range': (0.5, 2.0),     # 从 0.5 倍到 2.0 倍
        'step': 0.5,             # 每次增加 0.5
        'function': adjust_color,
        'description': '每次颜色调整0.5倍，范围0.5到2.0倍'
    },
    'adding_noise': {
        'range': (10, 100),      # 从噪声强度 10 到 100
        'step': 10,             # 每次增加 10
        'function': add_noise,
        'description': '每次增加10的噪声强度，范围10到100'
    },
    'mirroring': {
        'steps': ['horizontal_flip', 'vertical_flip'],
        'function': mirror_image,
        'description': '包括水平镜像和垂直镜像'
    }
}

###########################
#      核心处理逻辑
###########################

def move_images_to_original(base_path):
    """
    在 base_path 下创建 original 文件夹，并把 base_path 中所有的图片移动过去。
    """
    original_dir = os.path.join(base_path, 'original')
    os.makedirs(original_dir, exist_ok=True)

    # 找出所有图片文件
    all_files = os.listdir(base_path)
    image_files = [
        f for f in all_files
        if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif'))
        and not f.startswith('.')  # 排除隐藏文件
        and os.path.isfile(os.path.join(base_path, f))  # 确保是文件
    ]

    # 移动图片文件到 original/ 文件夹
    for img_file in image_files:
        src_path = os.path.join(base_path, img_file)
        dst_path = os.path.join(original_dir, img_file)
        shutil.move(src_path, dst_path)


def apply_transformations(base_path):
    """
    对 base_path 文件夹里的所有图片先移动到 original/，再进行多种变换。
    变换后的结果按不同参数，保存在 base_path 下对应的子文件夹中。
    """

    # 1. 确保 original/ 目录存在，并移动所有图片到该目录
    move_images_to_original(base_path)

    original_dir = os.path.join(base_path, 'original')
    print(f"所有图片已移动至: {original_dir}")

    # 2. 获取 original/ 下所有原始图像文件
    original_images = [
        f for f in os.listdir(original_dir)
        if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif'))
        and not f.startswith('.')
    ]
    
    if not original_images:
        print(f"在 {original_dir} 中未找到任何原始图像文件，结束。")
        return

    # 3. 对每种变换执行操作
    for transform_type, params in TRANSFORM_PARAMS.items():
        print(f"\n正在应用变换: {transform_type} ({params['description']})")

        # 如果是镜像变换
        if transform_type == 'mirroring':
            steps = params['steps']  # ['horizontal_flip', 'vertical_flip']
            for step in steps:
                transformed_dir = os.path.join(base_path, transform_type, step)
                os.makedirs(transformed_dir, exist_ok=True)

                for img_name in tqdm(original_images, desc=f" {transform_type.capitalize()} {step}", leave=False):
                    img_path = os.path.join(original_dir, img_name)
                    try:
                        with Image.open(img_path) as img:
                            img = img.convert('RGB')  # 确保图像为 RGB 模式
                            transformed_img = params['function'](img, step)
                            transformed_img.save(os.path.join(transformed_dir, img_name), format='PNG')
                    except Exception as e:
                        print(f"处理 {img_path} 时出错: {e}")

        else:
            # 针对其他数值型变换
            current_step = params['range'][0]
            while current_step <= params['range'][1]:
                # 构建子文件夹名称（如 rotation_-90, color_adjustment_1.0 等）
                if transform_type == 'color_adjustment':
                    step_str = f"{transform_type}_{current_step:.1f}"
                else:
                    # 例如 rotation_-90, scaling_80 等
                    step_str = f"{transform_type}_{int(current_step)}"

                transformed_dir = os.path.join(base_path, transform_type, step_str)
                os.makedirs(transformed_dir, exist_ok=True)

                for img_name in tqdm(original_images, desc=f" {transform_type.capitalize()} {step_str}", leave=False):
                    img_path = os.path.join(original_dir, img_name)
                    try:
                        with Image.open(img_path) as img:
                            img = img.convert('RGB')
                            # 执行具体变换
                            transformed_img = params['function'](img, current_step)
                            transformed_img.save(os.path.join(transformed_dir, img_name), format='PNG')
                    except Exception as e:
                        print(f"处理 {img_path} 时出错: {e}")

                # 增加步长
                current_step += params['step']

    print("\n所有变换已成功应用并保存。")