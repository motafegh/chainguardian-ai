// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

interface IOracle {
    function getPrice() external view returns (uint256);
}

/**
 * TEST 18: Oracle Manipulation
 * Expected: HIGH risk (>70)
 * Challenge: Uses external oracle without validation
 * Tests: Can model detect DeFi-specific issues?
 */
contract OracleManipulation {
    IOracle public priceOracle;
    mapping(address => uint256) public collateral;
    mapping(address => uint256) public debt;
    
    constructor(address _oracle) {
        priceOracle = IOracle(_oracle);
    }
    
    function depositCollateral() public payable {
        collateral[msg.sender] += msg.value;
    }
    
    // VULNERABILITY: Single oracle without TWAP or validation
    function borrow(uint256 amount) public {
        uint256 price = priceOracle.getPrice();  // Can be manipulated!
        uint256 maxBorrow = (collateral[msg.sender] * price) / 1e18;
        
        require(debt[msg.sender] + amount <= maxBorrow, "Undercollateralized");
        
        debt[msg.sender] += amount;
        payable(msg.sender).transfer(amount);
    }
}
