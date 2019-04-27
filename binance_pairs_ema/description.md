# Get all Binance USDT pairs and filter by {price vs EMA}

This script demonstrates how to query Binance for all active USDT trading pairs, get candle data for them and calculate EMAs for each. The results are then used save txt files with symbols filtered by criteria such as:

- Trading below EMA(50)
- Trading above EMA(50) and below EMA(200)
- Trading above EMA(200)

## Dependencies

- ```bfxhfindicators``` (technical analysis library made by Bitfinex)
- ```requests```
