// SPDX-License-Identifier: MIT
/*********************************************************************************************\
* Deployyyyer Memes: https://deployyyyer.fun
* Deployyyyer: https://deployyyyer.io
* Twitter: https://x.com/deployyyyer
* Telegram: https://t.me/Deployyyyer
/*********************************************************************************************/

pragma solidity ^0.8.23;

import "../interfaces/IStaking.sol";
import { IERC20 } from "../interfaces/IERC20.sol"; 

struct AppStorageStaking {
    address token;
    address owner;
    uint256 accRewardsPrecision;
    uint256 totalStakedAmount;
    uint256 withdrawTimeout;
    uint256 unallocatedETH;
    uint256 accRewardsPerShare;
    uint256 totalETHCollected;
    mapping(address => uint256) totalRewards;
    mapping(address => uint256) rewardDebt;
    mapping(address => uint256) stakedAmount;
    mapping(address => uint256) claimedAmount;
    mapping(address => uint256) claimableRewards;
    mapping(address => uint256) lastUnstakeTime;
    mapping(address => uint256) unstakedAmount;

}

contract Modifiers {
    AppStorageStaking internal s;
}
/// @title StakingPool
/// @dev 
contract StakingPool is IStaking, Modifiers {
    event Stake(address indexed user, uint256 amount);
    event Unstake(address indexed user, uint256 amount);
    event Withdraw(address indexed user, uint256 amount);
    event ClaimRewards(address indexed user, uint256 amount);
    event RewardsReceived(address indexed sender, uint256 amount, uint256 accRewardsPerShare);
    //event OwnershipTransferred(address indexed previousOwner, address indexed newOwner);

    constructor(IStaking.StakingParams memory params) {
        require(params.owner != address(0));
        s.owner = params.owner;
        //init appStorage 
        s.accRewardsPrecision = 1e18;  
        s.token = msg.sender;
        s.withdrawTimeout = params.withdrawTimeout;

    } 

    //tracking ownership in subgraph is not needed here, since ownership is unimportant
    /// @notice transfer ownership
    /// @dev
    function transferOwnership(address _newOwner) external override {
        require(msg.sender == s.owner);
        s.owner =  _newOwner;
    }
    
    /// @notice return owner address
    /// @dev
    function owner() external override view returns (address owner_) {
        owner_ = s.owner;
    }

    /// @notice rescue erc20 tokens from the contract
    /// @dev
    function rescueERC20(address _address) external {
        //only use of owner: as the rescue wallet! 
        bool ret = IERC20(_address).transfer(s.owner, IERC20(_address).balanceOf(address(this)));
        require(ret, "1");
    }

    /// @notice stake tokens
    /// @dev
    function stake(uint256 _amount) external override {
        uint256 pending = 0;
        require(_amount > 0);
        if (s.stakedAmount[msg.sender] > 0) {
            pending = ((s.stakedAmount[msg.sender] * s.accRewardsPerShare) / s.accRewardsPrecision) - s.rewardDebt[msg.sender];
        }

        uint256 unstakedAmount = s.unstakedAmount[msg.sender];
        if (unstakedAmount >= _amount) {
            s.unstakedAmount[msg.sender] -= _amount;
        } else {
            uint256 tokensNeeded = _amount - unstakedAmount;
            s.unstakedAmount[msg.sender] = 0;
            //requires staking contract to be approved by user
        	require(IERC20(s.token).transferFrom(msg.sender, address(this), tokensNeeded), "2");
        }
        
        s.stakedAmount[msg.sender] += _amount;
        s.rewardDebt[msg.sender] = s.stakedAmount[msg.sender] * s.accRewardsPerShare / s.accRewardsPrecision; 
        s.totalStakedAmount += _amount;

        if(pending > 0) {
            s.claimableRewards[msg.sender] += pending;
        }
        
        emit Stake(msg.sender, _amount);
    }

    /// @notice unstake staked tokens
    /// @dev
    function unstake(uint256 _amount) external override {
        require(_amount > 0 && s.stakedAmount[msg.sender] >= _amount, "3"); 
        uint256 pending = ((s.stakedAmount[msg.sender] * s.accRewardsPerShare) / s.accRewardsPrecision) - s.rewardDebt[msg.sender];
        s.stakedAmount[msg.sender] -= _amount;
        s.lastUnstakeTime[msg.sender] = block.timestamp;
        s.unstakedAmount[msg.sender] += _amount;

        s.rewardDebt[msg.sender] = s.stakedAmount[msg.sender] * s.accRewardsPerShare / s.accRewardsPrecision;
        s.totalStakedAmount -= _amount;

        if(pending > 0) {
            s.claimableRewards[msg.sender] += pending;
        }

        emit Unstake(msg.sender, _amount);
    }

    /// @notice restake unstaked tokens
    /// @dev
    function restake() external override {
        uint256 pending = 0;
        uint256 amountToRestake = s.unstakedAmount[msg.sender];
        require(amountToRestake > 0, "4"); 
        //allocateRewards();
        if (s.stakedAmount[msg.sender] > 0) {
            pending = ((s.stakedAmount[msg.sender] * s.accRewardsPerShare) / s.accRewardsPrecision) - s.rewardDebt[msg.sender];
        }

        s.unstakedAmount[msg.sender] = 0;
        s.stakedAmount[msg.sender] += amountToRestake;
        s.rewardDebt[msg.sender] = s.stakedAmount[msg.sender] * s.accRewardsPerShare / s.accRewardsPrecision;
        s.totalStakedAmount += amountToRestake;

        if(pending > 0) {
            s.claimableRewards[msg.sender] += pending;
        }
        emit Stake(msg.sender, amountToRestake);
    }

    /// @notice withdraw unstaked tokens
    /// @dev
    function withdraw() external override {
        uint256 toWithdraw = s.unstakedAmount[msg.sender];
        require(toWithdraw > 0, "5");
        require(block.timestamp >= s.lastUnstakeTime[msg.sender] + s.withdrawTimeout, "6");
        s.unstakedAmount[msg.sender] = 0;
        emit Withdraw(msg.sender, toWithdraw);
        require(IERC20(s.token).transfer(msg.sender, toWithdraw), "7");
        
    }

    /// @notice claim rewards in eth
    /// @dev
    function claimRewards() external override {
        s.claimableRewards[msg.sender] += ((s.stakedAmount[msg.sender] * s.accRewardsPerShare) / s.accRewardsPrecision) - s.rewardDebt[msg.sender];
        uint256 claimable = s.claimableRewards[msg.sender];
        require(claimable > 0, "8");
        s.rewardDebt[msg.sender] = s.stakedAmount[msg.sender] * s.accRewardsPerShare / s.accRewardsPrecision;
        uint256 amount = address(this).balance > claimable ? claimable : address(this).balance;
        s.claimableRewards[msg.sender] -= amount;
        s.claimedAmount[msg.sender] += amount; 
        emit ClaimRewards(msg.sender, amount);
        (bool sent,) = payable(msg.sender).call{value: amount}("");
        require(sent, "9");
        
    }
    
    /// @notice get details related to the user
    /// @dev
    function getUserDetails(address _user) external view returns (IStaking.StakingDetails memory) {
    	uint256 withdrawable = 0;
    	uint256 timeToWithdraw = 0;
    	uint256 claimable = s.claimableRewards[_user] + ((s.stakedAmount[_user] * s.accRewardsPerShare) / s.accRewardsPrecision) - s.rewardDebt[_user];
    	
    	if (block.timestamp >= s.lastUnstakeTime[_user] + s.withdrawTimeout) {
            withdrawable = s.unstakedAmount[_user];
        } else {
        	timeToWithdraw = block.timestamp - s.lastUnstakeTime[_user] + s.withdrawTimeout;
        }

        return IStaking.StakingDetails(claimable, withdrawable, s.unstakedAmount[_user], s.totalRewards[_user], timeToWithdraw, s.stakedAmount[_user]);
    }

    /// @notice receive
    /// @dev staing rewards in eth, sets accRewardsPerShare
    receive() external payable {
        uint256 amount = msg.value;
        require(amount > 0, "r");
        s.totalRewards[msg.sender] += amount;
        s.totalETHCollected += amount;
        if (s.totalStakedAmount == 0) {
            s.unallocatedETH += amount;
        } else {
            s.accRewardsPerShare += ((amount+s.unallocatedETH) * s.accRewardsPrecision) / s.totalStakedAmount;  
            s.unallocatedETH = 0;         
        }
        emit RewardsReceived(msg.sender, amount, s.accRewardsPerShare);
    }

}