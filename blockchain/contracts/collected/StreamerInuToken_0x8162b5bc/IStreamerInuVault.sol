// SPDX-License-Identifier: MIT
pragma solidity 0.8.23;
interface IStreamerInuVault {
    /// @dev Emits when STRM token send token to the contract and 
    /// call function receiveTax
    event UpdatedTaxAmount(uint256 taxAmount);
    /// @dev Throws if owner pass zero address
    error ZeroAddress();
    /// @dev Throws if owner pass zero value
    error ZeroValue();
    /// @dev Throws if sender isn't STRM token
    error AccessDenied();
    /// @dev Throws if IERC20 approve function returns false
    error ApproveFailed();
    /// @dev Throws if contract doesn't have enough balance of token\
    /// to make transfer or swap action
    error NotEnoughBalance();
    function setRouter(address _newRouter) external;
    function setPairFee( uint24 _fee) external;
    function receiveTax(uint256 _amount) external;
    function sellSi(
        uint256 _amount,
        address _recipient,
        uint256 _amountOutMin
    ) external;
    function withdrawUnexpectedTokens(address _token,address _recipient, uint256 _amount) external;
}
