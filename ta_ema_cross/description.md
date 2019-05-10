# Detect EMA Crosses for a List of Markets

This script uses 15 min candle data from HitBTC, for a predetermined number of market symbols, to calculate EMA values for two EMA periods (10 and 20). It then detects EMA crosses within a configurable window of historic EMA values (10 in this case) and prints the results on the terminal. EMA crosses in both directions are supported.

# Dependencies

- `requests`
- `bfxhfindicators`

# Default Configurations

- EMA periods: `[10,20]`
- Historic window: `10`
- Symbols: `20 USD pairs`
- Candle timeframes: `15m`
