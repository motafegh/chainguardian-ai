// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * TEST 12: False Positive Trap
 * Expected: LOW-MEDIUM risk (20-50)
 * Challenge: Looks vulnerable but is actually safe
 * Tests: Does model give false positives?
 */
contract FalsePositiveTrap {
    mapping(address => uint256) public balances;
    
    // Looks like unchecked call, but it's actually safe
    function withdraw(uint256 amount) public {
        require(balances[msg.sender] >= amount, "Insufficient");
        
        balances[msg.sender] -= amount;
        
        // This LOOKS dangerous but return value doesn't matter here
        // Because we already reduced balance
        msg.sender.call{value: amount}("");
        
        // Even if call fails, user loses funds (their problem)
        // Not a vulnerability for the contract
    }
    
    function deposit() public payable {
        balances[msg.sender] += msg.value;
    }
}
