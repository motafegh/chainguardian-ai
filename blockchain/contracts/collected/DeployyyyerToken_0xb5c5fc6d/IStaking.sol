// SPDX-License-Identifier: MIT
pragma solidity ^0.8.23;

interface IStaking {
    struct StakingParams {
            address owner;
            uint256 withdrawTimeout;
        }
    struct StakingDetails {
        uint256 claimable;
        uint256 withdrawable;
        uint256 unstakedAmount;
        uint256 totalRewards;
        uint256 timeToWithdraw;
        uint256 stakedAmount;
    }
    function transferOwnership(address _newOwner) external;
    function owner() external view returns (address);
    function rescueERC20(address _address) external;
    function stake(uint256 _amount) external;
    function unstake(uint256 _amount) external;
    function restake() external;
    function withdraw() external;
    function claimRewards() external;
    //function refreshPool() external;
    function getUserDetails(address) external view returns (StakingDetails memory);
}
