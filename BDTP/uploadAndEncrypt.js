import fs from "fs";
import path from "path";
import crypto from "crypto";
import { create } from "ipfs-http-client";

import readline from "readline";
import util from "util";

// 1) 读取本地公钥
const platformPublicKeyPEM = fs.readFileSync(
  "platform_public_key.pem",
  "utf-8"
);

// 2) 准备文件路径
const zipFilePath = path.join(process.cwd(), "dataset.zip");
const imgFilePath = path.join(process.cwd(), "sample_image.png");

// 3) 连接本地 IPFS 节点 (daemon)
const ipfs = create({
  url: "http://127.0.0.1:5001/api/v0",
});

// 4) 加密函数
function encryptCidWithPublicKey(cid, publicKeyPem) {
  const encryptedBuffer = crypto.publicEncrypt(
    publicKeyPem,
    Buffer.from(cid, "utf8")
  );
  return encryptedBuffer.toString("base64");
}

// 5) 生成元数据
function generateMetadata(title, description, imgCid, encryptedZipCid) {
  return {
    title,
    description,
    image: imgCid,
    zip_cid: encryptedZipCid,
  };
}

// 使用 readline 模块实现命令行交互
const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
});
const question = util.promisify(rl.question).bind(rl);

(async () => {
  try {
    // 在终端中依次提示用户输入
    const title = await question("请输入元数据的标题 (title): ");
    const description = await question("请输入元数据的描述 (description): ");
    rl.close(); // 关闭 readline

    console.log("Uploading dataset.zip to local IPFS...");
    const zipData = fs.readFileSync(zipFilePath);
    const zipResult = await ipfs.add(zipData);
    const cid_zip_1 = zipResult.cid.toString();
    console.log("CID of dataset.zip:", cid_zip_1);

    console.log("Uploading sample_image.png to local IPFS...");
    const imgData = fs.readFileSync(imgFilePath);
    const imgResult = await ipfs.add(imgData);
    const cid_img_1 = imgResult.cid.toString();
    console.log("CID of sample_image.png:", cid_img_1);

    console.log("Encrypting dataset.zip CID with platform public key...");
    const cid_zip_1_encrypted = encryptCidWithPublicKey(
      cid_zip_1,
      platformPublicKeyPEM
    );

    console.log("Generating metadata JSON...");
    const metadata = generateMetadata(
      title,
      description,
      cid_img_1,
      cid_zip_1_encrypted
    );

    console.log("Uploading metadata to local IPFS...");
    const metadataContent = JSON.stringify(metadata, null, 2);
    const metaResult = await ipfs.add(metadataContent);
    const metadataCID = metaResult.cid.toString();

    console.log("\n===== Final Data =====");
    // console.log("cid_zip_1 (raw):", cid_zip_1);
    // console.log("cid_zip_1_encrypted:", cid_zip_1_encrypted);
    // console.log("cid_img_1:", cid_img_1);
    console.log("NFT metadata JSON:", metadata);
    console.log("Metadata CID (uploaded):", metadataCID);
    console.log(`Check metadata at: http://127.0.0.1:8080/ipfs/${metadataCID}`);
  } catch (err) {
    console.error("Error in uploadAndEncrypt.js:", err);
    rl.close();
  }
})();
