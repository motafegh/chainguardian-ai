// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * TEST 19: Flash Loan Attack Vector
 * Expected: MEDIUM-HIGH risk (50-80)
 * Challenge: Vulnerable to flash loan price manipulation
 * Tests: Can model understand composability risks?
 */
contract FlashLoanVulnerable {
    mapping(address => uint256) public balances;
    uint256 public totalSupply;
    
    function deposit() public payable {
        balances[msg.sender] += msg.value;
        totalSupply += msg.value;
    }
    
    // VULNERABILITY: Price based on instant reserves
    // Can be manipulated with flash loans
    function getSharePrice() public view returns (uint256) {
        if (totalSupply == 0) return 1e18;
        return (address(this).balance * 1e18) / totalSupply;
    }
    
    function withdraw(uint256 shares) public {
        uint256 ethAmount = (shares * address(this).balance) / totalSupply;
        
        balances[msg.sender] -= shares;
        totalSupply -= shares;
        
        payable(msg.sender).transfer(ethAmount);
    }
}
