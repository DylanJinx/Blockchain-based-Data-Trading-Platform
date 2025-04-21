import React, { createContext, useContext, useState, useEffect } from "react";
import detectEthereumProvider from "@metamask/detect-provider";
import { ethers } from "ethers";

const Web3Context = createContext();

export const useWeb3 = () => useContext(Web3Context);

export const Web3Provider = ({ children }) => {
  const [account, setAccount] = useState(null);
  const [provider, setProvider] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [chainId, setChainId] = useState(null);
  const [signer, setSigner] = useState(null);
  const [networkName, setNetworkName] = useState("");

  useEffect(() => {
    const init = async () => {
      try {
        const detectedProvider = await detectEthereumProvider();

        if (detectedProvider) {
          const ethersProvider = new ethers.providers.Web3Provider(
            window.ethereum
          );
          setProvider(ethersProvider);

          // 检查是否已经连接
          const accounts = await ethersProvider.listAccounts();
          if (accounts.length > 0) {
            setAccount(accounts[0]);
            setIsConnected(true);
            setSigner(ethersProvider.getSigner());
          }

          const { chainId } = await ethersProvider.getNetwork();
          setChainId(chainId);
          updateNetworkName(chainId);

          // 监听账户变化
          window.ethereum.on("accountsChanged", (accounts) => {
            if (accounts.length > 0) {
              setAccount(accounts[0]);
              setIsConnected(true);
              setSigner(ethersProvider.getSigner());
            } else {
              setAccount(null);
              setIsConnected(false);
              setSigner(null);
            }
          });

          // 监听链变化
          window.ethereum.on("chainChanged", (chainId) => {
            const parsedChainId = parseInt(chainId, 16);
            setChainId(parsedChainId);
            updateNetworkName(parsedChainId);
            window.location.reload();
          });
        } else {
          console.error("请安装MetaMask!");
        }
      } catch (error) {
        console.error("初始化Web3出错:", error);
      }
    };

    init();

    return () => {
      if (window.ethereum) {
        window.ethereum.removeAllListeners("accountsChanged");
        window.ethereum.removeAllListeners("chainChanged");
      }
    };
  }, []);

  // 更新网络名称函数
  const updateNetworkName = (chainId) => {
    let name = "未知网络";
    switch (chainId) {
      case 1:
        name = "Ethereum主网";
        break;
      case 3:
        name = "Ropsten测试网";
        break;
      case 4:
        name = "Rinkeby测试网";
        break;
      case 5:
        name = "Goerli测试网";
        break;
      case 42:
        name = "Kovan测试网";
        break;
      case 31337:
        name = "Anvil本地网络";
        break;
      case 1337:
        name = "Ganache本地网络";
        break;
      default:
        name = `链ID: ${chainId}`;
    }
    setNetworkName(name);
  };

  const connectWallet = async () => {
    try {
      if (window.ethereum) {
        const accounts = await window.ethereum.request({
          method: "eth_requestAccounts",
        });

        if (accounts.length > 0) {
          setAccount(accounts[0]);
          setIsConnected(true);
          const ethersProvider = new ethers.providers.Web3Provider(
            window.ethereum
          );
          setSigner(ethersProvider.getSigner());
          return accounts[0];
        }
      } else {
        alert("请安装MetaMask!");
      }
    } catch (error) {
      console.error("连接钱包出错:", error);
    }
    return null;
  };

  // 切换账户函数
  const switchAccount = async () => {
    try {
      if (window.ethereum) {
        await window.ethereum.request({
          method: "wallet_requestPermissions",
          params: [{ eth_accounts: {} }],
        });

        // MetaMask将处理账户选择并通过accountsChanged事件更新
      } else {
        alert("请安装MetaMask!");
      }
    } catch (error) {
      console.error("切换账户出错:", error);
    }
  };

  const disconnectWallet = () => {
    setAccount(null);
    setIsConnected(false);
    setSigner(null);
  };

  // 用于前端生成RSA密钥对的函数
  const generateKeyPair = async () => {
    try {
      // 使用Web Crypto API生成RSA密钥对
      const keyPair = await window.crypto.subtle.generateKey(
        {
          name: "RSA-OAEP",
          modulusLength: 2048,
          publicExponent: new Uint8Array([1, 0, 1]),
          hash: "SHA-256",
        },
        true,
        ["encrypt", "decrypt"]
      );

      // 导出公钥为SPKI格式
      const publicKeySpki = await window.crypto.subtle.exportKey(
        "spki",
        keyPair.publicKey
      );

      // 导出私钥为PKCS8格式
      const privateKeyPkcs8 = await window.crypto.subtle.exportKey(
        "pkcs8",
        keyPair.privateKey
      );

      // 将ArrayBuffer转为Base64
      const publicKeyBase64 = arrayBufferToBase64(publicKeySpki);
      const privateKeyBase64 = arrayBufferToBase64(privateKeyPkcs8);

      // 格式化为PEM格式
      const publicKeyPem = `-----BEGIN PUBLIC KEY-----\n${publicKeyBase64}\n-----END PUBLIC KEY-----`;
      const privateKeyPem = `-----BEGIN PRIVATE KEY-----\n${privateKeyBase64}\n-----END PRIVATE KEY-----`;

      return {
        publicKey: publicKeyPem,
        privateKey: privateKeyPem,
      };
    } catch (error) {
      console.error("生成密钥对出错:", error);
      return null;
    }
  };

  // 帮助函数：将ArrayBuffer转换为Base64字符串
  const arrayBufferToBase64 = (buffer) => {
    const binary = String.fromCharCode.apply(null, new Uint8Array(buffer));
    return window
      .btoa(binary)
      .match(/.{1,64}/g)
      .join("\n");
  };

  return (
    <Web3Context.Provider
      value={{
        account,
        provider,
        signer,
        chainId,
        networkName,
        isConnected,
        connectWallet,
        switchAccount,
        disconnectWallet,
        generateKeyPair,
      }}
    >
      {children}
    </Web3Context.Provider>
  );
};
