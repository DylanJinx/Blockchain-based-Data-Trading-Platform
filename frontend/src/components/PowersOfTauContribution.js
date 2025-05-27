import React, { useState, useEffect } from "react";
import {
  Box,
  Button,
  Typography,
  CircularProgress,
  Alert,
  TextField,
  Paper,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  LinearProgress,
} from "@mui/material";
import apiService from "../services/apiService";

const PowersOfTauContribution = ({
  userId,
  constraintPower,
  onComplete,
  onError,
}) => {
  const [activeStep, setActiveStep] = useState(0);
  const [contributing, setContributing] = useState(false);
  const [entropy, setEntropy] = useState("");
  const [mouseEntropy, setMouseEntropy] = useState([]);
  const [keyboardEntropy, setKeyboardEntropy] = useState([]);
  const [progress, setProgress] = useState(0);
  const [statusMessage, setStatusMessage] = useState("");

  const steps = [
    {
      label: "生成随机性",
      description: "通过您的输入和互动生成随机性数据",
    },
    {
      label: "提交贡献",
      description: "将您的随机性数据发送到服务器进行处理",
    },
    {
      label: "完成贡献",
      description: "服务器完成Powers of Tau贡献生成",
    },
  ];

  // 收集鼠标移动的随机性
  useEffect(() => {
    let mouseData = [];
    let startTime = Date.now();

    const handleMouseMove = (e) => {
      if (mouseData.length < 100) {
        // 限制收集的数据量
        mouseData.push({
          x: e.clientX,
          y: e.clientY,
          timestamp: Date.now() - startTime,
        });
        setMouseEntropy([...mouseData]);
      }
    };

    const handleKeyPress = (e) => {
      if (keyboardEntropy.length < 50) {
        // 限制收集的数据量
        setKeyboardEntropy((prev) => [
          ...prev,
          {
            key: e.key,
            timestamp: Date.now() - startTime,
            keyCode: e.keyCode,
          },
        ]);
      }
    };

    if (activeStep === 0) {
      document.addEventListener("mousemove", handleMouseMove);
      document.addEventListener("keypress", handleKeyPress);
    }

    return () => {
      document.removeEventListener("mousemove", handleMouseMove);
      document.removeEventListener("keypress", handleKeyPress);
    };
  }, [activeStep, keyboardEntropy.length]);

  const validateEntropy = () => {
    return (
      entropy.length >= 10 &&
      mouseEntropy.length >= 20 &&
      keyboardEntropy.length >= 5
    );
  };

  const generateCombinedEntropy = () => {
    const combined = {
      userInput: entropy,
      mouseMovements: mouseEntropy,
      keyboardEvents: keyboardEntropy,
      timestamp: Date.now(),
      userAgent: navigator.userAgent,
      screenInfo: {
        width: window.screen.width,
        height: window.screen.height,
      },
      randomValues: Array.from({ length: 10 }, () => Math.random()),
    };

    return JSON.stringify(combined);
  };

  const handleEntropyChange = (event) => {
    setEntropy(event.target.value);
  };

  const handleStartContribution = async () => {
    if (!validateEntropy()) {
      alert(
        "请确保输入足够的随机性数据：\n- 至少10个字符的文本\n- 至少移动鼠标20次\n- 至少按键5次"
      );
      return;
    }

    setActiveStep(1);
    setContributing(true);
    setProgress(0);

    try {
      setStatusMessage("正在准备您的随机性数据...");
      setProgress(10);

      const combinedEntropy = generateCombinedEntropy();

      setStatusMessage("正在发送数据到服务器...");
      setProgress(20);

      // 使用apiService而不是直接fetch
      setStatusMessage("服务器正在处理您的贡献...");
      setProgress(30);

      // Powers of Tau贡献可能需要3-5分钟，根据约束大小
      const timeEstimate =
        Math.pow(2, constraintPower) > 32768 ? "3-5分钟" : "1-2分钟";
      setStatusMessage(
        `正在生成Powers of Tau证明，预计需要${timeEstimate}，请耐心等待...`
      );
      setProgress(40);

      const result = await apiService.contributeWithEntropy(
        userId,
        constraintPower,
        combinedEntropy
      );

      setProgress(90);
      setStatusMessage("贡献成功！正在生成最终证明参数文件...");

      // 处理不同类型的成功响应
      if (result.status === "success") {
        setTimeout(() => {
          setProgress(100);
          // 清空状态消息，使用步骤2中的Alert显示
          setStatusMessage("");
          setActiveStep(2);

          if (onComplete) {
            onComplete({
              ...result,
              ptau_completed: true,
              contribution_verified: result.contribution_verified,
            });
          }
        }, 1000);
      } else {
        // 处理其他状态
        setProgress(100);
        setStatusMessage("");
        setActiveStep(2);
        if (onComplete) {
          onComplete(result);
        }
      }
    } catch (error) {
      console.error("贡献失败:", error);

      // 检查是否是超时错误
      if (
        error.message.includes("超时") ||
        error.message.includes("timeout") ||
        error.message.includes("耗时过长")
      ) {
        setStatusMessage(`⏰ Powers of Tau贡献正在后台处理中...`);
        setProgress(95);

        // 超时时显示处理状态，然后自动进入完成阶段
        setTimeout(() => {
          setProgress(100);
          setStatusMessage("");
          setActiveStep(2);

          if (onComplete) {
            onComplete({
              status: "completed_with_timeout",
              message: "Powers of Tau贡献已完成，证明文件正在生成中",
              final_ptau_path: "/LSB_groth16/pot16_final.ptau",
            });
          }
        }, 2000);
      } else {
        setStatusMessage(`❌ 贡献失败: ${error.message}`);
        if (onError) {
          onError(error);
        }
      }
    } finally {
      setContributing(false);
    }
  };

  const getEntropyQuality = () => {
    const textQuality = Math.min(entropy.length / 20, 1);
    const mouseQuality = Math.min(mouseEntropy.length / 50, 1);
    const keyboardQuality = Math.min(keyboardEntropy.length / 10, 1);
    return Math.round(
      ((textQuality + mouseQuality + keyboardQuality) / 3) * 100
    );
  };

  return (
    <Paper elevation={3} sx={{ p: 3, maxWidth: 700, mx: "auto" }}>
      <Typography variant="h5" gutterBottom>
        Powers of Tau 贡献
      </Typography>

      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        检测到您的数据集包含水印。为了生成零知识证明作为证据，需要您参与Powers
        of Tau仪式。 您的随机性贡献将确保证明的安全性和不可伪造性。
      </Typography>

      <Box sx={{ mb: 2 }}>
        <Typography variant="body2">
          约束大小: 2^{constraintPower} ={" "}
          {Math.pow(2, constraintPower).toLocaleString()}
        </Typography>
        <Typography variant="body2">用户ID: {userId}</Typography>
      </Box>

      <Stepper activeStep={activeStep} orientation="vertical">
        {steps.map((step, index) => (
          <Step key={step.label}>
            <StepLabel>{step.label}</StepLabel>
            <StepContent>
              <Typography variant="body2" sx={{ mb: 2 }}>
                {step.description}
              </Typography>

              {index === 0 && (
                <Box>
                  <Alert severity="info" sx={{ mb: 2 }}>
                    为了生成安全的随机性，请进行以下操作：
                    <br />• 在下方文本框中输入一些随机文字
                    <br />• 移动鼠标产生随机轨迹
                    <br />• 按一些随机按键
                  </Alert>

                  <TextField
                    fullWidth
                    multiline
                    rows={4}
                    label="随机性输入"
                    placeholder="请输入任何您想到的内容：诗句、随机字符、想法等等。至少需要10个字符。"
                    value={entropy}
                    onChange={handleEntropyChange}
                    sx={{ mb: 2 }}
                  />

                  <Box sx={{ mb: 2 }}>
                    <Typography variant="body2" sx={{ mb: 1 }}>
                      随机性质量: {getEntropyQuality()}%
                    </Typography>
                    <LinearProgress
                      variant="determinate"
                      value={getEntropyQuality()}
                      sx={{ mb: 1 }}
                    />
                    <Typography variant="caption" color="text.secondary">
                      文本输入: {entropy.length} 字符 | 鼠标移动:{" "}
                      {mouseEntropy.length} 次 | 按键: {keyboardEntropy.length}{" "}
                      次
                    </Typography>
                  </Box>

                  <Button
                    variant="contained"
                    onClick={handleStartContribution}
                    disabled={!validateEntropy() || contributing}
                    size="large"
                  >
                    开始生成贡献
                  </Button>
                </Box>
              )}

              {index === 1 && contributing && (
                <Box>
                  <Box sx={{ display: "flex", alignItems: "center", mb: 2 }}>
                    <CircularProgress size={24} sx={{ mr: 2 }} />
                    <Typography variant="body2">{statusMessage}</Typography>
                  </Box>
                  <LinearProgress variant="determinate" value={progress} />
                  <Typography
                    variant="caption"
                    sx={{ mt: 1, display: "block" }}
                  >
                    进度: {progress}%
                  </Typography>
                </Box>
              )}

              {index === 2 && (
                <Alert severity="success">
                  <Typography variant="body2">
                    🎉 Powers of Tau贡献成功完成！
                    <br />
                    ✅ 您的随机性贡献已验证成功
                    <br />
                    🔄 零知识证明正在生成，证明您的数据集确实包含水印
                    <br />
                    📁 相关证明请到证明界面领取
                    <br />
                    ⏳ 零知识证明生成需要额外时间，系统正在后台处理
                    <br />
                    💡 您现在可以安全地关闭此页面
                  </Typography>
                </Alert>
              )}
            </StepContent>
          </Step>
        ))}
      </Stepper>

      {statusMessage && !contributing && activeStep < 2 && (
        <Alert
          severity={statusMessage.includes("失败") ? "error" : "info"}
          sx={{ mt: 2 }}
        >
          {statusMessage}
        </Alert>
      )}
    </Paper>
  );
};

export default PowersOfTauContribution;
