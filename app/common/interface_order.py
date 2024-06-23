import quickfix as fix
import datetime as dt

class OrderUpdateEvent:
	"""
	Capture order updates from server

	Attributes  
	ordId: str, default=None - Order ID for which the update applies to  
	timestamp: str, default=None - Timestamp of the order event  
	qty: float: default=None - Last filled quantity  
	price: float, default=None - Last filled price  
	status: str, default=None - Latest order status  
	ticker: str, default=None - Asset for which the update applies to  
	side: str, default=None - Trade side of the order  
	"""
	def __init__(self, ordId=None, timestamp=None, qty=None,
				 price=None, status=None, ticker=None, side=None,):
		self.id = ordId
		self.timestamp = timestamp
		self.qty = qty
		self.price = price
		self.status = status

		self.ticker = ticker
		self.side = side


class Order:
	"""
	Track orders placed to the server

	Attributes  
	ticker: str - Asset symbol for which the order is tracking  
	side: str - Trade side of the order  
	qty: float - Quantity of the asset to be ordered  
	ordtyp: str - Limit or market order type  
	security: str - Classification of the asset for ordering  
	price: float, default=0.0 - Limit price for asset ordering  
	"""
	def __init__(self, ticker, side, qty, 
				 ordtyp, security,  price=0.0):
		self.ticker = ticker			# Tag 55
		self.side = side				# Tag 54
		self.qty = qty					# Tag 38
		self.ordtyp = ordtyp			# Tag 40
		self.security = security		# Tag 167
		self.price = price				# Tag 44
		
		self.id = None					# Tag 11
		self.timestamp = None			# Tag 60
		self.ord_status = None			# Tag 39

	def to_fix_cancel(self):
		"""
		Returns a dictionary containing the required tags to send a FIX cancel order message
		"""
		_symbol_field = fix.Symbol().getField()
		_side_field = fix.Side().getField()
		_qty_field = fix.OrderQty().getField()
		_security_field = fix.SecurityType().getField()
		_id_field = fix.OrigClOrdID().getField()

		fix_repr = {
			_symbol_field: self.ticker,
			_side_field: self.side,
			_qty_field: self.qty,
			_security_field: self.security,
			_id_field: self.id
		}

		return fix_repr

	def __repr__(self):
		return f"Order({self.ticker}, {self.side}, {self.qty}, {self.ordtyp}, {self.security}, " \
			   f"{round(self.price, 2)}, {self.ord_status}, {self.id}, {self.timestamp})"

	def __str__(self):
		return f"Order {self.id} ({self.timestamp}) - Ticker: {self.ticker}, Security: {self.security}, Side: {self.side}, " \
			   f"Qty: {self.qty}, Type: {self.ordtyp}, Price: {self.price}, Status: {self.ord_status})"


class Trade:
	"""
	Track confirmed trades received from the server

	Attributes  
	ordID: str - Order ID for which the trade is related to  
	timestamp: str - Timestamp of the trade  
	ticker: str - Traded asset  
	side: str - Trade side  
	qty: float - Quantity of the asset for the particular trade id  
	price: float, default=0.0 - Price of the trades for the particular trade id. 
		Average price is calculated for partial order fills at different prices  
	"""
	def __init__(self, ordID, timestamp, ticker, 
				 side, qty, price):
		self.id = ordID					# Tag 11
		self.timestamp = timestamp		# Tag 52
		self.ticker = ticker			# Tag 55
		self.side = side				# Tag 54
		self.qty = qty					# Tag 32
		self.price = price				# Tag 31

	def __add__(self, other):
		if isinstance(other, Trade):
			if (self.side == other.side) and (self.ticker == other.ticker):
				_new_qty = self.qty + other.qty
				_new_price = (self.qty*self.price + other.qty*other.price)/_new_qty
				_new_timestamp = max(int(dt.datetime.strptime(self.timestamp, '%Y%m%d-%H:%M:%S.%f').timestamp()),
									 int(dt.datetime.strptime(other.timestamp, '%Y%m%d-%H:%M:%S.%f').timestamp())
									)
				_new_timestamp = (dt.datetime.fromtimestamp(_new_timestamp).strftime("%Y%m%d-%H:%M:%S.%f"))[:-3]
				return Trade(other.id, _new_timestamp, other.ticker, other.side, _new_qty, _new_price)
			else:
				print(self.id, self.side, other.id, other.side)
				print("Trade with same ID but different side and/or ticker. To check.")
		else:
			return NotImplemented

	def __repr__(self):
		return f"Trade({self.id}, {self.timestamp}, {self.ticker}, {self.side} ,{self.qty}, {round(self.price, 2)})"

	def __str__(self):
		return f"Trade {self.id} ({self.timestamp}) - Ticker: {self.ticker}, Side: {self.side}, Qty: {self.qty}, Price: {round(self.price, 2)}"
		


class AssetLedger:
	"""
	Ledger to hold all pending orders and confirmed trades for 
	a particular asset

	Attributes  
	name: str - Asset to which the ledger applies
	"""
	def __init__(self, name):
		self.name = name
		self.orders = {}
		self.trades = {}

	def add_order(self, new_order):
		"""
		Add new orders

		:param new_order: Order  
		"""
		self.orders[new_order.id] = new_order

	def remove_order(self, order):
		"""
		Remove existing orders

		:param order: Order | OrderEvent  
		"""
		try:
			del self.orders[order.id]
		except KeyError:
			print("Unable to remove Order {}".format(order.id))

	def update_order(self, order_event):
		"""
		Update existing orders with new order updates from server

		:param order_event: OrderEvent  
		"""
		try:
			curr_order = self.orders[order_event.id]
			if (curr_order.ticker==order_event.ticker) and (curr_order.side==order_event.side):
				curr_order.timestamp = order_event.timestamp
				curr_order.ord_status = order_event.status
				if order_event.status == fix.OrdStatus_PARTIALLY_FILLED:
					curr_order.qty -= order_event.qty
		except KeyError:
			print("Unable to update Order {}".format(order_event.id))

	def clear_orders(self):
		"""
		Clear all orders in the ledger 
		"""
		self.orders.clear()

	def get_order(self, order_id=None):
		"""
		Retrieve respective order based on the id. Retrieve all orders if order_id is None

		:param order_id: str
		"""
		if not order_id:
			return self.orders
		else:
			return self.orders[order_id]

	def add_trade(self, new_trade):
		"""
		Add new trades

		:param new_trade: Trade  
		"""
		if new_trade.id in self.trades:
			curr_trade = self.trades[new_trade.id]
			self.trades[new_trade.id] = curr_trade + new_trade
		else:
			self.trades[new_trade.id] = new_trade

	def remove_trade(self, trade):
		"""
		Remove existing trades

		:param trade: Trade  
		"""
		try:
			del self.trades[trade.id]
		except KeyError:
			print("No such trade exists for removal")

	def clear_trades(self):
		"""
		Clear all trades in the ledger 
		"""
		self.trades.clear()

	def get_trade(self, trade_id=None):
		"""
		Retrieve respective trade based on the id. Retrieve all trades if Order.id is None  

		:param trade_id: str
		"""
		if not trade_id:
			return self.trades
		else:
			return self.trades[trade_id]

	def calc_asset_trading_volume(self) -> float:
		"""
		Calculate total trading volume for the ledger in dollar amount
		"""
		trading_volume = 0
		for trade in self.trades.values():
			trading_volume += (trade.price * trade.qty)
		return trading_volume

	def calc_trading_pnl(self) -> float:
		"""
		Calculate total trading PnL for the ledger in dollar amount
		"""
		pnL = 0
		for trade in self.trades.values():
			if trade.side == fix.Side_SELL or trade.side == fix.Side_SELL_SHORT:
				pnL += (trade.price * trade.qty)
			elif trade.side == fix.Side_BUY:
				pnL -= (trade.price * trade.qty)
			else:
				raise ValueError("Unknown trading side")
		return pnL


	def calc_vwap(self) -> float:
		"""
		Calculate VWAP for the ledger in dollar amount
		"""
		trading_volume = 0
		total_quantity = 0
		for trade in self.trades.values():
			trading_volume += (trade.price * trade.qty)
			total_quantity += trade.qty
		if total_quantity == 0:
			# Return 0 in event no trade registered for an asset
			return 0
		else:
			return trading_volume / total_quantity

	def __str__(self):
		return f"Ledger: {self.name}, Orders: {len(self.orders)}, Trades: {len(self.trades)}"

	def __contains__(self, item):
		return (item.id in self.orders) or (item.id in self.trades)


class TradingBook:
	"""
	Trading Book to aggregate all trading asset ledgers

	Attributes  
	name: str - Name of the trading book  
	"""
	def __init__(self, name, assets):
		self.name = name
		self.ledgers = {}	# {ticker: AssetLedger}

		self._initialize_ledgers(assets)

	def _initialize_ledgers(self, assets):
		if isinstance(assets, list):
			for asset in assets:
				self.ledgers[asset] = AssetLedger(asset)
		elif isinstance(assets, str):
			self.ledgers[assets] = AssetLedger(assets)
		else:
			raise ValueError("Invalid asset for initializing trading book - {}".format(assets))

	def log_transaction(self, transaction):
		"""
		Add new transaction to respective ledger

		:param transaction: Order | OrderUpdateEvent | Trade
		"""
		if isinstance(transaction, Order) or isinstance(transaction, OrderUpdateEvent):
			self.ledgers[transaction.ticker].add_order(transaction)
		elif isinstance(transaction, Trade):
			self.ledgers[transaction.ticker].add_trade(transaction)
		else:
			raise ValueError("Invalid transaction")

	def erase_transaction(self, transaction):
		"""
		Remove transaction from respective ledger

		:param transaction: OrderUpdateEvent | Trade
		"""
		if isinstance(transaction, OrderUpdateEvent):
			if transaction.ticker:
				self.ledgers[transaction.ticker].remove_order(transaction)
			else:
				# Account for situation where order is rejected due unlucky
				# Only id is sent, no symbol tag
				for asset, ledger in self.ledgers.items():
					if transaction in ledger:
						self.ledgers[asset].remove_order(transaction)
		elif isinstance(transaction, Trade):
			self.ledgers[transaction.ticker].remove_trade(transaction)
		else:
			raise ValueError("Invalid transaction")

	def update_transaction(self, transaction):
		"""
		Update transaction for respective ledger with new order updates from server

		:param transaction: OrderUpdateEvent
		"""
		if isinstance(transaction, OrderUpdateEvent):
			self.ledgers[transaction.ticker].update_order(transaction)
		else:
			raise ValueError("Invalid transaction")

	def get_ledger(self, ticker=None):
		"""
		Get the ledger for a particular asset

		:param ticker: str
		"""
		if not ticker:
			return self.ledgers
		else:
			try:
				return self.ledgers[ticker]
			except KeyError:
				print("No such ledger in trading book to retrieve - {}".format(ticker))

	def clear_ledger(self, ticker):
		"""
		Remove the ledger for a particular asset

		:param ticker: str
		"""
		try:
			del self.ledgers[ticker]
		except KeyError:
			print("No such ledger in trading book to remove - {}".format(ticker))

	def reset_ledgers(self):
		"""
		Remove all ledgers
		"""
		self.ledgers.clear()

	def get_book_trading_volume(self, ticker=None):
		"""
		Get total trading volume for the trading book in dollar amount

		:param ticker: str
		"""
		trade_vol = 0
		try:
			if ticker is None:
				for ledger in self.ledgers.values():
					trade_vol += ledger.calc_asset_trading_volume()
			else:
				trade_vol += (self.get_ledger(ticker).calc_asset_trading_volume())
		except KeyError:
			print("No ledger for ticker {} to calculate trade volume".format(ticker))
		else:
			return round(trade_vol, 2)
				
	def get_book_pnl(self, ticker=None):
		"""
		Get total trading PnL for the trading book in dollar amount

		:param ticker: str
		"""
		pnL = 0
		try:
			if ticker is None:
				for ledger in self.ledgers.values():
					pnL += ledger.calc_trading_pnl()
			else:
				pnL += (self.get_ledger(ticker).calc_trading_pnl())
		except KeyError:
			print("No ledger for ticker {} to calculate PnL".format(ticker))
		else:
			return round(pnL, 2)

	def get_ledger_vwap(self, ticker=None):
		"""
		Get VWAP for each ledger in the trading book in dollar amount

		:param ticker: str
		"""
		ledger_vwap = {}
		try:
			if ticker is None:
				for asset, ledger in self.ledgers.items():
					ledger_vwap[asset] = round(ledger.calc_vwap(), 2)
			else:
				ledger_vwap[asset] = round(ledger.calc_vwap(), 2)
		except KeyError:
			print("No ledger for ticker {} to calculate VWAP".format(ticker))
		else:
			return ledger_vwap


