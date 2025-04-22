# 0 前期部署

## 0.1 启动程序

![四个后台](imgs/0-start.bmp)

四个终端分别运行：

```
# ① 本地区块链
anvil --host 0.0.0.0 --port 8545

# ② IPFS 节点
ipfs daemon

# ③ 启动 Agent / 后端
cd ../my_agent_project
export OPENAI_API_KEY=<---Your Key--->     # Windows: set OPENAI_API_KEY=...
python api_server.py

# ④ 启动前端
cd ../frontend
npm install                  # 首次启动需要
npm start
```

---

## 0.2 部署合约

![部署合约](imgs/1-deploy_contract.bmp)

```
cd python_call_contract
python deploy.py            # 生成 deploy_address.json
```

---

# 1 功能一：登记数据集

---

# 2 功能二：上/下架数据集

---

# 3 功能三：购买数据集

---

# 4 功能四：举报数据集
