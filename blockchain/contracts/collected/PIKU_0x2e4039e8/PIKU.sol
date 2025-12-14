// SPDX-License-Identifier: GPL-3.0
pragma solidity 0.8.19;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Burnable.sol";
import "@openzeppelin/contracts/token/ERC20/extensions/draft-ERC20Permit.sol";
import "@openzeppelin/contracts/access/Ownable2Step.sol";
import "contracts/interfaces/IPikuDefinitions.sol";

/**
 * @title PIKU
 * @notice Stable Coin Contract
 * @dev Only a single approved minter can mint new tokens
 */
contract PIKU is Ownable2Step, ERC20Burnable, ERC20Permit, IPikuDefinitions {
  address public minter;

  constructor(address admin) ERC20("Piku Utility Token", "PIKU") ERC20Permit("Piku Utility Token") {
    _mint(admin, 500_000_000 * 10 ** decimals());
    if (admin == address(0)) revert ZeroAddressException();
    _transferOwnership(admin);
  }

  function renounceOwnership() public view override onlyOwner {
    revert CantRenounceOwnership();
  }
}
