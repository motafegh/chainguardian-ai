// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * TEST 10: tx.origin Authentication
 * Expected: MEDIUM-HIGH risk (50-70)
 * Reason: Uses tx.origin instead of msg.sender
 */
contract TxOriginAuth {
    address public owner;
    
    constructor() {
        owner = msg.sender;
    }
    
    // VULNERABILITY: tx.origin can be exploited via phishing
    function withdraw() public {
        require(tx.origin == owner, "Not owner");
        payable(owner).transfer(address(this).balance);
    }
    
    receive() external payable {}
}
