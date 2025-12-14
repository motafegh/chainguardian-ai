// SPDX-License-Identifier: LGPL-3.0
pragma solidity 0.8.20;

import {ERC20} from '@openzeppelin/contracts/token/ERC20/ERC20.sol';
import {ERC20Burnable} from '@openzeppelin/contracts/token/ERC20/extensions/ERC20Burnable.sol';
import {ERC20Permit} from '@openzeppelin/contracts/token/ERC20/extensions/draft-ERC20Permit.sol';
import {Ownable2Step} from '@openzeppelin/contracts/access/Ownable2Step.sol';
import {AccessControl} from '@openzeppelin/contracts/access/AccessControl.sol';
import {Errors} from './helpers/Errors.sol';

/**
 * @title USDX
 * @notice Stable Coin Contract
 */
contract USDX is Ownable2Step, AccessControl, ERC20Burnable, ERC20Permit {
  bytes32 private constant MINTER_ROLE = keccak256('MINTER_ROLE');

  constructor(address _initialOwner) ERC20('USDX', 'USDX') ERC20Permit('USDX') {
    require(_initialOwner != address(0), Errors.ZERO_ADDRESS_NOT_VALID);
    _transferOwnership(_initialOwner);
  }

  function mint(address to, uint256 amount) external onlyRole(MINTER_ROLE) {
    _mint(to, amount);
  }

  function isMinter(address _minter) public view returns (bool) {
    return hasRole(MINTER_ROLE, _minter);
  }

  function addMinter(address _minter) external onlyOwner {
    _grantRole(MINTER_ROLE, _minter);
  }

  function removeMinter(address _minter) external onlyOwner {
    _revokeRole(MINTER_ROLE, _minter);
  }

  function renounceOwnership() public view override onlyOwner {
    revert(Errors.CANT_RENOUNCE_OWNERSHIP);
  }
}
