import fs from "fs";
import path from "path";
import crypto from "crypto";
import { create } from "ipfs-http-client";

// 连接本地IPFS节点
const ipfs = create({
  url: "http://127.0.0.1:5001/api/v0",
});

// 加密函数
function encryptCidWithPublicKey(cid, publicKeyPem) {
  const encryptedBuffer = crypto.publicEncrypt(
    publicKeyPem,
    Buffer.from(cid, "utf8")
  );
  return encryptedBuffer.toString("base64");
}

// 生成元数据
function generateMetadata(title, description, imgCid, encryptedZipCid) {
  return {
    title,
    description,
    image: imgCid,
    zip_cid: encryptedZipCid,
  };
}

async function main() {
  try {
    // 获取参数: datasetCid, imageCid, title, description, publicKeyPath
    const datasetCid = process.argv[2];
    const imageCid = process.argv[3];
    const title = process.argv[4];
    const description = process.argv[5];
    const publicKeyPath = process.argv[6];

    if (!datasetCid || !imageCid || !title || !description || !publicKeyPath) {
      console.error("缺少必要参数");
      console.error(
        "用法: node encryptAndUploadMetadata.js <datasetCid> <imageCid> <title> <description> <publicKeyPath>"
      );
      process.exit(1);
    }

    // 读取平台公钥
    const platformPublicKeyPEM = fs.readFileSync(publicKeyPath, "utf-8");

    // 加密数据集CID
    console.log("Encrypting dataset CID with platform public key...");
    const encryptedDatasetCid = encryptCidWithPublicKey(
      datasetCid,
      platformPublicKeyPEM
    );
    console.log("Encrypted CID:", encryptedDatasetCid);

    // 生成元数据
    const metadata = generateMetadata(
      title,
      description,
      imageCid,
      encryptedDatasetCid
    );

    // 转换为JSON并上传到IPFS
    console.log("Uploading metadata to IPFS...");
    const metadataContent = JSON.stringify(metadata, null, 2);
    const metadataResult = await ipfs.add(metadataContent);
    const metadataCid = metadataResult.cid.toString();

    // 输出结果
    console.log("\n===== Final Data =====");
    console.log("Dataset CID (raw):", datasetCid);
    console.log("Image CID:", imageCid);
    console.log("Encrypted Dataset CID:", encryptedDatasetCid);
    console.log("Metadata CID:", metadataCid);
    console.log("Metadata URL:", `http://127.0.0.1:8080/ipfs/${metadataCid}`);
    console.log("Metadata Content:", metadata);

    // 返回metadata CID (用于API解析)
    console.log(`METADATA_CID:${metadataCid}`);
    console.log(`METADATA_URL:http://127.0.0.1:8080/ipfs/${metadataCid}`);
  } catch (err) {
    console.error("Error:", err);
    process.exit(1);
  }
}

main();
