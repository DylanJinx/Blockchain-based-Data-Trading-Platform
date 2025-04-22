## 0. 启动程序

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

## 1. 部署合约

![部署合约](imgs/1-deploy_contract.bmp)

```
cd python_call_contract
python deploy.py            # 生成 deploy_address.json
```
