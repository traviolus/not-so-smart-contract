// SPDX-License-Identifier: GPL-3.0

pragma solidity ^0.7.4;

struct CoinInfo {
    uint256 requestId;
    uint256 currentPrice;
}

contract EthPrice {
    mapping(string => CoinInfo) coinPrice;

    function get(string calldata _coin) public view returns(uint256, uint256) {
        return (coinPrice[_coin].requestId, coinPrice[_coin].currentPrice);
    }

    function set(string calldata _coin, uint256 _requestId, uint256 _newPrice) public {
        coinPrice[_coin] = CoinInfo(_requestId, _newPrice);
    }
}