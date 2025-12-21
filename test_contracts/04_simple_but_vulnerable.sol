// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * TEST 4: Simple But Vulnerable
 * Expected: HIGH risk (>70)
 * Challenge: Minimal code but has vulnerability
 * Tests if model can detect issues in simple contracts
 */
contract SimpleButVulnerable {
    address public owner;
    
    constructor() {
        owner = msg.sender;
    }
    
    // VULNERABILITY: No access control!
    function changeOwner(address newOwner) public {
        owner = newOwner;  // Anyone can become owner!
    }
    
    function withdraw() public {
        require(msg.sender == owner, "Not owner");
        payable(owner).transfer(address(this).balance);
    }
    
    receive() external payable {}
}
