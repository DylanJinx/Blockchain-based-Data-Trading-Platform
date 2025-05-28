from PIL import Image
import numpy as np
import os
import json

def load_image(path):
    return Image.open(path).convert('RGB')  # 确保都是RGB

def ensure_directory_exists(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

def process_images(ori_path, wm_path, binary_watermark, chunk_pixels):
    """
    1. 读取 ori_path 下的原图、wm_path 下的水印图
    2. 使用与 watermark.py 一致的列优先 ('F') 方式展平像素
    3. 将对应的像素块以及当前的水印bit存进 json 文件
    """
    # 支持多种图像格式
    image_extensions = ['.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp']
    files = []
    for ext in image_extensions:
        files.extend([f for f in os.listdir(ori_path) if f.lower().endswith(ext)])
    
    # 创建输出根目录
    root_output_dir = './input_json_files'
    ensure_directory_exists(root_output_dir)
    
    for i, file in enumerate(files):
        ori_img = load_image(os.path.join(ori_path, file))
        wm_img  = load_image(os.path.join(wm_path, file))
        
        # PIL: ori_img.size = (width, height)
        width, height = ori_img.size
        
        # 以 (height, width, 3) 的格式展开 => np.shape=(height, width, 3)
        # 默认 np.array() 读出来是 [height, width, channels]
        # 然后用 order='F' 扁平化保证与 watermark.py "for x in range(width): for y in range(height):" 一致
        ori_pixels = np.array(ori_img).reshape(-1, 3, order='F')
        wm_pixels  = np.array(wm_img).reshape(-1, 3, order='F')
        
        total_pixels = width * height
        
        # 为每个分块大小创建单独的处理
        for chunk_pixel in chunk_pixels:
            zero_pixels = chunk_pixel - (total_pixels % chunk_pixel) if (total_pixels % chunk_pixel != 0) else 0
            
            # 计算扩展后的水印大小，并补充足够的 0
            extended_watermark_size = total_pixels * 3 + zero_pixels * 3
            extended_watermark = binary_watermark + [0] * (extended_watermark_size - len(binary_watermark))
            
            chunks = (total_pixels + chunk_pixel - 1) // chunk_pixel
            
            # 创建每个图像的独立目录（在根输出目录下）
            image_folder = os.path.join(root_output_dir, f'chunk_pixel_{chunk_pixel}/input_{i+1}')
            ensure_directory_exists(image_folder)
            
            for j in range(chunks):
                start_idx = j * chunk_pixel
                end_idx   = min((j + 1) * chunk_pixel, total_pixels)
                
                # 分块后，如果最后一块不足 chunk_pixel，就需要补零
                if end_idx - start_idx < chunk_pixel:
                    fill_size = (chunk_pixel - (end_idx - start_idx)) * 3
                    ori_fill = np.zeros((fill_size // 3, 3), dtype=int)
                    wm_fill  = np.zeros((fill_size // 3, 3), dtype=int)
                    ori_block_pixels = np.vstack([ori_pixels[start_idx:end_idx], ori_fill])
                    wm_block_pixels  = np.vstack([wm_pixels[start_idx:end_idx],  wm_fill])
                else:
                    ori_block_pixels = ori_pixels[start_idx:end_idx]
                    wm_block_pixels  = wm_pixels[start_idx:end_idx]

                # 特别处理最后一个分块
                if j == chunks - 1:
                    end_extend_idx = end_idx * 3 + zero_pixels * 3
                    current_watermark = extended_watermark[start_idx * 3 : end_extend_idx]
                else:
                    current_watermark = extended_watermark[start_idx * 3 : end_idx * 3]

                json_data = {
                    "originalPixelValues": ori_block_pixels.tolist(),
                    "Watermark_PixelValues": wm_block_pixels.tolist(),
                    "binaryWatermark": current_watermark,
                    "binaryWatermark_num": str(len(binary_watermark))  # 使用binary_watermark数组的总长度
                }

                output_filename = os.path.join(image_folder, f'input_{i+1}_{j+1}.json')
                with open(output_filename, 'w', encoding='utf-8') as f:
                    json.dump(json_data, f, indent=4)

            print(f'[处理完成] 图像 {i+1}: {file}, 分块大小 {chunk_pixel}, 分块数 {chunks}')

# 为'a-10e4_3-10e4'区间选择的分块大小
selected_chunk_pixels = [
    21420, 10710, 7140, 4284, 3570, 1948, 1785, 974, 932, 630, 
    476, 466, 315, 236, 233, 156, 117, 116, 94, 78, 67, 
    59, 58, 48, 39, 33, 30, 27, 25, 24, 22
]

# 水印内容
binary_watermark = [0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 0, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 1, 1, 0, 1, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 0, 1, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 1, 1, 0, 0, 1, 0, 0, 0, 1, 1, 0, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 1, 1, 0, 0, 0, 1, 1, 0, 0, 1, 1, 1, 0, 0, 0, 0, 1, 1, 0, 0, 1, 0, 1, 0, 0, 1, 1, 1, 0, 0, 1, 0, 0, 1, 1, 0, 1, 0, 1, 0, 0, 1, 1, 0, 0, 0, 1, 0, 0, 1, 1, 0, 0, 1, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 1, 1, 0, 0, 1, 0, 0, 0, 0, 1, 1, 0, 1, 0, 0, 0, 0, 1, 1, 0, 1, 1, 0, 0, 0, 1, 1, 0, 1, 0, 1, 0, 0, 1, 1, 1, 0, 0, 1, 0, 1, 1, 0, 0, 1, 0, 0, 0, 1, 1, 0, 0, 0, 1, 0, 0, 1, 1, 0, 0, 0, 1, 1, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 1, 1, 0, 1, 1, 0, 0, 1, 1, 0, 0, 0, 1, 0, 0, 1, 1, 0, 0, 0, 0, 1, 0, 1, 1, 0, 0, 0, 1, 0, 0, 0, 1, 1, 0, 1, 0, 1, 0, 0, 1, 1, 0, 1, 1, 1, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 1, 0, 0, 1, 1, 0, 0, 1, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 1, 1, 0, 1, 1, 0, 0, 1, 0, 0, 0, 1, 1, 0, 0, 1, 0, 1, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 0, 1, 1, 0, 0, 0, 1, 0, 1, 1, 0, 0, 1, 0, 0, 0, 0, 1, 1, 0, 0, 0, 1, 0, 0, 1, 1, 0, 1, 0, 1, 0, 0, 1, 1, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 0, 0, 1, 1, 1, 0, 0, 1, 0, 0, 1, 1, 1, 0, 0, 0, 0, 1, 1, 0, 0, 0, 1, 1, 0, 0, 1, 1, 0, 1, 1, 1, 0, 0, 1, 1, 0, 1, 1, 0, 0, 0, 1, 1, 0, 1, 0, 1, 0, 0, 1, 1, 0, 1, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 1, 1, 0, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 1, 1, 0, 0, 0, 0, 1, 0, 1, 1, 0, 0, 0, 0, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 1, 1, 0, 0, 1, 0, 1, 0]

# 原图和水印图目录（与 watermark.py 保持一致）
ori_path = './ori_pic'
wm_path  = './watermark_pic'

if __name__ == '__main__':
    if os.path.exists(ori_path) and os.path.exists(wm_path):
        print(f"[开始处理] ori_path={ori_path}, wm_path={wm_path}")
        process_images(ori_path, wm_path, binary_watermark, selected_chunk_pixels)
    else:
        print(f"[错误] 目录不存在: {ori_path} 或 {wm_path}")
