# 数据交易平台 – 智能合约套件

## 概览

本仓库包含三份 **Solidity 智能合约**，共同实现链上 **数据集登记、质押与交易** 流程。数据拥有者（可通过代理人或前端  dApp）铸造一枚 **不可转让的 NFT** 来代表数据集，在 **EscrowDeposit** 合约中缴纳上架保证金，并以加密 IPFS CID 的形式出售数据。买家支付  ETH，链上记录会向买家交付加密  CID，同时在满足条件时释放押金与交易款项。

```
          ┌──────────────────┐                    ┌───────────────────┐
          │ DataRegistration │── 调用 ──────────▶ │ EscrowDeposit     │
          └──────────────────┘                    └───────────────────┘
                   ▲                                        ▲
                   │ 拥有 NFT                               │ 持有保证金
                   │                                        │
          ┌──────────────────┐   协调交易            ┌───────────────────┐
          │   Data Owner     │◀──────────────────────▶│ DataTradingPlatform│
          └──────────────────┘                        └───────────────────┘
```

---

## 合约摘要

| 文件                          | 作用                   | 关键特性                                                                                                                                                                            |
| ----------------------------- | ---------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **`DataRegistration.sol`**    | 铸造 & 登记数据集  NFT | • SBT (不可转让  ERC‑721)<br>• `registerData()` 铸造并锁定数据集  NFT<br>• 维护 `saleHash → tokenId → dataOwner` 映射<br>• 铸造时向 **EscrowDeposit** 转入 `listStakeAmount` 保证金 |
| **`DataTradingPlatform.sol`** | 市场与支付路由         | • 发布 / 下架功能<br>• `purchaseData()` 处理 ETH 支付并记录买家加密  CID<br>• 管理上架状态与售价<br>• Admin / Agent 双角色权限控制                                                  |
| **`EscrowDeposit.sol`**       | 保证金管理             | • 持有上架保证金与举报保证金<br>• 独立映射区分数据拥有者保证金与举报人保证金<br>• `withdrawListDeposit()` / `withdrawInformerDeposit()` 在条件满足时退款                            |

---

## 合约部署顺序

1. **EscrowDeposit** – 负责托管保证金。
2. **DataRegistration** – 构造函数注入 EscrowDeposit 地址。
3. **DataTradingPlatform** – 构造函数注入 DataRegistration 地址。

---

## 快速上手

### 1. 安装依赖

```bash
forge install openzeppelin/openzeppelin-contracts
```

### 2. 编译

```bash
forge build
```

## 典型工作流

```solidity
// 1. 代理人为数据拥有者登记数据集
registration.registerData(
    dataOwner,
    encryptedZipCid,    // 存储于 tokenURI
    saleHash,           // keccak256(数据指纹)
    tokenPriceWei
);

// 2. 数据拥有者（或代理人）上架出售
tradingPlatform.listToken(tokenId, priceWei);

// 3. 买家购买
tradingPlatform.purchaseData{value: priceWei}(
    tokenId,
    buyerPubKeyEncryptedCid
);

// 4. 数据拥有者可在条件满足后提取上架保证金
escrow.withdrawListDeposit(tokenId);
```

---

## 测试

使用 Foundry 单元测试，位于 `test/` 目录：

```bash
forge test -vv
```

---

## 安全注意事项

- 代理人私钥应妥善保管，因其拥有登记和下架权限。
- CID 加密必须在客户端完成，确保使用安全的公钥方案。

---

## 许可证

本项目采用 **MIT License**，详情见 `LICENSE` 文件。
