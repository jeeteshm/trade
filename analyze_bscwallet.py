#!/usr/bin/python

import sys, os;
import argparse;
from os.path import expanduser;
import pandas as pd;
import math;
from datetime import datetime as dt;

__author__ = "Jeetesh Mangwani"

class Trade(object):
    def __init__(self, asset, type, amount, pricePerUnit, totalCost):
        self.asset = asset;
        self.type = type;
        self.amount = amount;
        self.pricePerUnit = pricePerUnit;
        self.totalCost = totalCost;

def main():
    parser = argparse.ArgumentParser(description="This script outputs realized & unrealized gains and losses, assest lots and adjusted cost basis");
    parser.add_argument("-bh", "--bschistory", type=str, help="The input xlsx file cotaining your Binance buy history", required=False, default = './trade/bsc-history.xlsx');
    parser.add_argument("-nh", "--normalizedhistory", type=str, help="The output xlsx file cotaining your normalized trade history", required=False, default = './trade/normalized-history.xlsx');
    parser.add_argument("-v", "--verbose", help="Whether to output verbose output messages", required=False, default=False);
    args = parser.parse_args();
    print("Input BSC History file: ", args.bschistory);
    print("Output Normalized History file: ", args.normalizedhistory);
    print("Verbosity of log messages: ", args.verbose);

    bscHistoryDfs = pd.read_excel(args.bschistory, sheet_name="sheet1")
    asset = 'BNB';
    outputDfs = pd.DataFrame({
        'dateTime': pd.Series([], dtype='str'),
        'asset': pd.Series([], dtype='str'),
        'type': pd.Series([], dtype='str'),
        'amount': pd.Series([], dtype='float'),
        'pricePerUnit': pd.Series([], dtype='float'),
        'totalCost': pd.Series([], dtype='float'),
        'txnFee': pd.Series([], dtype='float'),
    })

    for index, row in bscHistoryDfs.iterrows():
        ts = int(row['UnixTimestamp'])
        txnDateTime = dt.utcfromtimestamp(ts).isoformat()
        amountBought = row['Value_IN(BNB)']
        amountSold = row['Value_OUT(BNB)']
        txnFee = row['TxnFee(USD)']
        usdPricePerUnit = row['Historical $Price/BNB']

        if (amountBought > 0 and math.isclose(amountSold, 0.0)):
            type = 'BUY'
            amount = amountBought;
            pricePerUnit = usdPricePerUnit;
            totalCost = amount * pricePerUnit;
            outputDfs = outputDfs.append({
                'dateTime': txnDateTime,
                'asset': asset,
                'type': type,
                'amount': amount,
                'pricePerUnit': pricePerUnit,
                'totalCost': totalCost,
                'txnFee': txnFee}, ignore_index=True);
        elif (math.isclose(amountBought, 0.0) and amountSold > 0):
            type = 'SELL'
            amount = amountSold;
            pricePerUnit = usdPricePerUnit;
            totalCost = amount * pricePerUnit;
            outputDfs = outputDfs.append({
                'dateTime': txnDateTime,
                'asset': asset,
                'type': type,
                'amount': amount,
                'pricePerUnit': pricePerUnit,
                'totalCost': totalCost,
                'txnFee': txnFee}, ignore_index=True);

    outputDfs.sort_values(by=['dateTime'])
    print(outputDfs);
    outputDfs.to_excel(args.normalizedhistory)
main();
