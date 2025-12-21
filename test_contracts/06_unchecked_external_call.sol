// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * TEST 6: Unchecked External Call
 * Expected: HIGH risk (>70)
 * Reason: Doesn't check return value
 */
contract UncheckedExternalCall {
    function sendEther(address payable recipient) public payable {
        // VULNERABILITY: Return value not checked
        recipient.call{value: msg.value}("");
        // If call fails, function continues silently!
    }
    
    function sendEtherSafe(address payable recipient) public payable {
        // SAFE: Checks return value
        (bool success, ) = recipient.call{value: msg.value}("");
        require(success, "Transfer failed");
    }
}
