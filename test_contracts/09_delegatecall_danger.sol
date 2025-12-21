// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * TEST 9: Delegatecall Vulnerability
 * Expected: HIGH risk (>70)
 * Reason: User-controlled delegatecall
 */
contract DelegatecallDanger {
    address public implementation;
    
    constructor(address _impl) {
        implementation = _impl;
    }
    
    // VULNERABILITY: User can control delegatecall target
    function execute(address target, bytes memory data) public {
        (bool success, ) = target.delegatecall(data);
        require(success, "Delegatecall failed");
    }
}
