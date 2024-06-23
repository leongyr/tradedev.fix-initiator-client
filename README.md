# FIX Client
FIX client that sends random orders to a test FIX server

## 1. Python version
This project uses the following Python version:
```
3.12.2
```

## 2. Installing required dependencies
In the command line, navigate to the project folder and run the following command:
```
pip install -r requirements.txt
```

## 3. Running the project
The structure of the command to run the project is as such:

python main.py [-cfg CONFIG] [-o [ORDER]] [-t [THRESHOLD]]

-cfg: required configuration file for the FIX server, and is stored under the config directory \
-o: number of random orders to send to the FIX server, default value of 10 \
-t: threshold to determine send order frequencies, value between 0.0 and 1.0, with a higher value indicating higher likelihood of buy orders being sent compared to cancel orders

For the purpose of the project, please run the command as follows:
```
python main.py -cfg=config/fixapp.cfg -o=1000
```

## 4. General program flow
1. Synthetic orders are generated and sent to the FIX server, before being added into the respective ledgers within the trading book.
2. There are three possible replies from the FIX server:
   a. Execution report is received
   b. Cancel report is received
   c. Order Cancel Reject report is received
3. When an execution report is received, order events are created to update the orders if the order status is NEW or PARTIALLY_FILLED, remove the orders if the order status is FILLED, REJECTED or CANCELED, and trade events are created if the order status is PARTIALLY_FILLED or FILLED.
4. Trades with similar order id are first verified to have the same ticker and side before combining into a single trade entry, and trades will reflect the average price per quantity.

## 5. Results
After submission of all orders, there will be a delay of approximately 15 seconds to cater for order fulfillment requests to reach the client from the server prior to logging off. Once the trading session is completed, a trading session stats report will be printed.

Sample output:
```
Trading Session Stats
======================================================================
Trade Vol:	511630.03 USD
PnL:		241767.29 USD
VWAP:		{'MSFT': 204.31, 'AAPL': 131.92, 'BAC': 38.83}
======================================================================
```
