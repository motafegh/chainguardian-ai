// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * TEST 3: Complex But Safe
 * Expected: MEDIUM risk (40-60)
 * Challenge: High complexity but no vulnerabilities
 * Tests if model learned complexity = risk
 */
contract ComplexButSafe {
    struct User {
        address addr;
        uint256 balance;
        uint256 lastUpdate;
        bool isActive;
    }
    
    mapping(address => User) public users;
    mapping(address => mapping(address => uint256)) public allowances;
    address[] public userList;
    
    event UserRegistered(address indexed user);
    event BalanceUpdated(address indexed user, uint256 newBalance);
    event AllowanceSet(address indexed owner, address indexed spender, uint256 amount);
    
    modifier onlyActive() {
        require(users[msg.sender].isActive, "User not active");
        _;
    }
    
    modifier validAddress(address _addr) {
        require(_addr != address(0), "Invalid address");
        _;
    }
    
    function registerUser() external {
        require(!users[msg.sender].isActive, "Already registered");
        
        users[msg.sender] = User({
            addr: msg.sender,
            balance: 0,
            lastUpdate: block.timestamp,
            isActive: true
        });
        
        userList.push(msg.sender);
        emit UserRegistered(msg.sender);
    }
    
    function updateBalance(uint256 _amount) external onlyActive {
        users[msg.sender].balance = _amount;
        users[msg.sender].lastUpdate = block.timestamp;
        emit BalanceUpdated(msg.sender, _amount);
    }
    
    function setAllowance(address _spender, uint256 _amount) 
        external 
        onlyActive 
        validAddress(_spender) 
    {
        allowances[msg.sender][_spender] = _amount;
        emit AllowanceSet(msg.sender, _spender, _amount);
    }
    
    function getUserCount() external view returns (uint256) {
        return userList.length;
    }
    
    function getUser(address _addr) external view returns (User memory) {
        return users[_addr];
    }
    
    function getAllowance(address _owner, address _spender) 
        external 
        view 
        returns (uint256) 
    {
        return allowances[_owner][_spender];
    }
}
