// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * TEST 24: Intentional Honeypot
 * Expected: HIGH risk (>80)
 * Challenge: Designed to trap attackers
 * Tests: Can model detect intentionally malicious code?
 */
contract IntentionalHoneypot {
    address private owner;
    
    constructor() {
        owner = msg.sender;
    }
    
    // Looks like you can become owner...
    function becomeOwner() public payable {
        require(msg.value >= 1 ether);
        // But this doesn't actually change owner!
        address temp = owner;
        owner = temp;  // Sneaky: reassigns same value
    }
    
    // Only real owner can withdraw
    function withdraw() public {
        require(msg.sender == owner);
        payable(owner).transfer(address(this).balance);
    }
    
    receive() external payable {}
}
