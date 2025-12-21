// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * TEST 21: Governance Without Timelock
 * Expected: MEDIUM risk (40-60)
 * Challenge: Not technically vulnerable but risky design
 * Tests: Does model understand governance best practices?
 */
contract TimelockMissing {
    address public owner;
    uint256 public criticalParameter;
    
    constructor() {
        owner = msg.sender;
        criticalParameter = 100;
    }
    
    // RISK: Owner can change critical params instantly
    // Best practice: Use timelock for transparency
    function updateParameter(uint256 newValue) public {
        require(msg.sender == owner);
        criticalParameter = newValue;  // Instant change!
    }
    
    function sensitiveOperation() public {
        require(msg.value >= criticalParameter);
        // Critical operation
    }
}
