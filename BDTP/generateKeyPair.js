import crypto from "crypto";
import fs from "fs";

function generateKeyPair() {
  // 使用 RSA 2048 位
  const { publicKey, privateKey } = crypto.generateKeyPairSync("rsa", {
    modulusLength: 2048,
    publicKeyEncoding: {
      type: "spki",
      format: "pem",
    },
    privateKeyEncoding: {
      type: "pkcs8",
      format: "pem",
    },
  });

  // 将生成的密钥写入到本地文件
  fs.writeFileSync("platform_public_key.pem", publicKey);
  fs.writeFileSync("platform_private_key.pem", privateKey);

  console.log("Public key saved to platform_public_key.pem");
  console.log("Private key saved to platform_private_key.pem");
}

generateKeyPair();
