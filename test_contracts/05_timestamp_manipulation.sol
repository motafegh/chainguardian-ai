// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * TEST 5: Timestamp Dependency
 * Expected: MEDIUM-HIGH risk (50-70)
 * Reason: Uses block.timestamp for critical logic
 */
contract TimestampManipulation {
    uint256 public deadline;
    mapping(address => uint256) public lastClaim;
    
    constructor() {
        deadline = block.timestamp + 30 days;
    }
    
    // VULNERABILITY: Timestamp dependency
    function claim() public {
        require(block.timestamp < deadline, "Deadline passed");
        require(block.timestamp > lastClaim[msg.sender] + 1 days, "Too soon");
        
        lastClaim[msg.sender] = block.timestamp;
        
        // Give reward
        payable(msg.sender).transfer(1 ether);
    }
}
