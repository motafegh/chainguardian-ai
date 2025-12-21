// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * TEST 23: Only Events (No State Changes)
 * Expected: VERY LOW risk (0-15)
 * Challenge: Contract that only emits events
 * Tests: Does model understand "no risk" contracts?
 */
contract OnlyEvents {
    event DataLogged(address indexed user, uint256 data);
    event MessageLogged(string message);
    
    function logData(uint256 data) public {
        emit DataLogged(msg.sender, data);
    }
    
    function logMessage(string memory message) public {
        emit MessageLogged(message);
    }
}
