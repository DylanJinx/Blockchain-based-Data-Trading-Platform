import fs from "fs";
import path from "path";
import { create } from "ipfs-http-client";

// 连接本地IPFS节点
const ipfs = create({
  url: "http://127.0.0.1:5001/api/v0",
});

async function main() {
  try {
    // 获取要上传的文件路径
    const filePath = process.argv[2];

    if (!filePath) {
      console.error("请提供要上传的文件路径");
      process.exit(1);
    }

    if (!fs.existsSync(filePath)) {
      console.error(`文件不存在: ${filePath}`);
      process.exit(1);
    }

    console.log(`上传文件: ${filePath}`);

    // 读取文件数据
    const fileData = fs.readFileSync(filePath);

    // 上传到IPFS
    console.log("上传到IPFS...");
    const result = await ipfs.add(fileData);
    const cid = result.cid.toString();
    console.log(`上传成功，CID: ${cid}`);

    return cid;
  } catch (err) {
    console.error("Error:", err);
    process.exit(1);
  }
}

main();
