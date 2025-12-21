// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * TEST 17: Logic Error (Not Security Bug)
 * Expected: LOW-MEDIUM risk (20-50)
 * Challenge: Business logic error, not security vulnerability
 * Tests: Does model confuse bugs with vulnerabilities?
 */
contract LogicError {
    mapping(address => uint256) public votes;
    uint256 public totalVotes;
    
    function vote() public {
        votes[msg.sender]++;
        // LOGIC ERROR: Should increment totalVotes
        // But this won't cause funds loss or security breach
    }
    
    function getVotes(address voter) public view returns (uint256) {
        return votes[voter];
    }
    
    // Wrong calculation but not a security issue
    function getVotePercentage(address voter) public view returns (uint256) {
        if (totalVotes == 0) return 0;
        return (votes[voter] * 100) / totalVotes;  // Will always return 0!
    }
}
