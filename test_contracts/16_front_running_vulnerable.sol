// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * TEST 16: Front-Running Vulnerability
 * Expected: MEDIUM risk (40-60)
 * Challenge: MEV/front-running not detectable by static analysis
 * Tests: Model shouldn't flag this (it's game-theoretic, not code bug)
 */
contract FrontRunningVulnerable {
    uint256 public price = 1 ether;
    address public owner;
    
    constructor() {
        owner = msg.sender;
    }
    
    // Can be front-run but not a "vulnerability" per se
    function updatePrice(uint256 newPrice) public {
        require(msg.sender == owner);
        price = newPrice;
    }
    
    function buy() public payable {
        require(msg.value >= price);
        // Transfer NFT or token
    }
}
