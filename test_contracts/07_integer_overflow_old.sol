// SPDX-License-Identifier: MIT
pragma solidity ^0.7.0;  // Old version without auto-checks

/**
 * TEST 7: Integer Overflow (Old Solidity)
 * Expected: HIGH risk (>70)
 * Reason: No automatic overflow protection
 */
contract IntegerOverflowOld {
    mapping(address => uint256) public balances;
    
    function deposit() public payable {
        // VULNERABILITY: Can overflow in old Solidity
        balances[msg.sender] += msg.value;
    }
    
    function withdraw(uint256 amount) public {
        // VULNERABILITY: Can underflow
        balances[msg.sender] -= amount;
        payable(msg.sender).transfer(amount);
    }
}
