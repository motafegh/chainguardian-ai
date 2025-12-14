// SPDX-License-Identifier: MIT
pragma solidity 0.8.23;
interface IStreamerInuToken {
    /// @dev Emits when the contract owner set new percent of taxes
    event SetTaxPercent(uint256 _newTaxPercent);
    /// @dev Emits when the contract owner set SI/USDC pair
    event SetPair(address _pairAddress);
    /// @dev Emits when the contract owner set new address of SiVault contract
    event SetSiVault(address _newSiVault);
    /// @dev Throws if owner pass zero address
    error ZeroAddress();
    /// @dev Throws if owner pass zero value
    error ZeroValue();
    /// @dev Throws if owner pass tax percent which is greater then 5%
    error WrongTaxPercent();
    /// @dev Throws if passed address doesn't support IStreamerInuVault interface
    error WrongSiVault();
    /// @dev Throws if not owner tries to transfer token
    error IsPaused();
    /// @dev Throws if owner try to set SI/USDC pair second time
    error PairInitialized();
    function setTaxPercent(uint256 _taxPercent) external;
    function setPair(address _pairAddress) external;
    function setSiVault(address _siVault) external;
}
