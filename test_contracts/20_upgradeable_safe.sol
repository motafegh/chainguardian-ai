// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * TEST 20: Upgradeable Proxy (Safe Implementation)
 * Expected: LOW-MEDIUM risk (30-50)
 * Challenge: Uses delegatecall but safely
 * Tests: Can model distinguish safe vs unsafe delegatecall?
 */
contract UpgradeableSafe {
    address public implementation;
    address public admin;
    
    constructor(address _implementation) {
        implementation = _implementation;
        admin = msg.sender;
    }
    
    modifier onlyAdmin() {
        require(msg.sender == admin, "Not admin");
        _;
    }
    
    // SAFE: Admin-controlled upgrade
    function upgradeTo(address newImplementation) external onlyAdmin {
        implementation = newImplementation;
    }
    
    // SAFE: Fixed target (not user-controlled)
    fallback() external payable {
        address impl = implementation;
        assembly {
            calldatacopy(0, 0, calldatasize())
            let result := delegatecall(gas(), impl, 0, calldatasize(), 0, 0)
            returndatacopy(0, 0, returndatasize())
            
            switch result
            case 0 { revert(0, returndatasize()) }
            default { return(0, returndatasize()) }
        }
    }
}
