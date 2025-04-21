import React from "react";
import styled from "styled-components";

const Card = styled.div`
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  transition: transform 0.3s ease;

  &:hover {
    transform: translateY(-5px);
  }
`;

const CardImage = styled.div`
  width: 100%;
  height: 200px;
  background-image: url(${(props) =>
    props.src || "https://via.placeholder.com/300x200?text=No+Image"});
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
`;

const CardContent = styled.div`
  padding: 1rem;
`;

const CardTitle = styled.h3`
  margin: 0 0 0.5rem 0;
  font-size: 1.2rem;
  color: #1f2937;
`;

const CardDescription = styled.p`
  margin: 0 0 1rem 0;
  color: #6b7280;
  font-size: 0.9rem;
  height: 40px;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
`;

const CardFooter = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-top: 1px solid #e5e7eb;
  padding-top: 1rem;
`;

const Price = styled.div`
  font-weight: bold;
  color: #4f46e5;
`;

const NFTId = styled.div`
  font-size: 0.8rem;
  color: #6b7280;
  margin-bottom: 0.5rem;
`;

const BuyButton = styled.button`
  background-color: #4f46e5;
  color: white;
  border: none;
  border-radius: 5px;
  padding: 0.5rem 1rem;
  cursor: pointer;
  transition: background-color 0.3s ease;

  &:hover {
    background-color: #4338ca;
  }
`;

const NFTCard = ({ nft, onBuy }) => {
  // 确保图片URL有效
  const getValidImageUrl = (imageUrl) => {
    if (!imageUrl) return "https://via.placeholder.com/300x200?text=No+Image";

    // 如果已经是完整URL，直接返回
    if (imageUrl.startsWith("http://") || imageUrl.startsWith("https://")) {
      return imageUrl;
    }

    // 如果是IPFS格式的URL (ipfs://)
    if (imageUrl.startsWith("ipfs://")) {
      return imageUrl.replace("ipfs://", "http://127.0.0.1:8080/ipfs/");
    }

    // 如果只是CID，构建IPFS URL使用本地网关
    return `http://127.0.0.1:8080/ipfs/${imageUrl}`;
  };

  return (
    <Card>
      <CardImage src={getValidImageUrl(nft.image)} />
      <CardContent>
        <NFTId>Token ID: {nft.id}</NFTId>
        <CardTitle>{nft.title || `数据集 #${nft.id}`}</CardTitle>
        <CardDescription>{nft.description || "无描述"}</CardDescription>
        <CardFooter>
          <Price>{nft.price} ETH</Price>
          <BuyButton onClick={() => onBuy(nft)}>购买</BuyButton>
        </CardFooter>
      </CardContent>
    </Card>
  );
};

export default NFTCard;
