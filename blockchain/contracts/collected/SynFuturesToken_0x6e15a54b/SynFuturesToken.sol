// SPDX-License-Identifier: MIT
pragma solidity =0.8.19;

import  "@openzeppelin/contracts/token/ERC20/extensions/ERC20Permit.sol";

contract SynFuturesToken is ERC20Permit {
    uint public constant MAX_SUPPLY = 10_000_000_000 * (10 ** 18); // 10 billion F token with 18 decimals

    constructor(address vault) ERC20Permit('SynFutures') ERC20('SynFutures', 'F') {
        _mint(vault, MAX_SUPPLY);
    }
}

