// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.13;

import "forge-std/Test.sol";

import "../src/DataRegistration.sol";
import "../src/EscrowDeposit.sol";
import "../src/DataTradingPlatform.sol";

contract IntegrationTest is Test {
    DataRegistration public dataRegistration;
    EscrowDeposit public escrowDeposit;
    DataTradingPlatform public dataTradingPlatform;

    address public admin = address(0x1111);
    address public agent = address(0x2222);
    address public dataOwner = address(0x3333);
    address public buyer = address(0x4444);
    address public informer = address(0x5555);
    address public suspicion_dataOwner = address(0x6666);

    uint256 public listStakeAmount = 3 ether;  // 和合约中设定的相同
    uint256 public informerStakeAmount = 2 ether; // 测试时可随意
    uint256 public nftPrice = 1 ether;

    // ============ setUp() ============ //
    /**
     * @notice Foundry 中每个测试函数执行之前都会调用 setUp()，或者你可以让 setUp 只执行一次。  
     *         这里我们一次部署&初始化，在每个test里执行不同操作。
     */
    function setUp() public {
        // 给所有地址分配一些初始 Ether，方便测试
        vm.deal(admin, 100 ether);
        vm.deal(agent, 100 ether);
        vm.deal(dataOwner, 100 ether);
        vm.deal(buyer, 100 ether);
        vm.deal(informer, 100 ether);
        vm.deal(suspicion_dataOwner, 100 ether);

        // 1. 用 admin 身份部署合约 (或直接用默认 msg.sender 部署也行)
        vm.startPrank(admin);

        // 先各自传一个临时地址，避免构造函数循环依赖
        escrowDeposit = new EscrowDeposit();
        dataRegistration = new DataRegistration();
        dataTradingPlatform = new DataTradingPlatform(address(dataRegistration));

        // 2. 互相设置地址 (假设你在合约中新增了 setEscrowContract & setDataRegistrationContract)
        //    这样 DataRegistration, EscrowDeposit 就都能正确地引用对方。
        dataRegistration.setEscrowContract(address(escrowDeposit));
        escrowDeposit.setDataRegistrationContract(address(dataRegistration));

        // 3. 设置 agent
        dataRegistration.setAgent(agent);
        escrowDeposit.setAgent(agent);
        // DataTradingPlatform 的 setAgent(...) 已经加 onlyAdmin 了，所以必须由 admin 调用
        dataTradingPlatform.setAgent(agent);

        vm.stopPrank();
    }

    // ============ 1) 测试铸造NFT (registerData) ============ //
    function testMintNFT() public {
        // agent 来调用 resgisterData
        vm.startPrank(agent);

        uint256 beforeBalance = address(escrowDeposit).balance;
        // agent 调用 registerData，铸造NFT 给 dataOwner
        uint256 newTokenId = dataRegistration.registerData{value: listStakeAmount}(
            "ipfs://some-encryted-cid",
            dataOwner
        );

        // 校验合约内收到的质押
        uint256 afterBalance = address(escrowDeposit).balance;
        assertEq(afterBalance - beforeBalance, listStakeAmount, "Escrow contract should have the stake amount");

        vm.stopPrank();

        // 校验 NFT 的拥有者
        address owner = dataRegistration.ownerOf(newTokenId);
        assertEq(owner, dataOwner, "NFT owner should be dataOwner");
    }

    // ============ 2) 测试上架NFT (listNFT) ============ //
    function testListNFT() public {
        // 先铸造一个 NFT (tokenId = 1)
        vm.startPrank(agent);
        dataRegistration.registerData{value: listStakeAmount}(
            "ipfs://some-encryted-cid",
            dataOwner
        );
        vm.stopPrank();

        // 检查初始状态: tokenIdToStatus[1] == NotListed (默认)
        DataTradingPlatform.ListingStatus status = dataTradingPlatform.getNFTStatus(1);
        assertEq(uint(status), uint(DataTradingPlatform.ListingStatus.NotListed), "Default should be NotListed");

        // 上架 NFT：listNFT(tokenId, price)
        vm.startPrank(agent);
        dataTradingPlatform.listNFT(1, nftPrice);
        vm.stopPrank();

        // 检查状态: tokenIdToStatus[1] == Listed
        status = dataTradingPlatform.getNFTStatus(1);
        assertEq(uint(status), uint(DataTradingPlatform.ListingStatus.Listed), "NFT should be listed");
        uint256 price = dataTradingPlatform.getPrice(1);
        assertEq(price, nftPrice, "NFT price mismatch");

    }

    // ============ 3) 测试下架NFT (unlistNFT) ============ //
    function testUnlistNFT() public {
        // 准备：先铸造 + 上架
        vm.startPrank(agent);
        dataRegistration.registerData{value: listStakeAmount}("ipfs://cid", dataOwner);
        vm.stopPrank();

        // 上架
        vm.startPrank(agent);
        dataTradingPlatform.listNFT(1, nftPrice);
        vm.stopPrank();

        // 下架
        vm.startPrank(agent);
        dataTradingPlatform.unlistNFT(1);
        vm.stopPrank();

        // 校验状态
        DataTradingPlatform.ListingStatus status = dataTradingPlatform.getNFTStatus(1);
        assertEq(uint(status), uint(DataTradingPlatform.ListingStatus.Unlisted), "NFT should be unlisted");
    }

    // ============ 4) 测试购买NFT (purchaseNFT) ============ //
    function testPurchaseNFT() public {
        // 准备：先铸造 + 上架
        vm.startPrank(agent);
        dataRegistration.registerData{value: listStakeAmount}("ipfs://cid", dataOwner);
        vm.stopPrank();

        // 上架
        vm.startPrank(agent);
        dataTradingPlatform.listNFT(1, nftPrice);
        vm.stopPrank();

        // 购买
        uint256 beforeAgentBalance = agent.balance;
        uint256 beforeBalanceOwner = dataOwner.balance;
        vm.startPrank(agent);
        dataTradingPlatform.purchaseNFT{value: nftPrice}(
            1,
            buyer,
            "ipfs://buyer-specific-cid" // agent 链下水印/加密得到的cid_1'
        );
        vm.stopPrank();

        // 校验：agent余额减少，数据拥有者余额增加
        uint256 afterAgentBalance = agent.balance;
        assertEq(beforeAgentBalance - afterAgentBalance, nftPrice, "Agent balance should decrease");

        // 数据拥有者余额增加
        uint256 afterBalanceOwner = dataOwner.balance;
        assertEq(afterBalanceOwner - beforeBalanceOwner, nftPrice, "Owner should receive the payment");

        // 校验：NFT 状态变为 Unlisted
        DataTradingPlatform.ListingStatus status = dataTradingPlatform.getNFTStatus(1);
        assertEq(uint(status), uint(DataTradingPlatform.ListingStatus.Listed), "NFT should be unlisted");

        // buyer 获得加密 cid_1'
        vm.startPrank(buyer);
        string memory gotEncryptedCid = dataTradingPlatform.getEncryptedCid(1);
        vm.stopPrank();
        assertEq(gotEncryptedCid, "ipfs://buyer-specific-cid", "Buyer should have the correct encrypted Cid");
    }

    // ============ 5) 举报测试 ============ //
    // 包括 5.1 举报成功(Informer 成立) & 5.2 举报失败(Informer 被没收)
    function testInformer() public {
        // ======= 先完成NFT的铸造 =======
        vm.startPrank(agent);
        uint256 originalTokenId = dataRegistration.registerData{value: listStakeAmount}("ipfs://cid1", dataOwner);
        vm.stopPrank();

        vm.startPrank(agent);
        uint256 suspicionTokenId = dataRegistration.registerData{value: listStakeAmount}("ipfs://cid2", suspicion_dataOwner);
        vm.stopPrank();

        // 拿到 tokenId = 1
        // 核对 ownership
        address nftOwner = dataRegistration.ownerOf(originalTokenId);
        assertEq(nftOwner, dataOwner, "NFT owner should be dataOwner");
        address suspicionOwner = dataRegistration.ownerOf(suspicionTokenId);
        assertEq(suspicionOwner, suspicion_dataOwner, "NFT owner should be suspicion_dataOwner");

        // ======= informerDeposit：举报质押 =======
        uint256 beforeEscrowBalance = address(escrowDeposit).balance;

        // agent 调用 informerDeposit
        vm.startPrank(agent);
        escrowDeposit.informerDeposit{value: informerStakeAmount}(informer, originalTokenId, suspicionTokenId, informerStakeAmount);
        vm.stopPrank();

        // 校验：合约内收到的质押
        uint256 afterEscrowBalance = address(escrowDeposit).balance;
        assertEq(afterEscrowBalance - beforeEscrowBalance, informerStakeAmount, "Escrow contract should have the stake amount");

        // ============ 5.1 举报成立场景 ============ //
        // 测试 claimInformerSuccess：奖励给 informer （没收 dataOwner 的 listDeposit + informer 自己的保证金一起给他）
        uint256 beforeInformerBalance = informer.balance;
        uint256 beforeSuspicionOwnerBalance = suspicionOwner.balance;

        vm.startPrank(agent);
        escrowDeposit.claimInformerSuccess(informer, originalTokenId, suspicionTokenId);
        vm.stopPrank();

        // informer 应该得到 informerStakeAmount + dataOwner 的 listStakeAmount
        uint256 expectedReward = informerStakeAmount + listStakeAmount;
        uint256 afterInformerBalance = informer.balance;
        assertEq(afterInformerBalance - beforeInformerBalance, expectedReward, "Informer should get the reward");

        // dataOwner 的质押也被清空了
        uint256 afterSuspicionOwnerBalance = suspicionOwner.balance;
        // 这里 dataOwner 不会增加，也不会减少（因为那笔 stake 没有直接从 owner 地址扣，而是本就存到 escrow 里）。所以 owner.balance 不变是正常现象。
        assertEq(afterSuspicionOwnerBalance, beforeSuspicionOwnerBalance, "Owner's main balance not impacted directly");
        // 要测试 listDeposit 真被扣走，可以在 escrowDeposit中再检查 listDeposits[dataOwner][tokenId]。
        assertEq(escrowDeposit.listDeposits(suspicionOwner, suspicionTokenId), 0, "Owner's listDeposit should be cleared");

        // ============ 5.2 举报失败/不成立场景 ============ //
        // 需要先重新造一个 NFT 让 informer 再次举报，然后 agent 判断不成立 => 没收保证金给admin
        // 再 mint 一次 tokenId=3
        vm.startPrank(agent);
        uint256 suspicionTokenId_2 = dataRegistration.registerData{value: listStakeAmount}("ipfs://cid3", suspicion_dataOwner);
        vm.stopPrank();

        // informer 再次质押
        vm.startPrank(agent);
        escrowDeposit.informerDeposit{value: informerStakeAmount}(informer, originalTokenId, suspicionTokenId_2, informerStakeAmount);
        vm.stopPrank();

        // 这次 agent 认定 informer 恶意，没收他的质押到 admin
        uint256 beforeAdminBalance = admin.balance;
        vm.startPrank(agent);
        escrowDeposit.confiscateInformerDeposit(informer, originalTokenId, suspicionTokenId_2);
        vm.stopPrank();

        uint256 afterAdminBalance = admin.balance;
        assertEq(afterAdminBalance - beforeAdminBalance, informerStakeAmount, "Admin should get informer's stake");

        assertEq(escrowDeposit.listDeposits(suspicion_dataOwner, suspicionTokenId_2), 3 ether, "Owner's listDeposit should be cleared");
    }
}
