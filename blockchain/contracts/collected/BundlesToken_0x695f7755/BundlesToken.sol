// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {ERC20} from "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import {IAntfarmToken} from "./interfaces/IAntfarmToken.sol";

contract BundlesToken is ERC20 {
    IAntfarmToken public immutable antfarmToken;

    error InvalidAddress();
    error ZeroAmount();

    event Migrated(address indexed account, uint256 value);

    constructor(address _antfarmToken) ERC20("Bundles Token", "BUN") {
        if (_antfarmToken == address(0)) revert InvalidAddress();
        antfarmToken = IAntfarmToken(_antfarmToken);
    }

    function migrate(uint256 _value) external {
        _migrate(msg.sender, _value);
    }

    function migrateFor(address _account, uint256 _value) external {
        _migrate(_account, _value);
    }

    function _migrate(address _account, uint256 _value) internal {
        if (_value == 0) {
            revert ZeroAmount();
        }
        antfarmToken.transferFrom(msg.sender, address(this), _value);
        antfarmToken.burn(_value);
        _mint(_account, _value);

        emit Migrated(_account, _value);
    }

    function burn(uint256 _value) external {
        _burn(msg.sender, _value);
    }
}
