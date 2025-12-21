// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * TEST 15: Gas Griefing Attack
 * Expected: MEDIUM-HIGH risk (50-70)
 * Challenge: Subtle vulnerability not in typical datasets
 * Tests: Can model detect advanced attack vectors?
 */
contract GasGriefing {
    address[] public recipients;
    
    function addRecipient(address recipient) public {
        recipients.push(recipient);
    }
    
    // VULNERABILITY: Unbounded loop can run out of gas
    // Attacker can add many addresses to DOS the contract
    function distributeEther() public payable {
        uint256 share = msg.value / recipients.length;
        
        for (uint256 i = 0; i < recipients.length; i++) {
            payable(recipients[i]).transfer(share);
        }
    }
}
