import React, { useState, useEffect, useRef } from "react";
import styled from "styled-components";
import { useWeb3 } from "../utils/web3";
import apiService from "../utils/apiService";

const ChatContainer = styled.div`
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  height: 80vh;
`;

const ChatHeader = styled.div`
  background-color: #4f46e5;
  color: white;
  padding: 1rem;
  display: flex;
  align-items: center;
`;

const Avatar = styled.div`
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background-color: #fff;
  color: #4f46e5;
  display: flex;
  justify-content: center;
  align-items: center;
  font-weight: bold;
  margin-right: 1rem;
`;

const ChatTitle = styled.div`
  font-size: 1.2rem;
`;

const ChatMessages = styled.div`
  flex: 1;
  padding: 1rem;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 1rem;
`;

const Message = styled.div`
  padding: 0.8rem;
  border-radius: 8px;
  max-width: 70%;
  word-break: break-word;
  background-color: ${(props) => (props.isUser ? "#4f46e5" : "#f3f4f6")};
  color: ${(props) => (props.isUser ? "white" : "#1f2937")};
  align-self: ${(props) => (props.isUser ? "flex-end" : "flex-start")};
`;

const ChatInput = styled.div`
  display: flex;
  padding: 1rem;
  border-top: 1px solid #e5e7eb;
`;

const TextInput = styled.input`
  flex: 1;
  padding: 0.8rem;
  border: 1px solid #e5e7eb;
  border-radius: 5px 0 0 5px;
  font-size: 1rem;

  &:focus {
    outline: none;
    border-color: #4f46e5;
  }
`;

const SendButton = styled.button`
  background-color: #4f46e5;
  color: white;
  border: none;
  border-radius: 0 5px 5px 0;
  padding: 0 1.5rem;
  cursor: pointer;

  &:hover {
    background-color: #4338ca;
  }

  &:disabled {
    background-color: #9ca3af;
    cursor: not-allowed;
  }
`;

const ActionPanel = styled.div`
  background-color: #f9fafb;
  padding: 1rem;
  border-radius: 8px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  margin-top: 1rem;
`;

const ActionTitle = styled.h3`
  margin-top: 0;
  color: #1f2937;
  margin-bottom: 0.5rem;
`;

const ActionForm = styled.form`
  display: flex;
  flex-direction: column;
  gap: 1rem;
`;

const ActionInput = styled.input`
  padding: 0.8rem;
  border: 1px solid #e5e7eb;
  border-radius: 5px;
  font-size: 1rem;

  &:focus {
    outline: none;
    border-color: #4f46e5;
  }
`;

const ActionButton = styled.button`
  background-color: #4f46e5;
  color: white;
  border: none;
  border-radius: 5px;
  padding: 0.8rem;
  cursor: pointer;
  font-size: 1rem;
  margin-top: 0.5rem;

  &:hover {
    background-color: #4338ca;
  }

  &:disabled {
    background-color: #9ca3af;
    cursor: not-allowed;
  }
`;

const ErrorPanel = styled.div`
  background-color: #fee2e2;
  border: 1px solid #ef4444;
  border-radius: 8px;
  padding: 1rem;
  margin-top: 1rem;
  color: #b91c1c;
`;

const WarningPanel = styled.div`
  background-color: #fef3c7;
  border: 1px solid #f59e0b;
  border-radius: 8px;
  padding: 1rem;
  margin-top: 1rem;
  color: #b45309;
`;

const ConfirmTransferButton = styled(ActionButton)`
  background-color: #10b981;

  &:hover {
    background-color: #059669;
  }

  &:disabled {
    background-color: #9ca3af;
    cursor: not-allowed;
  }
`;

const SpinnerContainer = styled.div`
  display: inline-block;
  margin-right: 8px;
`;

const Spinner = styled.div`
  border: 3px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  border-top: 3px solid white;
  width: 16px;
  height: 16px;
  animation: spin 1s linear infinite;
  display: inline-block;

  @keyframes spin {
    0% {
      transform: rotate(0deg);
    }
    100% {
      transform: rotate(360deg);
    }
  }
`;

const WaitingSpinner = styled(Spinner)`
  border: 3px solid rgba(79, 70, 229, 0.3);
  border-top: 3px solid #4f46e5;
  width: 24px;
  height: 24px;
  display: inline-block;
  margin-right: 10px;
`;

const ChatPage = () => {
  const { isConnected, account, connectWallet, generateKeyPair } = useWeb3();
  const [messages, setMessages] = useState([
    { content: "您好！我是客服小x，有什么可以帮到您的吗？", isUser: false },
  ]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [action, setAction] = useState(null);
  const [actionData, setActionData] = useState({});
  const [waitingForTransfer, setWaitingForTransfer] = useState(false);
  const [keyPairGenerated, setKeyPairGenerated] = useState(null);
  const [processingPurchase, setProcessingPurchase] = useState(false);
  const [nftPrice, setNftPrice] = useState(null);
  const [registerError, setRegisterError] = useState(null);
  const [isCheckingRegisterStatus, setIsCheckingRegisterStatus] =
    useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    if (!localStorage.getItem("userId")) {
      localStorage.setItem(
        "userId",
        Date.now().toString(36) + Math.random().toString(36).substring(2)
      );
    }
    scrollToBottom();
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    console.log("状态更新: ", {
      waitingForTransfer,
      hasKeyPair: !!keyPairGenerated,
      action,
      processingPurchase,
      registerError,
    });
  }, [
    waitingForTransfer,
    keyPairGenerated,
    action,
    processingPurchase,
    registerError,
  ]);

  useEffect(() => {
    let intervalId;
    let retryCount = 0;
    const MAX_RETRIES = 3; // 每次API调用失败的最大重试次数
    const MAX_TOTAL_TIME = 10 * 60 * 1000; // 最长等待10分钟
    const startTime = Date.now();

    if (
      action === "register_data" &&
      waitingForTransfer &&
      !registerError &&
      !isCheckingRegisterStatus
    ) {
      const checkRegisterStatusWithRetry = async () => {
        // 检查是否超过最大等待时间
        if (Date.now() - startTime > MAX_TOTAL_TIME) {
          setMessages((prev) => [
            ...prev,
            {
              content: `数据集登记状态检查超时。如果您已完成转账，请稍后刷新页面查看状态，或联系平台客服。`,
              isUser: false,
            },
          ]);
          setWaitingForTransfer(false);
          setAction(null);
          setActionData({});
          clearInterval(intervalId);
          setIsCheckingRegisterStatus(false);
          return;
        }

        try {
          setIsCheckingRegisterStatus(true);
          console.log(`检查注册状态...(尝试次数: ${retryCount + 1})`);
          const result = await apiService.checkRegisterStatus(
            actionData.metadata_url,
            account
          );
          console.log("注册状态检查结果:", result);
          retryCount = 0; // 成功后重置重试计数

          if (result.status === "success") {
            // 成功登记
            setMessages((prev) => [
              ...prev,
              {
                content: `🎉 数据集登记成功！\nToken ID: ${
                  result.token_id
                }\n所有者: ${result.data_owner || account}\n元数据URL: ${
                  result.metadata_url || actionData.metadata_url
                }`,
                isUser: false,
              },
            ]);
            setWaitingForTransfer(false);
            setAction(null);
            setActionData({});
            clearInterval(intervalId);
            setIsCheckingRegisterStatus(false);
          } else if (result.status === "error") {
            // 登记错误
            setMessages((prev) => [
              ...prev,
              {
                content: `登记失败: ${result.message || "未知错误"}`,
                isUser: false,
              },
            ]);
            setWaitingForTransfer(false);
            setAction(null);
            setActionData({});
            clearInterval(intervalId);
            setIsCheckingRegisterStatus(false);
          } else if (result.status === "processing") {
            // 正在处理中
            const existingProcessingMsg = messages.some(
              (msg) =>
                !msg.isUser && msg.content.includes("已检测到转账，正在处理")
            );
            if (!existingProcessingMsg) {
              setMessages((prev) => [
                ...prev,
                {
                  content: `已检测到转账，正在处理铸造NFT，请稍候...`,
                  isUser: false,
                },
              ]);
            }
            setIsCheckingRegisterStatus(false);
          } else if (result.message && result.message.includes("检测到水印")) {
            // 检测到水印
            setRegisterError(result.message);
            setMessages((prev) => [
              ...prev,
              {
                content: result.message,
                isUser: false,
              },
            ]);
            setWaitingForTransfer(false);
            clearInterval(intervalId);
            setIsCheckingRegisterStatus(false);
          } else {
            // 其他状态
            setIsCheckingRegisterStatus(false);
          }
        } catch (error) {
          console.error("检查注册状态失败:", error);
          retryCount++; // 增加重试计数

          if (retryCount > MAX_RETRIES) {
            console.warn(`API调用连续失败${MAX_RETRIES}次，等待下一个周期`);
            retryCount = 0; // 重置重试计数
          } else {
            // 在短时间内重试
            setTimeout(() => {
              setIsCheckingRegisterStatus(false);
              checkRegisterStatusWithRetry();
            }, 3000); // 3秒后重试
            return; // 避免立即设置isCheckingRegisterStatus为false
          }

          setIsCheckingRegisterStatus(false);
        }
      };

      // 初始检查
      checkRegisterStatusWithRetry();

      // 设置周期性检查
      intervalId = setInterval(checkRegisterStatusWithRetry, 10000); // 每10秒检查一次
    }

    return () => {
      if (intervalId) {
        clearInterval(intervalId);
      }
    };
  }, [
    action,
    waitingForTransfer,
    actionData,
    account,
    messages,
    registerError,
    isCheckingRegisterStatus,
  ]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const handleInputChange = (e) => {
    setInput(e.target.value);
  };

  const handleSend = async (e) => {
    e?.preventDefault();

    if (!input.trim()) return;

    if (!isConnected) {
      const connected = await connectWallet();
      if (!connected) {
        alert("请先连接钱包");
        return;
      }
    }

    const userMessage = input;
    setMessages((prev) => [...prev, { content: userMessage, isUser: true }]);
    setInput("");
    setSending(true);

    try {
      const response = await apiService.sendMessage(userMessage, account);

      if (response.reply) {
        setMessages((prev) => [
          ...prev,
          { content: response.reply, isUser: false },
        ]);
      }

      if (response.action) {
        if (response.action !== action) {
          setWaitingForTransfer(false);
          setKeyPairGenerated(null);
          setProcessingPurchase(false);
          setNftPrice(null);
          setRegisterError(null);
        }
        setAction(response.action);
        setActionData({
          ...response,
          user_address: account,
        });
      } else {
        setAction(null);
        setActionData({});
        setWaitingForTransfer(false);
        setKeyPairGenerated(null);
        setProcessingPurchase(false);
        setNftPrice(null);
        setRegisterError(null);
      }
    } catch (error) {
      console.error("发送消息失败:", error);
      setMessages((prev) => [
        ...prev,
        { content: "抱歉，消息发送失败，请稍后再试。", isUser: false },
      ]);
    } finally {
      setSending(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const initiateNftPurchase = async () => {
    console.log("开始NFT购买流程");
    setMessages((prev) => [
      ...prev,
      {
        content: `正在处理NFT购买请求，正在检查NFT状态...`,
        isUser: false,
      },
    ]);

    // 生成密钥对
    const keyPair = await generateKeyPair();
    if (!keyPair) {
      setMessages((prev) => [
        ...prev,
        {
          content: "生成密钥对失败，请重试。",
          isUser: false,
        },
      ]);
      return;
    }

    const blob = new Blob([keyPair.privateKey], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "private_key.pem";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    setKeyPairGenerated(keyPair);
    console.log("已生成并保存密钥对");

    setMessages((prev) => [
      ...prev,
      {
        content:
          "已为您生成密钥对并自动下载了私钥文件。请务必保存好您的私钥，它将用于解密您购买的数据。",
        isUser: false,
      },
    ]);

    try {
      const nftDetails = await apiService.getNFTDetails(actionData.token_id);
      console.log("获取到NFT详情:", nftDetails);

      if (nftDetails.error || nftDetails.listing_status !== "Listed") {
        setMessages((prev) => [
          ...prev,
          {
            content: `无法购买NFT: ${nftDetails.error || "该NFT未上架销售"}`,
            isUser: false,
          },
        ]);
        setKeyPairGenerated(null);
        setAction(null);
        setActionData({});
        return;
      }

      setNftPrice(nftDetails.price);

      await new Promise((resolve) => {
        setWaitingForTransfer(true);
        setTimeout(resolve, 50);
      });

      setMessages((prev) => [
        ...prev,
        {
          content: `该NFT当前售价为 ${nftDetails.price} ETH。请向代理地址 0x70997970C51812dc3A010C7d01b50e0d17dc79C8 转账 ${nftDetails.price} ETH 以完成购买。\n\n系统将自动检测您的转账。如果您已完成转账但系统长时间未响应，可点击下方的"确认已转账"按钮继续处理。`,
          isUser: false,
        },
      ]);
    } catch (error) {
      console.error("获取NFT信息失败:", error);
      setMessages((prev) => [
        ...prev,
        {
          content: `获取NFT信息失败: ${
            error.message || "未知错误"
          }。请稍后再试。`,
          isUser: false,
        },
      ]);
      setKeyPairGenerated(null);
      setAction(null);
      setActionData({});
    }
  };

  const completePurchase = async () => {
    console.log("开始处理购买流程");
    setProcessingPurchase(true);

    setMessages((prev) => [
      ...prev,
      {
        content: "系统正在验证转账并处理购买流程，这可能需要几分钟时间...",
        isUser: false,
      },
    ]);

    try {
      const result = await apiService.buyNFT(
        actionData.token_id,
        account,
        keyPairGenerated.publicKey
      );

      console.log("购买结果:", result);

      if (result.status === "timeout") {
        setMessages((prev) => [
          ...prev,
          {
            content: `购买超时：系统未检测到您的转账交易。请确认您已经完成转账，或稍后再试。`,
            isUser: false,
          },
        ]);
        setProcessingPurchase(false);
        return;
      }

      if (result.status === "error") {
        setMessages((prev) => [
          ...prev,
          {
            content: `购买过程中出错：${
              result.message || "未知错误"
            }。请稍后重试或联系客服。`,
            isUser: false,
          },
        ]);
        setKeyPairGenerated(null);
        setWaitingForTransfer(false);
        setAction(null);
        setActionData({});
        setProcessingPurchase(false);
        setNftPrice(null);
        return;
      }

      const isMockCid =
        result.encrypted_cid &&
        result.encrypted_cid.startsWith("MOCK_ENCRYPTED_CID_");

      setMessages((prev) => [
        ...prev,
        {
          content: `🎉 NFT购买成功！您可以使用之前下载的私钥解密访问数据。\n\n购买详情：\nToken ID: ${
            actionData.token_id
          }\n购买者: ${account}\n\n您的私钥可以解密访问以下数据CID: ${
            result.encrypted_cid || "未获取到加密CID"
          }${isMockCid ? "\n\n注意: 由于系统原因，返回的是临时CID。" : ""}`,
          isUser: false,
        },
      ]);

      setKeyPairGenerated(null);
      setAction(null);
      setActionData({});
      setWaitingForTransfer(false);
      setProcessingPurchase(false);
      setNftPrice(null);
    } catch (error) {
      console.error("购买NFT失败:", error);

      let errorMessage = "未知错误";
      if (error.response && error.response.data) {
        errorMessage =
          error.response.data.error ||
          error.response.data.message ||
          "服务器错误";
      } else if (error.message) {
        errorMessage = error.message;
      }

      setMessages((prev) => [
        ...prev,
        {
          content: `购买失败: ${errorMessage}。请确认您已完成转账，或稍后再试。`,
          isUser: false,
        },
      ]);

      if (
        errorMessage.includes("超时") ||
        errorMessage.includes("未检测到转账")
      ) {
        setProcessingPurchase(false);
      } else {
        setKeyPairGenerated(null);
        setWaitingForTransfer(false);
        setAction(null);
        setActionData({});
        setProcessingPurchase(false);
        setNftPrice(null);
      }
    }
  };

  const handleAction = async (e) => {
    e.preventDefault();

    if (!isConnected) {
      await connectWallet();
      return;
    }

    try {
      let result;

      switch (action) {
        case "register_data":
          console.log("开始数据集登记，用户地址:", account);
          setMessages((prev) => [
            ...prev,
            {
              content: `正在处理数据集登记请求，用户地址: ${account}...`,
              isUser: false,
            },
          ]);

          // 先检查数据集是否存在水印
          try {
            // 调用 checkForWatermark.py 脚本检查数据集是否存在水印
            const checkResult = await apiService.checkDatasetWatermark(
              actionData.metadata_url
            );

            // 如果检测到水印，立即显示错误并阻止继续
            if (checkResult.has_watermark) {
              const errorMsg = `检测到该数据集存在水印！该数据集可能是从其他地方购买并转售的，为保护原创作者权益，禁止登记。`;

              // 使用同步方式更新所有相关状态
              await new Promise((resolve) => {
                setRegisterError(errorMsg);
                setAction(null);
                setActionData({});
                setWaitingForTransfer(false);
                setTimeout(resolve, 10); // 给一点时间处理状态更新
              });

              setMessages((prev) => [
                ...prev,
                {
                  content: errorMsg,
                  isUser: false,
                },
              ]);

              return;
            }
          } catch (error) {
            console.error("检查水印失败:", error);
            // 如果检查失败，记录日志，但仍继续流程
          }

          // 如果没有检测到水印，继续正常登记流程
          try {
            result = await apiService.registerData(
              actionData.metadata_url,
              account
            );

            console.log("数据集登记结果:", result);

            // 如果 API 返回错误信息，特别是有关水印的错误
            if (result.status === "error" || result.error) {
              const errorMsg = result.message || result.error || "登记失败";

              // 检查是否包含水印相关错误
              if (errorMsg.includes("水印") || errorMsg.includes("watermark")) {
                setRegisterError(errorMsg);
                setMessages((prev) => [
                  ...prev,
                  {
                    content: errorMsg,
                    isUser: false,
                  },
                ]);
                setAction(null);
                setActionData({});
                setWaitingForTransfer(false);
                return; // 提前返回，阻止后续转账流程
              } else {
                // 其他类型的错误
                setMessages((prev) => [
                  ...prev,
                  {
                    content: `登记失败: ${errorMsg}`,
                    isUser: false,
                  },
                ]);
                setAction(null);
                setActionData({});
                return;
              }
            }

            // 如果后端正常返回等待转账的状态
            if (result.status === "waiting_for_transfer") {
              setWaitingForTransfer(true);
              // 添加交易开始时间戳，用于超时检测
              setActionData({
                ...actionData,
                transferStartTime: Date.now(),
              });
              setMessages((prev) => [
                ...prev,
                {
                  content: `请向Agent地址转账 ${result.required_eth} ETH 以完成数据集登记: \n\n${result.agent_address}\n\n系统将等待您的转账交易，完成后会自动继续处理。`,
                  isUser: false,
                },
              ]);

              // 首次检查状态（立即检查一次）
              setTimeout(async () => {
                try {
                  const statusCheck = await apiService.checkRegisterStatus(
                    actionData.metadata_url,
                    account
                  );
                  console.log("初始状态检查结果:", statusCheck);
                } catch (error) {
                  console.error("初始状态检查失败:", error);
                }
              }, 3000); // 3秒后进行初始检查
            } else if (result.status === "success") {
              setMessages((prev) => [
                ...prev,
                {
                  content: `🎉 数据集登记成功！\nToken ID: ${result.token_id}\n所有者: ${result.data_owner}\n交易哈希: ${result.tx_hash}`,
                  isUser: false,
                },
              ]);
              setAction(null);
              setActionData({});
            } else {
              // 未知状态
              setMessages((prev) => [
                ...prev,
                {
                  content: `处理请求时发生未知情况: ${
                    result.message || "未知错误"
                  }`,
                  isUser: false,
                },
              ]);
              setAction(null);
              setActionData({});
            }
          } catch (error) {
            console.error("数据集登记失败:", error);

            // 检查响应中是否包含水印错误（HTTP 403）
            if (error.response && error.response.status === 403) {
              const errorMsg =
                error.response.data.error ||
                error.response.data.message ||
                "检测到数据集存在水印，禁止登记";
              setRegisterError(errorMsg);
              setMessages((prev) => [
                ...prev,
                {
                  content: errorMsg,
                  isUser: false,
                },
              ]);
              setAction(null);
              setActionData({});
              setWaitingForTransfer(false);
            } else {
              // 其他错误
              setMessages((prev) => [
                ...prev,
                {
                  content: `登记失败: ${error.message || "未知错误"}`,
                  isUser: false,
                },
              ]);
              setAction(null);
              setActionData({});
            }
          }
          break;

        case "list_nft":
          console.log("开始NFT上架，用户地址:", account);
          setMessages((prev) => [
            ...prev,
            {
              content: `正在处理NFT上架请求，用户地址: ${account}...`,
              isUser: false,
            },
          ]);

          result = await apiService.listNFT(
            actionData.token_id,
            actionData.price,
            account
          );
          setMessages((prev) => [
            ...prev,
            {
              content: `NFT上架成功！\n${result.output || ""}`,
              isUser: false,
            },
          ]);
          setAction(null);
          setActionData({});
          break;

        case "unlist_nft":
          result = await apiService.unlistNFT(
            actionData.token_id,
            actionData.user_address
          );
          setMessages((prev) => [
            ...prev,
            {
              content: `NFT下架成功！\n${result.output || ""}`,
              isUser: false,
            },
          ]);
          setAction(null);
          setActionData({});
          break;

        case "buy_nft":
          if (waitingForTransfer && keyPairGenerated && !processingPurchase) {
            await completePurchase();
          } else if (!keyPairGenerated) {
            await initiateNftPurchase();
          }
          break;

        case "report_nft":
          console.log("开始处理举报请求，用户地址:", account);
          setMessages((prev) => [
            ...prev,
            {
              content: `正在处理举报请求，检查 TokenID=${actionData.token_id_a} 和 TokenID=${actionData.token_id_b} 是否存在转售行为...`,
              isUser: false,
            },
          ]);

          setMessages((prev) => [
            ...prev,
            {
              content: `请向Agent地址转账 2.0 ETH 作为举报保证金:\n\n0x70997970C51812dc3A010C7d01b50e0d17dc79C8\n\n系统将等待您的转账，转账完成后会自动开始检测流程。如果举报成立，您将获得奖励；如果举报不成立，保证金将被没收。`,
              isUser: false,
            },
          ]);

          setWaitingForTransfer(true);
          setActionData({
            ...actionData,
            transferWaitStart: Date.now(),
          });

          // 检查转账函数
          const checkReportTransfer = async () => {
            console.log("检查举报转账状态...");
            try {
              const MAX_WAIT_TIME = 10 * 60 * 1000; // 10分钟
              if (Date.now() - actionData.transferWaitStart > MAX_WAIT_TIME) {
                setMessages((prev) => [
                  ...prev,
                  {
                    content: `等待转账超时。如果您已经完成转账但系统未检测到，请联系平台管理员。`,
                    isUser: false,
                  },
                ]);
                setWaitingForTransfer(false);
                setAction(null);
                setActionData({});
                return;
              }

              const transferCheckUrl = `${apiService.getBaseUrl()}/check-transfer`;
              const response = await fetch(transferCheckUrl, {
                method: "POST",
                headers: {
                  "Content-Type": "application/json",
                },
                body: JSON.stringify({
                  from_address: account,
                  to_address: "0x70997970C51812dc3A010C7d01b50e0d17dc79C8",
                  amount_eth: 2.0,
                  token_id_a: actionData.token_id_a,
                  token_id_b: actionData.token_id_b,
                }),
              });

              if (!response.ok) {
                setTimeout(checkReportTransfer, 5000);
                return;
              }

              const data = await response.json();
              console.log("转账检查结果:", data);

              if (data.status === "transfer_found") {
                setMessages((prev) => [
                  ...prev,
                  {
                    content: `已检测到您的转账！\n\n系统正在开始举报检测流程，这可能需要几分钟时间...`,
                    isUser: false,
                  },
                ]);

                const result = await apiService.reportNFT(
                  actionData.token_id_a,
                  actionData.token_id_b,
                  account
                );

                setTimeout(checkReportResult, 5000);
              } else {
                setTimeout(checkReportTransfer, 5000);
              }
            } catch (error) {
              console.error("检查转账状态失败:", error);
              setTimeout(checkReportTransfer, 5000);
            }
          };

          const checkReportResult = async () => {
            console.log("检查举报结果...");
            try {
              const resultCheckUrl = `${apiService.getBaseUrl()}/check-report-result`;
              const response = await fetch(resultCheckUrl, {
                method: "POST",
                headers: {
                  "Content-Type": "application/json",
                },
                body: JSON.stringify({
                  user_address: account,
                  token_id_a: actionData.token_id_a,
                  token_id_b: actionData.token_id_b,
                }),
              });

              if (!response.ok) {
                setTimeout(checkReportResult, 10000);
                return;
              }

              const data = await response.json();
              console.log("举报结果检查:", data);

              if (data.status === "completed") {
                let resultMessage = "";
                if (data.result === "proven") {
                  resultMessage = `✅ 举报成功！\n\n系统检测到TokenID=${actionData.token_id_a}和TokenID=${actionData.token_id_b}之间存在转售行为。\n\n您的保证金已返还，并获得了额外奖励。`;
                } else if (data.result === "rejected") {
                  resultMessage = `❌ 举报失败！\n\n系统未检测到转售行为，您的保证金已被没收。`;
                } else {
                  resultMessage = `举报检测已完成，但结果不明确。请联系平台管理员获取详细信息。`;
                }

                setMessages((prev) => [
                  ...prev,
                  {
                    content: resultMessage,
                    isUser: false,
                  },
                ]);

                setWaitingForTransfer(false);
                setAction(null);
                setActionData({});
              } else if (data.status === "processing") {
                setMessages((prev) => [
                  ...prev,
                  {
                    content: `检测仍在进行中: ${
                      data.progress || "正在分析数据集相似度..."
                    }`,
                    isUser: false,
                  },
                ]);
                setTimeout(checkReportResult, 10000);
              } else {
                setTimeout(checkReportResult, 10000);
              }
            } catch (error) {
              console.error("检查举报结果失败:", error);
              setTimeout(checkReportResult, 10000);
            }
          };

          setTimeout(checkReportTransfer, 5000);

          return;

        default:
          setMessages((prev) => [
            ...prev,
            {
              content: "不支持的操作类型。",
              isUser: false,
            },
          ]);
          setAction(null);
          setActionData({});
      }
    } catch (error) {
      console.error("执行操作失败:", error);
      setMessages((prev) => [
        ...prev,
        {
          content: `操作失败: ${
            error.response?.data?.error || error.message || "未知错误"
          }`,
          isUser: false,
        },
      ]);
      setKeyPairGenerated(null);
      setWaitingForTransfer(false);
      setAction(null);
      setActionData({});
      setProcessingPurchase(false);
      setNftPrice(null);
    }
  };

  const renderActionPanel = () => {
    console.log("渲染动作面板, 当前状态:", {
      action,
      waitingForTransfer,
      hasKeyPair: !!keyPairGenerated,
      processingPurchase,
      registerError,
    });

    if (
      action === "register_data" &&
      registerError &&
      registerError.includes("水印")
    ) {
      return (
        <ErrorPanel>
          <ActionTitle>数据集登记失败</ActionTitle>
          <p>{registerError}</p>
          <p>
            系统检测到该数据集可能是转售数据，为保护原创作者权益，禁止登记。
          </p>
          <ActionButton
            onClick={() => {
              setAction(null);
              setActionData({});
              setRegisterError(null);
            }}
            style={{ backgroundColor: "#ef4444" }}
          >
            关闭
          </ActionButton>
        </ErrorPanel>
      );
    }

    if (!action) return null;

    switch (action) {
      case "register_data":
        if (waitingForTransfer) {
          return (
            <ActionPanel>
              <ActionTitle>数据集登记</ActionTitle>
              <p>您想登记以下数据集：</p>
              <p>
                <strong>元数据URL：</strong> {actionData.metadata_url}
              </p>
              <p style={{ color: "#d97706", marginBottom: "0.5rem" }}>
                请向代理地址{" "}
                <strong>0x70997970C51812dc3A010C7d01b50e0d17dc79C8</strong> 转账
                3 ETH 以完成数据集登记。
              </p>
              <p style={{ color: "#4f46e5", marginBottom: "1rem" }}>
                系统将自动检测您的转账，完成后会自动继续处理。
              </p>
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                }}
              >
                <WaitingSpinner /> <span>等待转账中...</span>
              </div>
            </ActionPanel>
          );
        }

        return (
          <ActionPanel>
            <ActionTitle>数据集登记</ActionTitle>
            <p>您想登记以下数据集：</p>
            <p>
              <strong>元数据URL：</strong> {actionData.metadata_url}
            </p>
            <ActionButton onClick={handleAction}>确认登记</ActionButton>
          </ActionPanel>
        );

      case "list_nft":
        return (
          <ActionPanel>
            <ActionTitle>上架NFT</ActionTitle>
            <p>您想上架以下NFT：</p>
            <p>
              <strong>Token ID：</strong> {actionData.token_id}
            </p>
            <p>
              <strong>价格：</strong> {actionData.price} ETH
            </p>
            <ActionButton onClick={handleAction}>确认上架</ActionButton>
          </ActionPanel>
        );

      case "unlist_nft":
        return (
          <ActionPanel>
            <ActionTitle>下架NFT</ActionTitle>
            <p>您想下架以下NFT：</p>
            <p>
              <strong>Token ID：</strong> {actionData.token_id}
            </p>
            <ActionButton onClick={handleAction}>确认下架</ActionButton>
          </ActionPanel>
        );

      case "buy_nft":
        if (processingPurchase) {
          return (
            <ActionPanel>
              <ActionTitle>购买NFT</ActionTitle>
              <p>您想购买以下NFT：</p>
              <p>
                <strong>Token ID：</strong> {actionData.token_id}
              </p>
              <p>
                <strong>价格：</strong> {nftPrice} ETH
              </p>
              <p style={{ color: "#4f46e5", fontWeight: "bold" }}>
                正在验证转账并处理购买，请稍候...
              </p>
              <ActionButton disabled>
                <SpinnerContainer>
                  <Spinner />
                </SpinnerContainer>
                处理中
              </ActionButton>
            </ActionPanel>
          );
        } else if (waitingForTransfer && keyPairGenerated) {
          return (
            <ActionPanel>
              <ActionTitle>购买NFT</ActionTitle>
              <p>您想购买以下NFT：</p>
              <p>
                <strong>Token ID：</strong> {actionData.token_id}
              </p>
              <p>
                <strong>价格：</strong> {nftPrice} ETH
              </p>
              <p style={{ color: "#d97706", marginBottom: "0.5rem" }}>
                请向代理地址{" "}
                <strong>0x70997970C51812dc3A010C7d01b50e0d17dc79C8</strong> 转账{" "}
                {nftPrice} ETH。
              </p>
              <p style={{ color: "#4f46e5", marginBottom: "1rem" }}>
                系统将自动检测转账。如已转账但系统未响应，请点击下方按钮。
              </p>
              <ConfirmTransferButton onClick={handleAction}>
                确认已转账
              </ConfirmTransferButton>
            </ActionPanel>
          );
        } else if (keyPairGenerated) {
          return (
            <ActionPanel>
              <ActionTitle>购买NFT</ActionTitle>
              <p>您想购买以下NFT：</p>
              <p>
                <strong>Token ID：</strong> {actionData.token_id}
              </p>
              <p>正在处理购买交易...</p>
              <ActionButton disabled>
                <SpinnerContainer>
                  <Spinner />
                </SpinnerContainer>
                处理中
              </ActionButton>
            </ActionPanel>
          );
        } else {
          return (
            <ActionPanel>
              <ActionTitle>购买NFT</ActionTitle>
              <p>您想购买以下NFT：</p>
              <p>
                <strong>Token ID：</strong> {actionData.token_id}
              </p>
              <p>购买将生成密钥对，私钥将自动下载，请务必保存</p>
              <ActionButton onClick={handleAction}>确认购买</ActionButton>
            </ActionPanel>
          );
        }

      case "report_nft":
        if (waitingForTransfer) {
          return (
            <ActionPanel>
              <ActionTitle>举报NFT</ActionTitle>
              <p>您想举报以下NFT存在转售行为：</p>
              <p>
                <strong>Token ID A：</strong> {actionData.token_id_a}
              </p>
              <p>
                <strong>Token ID B：</strong> {actionData.token_id_b}
              </p>
              <p style={{ color: "#d97706", marginBottom: "0.5rem" }}>
                请向代理地址{" "}
                <strong>0x70997970C51812dc3A010C7d01b50e0d17dc79C8</strong> 转账
                2.0 ETH 作为举报保证金。
              </p>
              <p style={{ color: "#4f46e5", marginBottom: "1rem" }}>
                系统将自动检测您的转账，完成后会自动开始检测流程。
              </p>
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                }}
              >
                <WaitingSpinner /> <span>等待转账中...</span>
              </div>
            </ActionPanel>
          );
        }

        return (
          <ActionPanel>
            <ActionTitle>举报NFT</ActionTitle>
            <p>您想举报以下NFT存在转售行为：</p>
            <p>
              <strong>Token ID A：</strong> {actionData.token_id_a}
            </p>
            <p>
              <strong>Token ID B：</strong> {actionData.token_id_b}
            </p>
            <ActionButton onClick={handleAction}>确认举报</ActionButton>
          </ActionPanel>
        );

      default:
        return null;
    }
  };

  return (
    <div>
      <ChatContainer>
        <ChatHeader>
          <Avatar>AI</Avatar>
          <ChatTitle>客服小x</ChatTitle>
        </ChatHeader>

        <ChatMessages>
          {messages.map((message, index) => (
            <Message key={index} isUser={message.isUser}>
              {message.content}
            </Message>
          ))}
          <div ref={messagesEndRef} />
        </ChatMessages>

        <ChatInput>
          <TextInput
            type="text"
            value={input}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            placeholder="输入消息..."
            disabled={sending}
          />
          <SendButton onClick={handleSend} disabled={sending || !input.trim()}>
            发送
          </SendButton>
        </ChatInput>
      </ChatContainer>

      {renderActionPanel()}
    </div>
  );
};

export default ChatPage;
