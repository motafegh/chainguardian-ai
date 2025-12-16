/*

#####################################
Token generated with ❤️ on 20lab.app
#####################################

*/


// SPDX-License-Identifier: No License
pragma solidity 0.8.25;

import {IERC20, ERC20} from "./ERC20.sol";
import {ERC20Burnable} from "./ERC20Burnable.sol";
import {Ownable, Ownable2Step} from "./Ownable2Step.sol";
import {SafeERC20Remastered} from "./SafeERC20Remastered.sol";

import {Initializable} from "./Initializable.sol";
import "./IUniswapV2Factory.sol";
import "./IUniswapV2Pair.sol";
import "./IUniswapV2Router01.sol";
import "./IUniswapV2Router02.sol";

contract Knuxx_Bully_Of_ETH is ERC20, ERC20Burnable, Ownable2Step, Initializable {
    
    using SafeERC20Remastered for IERC20;
 
    mapping (address => bool) public blacklisted;

    IUniswapV2Router02 public routerV2;
    address public pairV2;
    mapping (address => bool) public AMMs;

    mapping (address => bool) public isExcludedFromLimits;

    uint256 public maxWalletAmount;

    uint256 public maxBuyAmount;
    uint256 public maxSellAmount;

    mapping (address => uint256) public lastTrade;
    uint256 public tradeCooldownTime;

    bool public tradingEnabled;
    mapping (address => bool) public isExcludedFromTradingRestriction;
 
    error InvalidToken(address tokenAddress);

    error TransactionBlacklisted(address from, address to);

    error InvalidAMM(address AMM);

    error MaxWalletAmountTooLow(uint256 maxWalletAmount, uint256 limit);
    error CannotExceedMaxWalletAmount(uint256 maxWalletAmount);

    error MaxTransactionAmountTooLow(uint256 maxAmount, uint256 limit);
    error CannotExceedMaxTransactionAmount(uint256 maxAmount);

    error InvalidTradeCooldownTime(uint256 tradeCooldownTime);
    error AddressInCooldown(address account);

    error TradingAlreadyEnabled();
    error TradingNotEnabled();
 
    event BlacklistUpdated(address indexed account, bool isBlacklisted);

    event RouterV2Updated(address indexed routerV2);
    event AMMUpdated(address indexed AMM, bool isAMM);

    event ExcludeFromLimits(address indexed account, bool isExcluded);

    event MaxWalletAmountUpdated(uint256 maxWalletAmount);

    event MaxBuyAmountUpdated(uint256 maxBuyAmount);
    event MaxSellAmountUpdated(uint256 maxSellAmount);

    event TradeCooldownTimeUpdated(uint256 tradeCooldownTime);

    event TradingEnabled();
    event ExcludeFromTradingRestriction(address indexed account, bool isExcluded);
 
    constructor()
        ERC20(unicode"Knuxx Bully Of ETH", unicode"KNUXX")
        Ownable(msg.sender)
    {
        assembly { if iszero(extcodesize(caller())) { revert(0, 0) } }
        address supplyRecipient = 0xdB2a4BB1E73DFaAFEd5508FcD161Ca6607a6D94d;
        
        _excludeFromLimits(supplyRecipient, true);
        _excludeFromLimits(address(this), true);
        _excludeFromLimits(address(0), true); 

        updateMaxWalletAmount(44444000000000 * (10 ** decimals()) / 10);

        updateMaxBuyAmount(22222200000000 * (10 ** decimals()) / 10);
        updateMaxSellAmount(22222200000000 * (10 ** decimals()) / 10);

        updateTradeCooldownTime(3600);

        excludeFromTradingRestriction(supplyRecipient, true);
        excludeFromTradingRestriction(address(this), true);

        _mint(supplyRecipient, 44000000000000000 * (10 ** decimals()) / 10);
        _transferOwnership(0xdB2a4BB1E73DFaAFEd5508FcD161Ca6607a6D94d);
    }
    
    /*
        This token is not upgradeable. Function afterConstructor finishes post-deployment setup.
    */
    function afterConstructor(address _router) initializer external {
        _updateRouterV2(_router);
    }

    function decimals() public pure override returns (uint8) {
        return 18;
    }
    
    function recoverToken(uint256 amount) external onlyOwner {
        _update(address(this), msg.sender, amount);
    }

    function recoverForeignERC20(address tokenAddress, uint256 amount) external onlyOwner {
        if (tokenAddress == address(this)) revert InvalidToken(tokenAddress);

        IERC20(tokenAddress).safeTransfer(msg.sender, amount);
    }

    function blacklist(address account, bool isBlacklisted) external onlyOwner {
        blacklisted[account] = isBlacklisted;

        emit BlacklistUpdated(account, isBlacklisted);
    }

    function _updateRouterV2(address router) private {
        routerV2 = IUniswapV2Router02(router);
        pairV2 = IUniswapV2Factory(routerV2.factory()).createPair(address(this), routerV2.WETH());

        _approve(address(this), router, type(uint256).max);
        _setAMM(router, true);
        _setAMM(pairV2, true);

        emit RouterV2Updated(router);
    }

    function setAMM(address AMM, bool isAMM) external onlyOwner {
        if (AMM == pairV2 || AMM == address(routerV2)) revert InvalidAMM(AMM);

        _setAMM(AMM, isAMM);
    }

    function _setAMM(address AMM, bool isAMM) private {
        AMMs[AMM] = isAMM;

        if (isAMM) { 
            _excludeFromLimits(AMM, true);

        }

        emit AMMUpdated(AMM, isAMM);
    }

    function excludeFromLimits(address account, bool isExcluded) external onlyOwner {
        _excludeFromLimits(account, isExcluded);
    }

    function _excludeFromLimits(address account, bool isExcluded) internal {
        isExcludedFromLimits[account] = isExcluded;

        emit ExcludeFromLimits(account, isExcluded);
    }

    function updateMaxWalletAmount(uint256 _maxWalletAmount) public onlyOwner {
        if (_maxWalletAmount < _maxWalletSafeLimit()) revert MaxWalletAmountTooLow(_maxWalletAmount, _maxWalletSafeLimit());

        maxWalletAmount = _maxWalletAmount;
        
        emit MaxWalletAmountUpdated(_maxWalletAmount);
    }

    function _maxWalletSafeLimit() private view returns (uint256) {
        return totalSupply() / 1000;
    }

    function _maxTxSafeLimit() private view returns (uint256) {
        return totalSupply() * 5 / 10000;
    }

    function updateMaxBuyAmount(uint256 _maxBuyAmount) public onlyOwner {
        if (_maxBuyAmount < _maxTxSafeLimit()) revert MaxTransactionAmountTooLow(_maxBuyAmount, _maxTxSafeLimit());

        maxBuyAmount = _maxBuyAmount;
        
        emit MaxBuyAmountUpdated(_maxBuyAmount);
    }

    function updateMaxSellAmount(uint256 _maxSellAmount) public onlyOwner {
        if (_maxSellAmount < _maxTxSafeLimit()) revert MaxTransactionAmountTooLow(_maxSellAmount, _maxTxSafeLimit());

        maxSellAmount = _maxSellAmount;
        
        emit MaxSellAmountUpdated(_maxSellAmount);
    }

    function updateTradeCooldownTime(uint256 _tradeCooldownTime) public onlyOwner {
        if (_tradeCooldownTime > 12 hours) revert InvalidTradeCooldownTime(_tradeCooldownTime);
            
        tradeCooldownTime = _tradeCooldownTime;
        
        emit TradeCooldownTimeUpdated(_tradeCooldownTime);
    }

    function enableTrading() external onlyOwner {
        if (tradingEnabled) revert TradingAlreadyEnabled();

        tradingEnabled = true;
        
        emit TradingEnabled();
    }

    function excludeFromTradingRestriction(address account, bool isExcluded) public onlyOwner {
        isExcludedFromTradingRestriction[account] = isExcluded;
        
        emit ExcludeFromTradingRestriction(account, isExcluded);
    }


    function _update(address from, address to, uint256 amount)
        internal
        override
    {
        _beforeTokenUpdate(from, to, amount);
        
        super._update(from, to, amount);
        
        _afterTokenUpdate(from, to, amount);
        
    }

    function _beforeTokenUpdate(address from, address to, uint256 amount)
        internal
        view
    {
        if (blacklisted[from] || blacklisted[to]) revert TransactionBlacklisted(from, to);

        if (AMMs[from] && !isExcludedFromLimits[to] && amount > maxBuyAmount) { // BUY
            revert CannotExceedMaxTransactionAmount(maxBuyAmount);
        }
    
        if (AMMs[to] && !isExcludedFromLimits[from] && amount > maxSellAmount) { // SELL
            revert CannotExceedMaxTransactionAmount(maxSellAmount);
        }
    
        if(!isExcludedFromLimits[from] && lastTrade[from] + tradeCooldownTime > block.timestamp) revert AddressInCooldown(from);
        if(!isExcludedFromLimits[to] && lastTrade[to] + tradeCooldownTime > block.timestamp) revert AddressInCooldown(to);

        // Interactions with DEX are disallowed prior to enabling trading by owner
        if (!tradingEnabled) {
            if ((AMMs[from] && !AMMs[to] && !isExcludedFromTradingRestriction[to]) || (AMMs[to] && !AMMs[from] && !isExcludedFromTradingRestriction[from])) {
                revert TradingNotEnabled();
            }
        }

    }

    function _afterTokenUpdate(address from, address to, uint256 amount)
        internal
    {
        if (!isExcludedFromLimits[to] && balanceOf(to) > maxWalletAmount) {
            revert CannotExceedMaxWalletAmount(maxWalletAmount);
        }

        if (AMMs[from] && !isExcludedFromLimits[to]) lastTrade[to] = block.timestamp;
        else if (AMMs[to] && !isExcludedFromLimits[from]) lastTrade[from] = block.timestamp;

    }
}
