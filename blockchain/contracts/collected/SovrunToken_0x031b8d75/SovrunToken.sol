// SPDX-License-Identifier: MIT
pragma solidity 0.8.23;

import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Votes.sol";
import "@openzeppelin/contracts/access/AccessControlEnumerable.sol";
import "@openzeppelin/contracts/utils/Context.sol";

import "./interfaces/ISovrunToken.sol";

/**
 * @title SovrunToken
 * @notice ERC20 token with access control and voting capabilities.
 * @dev This contract implements an ERC20 token with additional features
 *      such as role-based access control for minting and burning tokens,
 *      and support for snapshot voting via ERC20Votes.
 *
 * The contract uses OpenZeppelin's libraries for secure and efficient
 * token management and role management.
 *
 * Inherits from:
 * - Context: Provides information about the current execution context.
 * - AccessControlEnumerable: Enables role-based access control with enumeration.
 * - ERC20Votes: Implements voting functionality for token holders.
 * - ISovrunToken: Interface that defines the expected behavior of the SovrunToken contract,
 *              including minting and burning functions.
 */
contract SovrunToken is
    Context,
    AccessControlEnumerable,
    ERC20Votes,
    ISovrunToken
{
    bytes32 public constant MINTER_ROLE = keccak256("MINTER_ROLE");
    bytes32 public constant BURNER_ROLE = keccak256("BURNER_ROLE");

    error MissingRole(address account, bytes32 role);
    error TransferToContractNotAllowed(address attemptedAddress);
    error MintToContractNotAllowed(address attemptedAddress);
    error ZeroTransferNotAllowed();

    modifier onlyHasRole(bytes32 _role) {
        if (!hasRole(_role, _msgSender())) {
            revert MissingRole(_msgSender(), _role);
        }
        _;
    }

    constructor() ERC20Permit("SOVRUN") ERC20("SOVRUN", "SOVRN") {
        _setupRole(DEFAULT_ADMIN_ROLE, _msgSender());
    }

    /**
     * @notice Mints new tokens and assigns them to the specified address.
     * @dev Can only be called by an account with the MINTER_ROLE.
     * Emits a {Transfer} event indicating the amount of tokens minted.
     * It prevents minting tokens to the contract itself.
     *
     * @param _to The address to which the newly minted tokens will be assigned.
     * @param _amount The amount of tokens to mint.
     */
    function mint(
        address _to,
        uint256 _amount
    ) external override onlyHasRole(MINTER_ROLE) {
        if (_to == address(this)) revert MintToContractNotAllowed(_to);
        _mint(_to, _amount);
    }

    /**
     * @notice Burns a specified amount of tokens from a given address.
     * @dev Can only be called by an account with the BURNER_ROLE.
     * Emits a {Transfer} event indicating the amount of tokens burned.
     *
     * @param _from The address from which the tokens will be burned.
     * @param _amount The amount of tokens to burn.
     */
    function burn(
        address _from,
        uint256 _amount
    ) external override onlyHasRole(BURNER_ROLE) {
        _burn(_from, _amount);
    }

    /**
     * @notice Transfers tokens from one address to another.
     * @dev This function overrides the standard ERC20 transfer mechanism.
     *      It prevents transferring tokens to the contract itself.
     *      Reverts with a custom error if the recipient is the contract address and the amount transferred is zero.
     *
     * @param _from The address from which the tokens are being transferred.
     * @param _to The address to which the tokens are being transferred.
     * @param _amount The amount of tokens to transfer.
     */
    function _transfer(
        address _from,
        address _to,
        uint256 _amount
    ) internal override {
        if (_amount == 0) revert ZeroTransferNotAllowed();
        if (_to == address(this)) revert TransferToContractNotAllowed(_to);
        super._transfer(_from, _to, _amount);
    }
}
