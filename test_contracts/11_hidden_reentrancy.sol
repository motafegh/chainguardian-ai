// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * TEST 11: Hidden Reentrancy (Not Obvious)
 * Expected: HIGH risk (>70)
 * Challenge: Reentrancy hidden in modifier
 * Tests: Can model detect non-obvious patterns?
 */
contract HiddenReentrancy {
    mapping(address => uint256) public balances;
    
    modifier executeCallback() {
        _;
        // Reentrancy hidden here!
        (bool success, ) = msg.sender.call("");
        require(success);
    }
    
    function deposit() public payable {
        balances[msg.sender] += msg.value;
    }
    
    // Looks safe but modifier makes it vulnerable
    function withdraw(uint256 amount) public executeCallback {
        require(balances[msg.sender] >= amount);
        balances[msg.sender] -= amount;
        payable(msg.sender).transfer(amount);
    }
}
