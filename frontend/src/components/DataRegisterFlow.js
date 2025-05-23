import React, { useState, useEffect } from "react";
import apiService from "../services/apiService";
import {
  Typography,
  Box,
  CircularProgress,
  Alert,
  Button,
  LinearProgress,
} from "@mui/material";

// 数据登记流程组件 - 处理各种状态和错误
const DataRegisterFlow = ({
  metadata_url,
  dataset_cid,
  account,
  onComplete,
  onError,
  onCancel,
}) => {
  // 流程状态
  const [status, setStatus] = useState("initial"); // initial, checking_watermark, register, waiting_transfer, success, error
  const [message, setMessage] = useState("开始处理数据集登记...");
  const [error, setError] = useState(null);
  const [transferInfo, setTransferInfo] = useState(null);
  const [progress, setProgress] = useState(0);
  const [startTime, setStartTime] = useState(null);
  const [sessionId, setSessionId] = useState(null);

  // 在组件加载时开始流程
  useEffect(() => {
    startRegistrationFlow();
    return () => {
      // 清理函数
    };
  }, []);

  // 进度条更新
  useEffect(() => {
    let timer;
    if (status === "checking_watermark" || status === "waiting_transfer") {
      timer = setInterval(() => {
        setProgress((prevProgress) => {
          // 检查水印阶段，进度上限为90%
          if (status === "checking_watermark" && prevProgress >= 90) {
            return 90;
          }
          // 等待转账阶段，进度上限为95%
          if (status === "waiting_transfer" && prevProgress >= 95) {
            return 95;
          }
          return Math.min(prevProgress + 1, 100);
        });
      }, 1000);
    }

    return () => {
      if (timer) clearInterval(timer);
    };
  }, [status]);

  // 当处于等待转账状态时，定期检查转账状态
  useEffect(() => {
    let transferCheckInterval;

    if (status === "waiting_transfer" && transferInfo && sessionId) {
      // 立即执行一次检查
      checkTransferStatus();

      // 设置15秒检查一次
      transferCheckInterval = setInterval(() => {
        checkTransferStatus();
      }, 15000);

      // 设置总超时时间（30分钟）
      const timeoutTimer = setTimeout(() => {
        if (status === "waiting_transfer") {
          setStatus("error");
          setError("等待转账超时，请重新开始登记流程或联系客服。");
          clearInterval(transferCheckInterval);
        }
      }, 30 * 60 * 1000);

      return () => {
        clearInterval(transferCheckInterval);
        clearTimeout(timeoutTimer);
      };
    }
  }, [status, transferInfo, sessionId]);

  // 启动注册流程
  const startRegistrationFlow = async () => {
    try {
      setStartTime(Date.now());

      // 1. 检查水印
      await checkWatermark();

      // 2. 提交注册请求
      await registerData();
    } catch (error) {
      console.error("注册流程失败:", error);
      setStatus("error");
      setError(error.message || "注册过程中出错");
      if (onError) onError(error);
    }
  };

  // 检查水印
  const checkWatermark = async () => {
    setStatus("checking_watermark");
    setMessage("正在检查数据集是否存在水印，请稍候...");
    setProgress(0);

    try {
      const checkResult = await apiService.checkDatasetWatermark(
        metadata_url,
        dataset_cid
      );
      console.log("水印检查结果:", checkResult);

      // 处理超时
      if (checkResult.timeout) {
        throw new Error(`水印检查超时: ${checkResult.error}。请稍后重试。`);
      }

      // 处理水印检测
      if (checkResult.has_watermark) {
        throw new Error(
          "检测到该数据集存在水印！该数据集可能是从其他地方购买并转售的，为保护原创作者权益，禁止登记。"
        );
      }

      // 处理其他错误
      if (checkResult.error_occurred) {
        console.warn("水印检测过程中出现错误:", checkResult.error);
        setMessage(
          `水印检测过程中出现问题，但将继续登记流程。${checkResult.error}`
        );
        // 继续执行，不阻止登记流程
      } else {
        setMessage("水印检查完成，未检测到水印，正在提交登记请求...");
      }

      return true;
    } catch (error) {
      console.error("水印检查失败:", error);
      throw error;
    }
  };

  // 提交注册请求
  const registerData = async () => {
    setStatus("register");
    setMessage("正在提交数据集登记请求...");

    try {
      const result = await apiService.registerData(metadata_url, account);
      console.log("数据集登记结果:", result);

      // 处理各种返回状态
      if (result.status === "waiting_for_transfer") {
        setStatus("waiting_transfer");
        setSessionId(result.session_id);
        setTransferInfo({
          agent_address: result.agent_address,
          required_eth: result.required_eth,
          start_time: Date.now(),
        });
        setMessage(
          `请向Agent地址转账 ${result.required_eth} ETH 以完成数据集登记。系统将等待您的转账交易，完成后会自动继续处理。`
        );
      } else if (result.status === "success") {
        setStatus("success");
        setMessage(
          `数据集登记成功！Token ID: ${result.token_id}, 所有者: ${result.data_owner}`
        );
        if (onComplete) onComplete(result);
      } else if (result.status === "error") {
        throw new Error(result.message || "未知错误");
      } else {
        setMessage(`处理请求中，状态: ${result.status || "未知"}`);
      }
    } catch (error) {
      console.error("注册数据失败:", error);
      throw error;
    }
  };

  // 检查转账状态
  const checkTransferStatus = async () => {
    if (!metadata_url || !account || !sessionId) return;

    try {
      const statusCheck = await apiService.checkRegisterStatus(
        metadata_url,
        account
      );
      console.log("转账状态检查结果:", statusCheck);

      if (statusCheck.status === "success") {
        setStatus("success");
        setProgress(100);
        setMessage(
          `🎉 数据集登记成功！Token ID: ${statusCheck.token_id}, 所有者: ${statusCheck.data_owner}`
        );
        if (onComplete) onComplete(statusCheck);
      } else if (statusCheck.status === "processing") {
        setMessage(
          `已检测到转账，正在铸造NFT，请稍候... (交易哈希: ${
            statusCheck.tx_hash || "处理中"
          })`
        );
      } else if (statusCheck.status === "error") {
        setStatus("error");
        setError(statusCheck.message || "登记过程出错");
        if (onError) onError(new Error(statusCheck.message));
      }
    } catch (error) {
      console.error("检查转账状态失败:", error);
      // 检查状态失败不要中断等待过程，只记录日志
    }
  };

  // 渲染转账信息
  const renderTransferInfo = () => {
    if (!transferInfo) return null;

    return (
      <Box sx={{ mt: 2, p: 2, bgcolor: "background.paper", borderRadius: 1 }}>
        <Typography variant="subtitle1" gutterBottom>
          请转账以完成登记:
        </Typography>
        <Typography variant="body2" component="div" sx={{ my: 1 }}>
          <strong>收款地址:</strong> {transferInfo.agent_address}
        </Typography>
        <Typography variant="body2" component="div" sx={{ my: 1 }}>
          <strong>金额:</strong> {transferInfo.required_eth} ETH
        </Typography>
        <Alert severity="info" sx={{ mt: 2 }}>
          转账完成后，系统将自动检测并继续处理。如长时间未响应，请刷新页面重新检查状态。
        </Alert>
      </Box>
    );
  };

  // 渲染组件
  return (
    <Box sx={{ width: "100%", p: 2 }}>
      {/* 状态信息 */}
      <Typography variant="h6" gutterBottom>
        数据集登记流程
      </Typography>

      {/* 显示当前状态 */}
      <Typography variant="body1" gutterBottom>
        {message}
      </Typography>

      {/* 进度条 */}
      {(status === "checking_watermark" ||
        status === "register" ||
        status === "waiting_transfer") && (
        <Box sx={{ display: "flex", alignItems: "center", mt: 2 }}>
          <Box sx={{ width: "100%", mr: 1 }}>
            <LinearProgress variant="determinate" value={progress} />
          </Box>
          <Box sx={{ minWidth: 35 }}>
            <Typography variant="body2" color="text.secondary">{`${Math.round(
              progress
            )}%`}</Typography>
          </Box>
        </Box>
      )}

      {/* 转账信息 */}
      {status === "waiting_transfer" && renderTransferInfo()}

      {/* 错误信息 */}
      {status === "error" && (
        <Alert severity="error" sx={{ mt: 2 }}>
          {error || "处理过程中出错，请稍后重试。"}
        </Alert>
      )}

      {/* 成功信息 */}
      {status === "success" && (
        <Alert severity="success" sx={{ mt: 2 }}>
          {message}
        </Alert>
      )}

      {/* 取消按钮 */}
      {["checking_watermark", "register", "waiting_transfer"].includes(
        status
      ) && (
        <Button
          variant="outlined"
          color="secondary"
          sx={{ mt: 2 }}
          onClick={() => {
            if (onCancel) onCancel();
          }}
        >
          取消
        </Button>
      )}

      {/* 完成按钮 */}
      {["success", "error"].includes(status) && (
        <Button
          variant="contained"
          color={status === "success" ? "primary" : "secondary"}
          sx={{ mt: 2 }}
          onClick={() => {
            if (onComplete) onComplete();
          }}
        >
          {status === "success" ? "完成" : "关闭"}
        </Button>
      )}
    </Box>
  );
};

export default DataRegisterFlow;
