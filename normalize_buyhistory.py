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
    parser = argparse.ArgumentParser(description="This script normalizes the Binance buy history to a simpler format for other scripts to process");
    parser.add_argument("-bh", "--buyhistory", type=str, help="The input xlsx file cotaining your Binance buy history", required=False, default = './buy-history.xlsx');
    parser.add_argument("-nh", "--normalizedhistory", type=str, help="The output xlsx file cotaining your normalized trade history", required=False, default = './buy-history-normalized.xlsx');
    parser.add_argument("-fx", "--foreignexchange", type=str, help="The CAD-to-USD exchange rate chart", required=False, default = './trade/cad-usd.xlsx');
    parser.add_argument("-v", "--verbose", help="Whether to output verbose output messages", required=False, default=False);
    args = parser.parse_args();
    print("Input Buy History file: ", args.buyhistory);
    print("Input Currency Exchange rate file: ", args.foreignexchange);
    print("Output Normalized History file: ", args.normalizedhistory);
    print("Verbosity of log messages: ", args.verbose);

    buyhistoryDfs = pd.read_excel(args.buyhistory, sheet_name="sheet1")
    inputFxDfs = pd.read_excel(args.foreignexchange, sheet_name="sheet1")

    fxDfs = {};
    for index, row in inputFxDfs.iterrows():
        rateDt = dt.fromisoformat(str(row['Date'])).date()
        fxDfs[str(rateDt)] = row['Close']

    #print(fxDfs);

    outputDfs = pd.DataFrame({
        'dateTime': pd.Series([], dtype='str'),
        'asset': pd.Series([], dtype='str'),
        'type': pd.Series([], dtype='str'),
        'amount': pd.Series([], dtype='float'),
        'pricePerUnit': pd.Series([], dtype='float'),
        'totalCost': pd.Series([], dtype='float'),
        #'txnFee': pd.Series([], dtype='float'),
    })

    for index, row in buyhistoryDfs.iterrows():
        #ts = int(row['UnixTimestamp'])
        #txnDateTime = dt.utcfromtimestamp(ts).isoformat()
        txnDateTime = dt.fromisoformat(str(row['Date(UTC)']))
        amountAndAsset = str(row['Final Amount']).split(" ");
        asset = amountAndAsset[1];
        amountBought = float(amountAndAsset[0]);
        #amountSold = row['Value_OUT(BNB)']
        #txnFee = row['TxnFee(USD)']
        fiatCostAndCurrency = str(row['Amount']).split(" ");
        fiatCost = float(fiatCostAndCurrency[0]);
        fiatCurrency = str(fiatCostAndCurrency[1]);

        #print(txnDateTime, asset, amountBought, fiatCost, fiatCurrency);

        if (fiatCurrency == 'CAD'):
            exchangeRate = getExchangeRate(txnDateTime.date(), fxDfs);
            fiatCost = fiatCost * exchangeRate
            fiatCurrency = 'USD'

        usdPricePerUnit = fiatCost / amountBought;

        #print(txnDateTime, asset, amountBought, fiatCost, fiatCurrency);

        outputDfs = outputDfs.append({
            'dateTime': txnDateTime,
            'asset': asset,
            'type': 'BUY',
            'amount': amountBought,
            'pricePerUnit': usdPricePerUnit,
            'totalCost': fiatCost}, ignore_index=True);

    outputDfs = outputDfs.sort_values(by=['dateTime'])
    print(outputDfs);
    outputDfs.to_excel(args.normalizedhistory)

def getExchangeRate(tryDate, fxDfs):
    if str(tryDate) in fxDfs:
        exchangeRate = fxDfs[str(tryDate)]
    elif str(tryDate - timedelta(days=1)) in fxDfs:
        exchangeRate = fxDfs[str(tryDate - timedelta(days=1))]
    elif str(tryDate - timedelta(days=2)) in fxDfs:
        exchangeRate = fxDfs[str(tryDate - timedelta(days=2))]
    else:
        raise Exception("Couldn't find exchange rate for date:" + tryDate);

    return float(exchangeRate)

main();
