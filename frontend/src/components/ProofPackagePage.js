import React, { useState, useEffect } from "react";
import { useWeb3 } from "../utils/web3";
import styled from "styled-components";

const Container = styled.div`
  max-width: 1000px;
  margin: 0 auto;
  padding: 2rem;
`;

const Title = styled.h1`
  color: #1f2937;
  margin-bottom: 1rem;
  text-align: center;
`;

const StatusCard = styled.div`
  background-color: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 1.5rem;
  margin-bottom: 2rem;
`;

const StatusTitle = styled.h2`
  color: #374151;
  font-size: 1.25rem;
  margin-bottom: 1rem;
`;

const StatusBadge = styled.span`
  padding: 0.25rem 0.75rem;
  border-radius: 9999px;
  font-size: 0.875rem;
  font-weight: 500;
  color: white;
  background-color: ${(props) => {
    switch (props.status) {
      case "证明生成完成":
        return "#10b981";
      case "等待Powers of Tau贡献":
        return "#f59e0b";
      case "分块处理中":
        return "#6366f1";
      case "处理中":
        return "#8b5cf6";
      default:
        return "#6b7280";
    }
  }};
`;

const PackageGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 1.5rem;
  margin-top: 2rem;
`;

const PackageCard = styled.div`
  background-color: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  transition: box-shadow 0.3s ease;

  &:hover {
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  }
`;

const PackageTitle = styled.h3`
  color: #1f2937;
  font-size: 1.125rem;
  margin-bottom: 0.75rem;
`;

const PackageInfo = styled.div`
  color: #6b7280;
  font-size: 0.875rem;
  margin-bottom: 0.5rem;
`;

const DownloadButton = styled.button`
  background-color: #4f46e5;
  color: white;
  border: none;
  border-radius: 6px;
  padding: 0.75rem 1.5rem;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.3s ease;
  width: 100%;
  margin-top: 1rem;

  &:hover:not(:disabled) {
    background-color: #4338ca;
  }

  &:disabled {
    background-color: #9ca3af;
    cursor: not-allowed;
  }
`;

const RefreshButton = styled.button`
  background-color: #10b981;
  color: white;
  border: none;
  border-radius: 6px;
  padding: 0.5rem 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.3s ease;
  margin-bottom: 1rem;

  &:hover {
    background-color: #059669;
  }
`;

const EmptyState = styled.div`
  text-align: center;
  padding: 3rem;
  color: #6b7280;
`;

const LoadingSpinner = styled.div`
  border: 2px solid #f3f4f6;
  border-top: 2px solid #4f46e5;
  border-radius: 50%;
  width: 20px;
  height: 20px;
  animation: spin 1s linear infinite;
  margin: 0 auto;

  @keyframes spin {
    0% {
      transform: rotate(0deg);
    }
    100% {
      transform: rotate(360deg);
    }
  }
`;

const ErrorMessage = styled.div`
  background-color: #fef2f2;
  color: #dc2626;
  padding: 1rem;
  border-radius: 6px;
  margin-bottom: 1rem;
  border: 1px solid #fecaca;
`;

const ProofPackagePage = () => {
  const { account, isConnected } = useWeb3();
  const [proofStatus, setProofStatus] = useState(null);
  const [packages, setPackages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [downloading, setDownloading] = useState({});

  const API_BASE = "http://127.0.0.1:8765";

  const checkProofStatus = async () => {
    if (!account) return;

    setLoading(true);
    setError("");

    try {
      const response = await fetch(`${API_BASE}/api/check-proof-status`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          user_address: account,
        }),
      });

      const data = await response.json();

      if (data.status === "success") {
        setProofStatus(data);
      } else {
        setError(data.message || "查询证明状态失败");
      }
    } catch (err) {
      setError("网络错误：" + err.message);
    } finally {
      setLoading(false);
    }
  };

  const loadProofPackages = async () => {
    if (!account) return;

    try {
      const response = await fetch(`${API_BASE}/api/list-proof-packages`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          user_address: account,
        }),
      });

      const data = await response.json();

      if (data.status === "success") {
        setPackages(data.packages);
      } else {
        setError(data.message || "查询证明包失败");
      }
    } catch (err) {
      setError("网络错误：" + err.message);
    }
  };

  const downloadPackage = async (filename) => {
    setDownloading((prev) => ({ ...prev, [filename]: true }));

    try {
      const response = await fetch(
        `${API_BASE}/api/download-proof-package/${filename}`,
        {
          method: "GET",
        }
      );

      if (!response.ok) {
        throw new Error("下载失败");
      }

      // 创建下载链接
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.style.display = "none";
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      console.log(`证明包 ${filename} 下载成功`);
    } catch (err) {
      setError("下载失败：" + err.message);
    } finally {
      setDownloading((prev) => ({ ...prev, [filename]: false }));
    }
  };

  const refreshData = async () => {
    await Promise.all([checkProofStatus(), loadProofPackages()]);
  };

  useEffect(() => {
    if (isConnected && account) {
      refreshData();
    }
  }, [isConnected, account]);

  if (!isConnected) {
    return (
      <Container>
        <Title>零知识证明包</Title>
        <EmptyState>
          <p>请先连接钱包以查看您的证明包</p>
        </EmptyState>
      </Container>
    );
  }

  return (
    <Container>
      <Title>零知识证明包下载</Title>

      <RefreshButton onClick={refreshData} disabled={loading}>
        {loading ? "刷新中..." : "刷新状态"}
      </RefreshButton>

      {error && <ErrorMessage>{error}</ErrorMessage>}

      {/* 证明状态卡片 */}
      {proofStatus && (
        <StatusCard>
          <StatusTitle>证明状态</StatusTitle>
          <div style={{ marginBottom: "0.75rem" }}>
            <StatusBadge status={proofStatus.proof_status}>
              {proofStatus.proof_status}
            </StatusBadge>
          </div>
          <p style={{ color: "#6b7280", marginBottom: "0.5rem" }}>
            {proofStatus.status_detail}
          </p>
          <PackageInfo>
            <strong>用户ID:</strong> {proofStatus.user_id}
          </PackageInfo>
          <PackageInfo>
            <strong>可用证明包:</strong> {proofStatus.package_count} 个
          </PackageInfo>
        </StatusCard>
      )}

      {/* 证明包列表 */}
      {packages.length > 0 ? (
        <div>
          <h2 style={{ color: "#374151", marginBottom: "1rem" }}>
            可下载的证明包 ({packages.length})
          </h2>
          <PackageGrid>
            {packages.map((pkg, index) => (
              <PackageCard key={index}>
                <PackageTitle>证明包 #{index + 1}</PackageTitle>
                <PackageInfo>
                  <strong>生成时间:</strong> {pkg.creation_time}
                </PackageInfo>
                <PackageInfo>
                  <strong>文件大小:</strong> {pkg.size_mb} MB
                </PackageInfo>
                <PackageInfo>
                  <strong>证明文件数:</strong> {pkg.proof_files_count}
                </PackageInfo>
                <PackageInfo>
                  <strong>公开输入文件数:</strong> {pkg.public_files_count}
                </PackageInfo>
                <PackageInfo>
                  <strong>买家哈希:</strong> {pkg.buy_hash_short}
                </PackageInfo>
                <DownloadButton
                  onClick={() => downloadPackage(pkg.filename)}
                  disabled={downloading[pkg.filename]}
                >
                  {downloading[pkg.filename] ? (
                    <div
                      style={{
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        gap: "0.5rem",
                      }}
                    >
                      <LoadingSpinner />
                      下载中...
                    </div>
                  ) : (
                    "下载证明包"
                  )}
                </DownloadButton>
              </PackageCard>
            ))}
          </PackageGrid>
        </div>
      ) : (
        !loading && (
          <EmptyState>
            <h3>暂无可用的证明包</h3>
            <p>
              当您的数据集检测到水印并完成零知识证明生成后，证明包将出现在这里。
            </p>
            <p
              style={{
                marginTop: "1rem",
                fontSize: "0.875rem",
                color: "#9ca3af",
              }}
            >
              证明包包含验证您数据集确实包含水印的零知识证明文件。
            </p>
          </EmptyState>
        )
      )}

      {loading && !error && (
        <div style={{ textAlign: "center", padding: "2rem" }}>
          <LoadingSpinner />
          <p style={{ marginTop: "1rem", color: "#6b7280" }}>正在加载...</p>
        </div>
      )}
    </Container>
  );
};

export default ProofPackagePage;
