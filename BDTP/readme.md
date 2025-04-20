### 主要代码文件

| 文件名                        | 功能描述                                                    |
| ----------------------------- | ----------------------------------------------------------- |
| `generateKeyPair.js`          | 生成平台的 RSA 公钥与私钥，分别用于加密与解密数据集的 CID。 |
| `generateBobKeyPair.js`       | 生成数据买方（Bob）的 RSA 公钥与私钥。                      |
| `encryptAndUploadMetadata.js` | 使用平台公钥加密数据集 CID，并上传元数据到 IPFS 节点。      |
| `uploadAndEncrypt.js`         | 上传数据集及示例图片到 IPFS，并生成加密的元数据。           |
| `uploadForBuyer.js`           | 上传包含水印的数据集到 IPFS，并使用买方公钥进行加密。       |
| `uploadToIPFS.js`             | 上传任意文件到本地 IPFS 节点。                              |
| `downloadFromIPFS.js`         | 从 IPFS 下载文件到本地。                                    |

### CID 解密工具

- **`decryptCidWithPrivateKey.js`**
  - 本脚本用于在用户成功购买数据集后，通过用户提供的私钥文件 (`private_key.pem`) 解密前端返回的加密后的 CID。
  - 使用方法如下：
  ```bash
  node decryptCidWithPrivateKey.js <加密后的CID> [私钥文件路径]
  ```
  - 若省略私钥文件路径，则默认使用当前目录下的 `private_key.pem`。
  - 解密成功后，用户将获得数据集的原始 CID，并可使用以下方式访问数据：
    - 网关访问：`http://127.0.0.1:8080/ipfs/<解密后的CID>`
    - IPFS 命令行下载：`ipfs get <解密后的CID> -o 本地保存路径`

## 数据集说明

在 `data_zip` 文件夹中包含以下用于测试的数据集：

- **原始数据集**
- **转售数据集**
- **相似但非转售的数据集**
- **嵌入水印的数据集**

## 使用依赖与环境准备

- 安装 Node.js 环境（推荐版本：v16 或更高）。
- 安装项目依赖包：

```bash
npm install ipfs-http-client crypto fs path readline util
```

- 确保本地启动了 IPFS 节点：

```bash
ipfs daemon
```

## 引用本仓库

若您在学术论文或研究中使用了本平台，请在您的论文中引用此 GitHub 仓库的链接。

## 许可证

本项目采用 MIT 开源许可证，具体条款参见仓库中的`LICENSE`文件。

## 联系作者

如有问题或合作需求，欢迎通过以下方式联系：

- 邮箱：[hzhicheng@m.scnu.edu.cn](mailto:hzhicheng@m.scnu.edu.cn)
