import crypto from "crypto";
import fs from "fs";

// 解密函数
function decryptCidWithPrivateKey(encryptedCidBase64, privateKeyPem) {
  const encryptedBuffer = Buffer.from(encryptedCidBase64, "base64");
  const decryptedBuffer = crypto.privateDecrypt(
    {
      key: privateKeyPem,
    },
    encryptedBuffer
  );
  return decryptedBuffer.toString("utf8");
}

const encryptedCid = process.argv[2];
if (!encryptedCid) {
  console.error("Usage: node decryptCid.js <encryptedCidBase64>");
  process.exit(1);
}

const privateKeyPem = fs.readFileSync("platform_private_key.pem", "utf8");
const originalCid = decryptCidWithPrivateKey(encryptedCid, privateKeyPem);

console.log("Decrypted CID:", originalCid);
