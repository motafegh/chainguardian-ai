// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * TEST 13: Modern DeFi Pattern (Safe)
 * Expected: LOW-MEDIUM risk (20-50)
 * Challenge: Uses modern patterns not in training data
 * Tests: Can model generalize to new patterns?
 */
contract ModernDeFiSafe {
    error InsufficientBalance();
    error TransferFailed();
    error Unauthorized();
    
    mapping(address => uint256) private _balances;
    uint256 private _locked = 1;
    
    modifier nonReentrant() {
        require(_locked == 1, "Reentrant call");
        _locked = 2;
        _;
        _locked = 1;
    }
    
    // Modern: Custom errors instead of strings
    function withdraw(uint256 amount) external nonReentrant {
        if (_balances[msg.sender] < amount) {
            revert InsufficientBalance();
        }
        
        _balances[msg.sender] -= amount;
        
        (bool success, ) = msg.sender.call{value: amount}("");
        if (!success) {
            revert TransferFailed();
        }
    }
    
    function deposit() external payable {
        _balances[msg.sender] += msg.value;
    }
    
    function balanceOf(address account) external view returns (uint256) {
        return _balances[account];
    }
}
