// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * TEST 14: Assembly Usage (But Safe)
 * Expected: MEDIUM risk (40-60)
 * Challenge: Uses inline assembly (Slither flags this)
 * But assembly is safe and gas-optimized
 * Tests: Does model panic at assembly keyword?
 */
contract AssemblySafe {
    mapping(address => uint256) public balances;
    
    function deposit() public payable {
        balances[msg.sender] += msg.value;
    }
    
    // Safe assembly for gas optimization
    function getBalance(address account) public view returns (uint256 balance) {
        assembly {
            // Load balance from storage slot
            mstore(0x00, account)
            mstore(0x20, balances.slot)
            balance := sload(keccak256(0x00, 0x40))
        }
    }
    
    // Safe assembly for efficient transfer
    function withdraw(uint256 amount) public {
        require(balances[msg.sender] >= amount, "Insufficient");
        
        balances[msg.sender] -= amount;
        
        assembly {
            // Safe transfer using assembly
            let success := call(gas(), caller(), amount, 0, 0, 0, 0)
            if iszero(success) {
                revert(0, 0)
            }
        }
    }
}
