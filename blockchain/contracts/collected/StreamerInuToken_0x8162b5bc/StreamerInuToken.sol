// SPDX-License-Identifier: MIT
pragma solidity 0.8.23;

import {OFTV2} from "@layerzerolabs/solidity-examples/contracts/token/oft/v2/OFTV2.sol";
import {IERC165} from "@openzeppelin/contracts/utils/introspection/IERC165.sol";
import {IStreamerInuToken} from "./interfaces/IStreamerInuToken.sol";
import {IStreamerInuVault} from "./interfaces/IStreamerInuVault.sol";
/// @title StreamerInu OFT token
contract StreamerInuToken is OFTV2, IStreamerInuToken {
    /// @dev Stores ID of Ethereum chain
    uint256 public constant MINT_CHAIN_ID = 1;
    /// @dev Uses for calculation of tax amount
    uint256 public constant PRECISION = 1 * 10 ** 18;
    /// @dev Stores max tax percent which equals 40%
    /// The percent is use for taxing first 24h after deploy
    uint256 public constant MAX_TAX_PERCENT = 4 * 10 ** 17;
    /// @dev Stores address of Uniswap V3 Pool of STRM and USDC tokens;
    address public siUsdcPair;
    /// @dev Stores current tax percent, can be in range from 0% to 5%
    uint256 public taxPercent;
    /// @dev Stores address of taxes recipient SC, should be StreamerInuVault
    /// and implement IStreamerInuVault interface
    address public siVault;
    /// @dev Stores state of tradable state
    /// When false - only owner can transfer token
    /// After first set true, becames immutable
    bool public isTradable;
    constructor(
        string memory _name,
        string memory _symbol,
        uint8 _sharedDecimals,
        address _lzEndpoint,
        address _recipient
    ) OFTV2(_name, _symbol, _sharedDecimals, _lzEndpoint) {
        if (getChainId() == MINT_CHAIN_ID) {
            if (_recipient == address(0)) {
                revert ZeroAddress();
            }
            _mint(_recipient, 1_500_000_000 ether);
        }
    }

    /// @notice Set new tax percent
    /// @dev only owner can call the function
    /// tax percent must be in range [0% - 5%]
    /// @param _taxPercent percent of tax
    function setTaxPercent(uint256 _taxPercent) external onlyOwner {
        if (_taxPercent > MAX_TAX_PERCENT) {
            revert WrongTaxPercent();
        }
        taxPercent = _taxPercent;
        emit SetTaxPercent(_taxPercent);
    }
    /// @notice Set data of SI/USDC pair
    /// @dev only owner can call the function
    /// @param _pairAddress address of SI/USDC pair of Uniswap V3
    function setPair(address _pairAddress) external onlyOwner {
        if (_pairAddress == address(0)) {
            revert ZeroAddress();
        }
        if(siUsdcPair != address(0)){
            revert PairInitialized();
        }
        siUsdcPair = _pairAddress;
        emit SetPair(_pairAddress);
    }

    /// @notice Set new address of StreamerInuVault
    /// @dev only owner can call the function
    /// if passed address doesn't support 
    /// IStreamerInuVault interface, then revert
    /// @param _siVault new address of SiVault
    function setSiVault(address _siVault) external onlyOwner {
        _setSiVault(_siVault);
    }

    /// @notice Turn on transfer ability to all users
    /// @dev only owner can call the function
    function turnOnTrading() external onlyOwner{
        isTradable = true;
    }

    /// @notice Return chaind id of current network
    function getChainId() public view returns (uint256) {
        uint256 chainId;
        // solhint-disable-next-line no-inline-assembly
        assembly {
            chainId := chainid()
        }
        return chainId;
    }

    function _transfer(
        address from,
        address to,
        uint256 amount
    ) internal override {
        if(!isTradable && from!=owner() && from != address(0)){
            revert IsPaused();
        }
        // the if statement prevent blocking of transfer function
        // if some of the params haven't set
        if(siUsdcPair == address(0) || siVault == address(0)){
            super._transfer(from, to, amount);
        } else if (from == siUsdcPair) {
            uint256 tax = _getTaxAmount(amount);
            if (tax != 0) {
                super._transfer(from, siVault, tax);
                IStreamerInuVault(siVault).receiveTax(tax);
            }
            super._transfer(from, to, amount - tax);
        } else {
            super._transfer(from, to, amount);
        }
    }

    function _setSiVault(address _siVault) internal{
        if (_siVault == address(0)) {
            revert ZeroAddress();
        }
        if(!IERC165(_siVault).supportsInterface(type(IStreamerInuVault).interfaceId)){
            revert WrongSiVault();
        }
        siVault = _siVault;
        emit SetSiVault(_siVault);
    }

    function _getTaxAmount(uint256 _amountIn) internal view returns (uint256) {
        uint256 percent = taxPercent;
        if (percent == 0) {
            return 0;
        } else {
            return (((_amountIn * percent * PRECISION) / PRECISION) /
                PRECISION);
        }
    }
}
