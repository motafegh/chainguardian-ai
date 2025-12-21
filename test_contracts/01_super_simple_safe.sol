// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * TEST 1: Super Simple Safe Contract
 * Expected: LOW risk score (<30)
 * Reason: No vulnerabilities, minimal code
 */
contract SuperSimpleSafe {
    uint256 public value;
    
    function setValue(uint256 _value) public {
        value = _value;
    }
    
    function getValue() public view returns (uint256) {
        return value;
    }
}
