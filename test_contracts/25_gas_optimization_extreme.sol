// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * TEST 25: Extreme Gas Optimization
 * Expected: LOW-MEDIUM risk (20-50)
 * Challenge: Heavily optimized with assembly, packed storage
 * Tests: Does model panic at optimization patterns?
 */
contract GasOptimizationExtreme {
    // Packed storage
    uint128 public value1;
    uint128 public value2;
    
    function updateValues(uint128 _v1, uint128 _v2) external {
        assembly {
            // Pack both values into single SSTORE
            let packed := or(shl(128, _v1), _v2)
            sstore(0, packed)
        }
    }
    
    function getValues() external view returns (uint128, uint128) {
        assembly {
            let packed := sload(0)
            mstore(0x00, shr(128, packed))
            mstore(0x20, and(packed, 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF))
            return(0x00, 0x40)
        }
    }
}
