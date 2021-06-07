// SPDX-License-Identifier: GPL-3.0

pragma solidity ^0.7.4;

contract EthPrice {
    mapping(string => uint256) currentPrice;

    function get(string calldata _coin) public view returns(uint256) {
        return currentPrice[_coin];
    }

    function set(string calldata _coin, uint256 _newPrice) public {
        currentPrice[_coin] = _newPrice;
    }
}