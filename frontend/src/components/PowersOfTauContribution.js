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
      setProgress(20);

      const combinedEntropy = generateCombinedEntropy();

      setStatusMessage("正在发送数据到服务器...");
      setProgress(40);

      const response = await fetch("/api/contribute-with-entropy", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          user_id: userId,
          constraint_power: constraintPower,
          entropy: combinedEntropy,
        }),
      });

      setProgress(60);
      setStatusMessage("服务器正在处理您的贡献...");

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || "服务器处理失败");
      }

      const result = await response.json();

      setProgress(100);
      setStatusMessage("Powers of Tau贡献完成！");
      setActiveStep(2);

      if (onComplete) {
        onComplete(result);
      }
    } catch (error) {
      console.error("贡献失败:", error);
      setStatusMessage(`贡献失败: ${error.message}`);
      if (onError) {
        onError(error);
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
                    零知识证明已生成，证明您的数据集确实包含水印。
                    相关证明文件已保存在服务器端。
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
