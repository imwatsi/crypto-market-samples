# Subscribing to Multiple Channels via Websocket (Bitfinex)

A script demonstrating how to subscribe to multiple ticker and candle channels via Bitfinex's Websocket API. It gets all USD pairs on Bitfinex and then subscribes to their ticker and 15m candle channels. It also features a simple interactive tool to view ticker and candle details for a symbol on the terminal.

## Dependencies

- `requests`
- `websocket-client`

## Using the interactive tool

- After running the script, wait for it to print a statement saying `Tickers and candles loaded. You may query a symbol now.`
- Type in a symbol name and press ENTER, e.g. btcusd (it is not case-sensetive) or ltcusd
- The current ticker details as well as the latest candle will be printed
