import crypto from "crypto";
import fs from "fs";

function generateBobKeyPair() {
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

  fs.writeFileSync("bob_public_key.pem", publicKey);
  fs.writeFileSync("bob_private_key.pem", privateKey);

  console.log("Bob's Public key saved to bob_public_key.pem");
  console.log("Bob's Private key saved to bob_private_key.pem");
}

generateBobKeyPair();
