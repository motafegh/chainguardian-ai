// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title VulnerableBank
 * @notice INTENTIONALLY VULNERABLE for educational purposes
 * @dev Contains multiple vulnerabilities for ML training
 */
contract VulnerableBank {
    mapping(address => uint256) public balances;
    address public owner;
    
    event Deposit(address indexed user, uint256 amount);
    event Withdrawal(address indexed user, uint256 amount);
    
    constructor() {
        owner = msg.sender;
    }
    
    function deposit() public payable {
        require(msg.value > 0, "Must deposit something");
        balances[msg.sender] += msg.value;
        emit Deposit(msg.sender, msg.value);
    }
    
    /**
     * @notice VULNERABILITY 1: Reentrancy
     * @dev External call before state update
     */
    function withdraw(uint256 amount) public {
        require(balances[msg.sender] >= amount, "Insufficient balance");
        
        // 🚨 BUG: External call BEFORE state update
        (bool success, ) = msg.sender.call{value: amount}("");
        require(success, "Transfer failed");
        
        // State update happens AFTER (allows reentrancy)
        balances[msg.sender] -= amount;
        emit Withdrawal(msg.sender, amount);
    }
    
    /**
     * @notice VULNERABILITY 2: Unchecked transfer
     * @dev No access control on emergencyWithdraw
     */
    function emergencyWithdraw(address to, uint256 amount) public {
        // �� BUG: Anyone can call this, no onlyOwner check
        payable(to).transfer(amount);
    }
    
    /**
     * @notice VULNERABILITY 3: Timestamp dependence
     * @dev Using block.timestamp for logic
     */
    function canWithdraw() public view returns (bool) {
        // 🚨 BUG: Miners can manipulate timestamp slightly
        return block.timestamp % 2 == 0;
    }
    
    function getBalance() public view returns (uint256) {
        return balances[msg.sender];
    }
    
    // Fallback to receive ETH
    receive() external payable {}
}
