// SPDX-License-Identifier: GPL-3.0

pragma solidity ^0.7.4;

contract EthPrice {
    string currentPrice;

    constructor() {
        currentPrice = "0";
    }

    function get() public view returns(string memory) {
        return currentPrice;
    }

    function set(string calldata _newPrice) public {
        currentPrice = _newPrice;
    }
}