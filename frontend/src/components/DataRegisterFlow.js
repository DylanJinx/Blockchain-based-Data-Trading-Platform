import React, { useState, useEffect } from "react";
import apiService from "../services/apiService";
import PowersOfTauContribution from "./PowersOfTauContribution";
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
  const [status, setStatus] = useState("initial"); // initial, checking_watermark, powers_of_tau, register, waiting_transfer, success, error, copyright_violation
  const [message, setMessage] = useState("开始处理数据集登记...");
  const [error, setError] = useState(null);
  const [transferInfo, setTransferInfo] = useState(null);
  const [progress, setProgress] = useState(0);
  const [startTime, setStartTime] = useState(null);
  const [sessionId, setSessionId] = useState(null);

  // Powers of Tau 相关状态
  const [powersOfTauInfo, setPowersOfTauInfo] = useState(null);
  const [requiresUserContribution, setRequiresUserContribution] =
    useState(false);

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

      // 直接提交注册请求，让后端处理水印检测
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
      // 首先调用水印检测API
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
        // 检测到水印，需要调用登记API来启动Powers of Tau流程
        console.log("检测到水印，开始Powers of Tau流程");
        setMessage("检测到水印，正在准备零知识证明生成流程...");

        try {
          const registerResult = await apiService.registerData(
            metadata_url,
            account
          );
          console.log("登记结果（水印情况）:", registerResult);

          if (registerResult.status === "copyright_violation") {
            setStatus("copyright_violation");
            setMessage(registerResult.message);

            // 检查是否需要用户在浏览器中进行贡献
            if (registerResult.requires_user_contribution) {
              setPowersOfTauInfo({
                user_id: registerResult.user_id,
                constraint_power: registerResult.constraint_power,
                ptau_info: registerResult.ptau_info,
              });
              setRequiresUserContribution(true);
              setStatus("powers_of_tau");
              setMessage(
                "需要您在浏览器中完成Powers of Tau贡献来生成零知识证明"
              );
            }
            return false; // 不继续正常登记流程
          }
        } catch (registerError) {
          console.error("处理水印情况时出错:", registerError);
          throw new Error(`检测到水印且处理失败: ${registerError.message}`);
        }
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
    setMessage("正在检查数据集并提交登记请求...");

    try {
      const result = await apiService.registerData(metadata_url, account);
      console.log("数据集登记结果:", result);

      // 处理各种返回状态
      if (result.status === "copyright_violation") {
        // 处理水印侵权情况
        setStatus("copyright_violation");
        setMessage(result.message);

        // 检查是否需要用户在浏览器中进行贡献
        if (result.requires_user_contribution) {
          setPowersOfTauInfo({
            user_id: result.user_id,
            constraint_power: result.constraint_power,
            ptau_info: result.ptau_info,
          });
          setRequiresUserContribution(true);
          setStatus("powers_of_tau");
          setMessage("需要您在浏览器中完成Powers of Tau贡献来生成零知识证明");
        }
      } else if (result.status === "waiting_for_transfer") {
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

  // 处理Powers of Tau贡献完成
  const handlePowersOfTauComplete = (result) => {
    console.log("Powers of Tau贡献完成:", result);
    setStatus("success");
    setMessage(
      "🎉 Powers of Tau贡献成功完成！\n✅ 您的随机性贡献已验证成功\n🔄 零知识证明正在生成，证明您的数据集确实包含水印\n📁 相关证明请到证明界面领取\n⏳ 零知识证明生成需要额外时间，系统正在后台处理\n💡 您现在可以安全地关闭此页面"
    );
    setRequiresUserContribution(false);
    if (onComplete) {
      onComplete({
        status: "copyright_violation_proven",
        message: "已生成零知识证明证明数据集包含水印",
        proof_result: result,
      });
    }
  };

  // 处理Powers of Tau贡献错误
  const handlePowersOfTauError = (error) => {
    console.error("Powers of Tau贡献失败:", error);
    setStatus("error");
    setError(`零知识证明生成失败: ${error.message}`);
    setRequiresUserContribution(false);
    if (onError) onError(error);
  };

  // 检查转账状态
  const checkTransferStatus = async () => {
    if (!metadata_url || !account || !sessionId) return;

    try {
      // 首先检查注册状态
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
      } else if (
        statusCheck.status === "waiting_for_transfer" &&
        transferInfo
      ) {
        // 如果仍在等待转账，检查是否已经完成转账并触发后续流程
        try {
          const transferCheck = await apiService.checkTransfer(
            account,
            transferInfo.agent_address,
            transferInfo.required_eth,
            sessionId
          );

          console.log("转账检查结果:", transferCheck);

          if (transferCheck.status === "transfer_confirmed_minting_started") {
            setMessage("转账已确认，NFT铸造流程已启动，请稍候...");
            setProgress(80);
          } else if (transferCheck.status === "transfer_found") {
            setMessage("转账已确认，正在启动后续处理...");
          } else if (transferCheck.status === "no_transfer") {
            // 转账尚未完成，保持等待状态
            console.log("转账尚未完成，继续等待...");
          }
        } catch (transferError) {
          console.error("检查转账失败:", transferError);
          // 转账检查失败不影响主流程，继续通过状态检查
        }
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

      {/* Powers of Tau 贡献界面 */}
      {status === "powers_of_tau" &&
        requiresUserContribution &&
        powersOfTauInfo && (
          <PowersOfTauContribution
            userId={powersOfTauInfo.user_id}
            constraintPower={powersOfTauInfo.constraint_power}
            onComplete={handlePowersOfTauComplete}
            onError={handlePowersOfTauError}
          />
        )}

      {/* 转账信息 */}
      {status === "waiting_transfer" && renderTransferInfo()}

      {/* 侵权警告信息 */}
      {status === "copyright_violation" && !requiresUserContribution && (
        <Alert severity="warning" sx={{ mt: 2 }}>
          {message}
        </Alert>
      )}

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
      {[
        "checking_watermark",
        "register",
        "waiting_transfer",
        "powers_of_tau",
      ].includes(status) && (
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
      {["success", "error", "copyright_violation"].includes(status) &&
        !requiresUserContribution && (
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
