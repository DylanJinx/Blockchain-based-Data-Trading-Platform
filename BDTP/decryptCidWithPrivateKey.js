/**
 * decryptCidWithPrivateKey.js
 *
 * 这个脚本用于使用私钥解密加密后的CID
 * 用法: node decryptCidWithPrivateKey.js <加密的CID> <私钥文件路径>
 *
 * 示例: node decryptCidWithPrivateKey.js "加密的base64字符串" private_key.pem
 */

import fs from "fs";
import crypto from "crypto";
import { Buffer } from "buffer";
import { fileURLToPath } from "url";
import path from "path";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// 检查命令行参数
if (process.argv.length < 3) {
  console.error(
    "用法: node decryptCidWithPrivateKey.js <加密的CID> [私钥文件路径]"
  );
  console.error("如果省略私钥文件路径，将使用当前目录下的private_key.pem");
  process.exit(1);
}

// 从命令行获取加密的CID和私钥路径
const encryptedCid = process.argv[2];
const privateKeyPath =
  process.argv[3] || path.join(process.cwd(), "private_key.pem");

console.log("准备解密CID...");
console.log(`使用私钥文件: ${privateKeyPath}`);

// 检查私钥文件是否存在
try {
  if (!fs.existsSync(privateKeyPath)) {
    console.error(`错误: 私钥文件不存在: ${privateKeyPath}`);
    process.exit(1);
  }
} catch (err) {
  console.error(`检查私钥文件时出错: ${err.message}`);
  process.exit(1);
}

// 读取私钥
let privateKey;
try {
  privateKey = fs.readFileSync(privateKeyPath, "utf8");

  // 检查私钥格式
  if (!privateKey.includes("-----BEGIN PRIVATE KEY-----")) {
    console.error("错误: 私钥格式不正确，需要PEM格式的RSA私钥");
    process.exit(1);
  }

  console.log(`成功读取私钥，长度: ${privateKey.length} 字符`);
} catch (err) {
  console.error(`读取私钥文件失败: ${err.message}`);
  process.exit(1);
}

// 检查加密的CID格式
if (!encryptedCid || encryptedCid.startsWith("MOCK_")) {
  console.error(`警告: 输入的似乎是模拟加密的CID: ${encryptedCid}`);
  console.log("这可能是因为系统生成了备用CID，而不是真正加密的CID");
  console.log("如果这是一个模拟值，则无法解密");

  // 如果是MOCK_开头，尝试从其中提取原始CID
  if (encryptedCid && encryptedCid.startsWith("MOCK_")) {
    const parts = Buffer.from(encryptedCid, "base64").toString().split("_");
    if (parts.length > 2) {
      console.log(`可能的原始CID: ${parts[parts.length - 1]}`);
    }
  }

  process.exit(1);
}

// 解密函数
function decryptCid(encryptedBase64, privateKeyPem) {
  try {
    // 将Base64字符串转换为Buffer
    const encryptedBuffer = Buffer.from(encryptedBase64, "base64");

    // 使用私钥解密
    const decryptedBuffer = crypto.privateDecrypt(
      {
        key: privateKeyPem,
        padding: crypto.constants.RSA_PKCS1_OAEP_PADDING,
        oaepHash: "sha256",
      },
      encryptedBuffer
    );

    // 将解密后的Buffer转换为字符串
    return decryptedBuffer.toString("utf8");
  } catch (error) {
    throw new Error(`解密失败: ${error.message}`);
  }
}

// 尝试解密
try {
  console.log("开始解密...");
  const decryptedCid = decryptCid(encryptedCid, privateKey);

  console.log("\n===== 解密结果 =====");
  console.log(`解密后的CID: ${decryptedCid}`);
  console.log(`\n您现在可以通过以下方式访问您购买的数据:`);
  console.log(`1. 通过网关访问: http://127.0.0.1:8080/ipfs/${decryptedCid}`);
  console.log(
    `2. 或者使用IPFS CLI下载: ipfs get ${decryptedCid} -o 您的保存路径`
  );
} catch (error) {
  console.error(`解密过程出错: ${error.message}`);

  // 检查是否可能是padding错误，这通常意味着密钥不匹配
  if (error.message.includes("padding")) {
    console.error("这可能是因为使用了错误的私钥或加密的CID格式不正确");
  }

  process.exit(1);
}
