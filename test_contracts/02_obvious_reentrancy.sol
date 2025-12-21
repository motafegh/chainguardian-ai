// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * TEST 2: Obvious Reentrancy Vulnerability
 * Expected: HIGH risk score (>70)
 * Reason: Classic reentrancy pattern
 */
contract ObviousReentrancy {
    mapping(address => uint256) public balances;
    
    function deposit() public payable {
        balances[msg.sender] += msg.value;
    }
    
    // VULNERABLE: External call before state update
    function withdraw() public {
        uint256 amount = balances[msg.sender];
        
        // VULNERABILITY: Call before state change
        (bool success, ) = msg.sender.call{value: amount}("");
        require(success, "Transfer failed");
        
        // State update AFTER external call (wrong!)
        balances[msg.sender] = 0;
    }
}
