import React, { useState, useEffect } from "react";
import styled from "styled-components";
import { useWeb3 } from "../utils/web3";
import apiService from "../utils/apiService";
import NFTCard from "./NFTCard";

const PageContainer = styled.div`
  padding: 0 1rem;
`;

const MarketGrid = styled.div`
  display: flex;
  flex-wrap: nowrap;
  gap: 1.5rem;
  margin-top: 2rem;
  padding-bottom: 1.5rem;
  overflow-x: auto;
  scrollbar-width: thin;

  /* 优化滚动条样式 */
  &::-webkit-scrollbar {
    height: 8px;
  }

  &::-webkit-scrollbar-track {
    background: #f1f1f1;
    border-radius: 4px;
  }

  &::-webkit-scrollbar-thumb {
    background: #888;
    border-radius: 4px;
  }

  &::-webkit-scrollbar-thumb:hover {
    background: #555;
  }
`;

// 设置固定宽度的卡片容器
const CardWrapper = styled.div`
  flex: 0 0 auto;
  width: 280px;
`;

const PageHeader = styled.div`
  margin-bottom: 2rem;
`;

const Title = styled.h1`
  color: #1f2937;
  margin-bottom: 0.5rem;
`;

const Subtitle = styled.p`
  color: #6b7280;
  margin: 0;
`;

const LoadingSpinner = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  height: 200px;
  font-size: 1.2rem;
  color: #6b7280;
`;

const NoData = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  height: 200px;
  font-size: 1.2rem;
  color: #6b7280;
`;

const Modal = styled.div`
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
`;

const ModalContent = styled.div`
  background-color: white;
  border-radius: 8px;
  padding: 2rem;
  width: 90%;
  max-width: 500px;
  max-height: 90vh;
  overflow-y: auto;
`;

const ModalHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
`;

const CloseButton = styled.button`
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #6b7280;

  &:hover {
    color: #1f2937;
  }
`;

const KeyTextarea = styled.textarea`
  width: 100%;
  min-height: 120px;
  padding: 0.5rem;
  margin-bottom: 1rem;
  font-family: monospace;
  border: 1px solid #e5e7eb;
  border-radius: 5px;
  resize: vertical;
`;

const SaveKeyButton = styled.button`
  background-color: #10b981;
  color: white;
  border: none;
  border-radius: 5px;
  padding: 0.5rem 1rem;
  cursor: pointer;
  margin-bottom: 1rem;

  &:hover {
    background-color: #059669;
  }
`;

const ConfirmButton = styled.button`
  background-color: #4f46e5;
  color: white;
  border: none;
  border-radius: 5px;
  padding: 0.5rem 1rem;
  width: 100%;
  cursor: pointer;
  font-size: 1rem;

  &:hover {
    background-color: #4338ca;
  }
`;

// 分类标签组件
const CategoryTabs = styled.div`
  display: flex;
  margin-top: 1rem;
  border-bottom: 1px solid #e5e7eb;
`;

const CategoryTab = styled.div`
  padding: 0.75rem 1.5rem;
  cursor: pointer;
  font-weight: ${(props) => (props.active ? "bold" : "normal")};
  color: ${(props) => (props.active ? "#4f46e5" : "#6b7280")};
  border-bottom: ${(props) => (props.active ? "2px solid #4f46e5" : "none")};

  &:hover {
    color: #4f46e5;
  }
`;

// 分类区域标题
const CategoryTitle = styled.h2`
  margin-top: 2.5rem;
  margin-bottom: 1rem;
  color: #1f2937;
  font-size: 1.5rem;
`;

const MarketPage = () => {
  const { isConnected, account, connectWallet, generateKeyPair } = useWeb3();
  const [nfts, setNfts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedNft, setSelectedNft] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [keyPair, setKeyPair] = useState(null);
  const [activeTab, setActiveTab] = useState("all");

  useEffect(() => {
    fetchNFTs();
  }, []);

  const fetchNFTs = async () => {
    try {
      setLoading(true);
      const listedNFTs = await apiService.getListedNFTs();
      setNfts(listedNFTs);
    } catch (error) {
      console.error("获取NFT列表失败:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleBuy = async (nft) => {
    if (!isConnected) {
      const connected = await connectWallet();
      if (!connected) return;
    }

    // 生成RSA密钥对
    const newKeyPair = await generateKeyPair();
    setKeyPair(newKeyPair);

    setSelectedNft(nft);
    setShowModal(true);
  };

  const handleConfirmBuy = async () => {
    if (!selectedNft || !keyPair) return;

    try {
      const result = await apiService.buyNFT(
        selectedNft.id,
        account,
        keyPair.publicKey
      );

      alert(`购买成功！您现在可以使用您的私钥解密访问数据。`);
      setShowModal(false);

      // 刷新NFT列表
      fetchNFTs();
    } catch (error) {
      console.error("购买NFT失败:", error);
      alert(`购买失败: ${error.message || "未知错误"}`);
    }
  };

  const handleSaveKey = () => {
    if (!keyPair) return;

    const blob = new Blob([keyPair.privateKey], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "private_key.pem";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  // 根据不同类别筛选NFT
  const getFilteredNFTs = () => {
    if (activeTab === "all") return nfts;

    return nfts;
  };

  return (
    <PageContainer>
      <PageHeader>
        <Title>数据集市场</Title>
        <Subtitle>浏览并购买高质量的数据集</Subtitle>
      </PageHeader>

      <CategoryTabs>
        <CategoryTab
          active={activeTab === "all"}
          onClick={() => setActiveTab("all")}
        >
          全部数据集
        </CategoryTab>
        <CategoryTab
          active={activeTab === "popular"}
          onClick={() => setActiveTab("popular")}
        >
          热门推荐
        </CategoryTab>
        <CategoryTab
          active={activeTab === "new"}
          onClick={() => setActiveTab("new")}
        >
          最新上架
        </CategoryTab>
      </CategoryTabs>

      {loading ? (
        <LoadingSpinner>加载中...</LoadingSpinner>
      ) : nfts.length === 0 ? (
        <NoData>暂无上架的数据集</NoData>
      ) : (
        <>
          <CategoryTitle>推荐数据集</CategoryTitle>
          <MarketGrid>
            {getFilteredNFTs().map((nft) => (
              <CardWrapper key={nft.id}>
                <NFTCard nft={nft} onBuy={handleBuy} />
              </CardWrapper>
            ))}
          </MarketGrid>
        </>
      )}

      {showModal && (
        <Modal>
          <ModalContent>
            <ModalHeader>
              <h2>购买数据集</h2>
              <CloseButton onClick={() => setShowModal(false)}>
                &times;
              </CloseButton>
            </ModalHeader>

            <p>
              <strong>数据集：</strong> {selectedNft.title}
            </p>
            <p>
              <strong>价格：</strong> {selectedNft.price} ETH
            </p>

            <h3>您的私钥</h3>
            <p>
              请务必保存此私钥，它用于解密您购买的数据。这是唯一一次显示，关闭后将无法再次获取！
            </p>

            <KeyTextarea value={keyPair?.privateKey || ""} readOnly />

            <SaveKeyButton onClick={handleSaveKey}>保存私钥</SaveKeyButton>

            <ConfirmButton onClick={handleConfirmBuy}>确认购买</ConfirmButton>
          </ModalContent>
        </Modal>
      )}
    </PageContainer>
  );
};

export default MarketPage;
