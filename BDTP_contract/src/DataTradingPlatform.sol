// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;

import "@openzeppelin/contracts/token/ERC721/IERC721.sol";

contract DataTradingPlatform {

    // 数据登记合约地址
    address public dataRegistrationContract;

    address public admin;
    // 代理人的地址（AI代理或平台）
    address public agent;

    modifier onlyAdmin() {
        require(msg.sender == admin, "Only admin can call this function");
        _;
    }

    modifier onlyAgent() {
        require(msg.sender == agent, "Only agent can call this function");
        _;
    }

    modifier onlyDataOwner(uint256 tokenId) {
        address dataOwner = IERC721(dataRegistrationContract).ownerOf(tokenId);
        require(msg.sender == dataOwner, "Only the data owner can perform this action");
        _;
    }

    // 记录tokenId => 购买者 => 购买者公钥加密后的cid_1'
    mapping(uint256 => mapping(address => string)) public tokenIdToEncryptedCid;

    // NFT上架状态
    enum ListingStatus { NotListed, Listed, Unlisted }
    mapping(uint256 => ListingStatus) public tokenIdToStatus;
    // 记录tokenId对应的价格
    mapping(uint256 => uint256) public tokenIdToPrice;

    // 事件：上架、下架、购买
    event NFTListed(address indexed agent, uint256 indexed tokenId, uint256 price);
    event NFTUnlisted(address indexed agent, uint256 indexed tokenId);
    event NFTPurchased(address indexed buyer, uint256 indexed tokenId, address indexed dataOwner, uint256 amount, string encryptedCid);

    constructor(address _dataRegistrationContract) {
        dataRegistrationContract = _dataRegistrationContract;
        admin = msg.sender;
    }

    // 设置代理人的地址
    function setAgent(address _agent) external onlyAdmin(){
        agent = _agent;
    }

    // 1. 上架 NFT
    function listNFT(uint256 tokenId, uint256 price) external onlyAgent{
        require(tokenIdToStatus[tokenId] == ListingStatus.NotListed, "NFT is already listed");

        tokenIdToStatus[tokenId] = ListingStatus.Listed;
        tokenIdToPrice[tokenId] = price;
        
        emit NFTListed(msg.sender, tokenId, price);
    }

    // 2. 下架 NFT
    function unlistNFT(uint256 tokenId) external onlyAgent {
        require(tokenIdToStatus[tokenId] == ListingStatus.Listed, "NFT is not listed");

        tokenIdToStatus[tokenId] = ListingStatus.Unlisted;
        
        emit NFTUnlisted(msg.sender, tokenId);
    }

    // 3. 购买 NFT
    // agent 会处理链下的水印嵌入和加密逻辑，返回加密后的cid_1'
    function purchaseNFT(uint256 tokenId, address buyer, string calldata encryptedCid) external payable onlyAgent() {
        require(tokenIdToStatus[tokenId] == ListingStatus.Listed, "NFT is not listed for sale");
        require(msg.value == tokenIdToPrice[tokenId], "Incorrect payment amount");
        address dataOwner = IERC721(dataRegistrationContract).ownerOf(tokenId);
        // 资金转移：agent将资金转给数据拥有者
        (bool success, ) = payable(dataOwner).call{value: msg.value}("");
        require(success, "Payment to data owner failed");

        // 保存加密后的 cid_1'
        tokenIdToEncryptedCid[tokenId][buyer] = encryptedCid;

        emit NFTPurchased(msg.sender, tokenId, dataOwner, msg.value, encryptedCid);
    }

    // 获取NFT的当前状态
    function getNFTStatus(uint256 tokenId) external view returns (ListingStatus) {
        return tokenIdToStatus[tokenId];
    }

    // 获取加密后的cid_1'
    function getEncryptedCid(uint256 tokenId) external view returns (string memory) {
        return tokenIdToEncryptedCid[tokenId][msg.sender];
    }

    // 获取NFT的价格
    function getPrice(uint256 tokenId) external view returns (uint256) {
        return tokenIdToPrice[tokenId];
    }
}
