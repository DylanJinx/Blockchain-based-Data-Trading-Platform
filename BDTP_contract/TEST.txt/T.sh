No files changed, compilation skipped

Ran 5 tests for test/IntegrationTest.t.sol:IntegrationTest
[PASS] testInformer() (gas: 704809)
Traces:
  [764509] IntegrationTest::testInformer()
    ├─ [0] VM::startPrank(0x0000000000000000000000000000000000002222)
    │   └─ ← [Return] 
    ├─ [228044] DataRegistration::registerData{value: 3000000000000000000}("ipfs://cid1", 0x0000000000000000000000000000000000003333)
    │   ├─ [24602] EscrowDeposit::listDeposit{value: 3000000000000000000}(0x0000000000000000000000000000000000003333, 1, 3000000000000000000 [3e18])
    │   │   ├─ emit ListDeposited(dataOwner: 0x0000000000000000000000000000000000003333, tokenId: 1, amount: 3000000000000000000 [3e18])
    │   │   └─ ← [Stop] 
    │   ├─ emit Transfer(from: 0x0000000000000000000000000000000000000000, to: 0x0000000000000000000000000000000000003333, tokenId: 1)
    │   ├─ emit DataRegistered(dataOwner: 0x0000000000000000000000000000000000003333, tokenId: 1, tokenURI: "ipfs://cid1", saleHash: 0x4257b509ed3694faee40849622a75eb31c04fa8590d996f558051395a0045c15)
    │   └─ ← [Return] 1
    ├─ [0] VM::stopPrank()
    │   └─ ← [Return] 
    ├─ [0] VM::startPrank(0x0000000000000000000000000000000000002222)
    │   └─ ← [Return] 
    ├─ [197644] DataRegistration::registerData{value: 3000000000000000000}("ipfs://cid2", 0x0000000000000000000000000000000000006666)
    │   ├─ [24602] EscrowDeposit::listDeposit{value: 3000000000000000000}(0x0000000000000000000000000000000000006666, 2, 3000000000000000000 [3e18])
    │   │   ├─ emit ListDeposited(dataOwner: 0x0000000000000000000000000000000000006666, tokenId: 2, amount: 3000000000000000000 [3e18])
    │   │   └─ ← [Stop] 
    │   ├─ emit Transfer(from: 0x0000000000000000000000000000000000000000, to: 0x0000000000000000000000000000000000006666, tokenId: 2)
    │   ├─ emit DataRegistered(dataOwner: 0x0000000000000000000000000000000000006666, tokenId: 2, tokenURI: "ipfs://cid2", saleHash: 0x735a131571c31d80e899fd38c9ecabe75e91b0ee300b67e38265938f0283f578)
    │   └─ ← [Return] 2
    ├─ [0] VM::stopPrank()
    │   └─ ← [Return] 
    ├─ [638] DataRegistration::ownerOf(1) [staticcall]
    │   └─ ← [Return] 0x0000000000000000000000000000000000003333
    ├─ [0] VM::assertEq(0x0000000000000000000000000000000000003333, 0x0000000000000000000000000000000000003333, "NFT owner should be dataOwner") [staticcall]
    │   └─ ← [Return] 
    ├─ [638] DataRegistration::ownerOf(2) [staticcall]
    │   └─ ← [Return] 0x0000000000000000000000000000000000006666
    ├─ [0] VM::assertEq(0x0000000000000000000000000000000000006666, 0x0000000000000000000000000000000000006666, "NFT owner should be suspicion_dataOwner") [staticcall]
    │   └─ ← [Return] 
    ├─ [0] VM::startPrank(0x0000000000000000000000000000000000002222)
    │   └─ ← [Return] 
    ├─ [27148] EscrowDeposit::informerDeposit{value: 2000000000000000000}(0x0000000000000000000000000000000000005555, 1, 2, 2000000000000000000 [2e18])
    │   ├─ emit InformerDeposited(informer: 0x0000000000000000000000000000000000005555, originalTokenId: 1, suspicionTokenId: 2, amount: 2000000000000000000 [2e18])
    │   └─ ← [Stop] 
    ├─ [0] VM::stopPrank()
    │   └─ ← [Return] 
    ├─ [0] VM::assertEq(2000000000000000000 [2e18], 2000000000000000000 [2e18], "Escrow contract should have the stake amount") [staticcall]
    │   └─ ← [Return] 
    ├─ [0] VM::startPrank(0x0000000000000000000000000000000000002222)
    │   └─ ← [Return] 
    ├─ [14480] EscrowDeposit::claimInformerSuccess(0x0000000000000000000000000000000000005555, 1, 2)
    │   ├─ [638] DataRegistration::ownerOf(2) [staticcall]
    │   │   └─ ← [Return] 0x0000000000000000000000000000000000006666
    │   ├─ [0] 0x0000000000000000000000000000000000005555::fallback{value: 5000000000000000000}()
    │   │   └─ ← [Stop] 
    │   ├─ emit InformerSuccess(informer: 0x0000000000000000000000000000000000005555, dataOwner: 0x0000000000000000000000000000000000006666, originalTokenId: 1, suspicionTokenId: 2, totalReward: 5000000000000000000 [5e18])
    │   └─ ← [Stop] 
    ├─ [0] VM::stopPrank()
    │   └─ ← [Return] 
    ├─ [0] VM::assertEq(5000000000000000000 [5e18], 5000000000000000000 [5e18], "Informer should get the reward") [staticcall]
    │   └─ ← [Return] 
    ├─ [0] VM::assertEq(100000000000000000000 [1e20], 100000000000000000000 [1e20], "Owner's main balance not impacted directly") [staticcall]
    │   └─ ← [Return] 
    ├─ [703] EscrowDeposit::listDeposits(0x0000000000000000000000000000000000006666, 2) [staticcall]
    │   └─ ← [Return] 0
    ├─ [0] VM::assertEq(0, 0, "Owner's listDeposit should be cleared") [staticcall]
    │   └─ ← [Return] 
    ├─ [0] VM::startPrank(0x0000000000000000000000000000000000002222)
    │   └─ ← [Return] 
    ├─ [173244] DataRegistration::registerData{value: 3000000000000000000}("ipfs://cid3", 0x0000000000000000000000000000000000006666)
    │   ├─ [24602] EscrowDeposit::listDeposit{value: 3000000000000000000}(0x0000000000000000000000000000000000006666, 3, 3000000000000000000 [3e18])
    │   │   ├─ emit ListDeposited(dataOwner: 0x0000000000000000000000000000000000006666, tokenId: 3, amount: 3000000000000000000 [3e18])
    │   │   └─ ← [Stop] 
    │   ├─ emit Transfer(from: 0x0000000000000000000000000000000000000000, to: 0x0000000000000000000000000000000000006666, tokenId: 3)
    │   ├─ emit DataRegistered(dataOwner: 0x0000000000000000000000000000000000006666, tokenId: 3, tokenURI: "ipfs://cid3", saleHash: 0xf4d9aa8b98c87807f08584b6391a8fc5db1015d62d1c911b57b0bb2106ef0b84)
    │   └─ ← [Return] 3
    ├─ [0] VM::stopPrank()
    │   └─ ← [Return] 
    ├─ [0] VM::startPrank(0x0000000000000000000000000000000000002222)
    │   └─ ← [Return] 
    ├─ [25148] EscrowDeposit::informerDeposit{value: 2000000000000000000}(0x0000000000000000000000000000000000005555, 1, 3, 2000000000000000000 [2e18])
    │   ├─ emit InformerDeposited(informer: 0x0000000000000000000000000000000000005555, originalTokenId: 1, suspicionTokenId: 3, amount: 2000000000000000000 [2e18])
    │   └─ ← [Stop] 
    ├─ [0] VM::stopPrank()
    │   └─ ← [Return] 
    ├─ [0] VM::startPrank(0x0000000000000000000000000000000000002222)
    │   └─ ← [Return] 
    ├─ [12425] EscrowDeposit::confiscateInformerDeposit(0x0000000000000000000000000000000000005555, 1, 3)
    │   ├─ [0] 0x0000000000000000000000000000000000001111::fallback{value: 2000000000000000000}()
    │   │   └─ ← [Stop] 
    │   ├─ emit InformerConfiscated(informer: 0x0000000000000000000000000000000000005555, originalTokenId: 1, suspicionTokenId: 3, amount: 2000000000000000000 [2e18])
    │   └─ ← [Stop] 
    ├─ [0] VM::stopPrank()
    │   └─ ← [Return] 
    ├─ [0] VM::assertEq(2000000000000000000 [2e18], 2000000000000000000 [2e18], "Admin should get informer's stake") [staticcall]
    │   └─ ← [Return] 
    ├─ [703] EscrowDeposit::listDeposits(0x0000000000000000000000000000000000006666, 3) [staticcall]
    │   └─ ← [Return] 3000000000000000000 [3e18]
    ├─ [0] VM::assertEq(3000000000000000000 [3e18], 3000000000000000000 [3e18], "Owner's listDeposit should be cleared") [staticcall]
    │   └─ ← [Return] 
    └─ ← [Stop] 

[PASS] testListNFT() (gas: 311778)
Traces:
  [311778] IntegrationTest::testListNFT()
    ├─ [0] VM::startPrank(0x0000000000000000000000000000000000002222)
    │   └─ ← [Return] 
    ├─ [228053] DataRegistration::registerData{value: 3000000000000000000}("ipfs://some-encryted-cid", 0x0000000000000000000000000000000000003333)
    │   ├─ [24602] EscrowDeposit::listDeposit{value: 3000000000000000000}(0x0000000000000000000000000000000000003333, 1, 3000000000000000000 [3e18])
    │   │   ├─ emit ListDeposited(dataOwner: 0x0000000000000000000000000000000000003333, tokenId: 1, amount: 3000000000000000000 [3e18])
    │   │   └─ ← [Stop] 
    │   ├─ emit Transfer(from: 0x0000000000000000000000000000000000000000, to: 0x0000000000000000000000000000000000003333, tokenId: 1)
    │   ├─ emit DataRegistered(dataOwner: 0x0000000000000000000000000000000000003333, tokenId: 1, tokenURI: "ipfs://some-encryted-cid", saleHash: 0xb9e4e941c146d205258496beefdad28ec297a4e8f9bcdda85be591e53e85b445)
    │   └─ ← [Return] 1
    ├─ [0] VM::stopPrank()
    │   └─ ← [Return] 
    ├─ [2555] DataTradingPlatform::getNFTStatus(1) [staticcall]
    │   └─ ← [Return] 0
    ├─ [0] VM::assertEq(0, 0, "Default should be NotListed") [staticcall]
    │   └─ ← [Return] 
    ├─ [0] VM::startPrank(0x0000000000000000000000000000000000002222)
    │   └─ ← [Return] 
    ├─ [46871] DataTradingPlatform::listNFT(1, 1000000000000000000 [1e18])
    │   ├─ emit NFTListed(agent: 0x0000000000000000000000000000000000002222, tokenId: 1, price: 1000000000000000000 [1e18])
    │   └─ ← [Stop] 
    ├─ [0] VM::stopPrank()
    │   └─ ← [Return] 
    ├─ [555] DataTradingPlatform::getNFTStatus(1) [staticcall]
    │   └─ ← [Return] 1
    ├─ [0] VM::assertEq(1, 1, "NFT should be listed") [staticcall]
    │   └─ ← [Return] 
    ├─ [457] DataTradingPlatform::getPrice(1) [staticcall]
    │   └─ ← [Return] 1000000000000000000 [1e18]
    ├─ [0] VM::assertEq(1000000000000000000 [1e18], 1000000000000000000 [1e18], "NFT price mismatch") [staticcall]
    │   └─ ← [Return] 
    └─ ← [Stop] 

[PASS] testMintNFT() (gas: 255015)
Traces:
  [255015] IntegrationTest::testMintNFT()
    ├─ [0] VM::startPrank(0x0000000000000000000000000000000000002222)
    │   └─ ← [Return] 
    ├─ [225553] DataRegistration::registerData{value: 3000000000000000000}("ipfs://some-encryted-cid", 0x0000000000000000000000000000000000003333)
    │   ├─ [24602] EscrowDeposit::listDeposit{value: 3000000000000000000}(0x0000000000000000000000000000000000003333, 1, 3000000000000000000 [3e18])
    │   │   ├─ emit ListDeposited(dataOwner: 0x0000000000000000000000000000000000003333, tokenId: 1, amount: 3000000000000000000 [3e18])
    │   │   └─ ← [Stop] 
    │   ├─ emit Transfer(from: 0x0000000000000000000000000000000000000000, to: 0x0000000000000000000000000000000000003333, tokenId: 1)
    │   ├─ emit DataRegistered(dataOwner: 0x0000000000000000000000000000000000003333, tokenId: 1, tokenURI: "ipfs://some-encryted-cid", saleHash: 0xb9e4e941c146d205258496beefdad28ec297a4e8f9bcdda85be591e53e85b445)
    │   └─ ← [Return] 1
    ├─ [0] VM::assertEq(3000000000000000000 [3e18], 3000000000000000000 [3e18], "Escrow contract should have the stake amount") [staticcall]
    │   └─ ← [Return] 
    ├─ [0] VM::stopPrank()
    │   └─ ← [Return] 
    ├─ [638] DataRegistration::ownerOf(1) [staticcall]
    │   └─ ← [Return] 0x0000000000000000000000000000000000003333
    ├─ [0] VM::assertEq(0x0000000000000000000000000000000000003333, 0x0000000000000000000000000000000000003333, "NFT owner should be dataOwner") [staticcall]
    │   └─ ← [Return] 
    └─ ← [Stop] 

[PASS] testPurchaseNFT() (gas: 362183)
Traces:
  [362183] IntegrationTest::testPurchaseNFT()
    ├─ [0] VM::startPrank(0x0000000000000000000000000000000000002222)
    │   └─ ← [Return] 
    ├─ [228044] DataRegistration::registerData{value: 3000000000000000000}("ipfs://cid", 0x0000000000000000000000000000000000003333)
    │   ├─ [24602] EscrowDeposit::listDeposit{value: 3000000000000000000}(0x0000000000000000000000000000000000003333, 1, 3000000000000000000 [3e18])
    │   │   ├─ emit ListDeposited(dataOwner: 0x0000000000000000000000000000000000003333, tokenId: 1, amount: 3000000000000000000 [3e18])
    │   │   └─ ← [Stop] 
    │   ├─ emit Transfer(from: 0x0000000000000000000000000000000000000000, to: 0x0000000000000000000000000000000000003333, tokenId: 1)
    │   ├─ emit DataRegistered(dataOwner: 0x0000000000000000000000000000000000003333, tokenId: 1, tokenURI: "ipfs://cid", saleHash: 0xfc8405a6a6bf3d533aa8524eb72dd1850379a4e2aa1ea7616f5dbff766131987)
    │   └─ ← [Return] 1
    ├─ [0] VM::stopPrank()
    │   └─ ← [Return] 
    ├─ [0] VM::startPrank(0x0000000000000000000000000000000000002222)
    │   └─ ← [Return] 
    ├─ [48871] DataTradingPlatform::listNFT(1, 1000000000000000000 [1e18])
    │   ├─ emit NFTListed(agent: 0x0000000000000000000000000000000000002222, tokenId: 1, price: 1000000000000000000 [1e18])
    │   └─ ← [Stop] 
    ├─ [0] VM::stopPrank()
    │   └─ ← [Return] 
    ├─ [0] VM::startPrank(0x0000000000000000000000000000000000002222)
    │   └─ ← [Return] 
    ├─ [36939] DataTradingPlatform::purchaseNFT{value: 1000000000000000000}(1, 0x0000000000000000000000000000000000004444, "ipfs://buyer-specific-cid")
    │   ├─ [638] DataRegistration::ownerOf(1) [staticcall]
    │   │   └─ ← [Return] 0x0000000000000000000000000000000000003333
    │   ├─ [0] 0x0000000000000000000000000000000000003333::fallback{value: 1000000000000000000}()
    │   │   └─ ← [Stop] 
    │   ├─ emit NFTPurchased(buyer: 0x0000000000000000000000000000000000002222, tokenId: 1, dataOwner: 0x0000000000000000000000000000000000003333, amount: 1000000000000000000 [1e18], encryptedCid: "ipfs://buyer-specific-cid")
    │   └─ ← [Stop] 
    ├─ [0] VM::stopPrank()
    │   └─ ← [Return] 
    ├─ [0] VM::assertEq(1000000000000000000 [1e18], 1000000000000000000 [1e18], "Agent balance should decrease") [staticcall]
    │   └─ ← [Return] 
    ├─ [0] VM::assertEq(1000000000000000000 [1e18], 1000000000000000000 [1e18], "Owner should receive the payment") [staticcall]
    │   └─ ← [Return] 
    ├─ [555] DataTradingPlatform::getNFTStatus(1) [staticcall]
    │   └─ ← [Return] 1
    ├─ [0] VM::assertEq(1, 1, "NFT should be unlisted") [staticcall]
    │   └─ ← [Return] 
    ├─ [0] VM::startPrank(0x0000000000000000000000000000000000004444)
    │   └─ ← [Return] 
    ├─ [1375] DataTradingPlatform::getEncryptedCid(1) [staticcall]
    │   └─ ← [Return] "ipfs://buyer-specific-cid"
    ├─ [0] VM::stopPrank()
    │   └─ ← [Return] 
    ├─ [0] VM::assertEq("ipfs://buyer-specific-cid", "ipfs://buyer-specific-cid", "Buyer should have the correct encrypted Cid") [staticcall]
    │   └─ ← [Return] 
    └─ ← [Stop] 

[PASS] testUnlistNFT() (gas: 312116)
Traces:
  [312116] IntegrationTest::testUnlistNFT()
    ├─ [0] VM::startPrank(0x0000000000000000000000000000000000002222)
    │   └─ ← [Return] 
    ├─ [228044] DataRegistration::registerData{value: 3000000000000000000}("ipfs://cid", 0x0000000000000000000000000000000000003333)
    │   ├─ [24602] EscrowDeposit::listDeposit{value: 3000000000000000000}(0x0000000000000000000000000000000000003333, 1, 3000000000000000000 [3e18])
    │   │   ├─ emit ListDeposited(dataOwner: 0x0000000000000000000000000000000000003333, tokenId: 1, amount: 3000000000000000000 [3e18])
    │   │   └─ ← [Stop] 
    │   ├─ emit Transfer(from: 0x0000000000000000000000000000000000000000, to: 0x0000000000000000000000000000000000003333, tokenId: 1)
    │   ├─ emit DataRegistered(dataOwner: 0x0000000000000000000000000000000000003333, tokenId: 1, tokenURI: "ipfs://cid", saleHash: 0xfc8405a6a6bf3d533aa8524eb72dd1850379a4e2aa1ea7616f5dbff766131987)
    │   └─ ← [Return] 1
    ├─ [0] VM::stopPrank()
    │   └─ ← [Return] 
    ├─ [0] VM::startPrank(0x0000000000000000000000000000000000002222)
    │   └─ ← [Return] 
    ├─ [48871] DataTradingPlatform::listNFT(1, 1000000000000000000 [1e18])
    │   ├─ emit NFTListed(agent: 0x0000000000000000000000000000000000002222, tokenId: 1, price: 1000000000000000000 [1e18])
    │   └─ ← [Stop] 
    ├─ [0] VM::stopPrank()
    │   └─ ← [Return] 
    ├─ [0] VM::startPrank(0x0000000000000000000000000000000000002222)
    │   └─ ← [Return] 
    ├─ [2507] DataTradingPlatform::unlistNFT(1)
    │   ├─ emit NFTUnlisted(agent: 0x0000000000000000000000000000000000002222, tokenId: 1)
    │   └─ ← [Stop] 
    ├─ [0] VM::stopPrank()
    │   └─ ← [Return] 
    ├─ [555] DataTradingPlatform::getNFTStatus(1) [staticcall]
    │   └─ ← [Return] 2
    ├─ [0] VM::assertEq(2, 2, "NFT should be unlisted") [staticcall]
    │   └─ ← [Return] 
    └─ ← [Stop] 

Suite result: ok. 5 passed; 0 failed; 0 skipped; finished in 2.47ms (6.09ms CPU time)

Ran 1 test suite in 1.78s (2.47ms CPU time): 5 tests passed, 0 failed, 0 skipped (5 total tests)
