// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";

/**
 * @title DataRegistration
 * @notice 在本合约中，数据拥有者通过agent来上架数据（铸造NFT）。
 *         NFT不可转让，tokenURI中可存放加密的zip_cid等。
 */
contract DataRegistration is ERC721 {
    uint256 private _currentTokenId = 0;
    address public admin;
    address public agent;
    uint256 public listStakeAmount = 3 ether;

    // tokenId => tokenURI(如包含加密zip_cid等元数据)
    mapping(uint256 => string) private _tokenURIs;
    // tokenId => saleHash
    mapping(uint256 => bytes32) public tokenIdToSaleHash;
    // saleHash => tokenId
    mapping(bytes32 => uint256) public saleHashToTokenId;
    // saleHash => dataOwner
    mapping(bytes32 => address) public saleHashToDataOwner;
    // tokenId => timestamp
    mapping(uint256 => uint256) public tokenIdToTimestamp;

    // 质押合约地址
    address public escrowContract;

    constructor() ERC721("DataAssetNFT", "DAN") {
        admin = msg.sender;
    }

    event DataRegistered(
        address indexed dataOwner,
        uint256 indexed tokenId,
        string tokenURI,
        bytes32 saleHash
    );

    modifier onlyAdmin() {
        require(msg.sender == admin, "Only admin can call this function");
        _;
    }

    modifier onlyAgent() {
        require(msg.sender == agent, "Only agent can call this function");
        _;
    }

    /**
     * @dev 上架数据时，铸造NFT给_dataOwner（数据拥有者）
     * @param _tokenURI NFT元数据URI（可包含加密的zip_cid等）
     * @param _dataOwner 数据拥有者地址
     * 要求:
     *   1) 只能由agent调用
     *   2) msg.value == listStakeAmount
     *   3) 调用质押合约的listDeposit(...)
     */
    function registerData(
        string calldata _tokenURI,
        address _dataOwner
    ) onlyAgent external payable returns (uint256) {
        // (1) 先去给质押合约打保证金
        require(msg.value == listStakeAmount, "List stake amount mismatch");

        _currentTokenId++;
        uint256 newTokenId = _currentTokenId;
        // 调用质押合约：listDeposit(dataOwner, newTokenId, msg.value)
        (bool success, ) = escrowContract.call{value: msg.value}(
            abi.encodeWithSignature("listDeposit(address,uint256,uint256)", _dataOwner, newTokenId, msg.value)
        );
        require(success, "Escrow list deposit failed");

        // (2) 铸造NFT给 dataOwner
        
        _safeMint(_dataOwner, newTokenId);
        _tokenURIs[newTokenId] = _tokenURI;
        bytes32 _saleHash = computeSaleHash(_dataOwner, _tokenURI, block.timestamp);

        // 记录tokenId => saleHash
        tokenIdToSaleHash[newTokenId] = _saleHash;
        // 记录saleHash => tokenId
        saleHashToTokenId[_saleHash] = newTokenId;
        // 记录tokenId => dataOwner
        saleHashToDataOwner[_saleHash] = _dataOwner;
        // 记录tokenId => timestamp
        tokenIdToTimestamp[newTokenId] = block.timestamp;

        // (3) 记录事件
        emit DataRegistered(_dataOwner, newTokenId, _tokenURI, _saleHash);

        return newTokenId;
    }

    /**
     * @dev 计算saleHash, 用于标识某份数据 (H(dataOwner, cid, timestamp))
     */
    function computeSaleHash(address _dataOwner, string memory _cid, uint256 _timestamp) public pure returns (bytes32) {
        return keccak256(abi.encodePacked(_dataOwner, _cid, _timestamp));
    }

    /**
     * @notice 仅admin可设置agent地址。agent可以代表用户调用registerData
     */
    function setAgent(address _agent) onlyAdmin() external {
        agent = _agent;
    }

    /**
     * @notice 仅admin可设置质押合约地址
     */
    function setEscrowContract(address _escrowContract) onlyAdmin() external {
        escrowContract = _escrowContract;
    }

    // 重写tokenURI函数
    function tokenURI(uint256 tokenId) public view override returns (string memory) {
        return _tokenURIs[tokenId];
    }

    function getTokenIdToTimestamp(uint256 tokenId) public view returns (uint256) {
        return tokenIdToTimestamp[tokenId];
    }

    function getTokenIdToSaleHash(uint256 tokenId) public view returns (bytes32) {
        return tokenIdToSaleHash[tokenId];
    }

    // ========== 禁止NFT转让 ========== //
    /**
     * @dev 覆盖 _update(...) 来阻止正常的 from->to 转移
     */
    function _update(address to, uint256 tokenId, address auth)
        internal
        override
        returns (address)
    {
        address from = _ownerOf(tokenId);
        // 如果 from != 0 && to != 0，说明这是普通的持有者 -> 新地址 的转移，直接 revert
        // （from=0表示 mint；to=0 可能表示 burn，如果你也想禁止 burn，可以额外加判断）
        if (from != address(0) && to != address(0)) {
            revert("Non-transferable: transfer is disabled");
        }
        // 否则执行父类逻辑（mint 或 burn）
        return super._update(to, tokenId, auth);
    }

    // 禁止approve
    function approve(address , uint256 ) public pure override {
        revert("Approve not allowed");
    }

    // 禁止setApprovalForAll
    function setApprovalForAll(address , bool ) public pure override {
        revert("setApprovalForAll not allowed");
    }

}