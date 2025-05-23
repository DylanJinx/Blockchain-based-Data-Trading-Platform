import React, { useState, useEffect } from "react";
import {
  Container,
  Box,
  TextField,
  Button,
  Paper,
  Typography,
  List,
  ListItem,
  ListItemText,
  CircularProgress,
  Dialog,
  DialogContent,
} from "@mui/material";
import apiService from "../services/apiService";
import DataRegisterFlow from "../components/DataRegisterFlow";

const ChatPage = () => {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [userId] = useState(
    () => "user_" + Math.random().toString(36).substr(2, 9)
  );
  const [action, setAction] = useState(null);
  const [actionData, setActionData] = useState({});
  const [waitingForTransfer, setWaitingForTransfer] = useState(false);
  const [registerError, setRegisterError] = useState(null);

  // 添加用于渲染注册流程组件的状态
  const [dataRegisterFlow, setDataRegisterFlow] = useState(false);
  const [dataRegisterProps, setDataRegisterProps] = useState({});

  // 获取用户钱包地址
  const [account, setAccount] = useState("");

  useEffect(() => {
    // 模拟获取钱包地址
    setAccount("0x1234567890123456789012345678901234567890");

    // 初始欢迎信息
    setMessages([
      {
        content: "欢迎使用数据交易平台! 我是客服小x，请问有什么可以帮您?",
        isUser: false,
      },
    ]);
  }, []);

  // 处理消息发送
  const handleSendMessage = async () => {
    if (!inputMessage.trim()) return;

    const userMessage = {
      content: inputMessage,
      isUser: true,
    };

    setMessages((prev) => [...prev, userMessage]);
    setLoading(true);
    setInputMessage("");

    try {
      const response = await apiService.sendMessage(
        inputMessage,
        userId,
        account
      );

      if (response.action) {
        // 处理特殊动作
        setAction(response.action);
        setActionData(response);
      } else {
        // 正常回复
        setMessages((prev) => [
          ...prev,
          {
            content: response.reply,
            isUser: false,
          },
        ]);
      }
    } catch (error) {
      console.error("发送消息失败:", error);
      setMessages((prev) => [
        ...prev,
        {
          content: "抱歉，消息发送失败，请重试。",
          isUser: false,
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  // 处理特殊动作
  useEffect(() => {
    if (!action) return;

    const handleAction = async () => {
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

          // 显示注册流程组件
          setDataRegisterFlow(true);
          setDataRegisterProps({
            metadata_url: actionData.metadata_url,
            dataset_cid: extractCidFromMetadataUrl(actionData.metadata_url),
            account: account,
            onComplete: (result) => {
              console.log("数据集登记完成:", result);
              setMessages((prev) => [
                ...prev,
                {
                  content: `🎉 数据集登记成功！\n${
                    result?.token_id ? `Token ID: ${result.token_id}\n` : ""
                  }${
                    result?.data_owner ? `所有者: ${result.data_owner}\n` : ""
                  }${result?.tx_hash ? `交易哈希: ${result.tx_hash}` : ""}`,
                  isUser: false,
                },
              ]);
              setDataRegisterFlow(false);
              setAction(null);
              setActionData({});
            },
            onError: (error) => {
              console.error("数据集登记错误:", error);
              setMessages((prev) => [
                ...prev,
                {
                  content: `登记失败: ${error.message || "未知错误"}`,
                  isUser: false,
                },
              ]);
              setDataRegisterFlow(false);
              setAction(null);
              setActionData({});
            },
            onCancel: () => {
              setMessages((prev) => [
                ...prev,
                {
                  content: "您已取消数据集登记流程。",
                  isUser: false,
                },
              ]);
              setDataRegisterFlow(false);
              setAction(null);
              setActionData({});
            },
          });
          break;

        case "list_nft":
          // 其他动作的处理...
          break;

        case "unlist_nft":
          // 其他动作的处理...
          break;

        case "buy_nft":
          // 其他动作的处理...
          break;

        case "report_nft":
          // 其他动作的处理...
          break;

        default:
          console.warn("未知动作类型:", action);
      }
    };

    handleAction();
  }, [action, actionData, account]);

  // 添加用于提取 CID 的辅助函数
  const extractCidFromMetadataUrl = (url) => {
    if (!url) return "";

    // 尝试从 IPFS URL 中提取 CID
    // 例如: https://ipfs.io/ipfs/QmXZ4goAz... => QmXZ4goAz...
    const ipfsMatch = url.match(/\/ipfs\/([a-zA-Z0-9]+)/);
    if (ipfsMatch && ipfsMatch[1]) {
      return ipfsMatch[1];
    }

    // 尝试从其他格式的URL中提取
    const cidMatch = url.match(/([a-zA-Z0-9]{46})/);
    if (cidMatch && cidMatch[1]) {
      return cidMatch[1];
    }

    return "";
  };

  return (
    <Container maxWidth="md">
      <Box sx={{ my: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          数据交易平台
        </Typography>

        <Paper sx={{ p: 2, mb: 2, maxHeight: "400px", overflow: "auto" }}>
          <List>
            {messages.map((message, index) => (
              <ListItem
                key={index}
                sx={{
                  justifyContent: message.isUser ? "flex-end" : "flex-start",
                  mb: 1,
                }}
              >
                <Paper
                  elevation={1}
                  sx={{
                    p: 1,
                    bgcolor: message.isUser ? "primary.light" : "grey.100",
                    maxWidth: "70%",
                  }}
                >
                  <ListItemText
                    primary={message.content}
                    sx={{
                      "& .MuiListItemText-primary": {
                        whiteSpace: "pre-line",
                      },
                    }}
                  />
                </Paper>
              </ListItem>
            ))}
          </List>
        </Paper>

        <Box sx={{ display: "flex", alignItems: "center" }}>
          <TextField
            fullWidth
            variant="outlined"
            label="发送消息"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={(e) => e.key === "Enter" && handleSendMessage()}
            disabled={loading}
            sx={{ mr: 1 }}
          />
          <Button
            variant="contained"
            onClick={handleSendMessage}
            disabled={loading}
          >
            {loading ? <CircularProgress size={24} /> : "发送"}
          </Button>
        </Box>
      </Box>

      {/* 数据登记流程组件 */}
      {dataRegisterFlow && (
        <Dialog open={dataRegisterFlow} fullWidth maxWidth="md">
          <DialogContent>
            <DataRegisterFlow {...dataRegisterProps} />
          </DialogContent>
        </Dialog>
      )}
    </Container>
  );
};

export default ChatPage;
