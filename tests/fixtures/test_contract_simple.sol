// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract SimpleVulnerable {
    mapping(address => uint256) public balances;

    function deposit() public payable {
        balances[msg.sender] += msg.value;
    }

    // Reentrancy vulnerability: state update after external call
    function withdraw() public {
        uint256 amount = balances[msg.sender];

        // External call BEFORE state update (CEI violation!)
        (bool success, ) = msg.sender.call{value: amount}("");
        require(success, "Transfer failed");

        // State update AFTER external call
        balances[msg.sender] = 0;
    }

    // Unchecked low-level call
    function unsafeSend(address payable recipient, uint256 amount) public {
        recipient.call{value: amount}("");  // Return value not checked!
    }

    // Timestamp dependence
    function timeBasedReward() public view returns (uint256) {
        if (block.timestamp % 2 == 0) {
            return 100;
        }
        return 0;
    }
}
