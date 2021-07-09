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
    parser = argparse.ArgumentParser(description="This script normalizes the bscscan.com wallet transactions history to a simpler format for other scripts to process.");
    parser.add_argument("-wa", "--walletaddress", type=str, help="Your BSC wallet address", required=False, default = '');
    parser.add_argument("-wt", "--wallettransactions", type=str, help="The input xlsx file cotaining your wallet transactions", required=False, default = './wallet-transactions.xlsx');
    parser.add_argument("-it", "--internaltransactions", type=str, help="The input xlsx file cotaining your wallet internal transactions", required=False, default = './internal-transactions.xlsx');
    parser.add_argument("-bt", "--bep20transactions", type=str, help="The input xlsx file cotaining your wallet BEP20 token transactions", required=False, default = './bep20-transactions.xlsx');
    parser.add_argument("-nh", "--normalizedhistory", type=str, help="The output xlsx file cotaining your normalized wallet transactions", required=False, default = './wallethistory-normalized.xlsx');
    parser.add_argument("-v", "--verbose", help="Whether to output verbose output messages", required=False, default=False);
    args = parser.parse_args();
    print("Wallet Address: ", args.walletaddress);
    print("Input Wallet Transactions file: ", args.wallettransactions);
    print("Input Wallet Internal Transactions file: ", args.internaltransactions);
    print("Input Wallet BEP20 Token Transactions file: ", args.bep20transactions);
    print("Output Normalized History file: ", args.normalizedhistory);
    print("Verbosity of log messages: ", args.verbose);

    walletTransactionsDfs = pd.read_excel(args.wallettransactions, sheet_name="sheet1")
    internalTransactionsDfs = pd.read_excel(args.internaltransactions, sheet_name="sheet1")
    bep20TransactionsDfs = pd.read_excel(args.bep20transactions, sheet_name="sheet1")

    outputDfs = pd.DataFrame({
        'dateTime': pd.Series([], dtype='str'),
        'asset': pd.Series([], dtype='str'),
        'type': pd.Series([], dtype='str'),
        'amount': pd.Series([], dtype='float'),
        'pricePerUnit': pd.Series([], dtype='float'),
        'totalCost': pd.Series([], dtype='float'),
        #'txnFee': pd.Series([], dtype='float'),
    })

    for index, row in walletTransactionsDfs.iterrows():
        #ts = int(row['UnixTimestamp'])
        #txnDateTime = dt.utcfromtimestamp(ts).isoformat()
        txnDateTime = dt.fromisoformat(str(row['DateTime']))
        asset = 'BNB'
        valueIn = float(row['Value_IN(BNB)'])
        valueOut = float(row['Value_OUT(BNB)'])
        pricePerUnit = float(row['Historical $Price/BNB'])

        if (valueIn > 0.0 and math.isclose(0.0, valueOut)):
            buyOrSell = 'BUY'
        elif (valueOut > 0.0 and math.isclose(0.0, valueIn)):
            buyOrSell = 'SELL'
        elif (math.isclose(0.0, valueIn) and math.isclose(0.0, valueOut)):
            continue;
        else:
            raise Exception('Invalid row: ' + row)

        if (buyOrSell == "BUY"):
            totalCost = valueIn
            amount = totalCost / pricePerUnit

            outputDfs = outputDfs.append({
                'dateTime': txnDateTime,
                'asset': asset,
                'type': 'BUY',
                'amount': amount,
                'pricePerUnit': pricePerUnit,
                'totalCost': totalCost}, ignore_index=True);
        elif (buyOrSell == "SELL"):
            totalCost = valueOut
            amount = totalCost / pricePerUnit

            outputDfs = outputDfs.append({
                'dateTime': txnDateTime,
                'asset': asset,
                'type': 'SELL',
                'amount': amount,
                'pricePerUnit': pricePerUnit,
                'totalCost': totalCost}, ignore_index=True);
        else:
            raise Exception("Invalid trade type:" + row)

    for index, row in internalTransactionsDfs.iterrows():
        #ts = int(row['UnixTimestamp'])
        #txnDateTime = dt.utcfromtimestamp(ts).isoformat()
        txnDateTime = dt.fromisoformat(str(row['DateTime']))
        asset = 'BNB'
        valueIn = float(row['Value_IN(BNB)'])
        valueOut = float(row['Value_OUT(BNB)'])
        pricePerUnit = float(row['Historical $Price/BNB'])

        if (valueIn > 0.0 and math.isclose(0.0, valueOut)):
            buyOrSell = 'BUY'
        elif (valueOut > 0.0 and math.isclose(0.0, valueIn)):
            buyOrSell = 'SELL'
        elif (math.isclose(0.0, valueIn) and math.isclose(0.0, valueOut)):
            continue;
        else:
            raise Exception('Invalid row: ' + row)

        if (buyOrSell == "BUY"):
            totalCost = valueIn
            amount = totalCost / pricePerUnit

            outputDfs = outputDfs.append({
                'dateTime': txnDateTime,
                'asset': asset,
                'type': 'BUY',
                'amount': amount,
                'pricePerUnit': pricePerUnit,
                'totalCost': totalCost}, ignore_index=True);
        elif (buyOrSell == "SELL"):
            totalCost = valueOut
            amount = totalCost / pricePerUnit

            outputDfs = outputDfs.append({
                'dateTime': txnDateTime,
                'asset': asset,
                'type': 'SELL',
                'amount': amount,
                'pricePerUnit': pricePerUnit,
                'totalCost': totalCost}, ignore_index=True);
        else:
            raise Exception("Invalid trade type:" + row)

    for index, row in bep20TransactionsDfs.iterrows():
        #ts = int(row['UnixTimestamp'])
        #txnDateTime = dt.utcfromtimestamp(ts).isoformat()
        txnDateTime = dt.fromisoformat(str(row['DateTime']))
        asset = str(row['TokenSymbol'])
        fromAddress = str(row['From'])
        toAddress = str(row['To'])
        amount = float(row['Value'])
        pricePerUnit = 1.0 if asset == 'BUSD' else 0.0;
        totalCost = amount * pricePerUnit;

        if (toAddress == args.walletaddress):
            buyOrSell = 'BUY'
        elif (fromAddress == args.walletaddress):
            buyOrSell = 'SELL'
        else:
            raise Exception('Invalid row: ' + row)

        outputDfs = outputDfs.append({
            'dateTime': txnDateTime,
            'asset': asset,
            'type': buyOrSell,
            'amount': amount,
            'pricePerUnit': pricePerUnit,
            'totalCost': totalCost}, ignore_index=True);

    outputDfs = outputDfs.sort_values(by=['dateTime'])
    print(outputDfs);
    outputDfs.to_excel(args.normalizedhistory)

main();
