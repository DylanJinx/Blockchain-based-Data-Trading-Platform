import React, { useState } from "react";
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
} from "@mui/material";
// import * as snarkjs from "snarkjs";

const PowersOfTauContribution = ({
  userId,
  constraintPower,
  onComplete,
  onError,
}) => {
  const [activeStep, setActiveStep] = useState(0);
  const [contributing, setContributing] = useState(false);
  const [entropy, setEntropy] = useState("");
  const [progress, setProgress] = useState(0);
  const [statusMessage, setStatusMessage] = useState("");

  const steps = [
    {
      label: "下载初始文件",
      description: "从服务器下载初始Powers of Tau文件",
    },
    {
      label: "输入随机性",
      description: "请输入一些随机字符作为您的贡献",
    },
    {
      label: "生成贡献",
      description: "在浏览器中生成您的Powers of Tau贡献",
    },
    {
      label: "上传贡献",
      description: "将您的贡献上传到服务器",
    },
  ];

  const handleDownloadInitialPtau = async () => {
    try {
      setStatusMessage("正在下载初始Powers of Tau文件...");

      const response = await fetch(`/api/get-initial-ptau/${userId}`);
      if (!response.ok) {
        throw new Error(`下载失败: ${response.statusText}`);
      }

      const blob = await response.blob();
      const file = new File([blob], `pot${constraintPower}_0000.ptau`, {
        type: "application/octet-stream",
      });

      // 存储文件到组件状态（简化处理）
      window.initialPtauFile = file;

      setStatusMessage("初始文件下载完成");
      setActiveStep(1);
    } catch (error) {
      console.error("下载初始ptau文件失败:", error);
      onError(error);
    }
  };

  const validateEntropy = (value) => {
    return value.length >= 10; // 至少10个字符
  };

  const handleEntropyChange = (event) => {
    const value = event.target.value;
    setEntropy(value);
  };

  const handleProceedToContribution = () => {
    if (!validateEntropy(entropy)) {
      alert("请输入至少10个字符的随机文本");
      return;
    }
    setActiveStep(2);
    handleContribute();
  };

  const handleContribute = async () => {
    try {
      setContributing(true);
      setProgress(0);
      setStatusMessage("正在生成您的Powers of Tau贡献...");

      if (!window.initialPtauFile) {
        throw new Error("未找到初始ptau文件");
      }

      // 读取初始ptau文件
      const arrayBuffer = await window.initialPtauFile.arrayBuffer();
      const ptauData = new Uint8Array(arrayBuffer);

      setProgress(20);
      setStatusMessage("正在处理您的随机性输入...");

      // 暂时注释掉snarkjs调用，等解决编译问题后再启用
      setProgress(40);
      setStatusMessage("正在生成贡献，这可能需要一些时间...");

      // TODO: 重新启用snarkjs
      // const contributedPtau = await snarkjs.powersOfTau.contribute(
      //   ptauData,
      //   entropy,
      //   `User ${userId} browser contribution`
      // );

      // 临时模拟贡献数据
      const contributedPtau = ptauData; // 临时使用原始数据

      setProgress(80);
      setStatusMessage("贡献生成完成，正在上传...");
      setActiveStep(3);

      // 上传贡献
      await uploadContribution(contributedPtau);
    } catch (error) {
      console.error("生成贡献失败:", error);
      setStatusMessage(`贡献失败: ${error.message}`);
      onError(error);
    } finally {
      setContributing(false);
    }
  };

  const uploadContribution = async (contributedPtauData) => {
    try {
      setStatusMessage("正在上传您的贡献...");

      const formData = new FormData();
      const contributedFile = new Blob([contributedPtauData], {
        type: "application/octet-stream",
      });

      formData.append(
        "ptau_file",
        contributedFile,
        `pot${constraintPower}_0001.ptau`
      );
      formData.append("constraint_power", constraintPower.toString());

      const response = await fetch(`/api/upload-contribution/${userId}`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`上传失败: ${response.statusText}`);
      }

      const result = await response.json();

      setProgress(100);
      setStatusMessage("Powers of Tau贡献完成！");

      if (onComplete) {
        onComplete(result);
      }
    } catch (error) {
      console.error("上传贡献失败:", error);
      setStatusMessage(`上传失败: ${error.message}`);
      throw error;
    }
  };

  return (
    <Paper elevation={3} sx={{ p: 3, maxWidth: 600, mx: "auto" }}>
      <Typography variant="h5" gutterBottom>
        Powers of Tau 贡献
      </Typography>

      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        检测到您的数据集包含水印。为了生成零知识证明作为证据，需要您参与Powers
        of Tau仪式。 您的随机性贡献将确保证明的安全性和不可伪造性。
      </Typography>

      <Alert severity="warning" sx={{ mb: 2 }}>
        注意：当前版本暂时禁用了snarkjs库以解决编译问题。功能正在开发中。
      </Alert>

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
                <Button
                  variant="contained"
                  onClick={handleDownloadInitialPtau}
                  disabled={contributing}
                >
                  下载初始文件
                </Button>
              )}

              {index === 1 && (
                <Box>
                  <TextField
                    fullWidth
                    multiline
                    rows={3}
                    label="随机性输入"
                    placeholder="请输入一些随机字符、单词或句子。您可以按键盘上的随机键，或者输入任何您想到的内容。至少需要10个字符。"
                    value={entropy}
                    onChange={handleEntropyChange}
                    error={entropy.length > 0 && !validateEntropy(entropy)}
                    helperText={
                      entropy.length > 0 && !validateEntropy(entropy)
                        ? "至少需要10个字符"
                        : `当前长度: ${entropy.length}`
                    }
                    sx={{ mb: 2 }}
                  />
                  <Button
                    variant="contained"
                    onClick={handleProceedToContribution}
                    disabled={!validateEntropy(entropy) || contributing}
                  >
                    开始生成贡献
                  </Button>
                </Box>
              )}

              {index === 2 && contributing && (
                <Box>
                  <CircularProgress sx={{ mr: 2 }} />
                  <Typography variant="body2" component="span">
                    {statusMessage}
                  </Typography>
                  {progress > 0 && (
                    <Typography variant="body2" sx={{ mt: 1 }}>
                      进度: {progress}%
                    </Typography>
                  )}
                </Box>
              )}

              {index === 3 && (
                <Typography variant="body2" color="success.main">
                  {statusMessage}
                </Typography>
              )}
            </StepContent>
          </Step>
        ))}
      </Stepper>

      {statusMessage && !contributing && activeStep < 3 && (
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
