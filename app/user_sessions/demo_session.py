import time
import random

from ._base_user_session import (_BaseSession)
from app.utils.tools import (gen_synthetic_orders)
from app.common.interface_order import (TradingBook)


class DemoTradingBook(TradingBook):
	"""
	Trading book for purpose of demonstration
	Includes some qol methods which a typical trading book may not require/differ
	"""
	def __init__(self, name, assets):
		super().__init__(name, assets)

	def get_random_order(self):
		"""
		Get random available orders for sending cancellation orders to
		the server for the purpose of this demonstration
		"""
		_sym = random.choice( list( self.ledgers.keys() ) )
		_ledger = self.get_ledger(_sym)
		_orders = _ledger.get_order()
		if _orders:	
			order_id = random.choice( list( _orders.keys() ) )
			return _ledger.get_order(order_id)
		else:
			return None

	def display_stats(self):
		"""
		Display trade volume, PnL and VWAP stats for
		all assets within the trading book
		"""
		trade_vol = self.get_book_trading_volume()
		pnL = self.get_book_pnl()
		vwap = self.get_ledger_vwap()
		print("\n")
		print("Trading Session Stats")
		print("="*70)
		print(f"Trade Vol:\t{trade_vol} USD")
		print(f"PnL:\t\t{pnL} USD")
		print(f"VWAP:\t\t{vwap}")
		print("="*70)
		print("\n")


class DemoSession(_BaseSession):
	"""
	Demo session for sending buy and cancel orders to FIX server
	"""
	def __init__(self, args):
		super().__init__(args)
		self.tickers = ["MSFT", "AAPL", "BAC"]

	def start(self):
		"""
		Start the demo session
		"""
		demo_account = DemoTradingBook("fix-demo", self.tickers)
		callback_methods = {"add": demo_account.log_transaction,
							"remove": demo_account.erase_transaction,
							"update": demo_account.update_transaction}
		self.application.register_app_event_callback(callback_methods)
		try:
			self.initiator.start()
			time.sleep(1)
			count = 0
			while (count < self.args.order):
				choice = random.random()
				if choice <= self.args.threshold:
					order = gen_synthetic_orders(self.tickers)
					self.application.sendNewOrder(order)
					count += 1
				else:
					# Cancel orders randomly
					select_order = demo_account.get_random_order()
					if select_order is not None:
						self.application.cancelOrder(select_order.to_fix_cancel())
				time.sleep(0.1)
			# Buffer to allow all server updates to be captured before calculating trading stats
			time.sleep(15)

			## DEBUG
			# for ticker in self.tickers:
			# 	print(demo_account.get_ledger(ticker).get_order())
			# 	print(demo_account.get_ledger(ticker).get_trade())

			self.initiator.stop()
			# Display calculated stats after end of trading session
			demo_account.display_stats()
		except Exception as e:
			print(e)

