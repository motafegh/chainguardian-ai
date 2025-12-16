// SPDX-License-Identifier: MIT
/*********************************************************************************************\
* Deployyyyer Memes: https://deployyyyer.fun
* Deployyyyer: https://deployyyyer.io
* Twitter: https://x.com/deployyyyer
* Telegram: https://t.me/Deployyyyer
/*********************************************************************************************/

pragma solidity ^0.8.23; 
import {IStaking} from "../interfaces/IStaking.sol";
import {StakingPool} from "./StakingPool.sol";

library SafeCall {
    /**
     * @notice Perform a low level call without copying any returndata
     *
     * @param _target   Address to call
     * @param _gas      Amount of gas to pass to the call
     * @param _value    Amount of value to pass to the call
     * @param _calldata Calldata to pass to the call
     */
    function call(
        address _target,
        uint256 _gas,
        uint256 _value,
        bytes memory _calldata
    ) internal returns (bool) {
        bool _success;
        assembly {
            _success := call(
                _gas, // gas
                _target, // recipient
                _value, // ether value
                add(_calldata, 0x20), // inloc
                mload(_calldata), // inlen
                0, // outloc
                0 // outlen
            )
        }
        return _success;
    }
}


interface IHelper {
	function isValidRouter(address router) external view returns (bool);
}


interface IERC20 {
    function name() external view returns (string memory);

    function symbol() external view returns (string memory);

    function decimals() external view returns (uint8);

    function totalSupply() external view returns (uint256);

    function balanceOf(address _owner) external view returns (uint256 balance);

    function transferFrom(
        address _from,
        address _to,
        uint256 _value
    ) external returns (bool success);

    function transfer(address _to, uint256 _value) external returns (bool success);

    function approve(address _spender, uint256 _value) external returns (bool success);

    function allowance(address _owner, address _spender) external view returns (uint256 remaining);
    event Transfer(address indexed from, address indexed to, uint256 value);
    event Approval(address indexed ownerAddress, address indexed spender, uint256 value);
}

interface IUniswapV2Factory {
    function createPair(address tokenA, address tokenB) external returns (address pair);

}

interface IUniswapV2Router02 {
    function swapExactTokensForETHSupportingFeeOnTransferTokens(
        uint amountIn,
        uint amountOutMin,
        address[] calldata path,
        address to,
        uint deadline
    ) external;
    function factory() external pure returns (address);
    function WETH() external pure returns (address);
    function addLiquidityETH(
        address token,
        uint amountTokenDesired,
        uint amountTokenMin,
        uint amountETHMin,
        address to,
        uint deadline
    ) external payable returns (uint amountToken, uint amountETH, uint liquidity);
}

interface ITeamFinanceLocker {
    function lockToken(
        address _tokenAddress,
        address _withdrawalAddress,
        uint256 _amount,
        uint256 _unlockTime,
        bool _mintNFT, 
        address referrer
    ) external payable returns (uint256 _id);
}


/// @title DeployyyyerToken 
/// @notice Contains methods related to ERC20
/// @dev 
contract DeployyyyerToken is IERC20 {
    address owner_; 
    uint256 minLiq;
    uint256 lockerId;
    address teamFinanceLocker;

    mapping(address => bool)  isExTxLimit; //is excluded from transaction limit
    mapping(address => bool)  isExWaLimit; //is excluded from wallet limit
    mapping (address => uint256)  balances; //ERC20 balance
    mapping (address => mapping (address => uint256))  allowances; //ERC20 balance

    address payable taxWallet; //tax wallet for the token
    address payable deployyyyerCa; //deployyyyer contract address

    
    // Reduction Rules
    uint256  buyCount; 

    uint256 initTaxType; //0-time,1-buyCount,2-hybrid,3-none
    //interval*1, lastIntEnd+(interval*2), lastIntEnd+(interval*3)
    uint256 initInterval; //seconds 0-1 hour(if 1m: 1m, 3m, 6m, 10m)
    uint256 countInterval; //0-100 

    //current taxes
    uint256  taxBuy; 
    uint256  maxBuyTax; //40%
    uint256  minBuyTax; //0

    uint256  taxSell; 
    uint256  maxSellTax; //40%
    uint256  minSellTax; //0

    uint256  tradingOpened;

    // Token Information
    uint8   decimals_;
    uint256   tTotal;
    string   name_;
    string   symbol_;

    // Contract Swap Rules 
    uint256 lastSwapBlock;
    uint256 preventSwap; //50            
    uint256  taxSwapThreshold; //0.1%
    uint256  maxTaxSwap; //1%
    uint256  maxWallet; //1%
    uint256  maxTx;

    IUniswapV2Router02  uniswapV2Router;
    address  uniswapV2Pair;
    
    bool  tradingOpen; //true if liquidity pool is created
    bool  inSwap;
    bool  walletLimited;
    bool isFreeTier;
    bool isBurnt;
    bool isRetrieved;
    uint256 lockPeriod_;
    uint256 stakingShare;
    address stakingContract;

    uint256 lastSwap;


    bool liquidityOpen;
    uint256 halfLp;
    uint256 lpTax;
    event TradingEnabled(address pair, uint256 liq, uint256 lockPeriod, bool isBurnt, address router);
	event TaxMade(uint256 amount);
    event TaxGiven(uint256 amount);
    event StakingMade(uint256 amount);
    event ExternalLocked(uint256 id, uint256 lockPeriod);
    event OwnershipTransferred(address indexed previousOwner, address indexed newOwner);
    
    event IncreasedLimits(uint256 maxWallet, uint256 maxTx);
    event LockUpdated(uint256 ldays);
    event LockRetrieved();
    event SocialsSet(string telegram, string twitter, string website);
    event LpBurnt();
    event StakingLaunched(address stakingPool, address owner, uint256 share);
    event StakingShareIncreased(uint256 share);
    event StakingArgs(IStaking.StakingParams params);

    struct InitParams {
        address owner;
        address taxWallet;
        address teamFinanceLocker;
        uint256 minLiq; 
        uint256 supply;
        uint256 initTaxType; //0-time,1-buyCount,2-hybrid
        uint256 initInterval; //seconds 0-1 hour(if 1m: 1m, 3m, 6m, 10m)
        uint256 countInterval; //0-100 
        uint256  maxBuyTax; //40%
        uint256  minBuyTax; //0
        uint256  maxSellTax; //40%
        uint256  minSellTax; //0
        uint256 lpTax;
        uint256 maxWallet;
        uint256 maxTx;
        uint256 preventSwap;
        uint256 maxSwap;
        uint256 taxSwapThreshold;
        string  name;
        string  symbol;
        bool isFreeTier;
    }


    struct LPDetails {
        address pair;
        uint256 buycount;
        uint256 taxBuy;
        uint256 taxSell;
        uint256 lockDays;
        bool isBurnt;
        uint256 tradingOpened;
        bool walletLimited;
        address stakingContract; //address(0) backward comp
        uint256 stakingShare; //external lock id here
        uint256 maxTx;
        uint256 maxWallet;
        address router;
        address presale; //address(0) backward comp
    }

    //reentrancy lock
    modifier lockTheSwap {
        inSwap = true;
        _;
        inSwap = false;
    }

    /// @notice Constructor of Diamond Proxy for a launched token
    constructor(InitParams memory params) {
        owner_ = params.owner;
        emit OwnershipTransferred(address(0), owner_);
        teamFinanceLocker = params.teamFinanceLocker;
        // adding ERC165 data

        deployyyyerCa = payable(msg.sender);
 
        minLiq = params.minLiq;
        taxBuy = params.maxBuyTax; //20%
        maxBuyTax = params.maxBuyTax;
        minBuyTax = params.minBuyTax;

        taxSell = params.maxSellTax; //20%
        maxSellTax = params.maxSellTax;
        minSellTax = params.minSellTax;
        lpTax = params.lpTax;
        
        initTaxType = params.initTaxType;
        initInterval = params.initInterval;
        countInterval = params.countInterval;

        // Reduction Rules
        buyCount = 0; 
        isFreeTier = params.isFreeTier;
    

        // Token Information
        decimals_ = 18;

        taxWallet = payable(params.taxWallet);
        
        name_ = params.name;
        symbol_ = params.symbol;
        tTotal = params.supply;

        // Contract Swap Rules            
        taxSwapThreshold = params.taxSwapThreshold; //0.1%
        maxTaxSwap = params.maxSwap; //1%
        walletLimited = true;
        
        
        maxWallet = tTotal * params.maxWallet / 10000;  //1% (allow 1 - 100)
        maxTx = tTotal * params.maxTx / 10000;
        if (params.maxWallet == 10000 && params.maxTx == 10000) {
            walletLimited = false;
        }
        emit IncreasedLimits(params.maxWallet, params.maxTx);
        balances[address(this)] = tTotal;
        emit Transfer(address(0), address(this), tTotal);

        preventSwap = params.preventSwap;

    } 


    /// @notice Create liquidity pool and start trading for the token
    /// @dev
    function startTrading(uint256 lockPeriod, bool shouldBurn, address router) external payable  {
        require(msg.sender == owner_, "o");
        require(!tradingOpen, "1");
        require(address(this).balance >= minLiq, "2");
        if(!shouldBurn) {
            require(lockPeriod >= 14);
        } 
        
        tradingOpen = true;

        uint256 maxTxTemp = maxTx;
        uint256 maxWalletTemp = maxWallet;
        bool walletLimitedTemp = walletLimited;
        
        if(walletLimited == true) {
            maxTx = tTotal;
            maxWallet = tTotal;
            walletLimited = false;
        }
        

        isExTxLimit[address(this)] = true;
        isExTxLimit[owner_] = true;
        isExTxLimit[address(0x000000000000000000000000000000000000dEaD)] = true;

        isExWaLimit[address(this)] = true;
        isExWaLimit[owner_] = true;
        isExWaLimit[address(0x000000000000000000000000000000000000dEaD)] = true;
        
        //0x000000000000000000000000000000000000dEaD or address(0)
        address liqOwner = address(this);
        if(shouldBurn) {
            liqOwner = address(0);
            isBurnt = true;
        } else {
            lockPeriod_ = lockPeriod;
            isBurnt = false;
        }

        uint256 liqBalance = balances[address(this)];
        tradingOpened = block.timestamp;
        
        require(IHelper(deployyyyerCa).isValidRouter(router));
        uniswapV2Router = IUniswapV2Router02(router);
        allowances[address(this)][address(uniswapV2Router)] = tTotal;
        uniswapV2Pair = IUniswapV2Factory(uniswapV2Router.factory()).createPair(address(this), uniswapV2Router.WETH());
        isExWaLimit[address(uniswapV2Pair)] = true;
        isExTxLimit[address(uniswapV2Pair)] = true;
        isExTxLimit[address(uniswapV2Router)] = true;
        isExWaLimit[address(uniswapV2Router)] = true;
        
        
        emit TradingEnabled(uniswapV2Pair, address(this).balance, lockPeriod_, shouldBurn, address(uniswapV2Router));
        require(IERC20(uniswapV2Pair).approve(address(uniswapV2Router), type(uint).max), "3");
        
        uniswapV2Router.addLiquidityETH{value: address(this).balance}(address(this),liqBalance,0,0,liqOwner,block.timestamp+60);
        liquidityOpen = true;
        
        if(walletLimitedTemp == true) {
            maxTx = maxTxTemp;
            maxWallet = maxWalletTemp;
            walletLimited = true;
        }

    }

    function lockOnTeamFinance(uint256 lps, bool ref) external payable  {
        require(msg.sender ==  owner_ && isBurnt == false && isRetrieved == false && tradingOpen == true && lps >= 3600 * 24 * 14, "o");
        //require(isBurnt == false && isRetrieved == false && tradingOpen == true, "lt");
        //require(lps >= 3600 * 24 * 14, "ls");
        uint256 lpBalance = IERC20(uniswapV2Pair).balanceOf(address(this));
        IERC20(uniswapV2Pair).approve(teamFinanceLocker, lpBalance);
        lockerId = ITeamFinanceLocker(teamFinanceLocker).lockToken{value: msg.value}(uniswapV2Pair, msg.sender, lpBalance, block.timestamp + lps, false, ref?address(deployyyyerCa):address(0));
        isRetrieved = true;
        emit ExternalLocked(lockerId, lps);
        //emit ExternalLocked(lockPeriodSec);
    }

    /// @notice Burn the liquidity pool tokens of the token
    function burnLP() external  {
        require(msg.sender == owner_, "o");
        require(!isBurnt && !isRetrieved && tradingOpen, "a"); 
        isBurnt = true;
        emit LpBurnt();
        require(IERC20(uniswapV2Pair).transfer(address(0x000000000000000000000000000000000000dEaD), IERC20(   uniswapV2Pair).balanceOf(address(this))), "o2");        
    }

    /// @notice Get lp lock period remaining
    /// @return lpldays lock days remaining 
    function getLockleft() private view returns (uint256) {
        if(!tradingOpen) {
            return 0;
        }
        //time traversed in days
        uint256 tt = ((block.timestamp - tradingOpened)/86400);
        if (tt > lockPeriod_) {
            return 0;
        } else {
            return lockPeriod_ - tt;
        }

    }
    
    /// @notice Extend LP lock
    /// @dev should not be already retrieved or burnt
    /// @param ldays no of days to extend
    function extendLock(uint256 ldays) external  {
        require(msg.sender == owner_, "o");
        require(!isRetrieved && !isBurnt && tradingOpen, "a");
        //expired lock 
        if((tradingOpened + (lockPeriod_*86400)) < block.timestamp) {
            lockPeriod_ = (block.timestamp - tradingOpened)/86400;
        }
        lockPeriod_ += ldays; 
        emit LockUpdated(lockPeriod_);
        
    }
    
    /// @notice Retrieve LP tokens
    /// @dev should not be already retrieved or burnt
    function retrieveLock() external  {
        require(msg.sender == owner_, "o");
        require(!isRetrieved && !isBurnt && tradingOpen, "a");
        if((tradingOpened + (lockPeriod_*60*60*24)) < block.timestamp) {
            isRetrieved = true;
            
            uint256 bal = IERC20(uniswapV2Pair).balanceOf(address(this));
            emit LockRetrieved();
            require(IERC20(uniswapV2Pair).transfer(msg.sender, bal), "b");
            
        }
    }

    function increaseLimits(uint256 maxwallet, uint256 maxtx) external {
        require(msg.sender ==  owner_ && walletLimited, "o");
        //require(walletLimited);
        require(tTotal * maxwallet / 10000 >= maxWallet && maxwallet <= 10000, "a");
        require(tTotal * maxtx / 10000 >= maxTx && maxtx <= 10000, "b");
        maxWallet = tTotal * maxwallet / 10000;   
        maxTx = tTotal * maxtx / 10000;
        
        if (maxwallet == 10000 && maxtx == 10000) {
            walletLimited = false;
        }

        emit IncreasedLimits(maxwallet, maxtx);
    }

    ///@dev Returns the name of the token.
    function name() external view override returns (string memory) {
        return name_;
    }

    ///@dev Returns the symbol of the token, usually a shorter version of name.
    function symbol() external view override returns (string memory) {
        return symbol_;
    }

    ///@dev Returns the number of decimals used to get its user representation.
    function decimals() external view override returns (uint8) {
        return decimals_;
    }

    ///@dev Returns the value of tokens in existence.
    function totalSupply() public view override returns (uint256) {
        return tTotal;
    }

    ///@dev Returns the value of tokens owned by account.
    function balanceOf(address account) public view override returns (uint256) {
        return balances[account];
    }

    ///@dev Moves a amount of tokens from the caller's account to receipient.
    function transfer(address recipient, uint256 amount) external override returns (bool) {
        _transfer(msg.sender, recipient, amount);
        return true;
    }

    ///@dev Returns the remaining number of tokens that `spender` will be
    // allowed to spend on behalf of `owner` through {transferFrom}. This is
    // zero by default
    function allowance(address owner, address spender) external view override returns (uint256) {
        return allowances[owner][spender];
    }

    /**
     * @dev Sets a `value` amount of tokens as the allowance of `spender` over the
     * caller's token   
     *
     * Returns a boolean value indicating whether the operation succeeded.
     *
     * IMPORTANT: Beware that changing an allowance with this method brings the risk
     * that someone may use both the old and the new allowance by unfortunate
     * transaction ordering. One possible solution to mitigate this race
     * condition is to first reduce the spender's allowance to 0 and set the
     * desired value afterwards:
     * https://github.com/ethereum/EIPs/issues/20#issuecomment-263524729
     *
     * Emits an {Approval} event.
     */
    function approve(address spender, uint256 amount) external override returns (bool) {
        _approve(msg.sender, spender, amount);
        return true;
    }

    /**
     * @dev Moves a `value` amount of tokens from `from` to `to` using the
     * allowance mechanism. `value` is then deducted from the caller's
     * allowance.
     *
     * Returns a boolean value indicating whether the operation succeeded.
     *
     * Emits a {Transfer} event.
     */
    function transferFrom(address sender, address recipient, uint256 amount) public override returns (bool) {
        require(amount <= allowances[sender][msg.sender], "25");
        _approve(sender, msg.sender,allowances[sender][msg.sender] - amount);
        _transfer(sender, recipient, amount);
        return true;
    }
    
    function _approve(address _owner, address _spender, uint256 _amount) private {
        require(_owner != address(0));
        require(_spender != address(0));
        allowances[_owner][_spender] = _amount;
        emit Approval(_owner, _spender, _amount);
    }

    /// @notice sets tax for the trade
    /// @dev 
    function _setTax(bool isBuy) private {
        uint256 maxTax;
        uint256 minTax;
        uint256 tax;
        if(isBuy) {
            maxTax = maxBuyTax;
            minTax = minBuyTax;
            tax = taxBuy;
        } else {
            maxTax = maxSellTax;
            minTax = minSellTax;
            tax = taxSell;
        }

        if(tax != minTax) {
            if(initTaxType == 0) {
                if (block.timestamp >= (tradingOpened + (initInterval))) {
                    tax = minTax; 
                }
                else if (block.timestamp >= (tradingOpened + (initInterval/2))) {
                    tax = minTax + (maxTax - minTax)/4;
                }
                else if (block.timestamp >= (tradingOpened + (initInterval/4))) {
                    tax = minTax + ((maxTax - minTax)/2);
                }
                else {       
                    tax = maxTax; 
                }        
                  
            } else if(initTaxType == 1) {
                if (buyCount > (countInterval)) {
                    tax = minTax; 
                } else {       
                    tax = maxTax; 
                } 
                //this is forced after 2hrs
                if(block.timestamp >= (tradingOpened + 7200)) {
                    tax = minTax;
                }      

            } else if(initTaxType == 2){
                if (buyCount > (countInterval) || block.timestamp >= (tradingOpened + (initInterval))) {
                    tax = minTax; 
                }
                else if (buyCount > (countInterval/2) || block.timestamp >= (tradingOpened + (initInterval/2))) {
                    tax = minTax + (maxTax - minTax)/4;
                }
                else if (buyCount > (countInterval/4) || block.timestamp >= (tradingOpened + (initInterval/4))) {
                    tax = minTax + ((maxTax - minTax)/2);
                }
                else {       
                    tax = maxTax; 
                }        
            // } else if(   initTaxType == 3) { //check block number}        
                
            } else {
                tax = minTax; 
            }

            if(isBuy) {
                   taxBuy = tax;
            } else {
                   taxSell = tax;
            }
        }

    }

    /// @notice internal method of transfer
    /// @dev 
    function _transfer(address from, address to, uint256 amount) private {
        require(from != address(0) && to != address(0));
        //require(to != address(0));
        //require(amount > 0); //compliance erc20
        require(balances[from] >= amount, "66");
        uint256 taxAmount=0;
        
        if (tradingOpen &&  walletLimited && !isExTxLimit[from] && !isExTxLimit[to])
            require(maxTx >= amount, "30");
        if (tradingOpen && walletLimited && !isExWaLimit[to])
            require((balances[to] + amount) <= maxWallet, "31");
         
        if (from != owner_ && to != owner_ && liquidityOpen == true) {
            if (from == uniswapV2Pair && to != address(uniswapV2Router)) {
            	//buy from uniswap, only if amount > 0
                buyCount++;
                _setTax(true);

            	taxAmount = amount * taxBuy / 100;
                //console.log("_setTaxDone");
                
                
            }
            if(to == uniswapV2Pair && from!= address(this)) {
            	//sell from uniswap
                _setTax(false);
                taxAmount = amount * taxSell / 100;    
            }
        }

        uint256 contractTokenBalance = balanceOf(address(this));
        bool swapped = false;
        if (!inSwap && to == uniswapV2Pair && from!= address(this) && contractTokenBalance > 0 && buyCount > preventSwap) {
            //we swap only on sell to uniswap pool
            if(contractTokenBalance > taxSwapThreshold || ((block.timestamp - tradingOpened) > (86400) && minBuyTax == 0 && minSellTax == 0)) {
                if(block.number > lastSwapBlock) {
                    if(contractTokenBalance < maxTaxSwap) {
                        swapTokensForEth(contractTokenBalance);
                    }
                    else {
                        swapTokensForEth(maxTaxSwap);
                    }
                    sendETHToFee(address(this).balance);
                    swapped = true;
                    lastSwapBlock = block.number;
                }
            }
        }

        if(taxAmount > 0) {
            balances[address(this)] = balances[address(this)] + (taxAmount);
            emit Transfer(from, address(this), taxAmount);
        }

        //from can be taxWallet
        balances[from] = balances[from] - amount;
        balances[to] = balances[to] + amount - taxAmount;
        emit Transfer(from, to, amount - taxAmount);
        
        if(swapped) {
            //everything else is taken care, anything left is for token's tax wallet
            //this call needs to be safe from reverts, consuming all gas and return bombs
            bool ttax = SafeCall.call(taxWallet, 100000, address(this).balance, "");
            if(ttax)
                emit TaxMade(address(this).balance);
        }

    }

    /// @notice swaps tokens from tax into eth
    /// @dev this is nonrentrant using lockTheSwap
    function swapTokensForEth(uint256 tokenAmount) private lockTheSwap {
        address[] memory path = new address[](2);
        path[0] = address(this);
        path[1] = uniswapV2Router.WETH();

        if(lpTax > 0) { 
            halfLp = tokenAmount * lpTax / 200;  
            tokenAmount -= halfLp; 
            lastSwap = tokenAmount;
        }

        _approve(address(this), address(uniswapV2Router), tokenAmount);
           uniswapV2Router.swapExactTokensForETHSupportingFeeOnTransferTokens(
            tokenAmount,
            0,
            path,
            address(this),
            block.timestamp
        );
    }

    /// @notice sends the eth to respective tax wallets 
    /// @dev 
    function sendETHToFee(uint256 amount) private {  
        uint256 da = 0;
        uint256 ethLpShare = 0;
        uint256 spshare = 0;
        uint256 halfLpTemp;
        //s.isFreeTier && 
        if(isFreeTier == true && ((block.timestamp - tradingOpened) < (86400*90))) {     
            da = amount * 10 / 100;
            emit TaxGiven(da);
            (bool stax, ) =  deployyyyerCa.call{value: da}("");
            require(stax, "99");
        }
        if(lpTax > 0 && halfLp > 0) {
            //newly added liquidity is also locked
            //address liqOwner = address(this);
            
            //we should also be keeping half of lp in tokens, so that u add equal amount of eth and token to lp
            ethLpShare = halfLp * amount / lastSwap;
            halfLpTemp = halfLp;
            halfLp = 0;
            lastSwap = 0;
            _approve(address(this), address(uniswapV2Router), halfLpTemp);
            uniswapV2Router.addLiquidityETH{ value: ethLpShare }(
                address(this),
                halfLpTemp,
                0,
                0,
                address(this),
                block.timestamp + 60
            );

            
        }
        if(stakingContract != address(0)) {
            spshare = (amount - da - ethLpShare) * stakingShare / 100;
            //stakingContract is safe since its our own! 
            (bool sent, ) = stakingContract.call{value: spshare}("");
            require(sent, "s9");
            emit StakingMade(spshare);
        }
    }

    /// @notice recovers eth to tax wallet if any
    /// @dev 
    function recoverEth() private {
        //blocked while trading is disabled
        if(!inSwap && tradingOpen) { 
            uint256 contractETHBalance = address(this).balance;
            if(contractETHBalance > 0) {
                sendETHToFee(contractETHBalance);
                (bool ttax, ) = taxWallet.call{value: address(this).balance}("");
                if(ttax)
                    emit TaxMade(address(this).balance);
            }
        }

    }

    /// @notice rescues any erc20 tokens sent to contract, also recovers eth to tax wallet if any
    /// @dev trying to rescue own token or own lp tokens will revert
    function rescueERC20(address _address) external {
        //block pulling out lp
        require(_address != uniswapV2Pair); 
        require(_address != address(this));
        
        require(IERC20(_address).transfer(taxWallet, IERC20(_address).balanceOf(address(this))), "r");
        recoverEth();
    }
    
    /// @notice Set the address of the new owner of the contract
    /// @param _newOwner The address of the new owner of the contract
    function transferOwnership(address _newOwner) external {
        require(msg.sender == owner_, "o");
        emit OwnershipTransferred(owner_, _newOwner);
        //isExTxLimit[owner_] = false;
        //isExWaLimit[owner_] = false;
        owner_ = _newOwner;
        isExTxLimit[owner_] = true;
        isExWaLimit[owner_] = true;
        
    }
    
    /// @notice Get the address of the owner
    /// @return The address of the owner.
    function owner() public view returns (address) {
        //address _owner = owner_;
        return owner_;
    }
    

    /// @notice Get liquidity pool details of the token
    /// @return IOwnership.LPDetails
    /// @dev 
    function getLPDetails() external view returns (LPDetails memory) {
        return LPDetails(uniswapV2Pair, buyCount, taxBuy, taxSell, getLockleft(), isBurnt, tradingOpened, walletLimited, stakingContract, stakingShare, maxTx, maxWallet, address(uniswapV2Router), address(0));
    }


    /// @notice increase revenue share to staking pool for the token
    /// @dev 
    function increaseStakingShare(uint256 share) external {
        require(msg.sender == owner_ && stakingShare > 0 && share > 0, "o");
        //staking pool is live
        //require(stakingShare > 0 && share > 0);
        stakingShare += share;
        require(stakingShare <= 100, "os");
        emit StakingShareIncreased(stakingShare);
    }

    /// @notice launch staking pool for the token
    /// @dev 
    function launchStaking(uint256 share, IStaking.StakingParams memory params) external {
        require(msg.sender == owner_, "o");
        require(stakingShare == 0 && share > 0 && share <= 100, "y");
        //require(stakingShare == 0, "o12");
        require(params.withdrawTimeout >= 2 days && params.withdrawTimeout < 10 days, "z");
        stakingShare = share;
        params.owner = msg.sender;
        
        StakingPool stakingPool = new StakingPool(params);
        isExTxLimit[address(stakingPool)] = true;
        isExWaLimit[address(stakingPool)] = true;
        emit StakingLaunched(address(stakingPool), msg.sender, stakingShare);
        emit StakingArgs(params);
        stakingContract = payable(address(stakingPool));

    }
    
    /// @notice receive eth
    receive() external payable {}

}