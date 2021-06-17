#!/usr/bin/python

import sys, os;
import argparse;
from os.path import expanduser;
import pandas as pd;
import math;
from datetime import datetime as dt;
from datetime import timedelta;

__author__ = "Jeetesh Mangwani"

def main():
    parser = argparse.ArgumentParser(description="This script outputs realized & unrealized gains and losses, assest lots and adjusted cost basis");
    parser.add_argument("-th", "--tradehistory", type=str, help="The input xlsx file cotaining your Binance trade history", required=False, default = './trade-history.xlsx');
    parser.add_argument("-nh", "--normalizedhistory", type=str, help="The output xlsx file cotaining your normalized trade history", required=False, default = './trade-history-normalized.xlsx');
    parser.add_argument("-v", "--verbose", help="Whether to output verbose output messages", required=False, default=False);
    args = parser.parse_args();
    print("Input Buy History file: ", args.tradehistory);
    print("Output Normalized History file: ", args.normalizedhistory);
    print("Verbosity of log messages: ", args.verbose);

    tradeHistoryDfs = pd.read_excel(args.tradehistory, sheet_name="sheet1")

    outputDfs = pd.DataFrame({
        'dateTime': pd.Series([], dtype='str'),
        'asset': pd.Series([], dtype='str'),
        'type': pd.Series([], dtype='str'),
        'amount': pd.Series([], dtype='float'),
        'pricePerUnit': pd.Series([], dtype='float'),
        'totalCost': pd.Series([], dtype='float'),
        #'txnFee': pd.Series([], dtype='float'),
    })

    for index, row in tradeHistoryDfs.iterrows():
        #ts = int(row['UnixTimestamp'])
        #txnDateTime = dt.utcfromtimestamp(ts).isoformat()
        txnDateTime = dt.fromisoformat(str(row['Date(UTC)']))
        mainCoin, baseCoin = splitCoinPair(row['Market'])
        buyOrSell = str(row['Type'])

        if (buyOrSell == "BUY"):
            # bought main coin
            # sold base coin
            baseCoinPrice = float(row['Base Coin Unit Price'])
            mainCoinAmount = float(row['Amount'])
            mainCoinPrice = baseCoinPrice * float(row['Price'])
            totalCost = mainCoinAmount * mainCoinPrice
            baseCoinAmount = totalCost / baseCoinPrice

            outputDfs = outputDfs.append({
                'dateTime': txnDateTime,
                'asset': mainCoin,
                'type': 'BUY',
                'amount': mainCoinAmount,
                'pricePerUnit': mainCoinPrice,
                'totalCost': totalCost}, ignore_index=True);

            outputDfs = outputDfs.append({
                'dateTime': txnDateTime,
                'asset': baseCoin,
                'type': 'SELL',
                'amount': baseCoinAmount,
                'pricePerUnit': baseCoinPrice,
                'totalCost': totalCost}, ignore_index=True);
        elif (buyOrSell == "SELL"):
            # sold main coin
            # bought base coin
            baseCoinPrice = float(row['Base Coin Unit Price'])
            mainCoinAmount = float(row['Amount'])
            mainCoinPrice = baseCoinPrice * float(row['Price'])
            totalCost = mainCoinAmount * mainCoinPrice
            baseCoinAmount = totalCost / baseCoinPrice

            outputDfs = outputDfs.append({
                'dateTime': txnDateTime,
                'asset': mainCoin,
                'type': 'SELL',
                'amount': mainCoinAmount,
                'pricePerUnit': mainCoinPrice,
                'totalCost': totalCost}, ignore_index=True);

            outputDfs = outputDfs.append({
                'dateTime': txnDateTime,
                'asset': baseCoin,
                'type': 'BUY',
                'amount': baseCoinAmount,
                'pricePerUnit': baseCoinPrice,
                'totalCost': totalCost}, ignore_index=True);
        else:
            raise Exception("Invalid trade type:" + row)

    outputDfs = outputDfs.sort_values(by=['dateTime'])
    print(outputDfs);
    outputDfs.to_excel(args.normalizedhistory)

def splitCoinPair(coinPair):
    baseCoins = [
        "USDT",
        "BNB",
        "ETH",
        "USDC",
        "BTC",
        "BUSD"
    ];

    coinPair = str(coinPair);
    for baseCoin in baseCoins:
        if coinPair.endswith(baseCoin):
            mainCoin = coinPair.replace(baseCoin, "")
            return mainCoin, baseCoin

    raise Exception("Invalid coin pair: " + coinPair)
main();
