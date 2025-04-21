import React, { useState, useRef } from "react";
import styled from "styled-components";
import { useWeb3 } from "../utils/web3";
import apiService from "../utils/apiService";
import axios from "axios";

const PageContainer = styled.div`
  display: flex;
  flex-direction: column;
  gap: 2rem;
`;

const PageHeader = styled.div`
  margin-bottom: 1rem;
`;

const Title = styled.h1`
  color: #1f2937;
  margin-bottom: 0.5rem;
`;

const Subtitle = styled.p`
  color: #6b7280;
  margin: 0;
`;

const Card = styled.div`
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  padding: 2rem;
`;

const Form = styled.form`
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
`;

const FormGroup = styled.div`
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
`;

const Label = styled.label`
  font-weight: 500;
  color: #1f2937;
`;

const Input = styled.input`
  padding: 0.75rem;
  border: 1px solid #e5e7eb;
  border-radius: 5px;
  font-size: 1rem;

  &:focus {
    outline: none;
    border-color: #4f46e5;
  }
`;

const Textarea = styled.textarea`
  padding: 0.75rem;
  border: 1px solid #e5e7eb;
  border-radius: 5px;
  font-size: 1rem;
  min-height: 100px;
  resize: vertical;

  &:focus {
    outline: none;
    border-color: #4f46e5;
  }
`;

const FileInputContainer = styled.div`
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
`;

const FileInputLabel = styled.label`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border: 2px dashed #e5e7eb;
  border-radius: 5px;
  padding: 2rem;
  cursor: pointer;
  transition: border-color 0.3s ease;

  &:hover {
    border-color: #4f46e5;
  }
`;

const FileInput = styled.input`
  position: absolute;
  top: 0;
  left: 0;
  opacity: 0;
  width: 0;
  height: 0;
`;

const FilePreview = styled.div`
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  background-color: #f9fafb;
  border-radius: 5px;
`;

const FileIcon = styled.div`
  font-size: 1.5rem;
  color: #4f46e5;
`;

const FileDetails = styled.div`
  flex: 1;
`;

const FileName = styled.div`
  font-weight: 500;
  color: #1f2937;
`;

const FileSize = styled.div`
  font-size: 0.875rem;
  color: #6b7280;
`;

const RemoveButton = styled.button`
  background: none;
  border: none;
  color: #ef4444;
  cursor: pointer;
  font-size: 1.25rem;

  &:hover {
    color: #dc2626;
  }
`;

const SubmitButton = styled.button`
  background-color: #4f46e5;
  color: white;
  border: none;
  border-radius: 5px;
  padding: 0.75rem;
  font-size: 1rem;
  cursor: pointer;
  transition: background-color 0.3s ease;

  &:hover {
    background-color: #4338ca;
  }

  &:disabled {
    background-color: #9ca3af;
    cursor: not-allowed;
  }
`;

const StepContainer = styled.div`
  display: flex;
  justify-content: space-between;
  margin-bottom: 2rem;
`;

const Step = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 33%;
`;

const StepNumber = styled.div`
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background-color: ${(props) => (props.active ? "#4f46e5" : "#e5e7eb")};
  color: ${(props) => (props.active ? "white" : "#6b7280")};
  display: flex;
  justify-content: center;
  align-items: center;
  font-weight: bold;
  margin-bottom: 0.5rem;
`;

const StepTitle = styled.div`
  font-weight: ${(props) => (props.active ? "bold" : "normal")};
  color: ${(props) => (props.active ? "#1f2937" : "#6b7280")};
`;

const StepLine = styled.div`
  flex: 1;
  height: 2px;
  background-color: #e5e7eb;
  margin: 15px 10px 0 10px;
`;

const ResultCard = styled.div`
  background-color: #f3f4f6;
  border-radius: 8px;
  padding: 1.5rem;
  margin-top: 1rem;
`;

const ResultItem = styled.div`
  margin-bottom: 1rem;
`;

const ResultLabel = styled.div`
  font-weight: 500;
  color: #1f2937;
  margin-bottom: 0.25rem;
`;

const ResultValue = styled.div`
  color: #4f46e5;
  font-family: monospace;
  word-break: break-all;
`;

const formatFileSize = (bytes) => {
  if (bytes === 0) return "0 Bytes";
  const k = 1024;
  const sizes = ["Bytes", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
};

const UploadPage = () => {
  const { isConnected, account, connectWallet } = useWeb3();
  const [step, setStep] = useState(1);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [datasetFile, setDatasetFile] = useState(null);
  const [imageFile, setImageFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);
  const [registering, setRegistering] = useState(false);
  const [registerResult, setRegisterResult] = useState(null);

  const datasetInputRef = useRef(null);
  const imageInputRef = useRef(null);

  const handleDatasetChange = (e) => {
    if (e.target.files[0]) {
      setDatasetFile(e.target.files[0]);
    }
  };

  const handleImageChange = (e) => {
    if (e.target.files[0]) {
      setImageFile(e.target.files[0]);
    }
  };

  const handleRemoveDataset = () => {
    setDatasetFile(null);
    if (datasetInputRef.current) {
      datasetInputRef.current.value = "";
    }
  };

  const handleRemoveImage = () => {
    setImageFile(null);
    if (imageInputRef.current) {
      imageInputRef.current.value = "";
    }
  };

  const handleNextStep = () => {
    if (step === 1) {
      if (!datasetFile || !imageFile || !title.trim() || !description.trim()) {
        alert("请填写所有字段并上传所需文件");
        return;
      }
      setStep(2);
    } else if (step === 2) {
      handleUpload();
    }
  };

  const handlePrevStep = () => {
    if (step > 1) {
      setStep(step - 1);
    }
  };

  const handleUpload = async () => {
    if (!isConnected) {
      const connected = await connectWallet();
      if (!connected) {
        alert("请先连接钱包");
        return;
      }
    }

    setUploading(true);

    try {
      // 1. 上传数据集到IPFS
      console.log("开始上传数据集...");
      const datasetFormData = new FormData();
      datasetFormData.append("file", datasetFile);
      const datasetResponse = await axios.post(
        "http://localhost:8765/api/upload-to-ipfs",
        datasetFormData
      );
      console.log("数据集上传成功:", datasetResponse.data);
      const datasetCid = datasetResponse.data.cid;

      // 2. 上传图片到IPFS
      console.log("开始上传图片...");
      const imageFormData = new FormData();
      imageFormData.append("file", imageFile);
      const imageResponse = await axios.post(
        "http://localhost:8765/api/upload-to-ipfs",
        imageFormData
      );
      console.log("图片上传成功:", imageResponse.data);
      const imageCid = imageResponse.data.cid;

      // 3. 创建加密的元数据，包括用平台公钥加密的数据集CID
      console.log("创建加密的元数据...");
      const metadataResponse = await axios.post(
        "http://localhost:8765/api/create-encrypted-metadata",
        {
          dataset_cid: datasetCid,
          image_cid: imageCid,
          title,
          description,
        }
      );
      console.log("元数据创建成功:", metadataResponse.data);

      // 4. 更新上传结果
      setUploadResult({
        datasetCid,
        imageCid,
        metadataCid: metadataResponse.data.metadata_cid,
        metadataUrl: metadataResponse.data.metadata_url,
      });

      setStep(3);
    } catch (error) {
      console.error("上传文件失败:", error);
      if (error.response) {
        console.error("错误响应:", error.response.data);
      }
      alert(`上传失败: ${error.message || "未知错误"}`);
    } finally {
      setUploading(false);
    }
  };

  const handleRegister = async () => {
    if (!uploadResult || !uploadResult.metadataUrl) {
      alert("请先完成上传");
      return;
    }

    if (!isConnected) {
      const connected = await connectWallet();
      if (!connected) {
        alert("请先连接钱包");
        return;
      }
    }

    setRegistering(true);

    try {
      const result = await apiService.registerData(
        uploadResult.metadataUrl,
        account
      );
      setRegisterResult(result);
    } catch (error) {
      console.error("数据集登记失败:", error);
      alert(`登记失败: ${error.message || "未知错误"}`);
    } finally {
      setRegistering(false);
    }
  };

  const renderStepOne = () => (
    <Form>
      <FormGroup>
        <Label htmlFor="title">标题</Label>
        <Input
          id="title"
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="数据集标题"
          required
        />
      </FormGroup>

      <FormGroup>
        <Label htmlFor="description">描述</Label>
        <Textarea
          id="description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="详细描述您的数据集..."
          required
        />
      </FormGroup>

      <FormGroup>
        <Label>数据集文件 (ZIP)</Label>
        <FileInputContainer>
          {!datasetFile ? (
            <FileInputLabel htmlFor="dataset">
              <div>点击或拖放上传数据集 (ZIP格式)</div>
            </FileInputLabel>
          ) : (
            <FilePreview>
              <FileIcon>📁</FileIcon>
              <FileDetails>
                <FileName>{datasetFile.name}</FileName>
                <FileSize>{formatFileSize(datasetFile.size)}</FileSize>
              </FileDetails>
              <RemoveButton onClick={handleRemoveDataset}>×</RemoveButton>
            </FilePreview>
          )}
          <FileInput
            id="dataset"
            type="file"
            accept=".zip"
            onChange={handleDatasetChange}
            ref={datasetInputRef}
            required
          />
        </FileInputContainer>
      </FormGroup>

      <FormGroup>
        <Label>预览图片</Label>
        <FileInputContainer>
          {!imageFile ? (
            <FileInputLabel htmlFor="image">
              <div>点击或拖放上传预览图片</div>
            </FileInputLabel>
          ) : (
            <FilePreview>
              <FileIcon>🖼️</FileIcon>
              <FileDetails>
                <FileName>{imageFile.name}</FileName>
                <FileSize>{formatFileSize(imageFile.size)}</FileSize>
              </FileDetails>
              <RemoveButton onClick={handleRemoveImage}>×</RemoveButton>
            </FilePreview>
          )}
          <FileInput
            id="image"
            type="file"
            accept="image/*"
            onChange={handleImageChange}
            ref={imageInputRef}
            required
          />
        </FileInputContainer>
      </FormGroup>

      <SubmitButton type="button" onClick={handleNextStep}>
        下一步
      </SubmitButton>
    </Form>
  );

  const renderStepTwo = () => (
    <div>
      <h2>确认信息</h2>

      <div className="card">
        <h3>数据集信息</h3>
        <p>
          <strong>标题：</strong> {title}
        </p>
        <p>
          <strong>描述：</strong> {description}
        </p>
        <p>
          <strong>数据集文件：</strong> {datasetFile?.name} (
          {formatFileSize(datasetFile?.size)})
        </p>
        <p>
          <strong>预览图片：</strong> {imageFile?.name} (
          {formatFileSize(imageFile?.size)})
        </p>
      </div>

      <div style={{ display: "flex", gap: "1rem", marginTop: "1.5rem" }}>
        <SubmitButton
          type="button"
          onClick={handlePrevStep}
          style={{ backgroundColor: "#6b7280" }}
        >
          上一步
        </SubmitButton>
        <SubmitButton
          type="button"
          onClick={handleNextStep}
          disabled={uploading}
        >
          {uploading ? "上传中..." : "上传到IPFS"}
        </SubmitButton>
      </div>
    </div>
  );

  const renderStepThree = () => (
    <div>
      <h2>上传结果</h2>

      {uploadResult && (
        <ResultCard>
          <ResultItem>
            <ResultLabel>数据集CID</ResultLabel>
            <ResultValue>{uploadResult.datasetCid}</ResultValue>
          </ResultItem>
          <ResultItem>
            <ResultLabel>图片CID</ResultLabel>
            <ResultValue>{uploadResult.imageCid}</ResultValue>
          </ResultItem>
          <ResultItem>
            <ResultLabel>元数据CID</ResultLabel>
            <ResultValue>{uploadResult.metadataCid}</ResultValue>
          </ResultItem>
          <ResultItem>
            <ResultLabel>元数据URL</ResultLabel>
            <ResultValue>{uploadResult.metadataUrl}</ResultValue>
          </ResultItem>
        </ResultCard>
      )}

      {registerResult ? (
        <div style={{ marginTop: "1.5rem" }}>
          <h3>登记结果</h3>
          <ResultCard>
            <ResultItem>
              <ResultLabel>状态</ResultLabel>
              <ResultValue>{registerResult.status}</ResultValue>
            </ResultItem>
            <ResultItem>
              <ResultLabel>消息</ResultLabel>
              <ResultValue>{registerResult.message}</ResultValue>
            </ResultItem>
            {registerResult.output && (
              <ResultItem>
                <ResultLabel>详细输出</ResultLabel>
                <ResultValue style={{ whiteSpace: "pre-wrap" }}>
                  {registerResult.output}
                </ResultValue>
              </ResultItem>
            )}
          </ResultCard>
        </div>
      ) : (
        <SubmitButton
          type="button"
          onClick={handleRegister}
          disabled={registering}
          style={{ marginTop: "1.5rem" }}
        >
          {registering ? "登记中..." : "登记数据集"}
        </SubmitButton>
      )}
    </div>
  );

  return (
    <PageContainer>
      <PageHeader>
        <Title>上传数据集</Title>
        <Subtitle>将您的数据集上传到IPFS并铸造成NFT</Subtitle>
      </PageHeader>

      <StepContainer>
        <Step>
          <StepNumber active={step >= 1}>1</StepNumber>
          <StepTitle active={step >= 1}>填写信息</StepTitle>
        </Step>
        <StepLine />
        <Step>
          <StepNumber active={step >= 2}>2</StepNumber>
          <StepTitle active={step >= 2}>上传到IPFS</StepTitle>
        </Step>
        <StepLine />
        <Step>
          <StepNumber active={step >= 3}>3</StepNumber>
          <StepTitle active={step >= 3}>登记NFT</StepTitle>
        </Step>
      </StepContainer>

      <Card>
        {step === 1 && renderStepOne()}
        {step === 2 && renderStepTwo()}
        {step === 3 && renderStepThree()}
      </Card>
    </PageContainer>
  );
};

export default UploadPage;
