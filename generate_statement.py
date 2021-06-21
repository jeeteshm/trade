#!/usr/bin/python

import sys, os;
import argparse;
from os.path import expanduser;
import pandas as pd;
import math;

__author__ = "Jeetesh Mangwani"

def main():
    parser = argparse.ArgumentParser(description="This script outputs realized & unrealized gains and losses, assest lots and adjusted cost basis");
    parser.add_argument("-bh", "--buyhistory", type=str, help="The input xlsx file cotaining your Binance buy history", required=False, default="buyhistory-normalized.xlsx");
    parser.add_argument("-th", "--tradehistory", type=str, help="The input xlsx file containing your Binance trade history", required=False, default="trade-history-normalized.xlsx");
    parser.add_argument("-r", "--rates", type=str, help="The input xlsx file containing your Binance trade history", required=False, default="asset-rates.xlsx");
    parser.add_argument("-st", "--statement", type=str, help="The output xlsx file containing your gains and losses and asset lots", required=False, default="statement.xlsx");
    parser.add_argument("-ul", "--unsoldlots", type=str, help="The output xlsx file containing your unsold asset lots", required=False, default="unsoldlots.xlsx");
    parser.add_argument("-v", "--verbose", help="Whether to output verbose output messages", required=False, default=False);
    args = parser.parse_args();
    print("Input Buy History file: ", args.buyhistory);
    print("Input Trade History file: ", args.tradehistory);
    print("Input Asset Rates file: ", args.rates);
    print("Output Gain-Loss statement file: ", args.statement);
    print("Output Unsold Lots file: ", args.unsoldlots);
    print("Verbosity of log messages: ", args.verbose);

    buyHistoryDfs = pd.read_excel(args.buyhistory, sheet_name="Sheet1")
    tradeHistoryDfs = pd.read_excel(args.tradehistory, sheet_name="Sheet1")
    ratesDfs = pd.read_excel(args.rates, sheet_name="Sheet1")
    # print(buyHistoryDfs);
    # print(tradeHistoryDfs);
    historyDfs = tradeHistoryDfs.append(buyHistoryDfs);
    historyDfs = historyDfs.sort_values(by=['dateTime']);
    historyDfs = historyDfs.set_index(i for i in range(len(historyDfs.index)));
    #print(historyDfs);

    #historyDfs.to_excel("debug.xlsx")

    outputFormat = {
        'dateTime': pd.Series([], dtype='str'),
        'asset': pd.Series([], dtype='str'),
        'type': pd.Series([], dtype='str'),
        'amount': pd.Series([], dtype='float'),
        'txnPricePerUnit': pd.Series([], dtype='float'),
        'totalCost': pd.Series([], dtype='float'),
        'currentPricePerUnit': pd.Series([], dtype='float'),

        # for BUYs
        'unsoldAmount': pd.Series([], dtype='float'),
        'soldAmount': pd.Series([], dtype='float'),
        'unrealizedGain': pd.Series([], dtype='float'),
        'unrealizedGainPercent': pd.Series([], dtype='float'),

        #for SELLs
        'interestLot': pd.Series([], dtype='float'),
        'realizedGain': pd.Series([], dtype='float'),
        'realizedGainPercent': pd.Series([], dtype='float'),

        # details for BUYs
        'soldInLots': pd.Series([], dtype='str'),
        'sellingDates': pd.Series([], dtype='str'),

        # details for SELLs
        'boughtInLots': pd.Series([], dtype='str'),
        'buyingDates': pd.Series([], dtype='str'),
        'lotGains': pd.Series([], dtype='str'),
    };

    statementDfs = pd.DataFrame(outputFormat);

    rates = {};
    scratchPad = {};
    runningLots = {};

    for index, row in ratesDfs.iterrows():
        rates[str(row['asset'])]=float(row['pricePerUnit'])

    # print(rates);

    for index, row in historyDfs.iterrows():
        txnDateTime = str(row['dateTime']);
        asset = str(row['asset']);
        type = str(row['type']);
        amount = float(row['amount']);
        txnPricePerUnit = float(row['pricePerUnit']);
        totalCost = float(row['totalCost']);

        if asset not in rates:
            raise Exception("Could not find rate for asset: " + asset);
        currentPricePerUnit = rates[asset];

        if (type == "BUY"):
            runningRate = rates[asset];
            unrealizedLotGain = amount * (runningRate - txnPricePerUnit);
            unrealizedLotGainPercent = unrealizedLotGain / (amount * txnPricePerUnit) * 100
            scratchPad[index] = {
                'dateTime': txnDateTime,
                'asset': asset,
                'type': 'BUY',
                'amount': amount,
                'txnPricePerUnit': txnPricePerUnit,
                'totalCost': totalCost,
                'currentPricePerUnit': currentPricePerUnit,

                'unsoldAmount': amount,
                'soldAmount': 0.0,
                'unrealizedGain': unrealizedLotGain,
                'unrealizedGainPercent': unrealizedLotGainPercent,
                'soldInLots': [],
                'sellingDates': [],

                'boughtInLots': [],
                'buyingDates': [],
                'interestLot': 0.0,
                'lotGains': [],
                'realizedGain': 0.0,
                'realizedGainPercent': 0.0,
            };

            if asset not in runningLots:
                runningLots[asset] = [];

            runningLots[asset].append(index)
        elif (type == "SELL"):
            wantToSell = amount;
            boughtInLots = [];
            buyingDates = [];
            interestLot = 0.0;
            lotGains = [];
            realizedGain = 0.0;
            costBasis = 0.0;

            while(math.isclose(wantToSell, 0.0) == False):
                if not runningLots[asset]:
                    print("Selling more than you bought! Classifying as interest: " + str(row));
                    selling = wantToSell;
                    interestLot = wantToSell;
                    #buyingDates.append('unknown');
                    costPrice = 0.0;
                    costBasis += selling * costPrice;
                    sellingPrice = txnPricePerUnit;
                    lotGain = selling * (sellingPrice - costPrice);
                    lotGains.append(lotGain);
                    realizedGain += lotGain;
                    wantToSell -= selling;
                else:
                    oldestLotIndex = runningLots[asset][0];
                    oldestLot = scratchPad[oldestLotIndex];

                    if(oldestLot['unsoldAmount'] < wantToSell
                        or math.isclose(wantToSell, oldestLot['unsoldAmount'])):
                        del runningLots[asset][0]
                        selling = oldestLot['unsoldAmount'];
                        oldestLot['soldAmount'] += selling
                        if math.isclose(oldestLot['amount'], oldestLot['soldAmount']) == False:
                            raise Exception("Sold everything but amounts don't match: "
                                + str(oldestLot) + str(row));
                        oldestLot['unsoldAmount'] = 0.0;
                        oldestLot['soldInLots'].append(selling);
                        oldestLot['sellingDates'].append(txnDateTime);

                        boughtInLots.append(selling);
                        buyingDates.append(oldestLot['dateTime']);
                        costPrice = oldestLot['txnPricePerUnit'];
                        costBasis += selling * costPrice;
                        sellingPrice = txnPricePerUnit;
                        lotGain = selling * (sellingPrice - costPrice);
                        lotGains.append(lotGain);
                        realizedGain += lotGain;
                        wantToSell -= selling;
                    else:
                        selling = wantToSell;
                        oldestLot['soldAmount'] += selling
                        oldestLot['unsoldAmount'] -= selling
                        oldestLot['soldInLots'].append(selling);
                        oldestLot['sellingDates'].append(txnDateTime);

                        boughtInLots.append(selling);
                        buyingDates.append(oldestLot['dateTime']);
                        costPrice = oldestLot['txnPricePerUnit'];
                        costBasis += selling * costPrice;
                        sellingPrice = txnPricePerUnit;
                        lotGain = selling * (sellingPrice - costPrice);
                        lotGains.append(lotGain);
                        realizedGain += lotGain;
                        wantToSell -= selling;

            realizedGainPercent = realizedGain / costBasis * 100;
            scratchPad[index] = {
                'dateTime': txnDateTime,
                'asset': asset,
                'type': 'SELL',
                'amount': amount,
                'txnPricePerUnit': txnPricePerUnit,
                'totalCost': totalCost,
                'currentPricePerUnit': currentPricePerUnit,

                'unsoldAmount': 0.0,
                'soldAmount': 0.0,
                'unrealizedGain': 0.0,
                'unrealizedGainPercent': 0.0,
                'soldInLots': [],
                'sellingDates': [],

                'boughtInLots': boughtInLots,
                'buyingDates': buyingDates,
                'interestLot': interestLot,
                'lotGains': lotGains,
                'realizedGain': realizedGain,
                'realizedGainPercent': realizedGainPercent
            };
        else:
            raise Exception("Invalid row: " + row);

    for key, txn in scratchPad.items():
        statementDfs = statementDfs.append({
            'dateTime': txn['dateTime'],
            'asset': txn['asset'],
            'type': txn['type'],
            'amount': txn['amount'],
            'txnPricePerUnit': txn['txnPricePerUnit'],
            'currentPricePerUnit': txn['currentPricePerUnit'],
            'totalCost': txn['totalCost'],

            'unsoldAmount': txn['unsoldAmount'],
            'soldAmount': txn['soldAmount'],
            'unrealizedGain': txn['unrealizedGain'],
            'unrealizedGainPercent': txn['unrealizedGainPercent'],
            'soldInLots': str(txn['soldInLots']),
            'sellingDates': str(txn['sellingDates']),

            'boughtInLots': str(txn['boughtInLots']),
            'buyingDates': str(txn['buyingDates']),
            'interestLot': txn['interestLot'],
            'lotGains': str(txn['lotGains']),
            'realizedGain': txn['realizedGain'],
            'realizedGainPercent': txn['realizedGainPercent'],
        }, ignore_index=True);

    lotsDfs = pd.DataFrame(outputFormat);
    portfolioAdjustedCostBasis = 0.0
    portfolioUnrealizedGain = 0.0
    portfolioUnrealizedGainPercent = 0.0
    for asset, keys in runningLots.items():
        #print(asset);
        sheetName = asset;
        totalUnsoldAmount = 0.0;
        adjustedCostBasis = 0.0;
        totalUnrealizedGain = 0.0;
        totalUnrealizedGainPercent = 0.0;
        for key in keys:
            txn = scratchPad[key];
            totalUnsoldAmount += txn['unsoldAmount']
            adjustedCostBasis += txn['unsoldAmount'] * txn['txnPricePerUnit']
            totalUnrealizedGain += txn['unrealizedGain']
            #print(scratchPad[key]);
            lotsDfs = lotsDfs.append({
                'dateTime': txn['dateTime'],
                'asset': txn['asset'],
                'type': txn['type'],
                'amount': txn['amount'],
                'txnPricePerUnit': txn['txnPricePerUnit'],
                'currentPricePerUnit': txn['currentPricePerUnit'],
                'totalCost': txn['totalCost'],

                'unsoldAmount': txn['unsoldAmount'],
                'soldAmount': txn['soldAmount'],
                'unrealizedGain': txn['unrealizedGain'],
                'unrealizedGainPercent': txn['unrealizedGainPercent'],
                'soldInLots': str(txn['soldInLots']),
                'sellingDates': str(txn['sellingDates']),

                'boughtInLots': str(txn['boughtInLots']),
                'buyingDates': str(txn['buyingDates']),
                'interestLot': txn['interestLot'],
                'lotGains': str(txn['lotGains']),
                'realizedGain': txn['realizedGain'],
                'realizedGainPercent': txn['realizedGainPercent'],
            }, ignore_index=True);
        totalUnrealizedGainPercent = 0.0 if math.isclose(adjustedCostBasis, 0.0) else totalUnrealizedGain / adjustedCostBasis * 100;
        portfolioAdjustedCostBasis += adjustedCostBasis;
        portfolioUnrealizedGain += totalUnrealizedGain
        lotsDfs = lotsDfs.append({
            'asset': txn['asset'],
            'currentPricePerUnit': txn['currentPricePerUnit'],
            'adjustedCostBasis': float(adjustedCostBasis),

            'unsoldAmount': totalUnsoldAmount,
            'unrealizedGain': totalUnrealizedGain,
            'unrealizedGainPercent': totalUnrealizedGainPercent,
        }, ignore_index=True);
    portfolioUnrealizedGainPercent = 0.0 if math.isclose(portfolioAdjustedCostBasis, 0.0) else portfolioUnrealizedGain / portfolioAdjustedCostBasis * 100
    lotsDfs = lotsDfs.append({
        'asset': '*',
        'adjustedCostBasis': float(portfolioAdjustedCostBasis),
        'unrealizedGain': portfolioUnrealizedGain,
        'unrealizedGainPercent': portfolioUnrealizedGainPercent,
    }, ignore_index=True);

    lotsDfs.to_excel(args.unsoldlots, 'sheet1');
    #print(outputDfs);
    statementDfs.to_excel(args.statement, "sheet1")

main();
