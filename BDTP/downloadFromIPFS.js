// downloadFromIPFS.js
import { create } from "ipfs-http-client";
import fs from "fs";
import path from "path";

// 从命令行获取参数
const [, , cidVal, outputNameArg] = process.argv;
if (!cidVal) {
  console.error("用法: node downloadFromIPFS.js <cid> [outputFileName]");
  process.exit(1);
}
const outputFile = outputNameArg || "dataset.zip";

// 连接本地 IPFS 节点 (daemon)
const ipfs = create({ url: "http://127.0.0.1:5001/api/v0" });

async function downloadFile(cid, outputPath) {
  console.log(`开始从 IPFS 下载: cid=${cid}`);
  const chunks = [];
  for await (const chunk of ipfs.cat(cid)) {
    chunks.push(chunk);
  }
  const fileData = Buffer.concat(chunks);

  fs.writeFileSync(outputPath, fileData);
  console.log(`已成功下载到本地文件: ${outputPath}`);
}

async function main() {
  try {
    await downloadFile(cidVal, outputFile);
  } catch (err) {
    console.error("下载失败:", err);
    process.exit(1);
  }
}

main();
