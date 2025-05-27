# 零知识证明水印系统实现方案

## 概述

本文档详细说明了将现有水印系统与零知识证明系统集成的完整实现方案。该方案确保水印嵌入/检测与 LSB_groth16 系统完全兼容，同时保持现有的 buy_hash 生成机制。

## 系统架构

```
购买流程 → 水印嵌入 → ZK输入生成 → 数据保存
    ↓
登记流程 → 水印检测 → 查找输入数据 → 计算约束 → 生成ZK证明
```

## 技术实现详解

### 第一阶段：统一水印处理方式

#### 1.1 修改 `my_agent_project/features/addWatermark.py`

**目标：** 使嵌入方式与 LSB_groth16/watermark.py 完全一致，但保持 buy_hash 内容

**核心修改：**

```python
def add_lsb_watermark_v2(image_path, buy_hash, output_path):
    """
    使用与LSB_groth16完全一致的列优先嵌入方式
    水印内容：buy_hash (保持原有计算方式)
    剩余位处理：自动填充'0'实现清零
    """
    # 1. 加载图像并转为RGB
    image = Image.open(image_path).convert('RGB')
    pixel = image.load()
    width, height = image.size

    # 2. 将buy_hash转换为二进制字符串 (保持原有逻辑)
    binary_watermark = ''.join([bin(ord(c))[2:].rjust(8, '0') for c in buy_hash])

    # 3. 计算总容量并填充 (关键：与LSB_groth16一致)
    total_capacity = width * height * 3
    if len(binary_watermark) < total_capacity:
        padded_secret = binary_watermark + '0' * (total_capacity - len(binary_watermark))
    else:
        padded_secret = binary_watermark[:total_capacity]

    # 4. 列优先遍历嵌入 (关键：与LSB_groth16完全一致)
    index = 0
    for x in range(width):  # 列优先
        for y in range(height):
            r, g, b = pixel[x, y]
            # RGB三通道LSB嵌入
            r = (r & 0xFE) | int(padded_secret[index])
            index += 1
            g = (g & 0xFE) | int(padded_secret[index])
            index += 1
            b = (b & 0xFE) | int(padded_secret[index])
            index += 1
            pixel[x, y] = (r, g, b)

    # 5. 保存图像
    image.save(output_path, format='PNG')
```

**修改要点：**

- 移除现有的`pixels.reshape(-1)`行优先方式
- 采用`for x: for y:`列优先遍历
- 使用填充方式处理剩余位（而非显式循环清零）
- 保持 buy_hash 生成和转换逻辑不变

#### 1.2 修改 `my_agent_project/features/checkForWatermark.py`

**目标：** 使检测方式与嵌入方式完全对应

**核心修改：**

```python
def extract_lsb_watermark_v2(image_path, expected_length=512):
    """
    使用与嵌入一致的列优先提取方式
    """
    # 1. 加载图像
    image = Image.open(image_path).convert('RGB')
    pixel = image.load()
    width, height = image.size

    # 2. 列优先提取LSB (与嵌入顺序完全一致)
    bits = []
    for x in range(width):  # 列优先
        for y in range(height):
            if len(bits) >= expected_length:
                break
            r, g, b = pixel[x, y]
            # 按RGB顺序提取LSB
            bits.append(str(r & 1))
            if len(bits) >= expected_length:
                break
            bits.append(str(g & 1))
            if len(bits) >= expected_length:
                break
            bits.append(str(b & 1))
        if len(bits) >= expected_length:
            break

    # 3. 转换为字符串
    bit_string = ''.join(bits)
    chars = []
    for i in range(0, len(bit_string), 8):
        if i + 8 <= len(bit_string):
            byte = bit_string[i:i+8]
            char_code = int(byte, 2)
            chars.append(chr(char_code))

    return ''.join(chars)
```

**修改要点：**

- 移除 numpy 数组处理方式
- 采用与嵌入完全一致的列优先遍历
- 确保 RGB 通道提取顺序一致

### 第二阶段：零知识证明输入数据生成

#### 2.1 在购买时生成初步输入数据

**实现位置：** `my_agent_project/features/addWatermark.py`

**新增功能：**

```python
def generate_zk_input_data(original_image_path, watermarked_image_path, buy_hash, output_dir):
    """
    在购买时生成ZK证明所需的初步输入数据
    使用列优先方式读取像素值，与LSB_groth16/generate_input.py一致
    """
    # 1. 加载原始和水印图像
    ori_img = Image.open(original_image_path).convert('RGB')
    wm_img = Image.open(watermarked_image_path).convert('RGB')

    width, height = ori_img.size
    total_pixels = width * height

    # 2. 关键：使用列优先方式展平像素 (与LSB_groth16一致)
    ori_pixels = np.array(ori_img).reshape(-1, 3, order='F')  # Fortran order
    wm_pixels = np.array(wm_img).reshape(-1, 3, order='F')

    # 3. 将buy_hash转换为二进制数组
    binary_watermark = []
    for c in buy_hash:
        binary_watermark.extend([int(b) for b in bin(ord(c))[2:].rjust(8, '0')])

    # 4. 扩展水印到全容量 (与LSB_groth16一致)
    extended_watermark_size = total_pixels * 3
    if len(binary_watermark) < extended_watermark_size:
        extended_watermark = binary_watermark + [0] * (extended_watermark_size - len(binary_watermark))
    else:
        extended_watermark = binary_watermark[:extended_watermark_size]

    # 5. 生成初步输入数据
    initial_input_data = {
        "metadata": {
            "buy_hash": buy_hash,
            "total_pixels": total_pixels,
            "image_dimensions": [width, height],
            "watermark_length": len(binary_watermark),
            "timestamp": time.time()
        },
        "pixel_data": {
            "original_pixels": ori_pixels.tolist(),
            "watermarked_pixels": wm_pixels.tolist(),
            "binary_watermark": extended_watermark
        }
    }

    # 6. 保存初步输入数据
    output_file = os.path.join(output_dir, f"initial_input_{buy_hash[:16]}.json")
    os.makedirs(output_dir, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(initial_input_data, f, indent=2)

    return output_file

def process_image_folder_with_zk_data(input_folder, output_folder, buy_hash, zk_output_dir):
    """
    修改原有的process_image_folder函数，增加ZK数据生成
    """
    processed_count = 0
    zk_files = []

    # ... 原有的图像处理逻辑 ...

    for root, dirs, files in os.walk(input_folder):
        for file in files:
            if any(file.lower().endswith(fmt) for fmt in supported_formats):
                input_path = os.path.join(root, file)
                output_path = os.path.join(output_folder, rel_path)

                # 嵌入水印 (使用新的v2函数)
                if add_lsb_watermark_v2(input_path, buy_hash, output_path):
                    processed_count += 1

                    # 生成ZK输入数据
                    zk_file = generate_zk_input_data(
                        input_path, output_path, buy_hash,
                        os.path.join(zk_output_dir, f"image_{processed_count}")
                    )
                    zk_files.append(zk_file)

    return processed_count, zk_files
```

#### 2.2 修改主流程集成 ZK 数据生成

**修改位置：** `my_agent_project/features/addWatermark.py` 的 `main()` 函数

```python
def main(token_id=None, buyer_address=None, sale_hash=None):
    # ... 现有逻辑 ...

    # 定义ZK数据输出目录
    zk_base_dir = os.path.join(DATA_DIR, "zk_inputs")
    if token_id and buyer_address:
        zk_session_dir = os.path.join(zk_base_dir, f"token_{token_id}_buyer_{buyer_address[:8]}")
    else:
        zk_session_dir = os.path.join(zk_base_dir, f"test_session_{int(time.time())}")

    # 处理图像并生成ZK数据
    processed_count, zk_files = process_image_folder_with_zk_data(
        dataset_folder, watermark_folder, buy_hash, zk_session_dir
    )

    # 保存ZK会话信息
    zk_session_info = {
        "buy_hash": buy_hash,
        "token_id": token_id,
        "buyer_address": buyer_address,
        "zk_input_files": zk_files,
        "total_images": processed_count,
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }

    zk_session_file = os.path.join(zk_session_dir, "session_info.json")
    with open(zk_session_file, 'w') as f:
        json.dump(zk_session_info, f, indent=2)
```

### 第三阶段：登记时的 ZK 证明生成

#### 3.1 修改 `my_agent_project/features/checkForWatermark.py`

**新增功能：** 检测到水印后查找对应的 ZK 输入数据

```python
def find_zk_input_for_buy_hash(detected_buy_hash):
    """
    根据检测到的buy_hash查找对应的ZK输入数据
    """
    zk_base_dir = os.path.join(os.path.dirname(__file__), "..", "data", "zk_inputs")

    if not os.path.exists(zk_base_dir):
        return None

    # 搜索所有会话目录
    for session_dir in os.listdir(zk_base_dir):
        session_path = os.path.join(zk_base_dir, session_dir)
        if not os.path.isdir(session_path):
            continue

        session_info_file = os.path.join(session_path, "session_info.json")
        if os.path.exists(session_info_file):
            try:
                with open(session_info_file, 'r') as f:
                    session_info = json.load(f)

                if session_info.get("buy_hash") == detected_buy_hash:
                    return {
                        "session_dir": session_path,
                        "session_info": session_info,
                        "zk_input_files": session_info.get("zk_input_files", [])
                    }
            except Exception as e:
                logging.error(f"读取会话信息失败 {session_info_file}: {e}")

    return None

def calculate_optimal_constraints_and_chunk(total_pixels):
    """
    计算最优约束参数 X、分块数M、像素数m
    """
    # 基于Powers of Tau约束范围计算
    base_constraints_per_pixel = 1125 * 2  # 每个像素的基础约束数

    # 计算总约束需求
    total_constraints_needed = total_pixels * 3 * base_constraints_per_pixel

    # 找到合适的Power of Tau大小 (X)
    constraint_power = 1
    while 2**constraint_power < total_constraints_needed:
        constraint_power += 1

    max_constraints = 2**constraint_power
    max_pixels_per_chunk = max_constraints // base_constraints_per_pixel // 3

    # 计算最优分块
    if total_pixels <= max_pixels_per_chunk:
        # 单个分块就够
        chunk_size = total_pixels  # m
        num_chunks = 1  # M
    else:
        # 需要多个分块
        chunk_size = max_pixels_per_chunk  # m
        num_chunks = (total_pixels + chunk_size - 1) // chunk_size  # M

    return {
        "constraint_power": constraint_power,  # X
        "chunk_size": chunk_size,  # m
        "num_chunks": num_chunks,  # M
        "total_pixels": total_pixels,
        "ptau_file": f"pot{constraint_power}_final.ptau"
    }
```

#### 3.2 生成最终的分块输入文件

```python
def generate_final_chunked_inputs(zk_input_info, chunk_params, output_dir):
    """
    根据最优约束参数，将初步输入数据分块为最终的input.json文件
    """
    chunk_size = chunk_params["chunk_size"]
    num_chunks = chunk_params["num_chunks"]

    # 创建输出目录
    chunk_output_dir = os.path.join(output_dir, f"chunk_pixel_{chunk_size}")
    os.makedirs(chunk_output_dir, exist_ok=True)

    final_input_files = []

    # 处理每个图像的初步输入数据
    for i, zk_file in enumerate(zk_input_info["zk_input_files"]):
        if not os.path.exists(zk_file):
            continue

        with open(zk_file, 'r') as f:
            initial_data = json.load(f)

        pixel_data = initial_data["pixel_data"]
        ori_pixels = np.array(pixel_data["original_pixels"])
        wm_pixels = np.array(pixel_data["watermarked_pixels"])
        binary_watermark = pixel_data["binary_watermark"]

        total_pixels = len(ori_pixels)

        # 按chunk_size分块
        for chunk_idx in range(num_chunks):
            start_pixel = chunk_idx * chunk_size
            end_pixel = min((chunk_idx + 1) * chunk_size, total_pixels)

            # 获取当前分块的像素数据
            if end_pixel - start_pixel < chunk_size:
                # 最后一块需要填充
                fill_size = chunk_size - (end_pixel - start_pixel)
                chunk_ori = np.vstack([
                    ori_pixels[start_pixel:end_pixel],
                    np.zeros((fill_size, 3), dtype=int)
                ])
                chunk_wm = np.vstack([
                    wm_pixels[start_pixel:end_pixel],
                    np.zeros((fill_size, 3), dtype=int)
                ])
                chunk_watermark = binary_watermark[start_pixel*3:end_pixel*3] + [0] * (fill_size * 3)
            else:
                chunk_ori = ori_pixels[start_pixel:end_pixel]
                chunk_wm = wm_pixels[start_pixel:end_pixel]
                chunk_watermark = binary_watermark[start_pixel*3:end_pixel*3]

            # 生成最终的input.json (与LSB_groth16格式完全一致)
            final_input_data = {
                "originalPixelValues": chunk_ori.tolist(),
                "Watermark_PixelValues": chunk_wm.tolist(),
                "binaryWatermark": chunk_watermark,
                "binaryWatermark_num": str(len(initial_data["pixel_data"]["binary_watermark"]))
            }

            # 保存分块文件
            output_file = os.path.join(chunk_output_dir, f"input_{i+1}_{chunk_idx+1}.json")
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(final_input_data, f, indent=4)

            final_input_files.append(output_file)

    return final_input_files
```

### 第四阶段：零知识证明生成系统

#### 4.1 修改 `LSB_groth16/create_LSB_i.py`

**主要修改：** 适配动态参数系统

```python
def create_zk_proof_project(chunk_params, input_files_dir, output_base_dir):
    """
    根据动态参数创建零知识证明项目

    参数:
    chunk_params: 从calculate_optimal_constraints_and_chunk()返回的参数
    input_files_dir: 最终分块输入文件目录
    output_base_dir: 输出基础目录
    """
    chunk_size = chunk_params["chunk_size"]  # m
    constraint_power = chunk_params["constraint_power"]  # X
    ptau_file = chunk_params["ptau_file"]

    # 创建项目目录
    project_name = f"LSB_{chunk_size}_proof"
    destination_folder = os.path.join(output_base_dir, project_name)

    # 复制LSB模板 (替换原有的硬编码source_folder)
    source_template = os.path.join(os.path.dirname(__file__), "..", "LSB_groth16", "LSB_i")
    if os.path.exists(destination_folder):
        shutil.rmtree(destination_folder)
    shutil.copytree(source_template, destination_folder)

    # 创建LSB子目录
    lsb_dir = os.path.join(destination_folder, "LSB")

    # 复制输入文件 (替换原有的selected_chunk_pixels循环)
    input_destination = os.path.join(lsb_dir, f"input_json_chunk_pixel_{chunk_size}")
    if os.path.exists(input_destination):
        shutil.rmtree(input_destination)
    shutil.copytree(input_files_dir, input_destination)

    # 复制ptau文件 (使用动态计算的ptau文件)
    ptau_source = os.path.join(os.path.dirname(__file__), "..", "LSB_groth16", ptau_file)
    ptau_dest_dir = os.path.join(lsb_dir, "ptau")
    os.makedirs(ptau_dest_dir, exist_ok=True)
    ptau_dest = os.path.join(ptau_dest_dir, ptau_file)

    if os.path.exists(ptau_source):
        shutil.copy2(ptau_source, ptau_dest)
    else:
        raise FileNotFoundError(f"Required ptau file not found: {ptau_source}")

    # 修改脚本文件 (替换原有的占位符替换逻辑)
    update_script_files(lsb_dir, chunk_size, ptau_file)

    return destination_folder

def update_script_files(lsb_dir, chunk_size, ptau_file):
    """
    更新脚本文件中的参数 (替换原有的硬编码替换)
    """
    # 更新B_witness.py
    b_witness_file = os.path.join(lsb_dir, "B_witness.py")
    if os.path.exists(b_witness_file):
        with open(b_witness_file, "r", encoding='utf-8') as f:
            content = f.read()
        content = content.replace("input_json_chunk_pixel_hownumberPixels",
                                 f"input_json_chunk_pixel_{chunk_size}")
        with open(b_witness_file, "w", encoding='utf-8') as f:
            f.write(content)

    # 更新C_zkey_time.py
    c_zkey_file = os.path.join(lsb_dir, "C_zkey_time.py")
    if os.path.exists(c_zkey_file):
        with open(c_zkey_file, "r", encoding='utf-8') as f:
            content = f.read()
        content = content.replace("pothownumberptau_final.ptau", ptau_file)
        with open(c_zkey_file, "w", encoding='utf-8') as f:
            f.write(content)

    # 更新LSB.circom
    lsb_circom_file = os.path.join(lsb_dir, "LSB.circom")
    if os.path.exists(lsb_circom_file):
        with open(lsb_circom_file, "r", encoding='utf-8') as f:
            content = f.read()
        content = content.replace("hownumberPixels", str(chunk_size))
        content = content.replace("numPixelscheng3", str(chunk_size * 3))
        with open(lsb_circom_file, "w", encoding='utf-8') as f:
            f.write(content)
```

#### 4.2 集成到 checkForWatermark 主流程

```python
def main():
    # ... 现有的水印检测逻辑 ...

    if watermark_found:
        print("1")  # 保持现有输出格式

        if args.verbose:
            # 生成零知识证明
            for detected_hash in detected_watermarks:
                zk_input_info = find_zk_input_for_buy_hash(detected_hash)
                if zk_input_info:
                    print(f"\n找到ZK输入数据，开始生成零知识证明...")

                    # 计算最优约束参数
                    # 假设从第一个图像获取总像素数
                    total_pixels = 100000  # 需要从实际数据计算
                    chunk_params = calculate_optimal_constraints_and_chunk(total_pixels)

                    print(f"最优约束参数:")
                    print(f"  约束大小 (X): 2^{chunk_params['constraint_power']}")
                    print(f"  分块大小 (m): {chunk_params['chunk_size']}")
                    print(f"  分块数量 (M): {chunk_params['num_chunks']}")
                    print(f"  PTAU文件: {chunk_params['ptau_file']}")

                    # 生成最终分块输入文件
                    zk_proof_dir = os.path.join("data", "zk_proofs", f"proof_{detected_hash[:16]}")
                    final_inputs = generate_final_chunked_inputs(
                        zk_input_info, chunk_params, zk_proof_dir
                    )

                    # 创建ZK证明项目
                    proof_project = create_zk_proof_project(
                        chunk_params,
                        os.path.join(zk_proof_dir, f"chunk_pixel_{chunk_params['chunk_size']}"),
                        zk_proof_dir
                    )

                    print(f"ZK证明项目已创建: {proof_project}")
                    print(f"执行证明生成: cd {proof_project} && bash generate_proof.sh")
```

## 数据流和文件组织

### 购买时的数据流

```
原始数据集 → 解压 → 逐图像处理:
  ├── 嵌入buy_hash水印 (列优先方式)
  ├── 生成initial_input_X.json (列优先像素数据)
  └── 保存到 data/zk_inputs/token_X_buyer_Y/
```

### 登记时的数据流

```
检测到水印 → 提取buy_hash → 查找ZK输入数据:
  ├── 计算最优约束 (X, M, m)
  ├── 分块生成最终input.json
  ├── 创建ZK证明项目
  └── 执行证明生成
```

### 文件组织结构

```
my_agent_project/
├── data/
│   ├── zk_inputs/                    # ZK输入数据
│   │   ├── token_1_buyer_0x1234/     # 按购买会话组织
│   │   │   ├── session_info.json    # 会话信息
│   │   │   ├── image_1/
│   │   │   │   └── initial_input_abc123.json
│   │   │   └── image_2/
│   │   │       └── initial_input_def456.json
│   │   └── token_2_buyer_0x5678/
│   └── zk_proofs/                    # ZK证明项目
│       ├── proof_abc123def456/       # 按buy_hash命名
│       │   ├── chunk_pixel_1024/     # 最终分块输入
│       │   │   ├── input_1_1.json
│       │   │   └── input_1_2.json
│       │   └── LSB_1024_proof/       # 证明项目
│       │       ├── LSB/
│       │       └── generate_proof.sh
│       └── proof_789abc012def/
└── LSB_groth16/                      # 参考模板
    ├── pot14_final.ptau              # Powers of Tau文件
    ├── pot15_final.ptau
    ├── pot16_final.ptau
    └── LSB_i/                        # 模板项目
```

## 实施时间表

### 第一周：基础修改

- [ ] 修改 addWatermark.py 的嵌入方式
- [ ] 修改 checkForWatermark.py 的提取方式
- [ ] 测试水印嵌入/检测一致性

### 第二周：ZK 数据生成

- [ ] 实现购买时的初步输入数据生成
- [ ] 集成到现有购买流程
- [ ] 测试数据生成正确性

### 第三周：登记时 ZK 证明

- [ ] 实现检测时的输入数据查找
- [ ] 实现最优约束计算
- [ ] 实现最终分块处理

### 第四周：ZK 项目生成

- [ ] 修改 create_LSB_i.py 适配动态参数
- [ ] 集成完整的证明生成流程
- [ ] 端到端测试

## 测试计划

### 单元测试

- [ ] 水印嵌入/检测一致性测试
- [ ] 像素排列顺序验证
- [ ] 约束计算准确性测试

### 集成测试

- [ ] 完整购买 → 水印 →ZK 数据流程
- [ ] 完整登记 → 检测 → 证明流程
- [ ] 多图像、多分块场景测试

### 性能测试

- [ ] 大图像处理性能
- [ ] ZK 证明生成时间
- [ ] 存储空间使用

通过这个详细的实施方案，我们将能够构建一个完整的、与 LSB_groth16 兼容的零知识证明水印系统，为数据交易平台提供强有力的侵权证明能力。
