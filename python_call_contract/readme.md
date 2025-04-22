# BDTP Python 脚本套件

本目录包含若干 **Python 脚本**，用于在本地 **Anvil/Foundry** 测试链上部署并操作 **BDTP‑区块链数据交易平台** 的核心智能合约。  
你可以借助这些脚本完成 **合约部署、NFT 上架 / 下架、购买、查询、举报以及 Gas 消耗分析** 等全流程操作。

> **提示**：所有脚本默认使用本地 `http://127.0.0.1:8545` RPC 端口以及 Anvil 预置的前两个账户  
> （`admin` —— index 0，`agent` —— index 1）。如有自定义请修改脚本最上方的常量。

---

## 1. 依赖与环境

```bash
# Python 3.9+
pip install -r ../requirements.txt   # 需包含 web3, requests, tabulate 等
# 或手动安装
pip install web3 requests tabulate
```

同时需要提前**编译合约**并确保 `../BDTP_contract/out/` 目录下存在各合约的 `*.json` 产物文件  
（可通过  `forge build`  获得）。

---

## 2. 快速开始

```bash
# ① 启动本地测试链（Anvil）
anvil --host 0.0.0.0 --port 8545

# ② 部署所有合约（生成 deploy_address.json）
python deploy.py

# ③ 铸造并上架一个 NFT（示例 tokenId=1, 价格 0.5 ETH）
python function_2_list_nft.py <alice地址> 1 0.5
```

---

## 3. 脚本清单 & 使用方式

| 脚本                         | 功能简介                                                                                                                            | 典型用法                                                                                                                    |
| ---------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| **deploy.py**                | 一键部署 `DataRegistration`, `DataTradingPlatform`, `EscrowDeposit` 等合约；部署完成后自动生成 `deploy_address.json` 供其它脚本读取 | `python deploy.py`                                                                                                          |
| **function_2_list_nft.py**   | 以 _Agent_ 角色将指定 `tokenId` 上架到交易平台并设置价格                                                                            | `python function_2_list_nft.py <alice_addr> <token_id> <price_in_eth>`                                                      |
| **function_3_unlist_nft.py** | 将已上架的 `tokenId` 下架                                                                                                           | `python function_3_unlist_nft.py <alice_addr> <token_id>`                                                                   |
| **function_4_buy_nft.py**    | Bob 购买 NFT；分两步执行<br/>1) `check` 查看价格与状态；2) `purchase` 发送交易并等待链上转账确认                                    | `python function_4_buy_nft.py check <tokenId>`<br/>`python function_4_buy_nft.py purchase <bob_addr> <tokenId> <price_eth>` |
| **function_7_informer.py**   | 一步完成 _举报_ 流程：监听 jinx 账户 →agent 的质押；比对可疑/原始数据；调用 `EscrowDeposit.informerDeposit` 并启动 XRID 检测        | `python function_7_informer.py report <tokenId_original> <tokenId_suspicion> <jinx_addr>`                                   |
| **get_listed_nfts.py**       | 列出当前所有 **已上架** 的 NFT （tokenId、价格、元数据 URL）                                                                        | `python get_listed_nfts.py`                                                                                                 |
| **get_nft_details.py**       | 查询单个 NFT 的链上属性、上架状态、价格及元数据                                                                                     | `python get_nft_details.py <tokenId>`                                                                                       |
| **gas_cost_analysis.py**     | 顺序执行系统核心流程并统计每一步的 Gas 消耗，结果以表格及 `gas_report.csv` 输出                                                     | `python gas_cost_analysis.py`                                                                                               |

---

## 4. 文件结构说明

```
.
├── deploy.py                    # 部署脚本
├── deploy_address.json          # 部署后自动生成的合约地址映射
├── function_2_list_nft.py       # 功能二：上架 NFT
├── function_3_unlist_nft.py     # 功能三：下架 NFT
├── function_4_buy_nft.py        # 功能四：购买 NFT
├── function_7_informer.py       # 功能五：举报与检测
├── get_listed_nfts.py           # 查询全部上架 NFT
├── get_nft_details.py           # 查询单个 NFT 详情
├── gas_cost_analysis.py         # Gas 消耗分析
└── README.md                    # 当前文件
```

---

## 5. 常见问题（FAQ）

1. **脚本卡在  “等待交易确认”**  
   确认 Anvil RPC 正在运行且未清空链数据；同时检查 gasPrice 与账户余额是否足够。

2. **找不到合约 ABI**  
   请检查合约产物路径与文件名是否匹配脚本中的 `../BDTP_contract/out/...` 设置。

3. **账户地址/私钥无效**  
   默认私钥仅适用于本地 Anvil。连接其他网络时请替换为你自己的测试/private key，并确保对应账户拥有足够 ETH。

---

## 6. 许可证

本项目采用  MIT License  发布，详见根目录  `LICENSE`  文件。
