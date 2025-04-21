// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;

import "@openzeppelin/contracts/token/ERC721/IERC721.sol";

/**
 * @title EscrowDeposit
 * @notice 管理上架保证金 & 举报保证金等。
 */
contract EscrowDeposit {
    // 数据登记合约地址
    address public dataRegistrationContract;

    // ============ 上架保证金 ============ //
    // listDeposits[dataOwner][tokenId] = dataOwner 在该 tokenId 上质押的金额
    mapping(address => mapping(uint256 => uint256)) public listDeposits;

    // 事件
    event ListDeposited(address indexed dataOwner, uint256 indexed tokenId, uint256 amount);
    event ListWithdrawn(address indexed dataOwner, uint256 indexed tokenId, uint256 amount);

    // ============ 举报保证金 ============ //
    // informer => original tokenId => suspicion tokenId => informer 在该 tokenId 上质押的金额
    mapping(address => mapping(uint256 => mapping(uint256 => uint256))) public informerDeposits;

    // 事件
    event InformerDeposited(address indexed informer, uint256 indexed originalTokenId, uint256 indexed suspicionTokenId, uint256 amount);
    event InformerSuccess(address indexed informer, address dataOwner, uint256 indexed originalTokenId, uint256 indexed suspicionTokenId, uint256 totalReward);
    event InformerConfiscated(address indexed informer, uint256 indexed originalTokenId, uint256 indexed suspicionTokenId, uint256 amount);

    address public admin;
    address public agent;
    constructor() {
        admin = msg.sender;
    }

    modifier onlyAdmin() {
        require(msg.sender == admin, "Only admin can call this function");
        _;
    }

    modifier onlyAgent() {
        require(msg.sender == agent, "Only agent can call this function");
        _;
    }

    function setAgent(address _agent) onlyAdmin() external {
        agent = _agent;
    }

    function setDataRegistrationContract(address _dataRegistrationContract) onlyAdmin() external {
        dataRegistrationContract = _dataRegistrationContract;
    }

    // ============ 1) 数据拥有者 上架保证金逻辑 ============ //
    /**
     * @notice 用户(数据拥有者)上架NFT时，由 DataRegistration 合约调用
     *         msg.value == _amount
     * @param _dataOwner 数据拥有者地址
     * @param tokenId    对应的NFT
     * @param _amount    质押金额
     */
    function listDeposit(address _dataOwner, uint256 tokenId, uint256 _amount) external payable {
        require(msg.value == _amount, "Value mismatch");

        // 累加质押
        listDeposits[_dataOwner][tokenId] += _amount;

        emit ListDeposited(_dataOwner, tokenId, _amount);
    }

    /**
     * @notice 将 dataOwner 在 tokenId 上的质押“正常退还”给 dataOwner (无违规或主动下架等情况)
     *         只有Agent能调用，避免数据拥有者私自取回。
     */
    function withdrawListDeposit(address _dataOwner, uint256 tokenId) external onlyAgent {
        uint256 amt = listDeposits[_dataOwner][tokenId];
        require(amt > 0, "No deposit to withdraw");

        listDeposits[_dataOwner][tokenId] = 0;

        // 直接转给 dataOwner
        (bool success, ) = payable(_dataOwner).call{value: amt}("");
        require(success, "Withdraw transfer failed");

        emit ListWithdrawn(_dataOwner, tokenId, amt);
    }

    // ============ 2) 举报者 保证金逻辑 ============ //

    /**
     * @notice 举报者对某tokenId进行举报时，需要质押保证金
     */
    function informerDeposit(address _informer, uint256 originalTokenId, uint256 suspicionTokenId, uint256 _amount) external payable onlyAgent {
        require(msg.value == _amount, "Value mismatch");

        informerDeposits[_informer][originalTokenId][suspicionTokenId] += _amount;

        emit InformerDeposited(_informer, originalTokenId, suspicionTokenId, _amount);
    }

    /**
     * @dev agent 调用：举报成立，奖励给informer
     *      - informer 获得自己质押的保证金 + dataOwner 质押的保证金
     *      - 两份保证金都清零
     */
    function claimInformerSuccess(address _informer, uint256 originalTokenId, uint256 suspicionTokenId) external onlyAgent {
        uint256 informerAmt = informerDeposits[_informer][originalTokenId][suspicionTokenId];
        require(informerAmt > 0, "No informer deposit found");

        address _dataOwner = IERC721(dataRegistrationContract).ownerOf(suspicionTokenId);

        uint256 ownerAmt = listDeposits[_dataOwner][suspicionTokenId];
        require(ownerAmt > 0, "No owner deposit found");

        // 清零
        informerDeposits[_informer][originalTokenId][suspicionTokenId] = 0;
        listDeposits[_dataOwner][suspicionTokenId] = 0;

        uint256 totalReward = informerAmt + ownerAmt;

        // 转给informer
        (bool success, ) = payable(_informer).call{value: totalReward}("");
        require(success, "Transfer to informer failed");

        emit InformerSuccess(_informer, _dataOwner, originalTokenId, suspicionTokenId, totalReward);
    }

    /**
     * @dev agent 调用：举报无效/恶意，没收 informer 的保证金给admin
     */
    function confiscateInformerDeposit(address _informer, uint256 originalTokenId, uint256 suspicionTokenId) external onlyAgent {
        uint256 amt = informerDeposits[_informer][originalTokenId][suspicionTokenId];
        require(amt > 0, "No informer deposit to confiscate");

        informerDeposits[_informer][originalTokenId][suspicionTokenId] = 0;

        // 转给admin
        (bool success, ) = payable(admin).call{value: amt}("");
        require(success, "ConfiscateInformerDeposit transfer failed");

        emit InformerConfiscated(_informer, originalTokenId, suspicionTokenId, amt);
    }
    
    // 合约可收ETH
    receive() external payable {}
}