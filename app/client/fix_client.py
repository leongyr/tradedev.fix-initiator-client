import quickfix as fix
import quickfix42 as fix42
import datetime as dt

from app.utils.tools import (unicode_fix, extract_tag_value_pair_from)
from app.common.interface_order import (OrderUpdateEvent, Trade)

class FixClient(fix.Application):
	"""
	FIX initiator client for connecting with the FIX server to send buy and cancel orders
	"""

	orderID = 0
	curr_sess = None
	app_event_callbacks = {"add": None, "remove": None, "update": None}

	_msg_typ_field = fix.MsgType().getField()				# Tag 35 - fromApp
	_ord_status_field = fix.OrdStatus().getField()			# Tag 39 - fromApp
	_symbol_field = fix.Symbol().getField()					# Tag 55 - _handle_exec_report
	_side_field = fix.Side().getField()						# Tag 54 - _handle_exec_report
	_qty_field = fix.OrderQty().getField()					# Tag 38 - _handle_exec_report
	_last_filled_qty_field = fix.LastShares().getField()	# Tag 32 - _handle_exec_report
	_id_field = fix.ClOrdID().getField()					# Tag 11 - _handle_exec_report
	_price_field = fix.Price().getField()					# Tag 44 - _handle_exec_report
	_last_filled_price_field = fix.LastPx().getField()		# Tag 31 - _handle_exec_report
	_sending_time_field = fix.SendingTime().getField()		# Tag 52 - _handle_exec_report
	_msg_field = fix.Text().getField()						# Tag 58 - _handle_reject/_handle_order_cancel_reject
	_orig_clorid_field = fix.OrigClOrdID().getField()		# Tag 41 - _handle_order_cancel_reject
	_transact_time_field = fix.TransactTime().getField()	# Tag 60 - sendNewOrder/cancelOrder
	

	def onCreate(self, sessionID):
		return

	def onLogon(self, sessionID):
		self.curr_sess = sessionID
		print("LOGON: {}".format(sessionID))
		return

	def onLogout(self, sessionID):
		print("LOGOUT: {}".format(sessionID))
		return

	def toAdmin(self, message, sessionID):
		return

	def toApp(self, message, sessionID):
		fix_str = unicode_fix(str(message))
		print("TOAPP: {}".format(fix_str))
		return

	def fromAdmin(self, message, sessionID):
		fix_str = unicode_fix(str(message))
		print("ADMIN: {}".format(fix_str))
		return

	def fromApp(self, message, sessionID):
		source = "FROM APP"
		fix_str = unicode_fix(str(message))
		print("{}: {}".format(source, fix_str))

		msg_typ = message.getHeader().getField(self._msg_typ_field)

		if msg_typ == fix.MsgType_ExecutionReport:
			ord_status = message.getField(self._ord_status_field)
			self._handle_exec_report(ord_status, fix_str, source)
		elif msg_typ == fix.MsgType_Reject:
			self._handle_reject(fix_str, source)
		elif msg_typ == fix.MsgType_OrderCancelReject:
			self._handle_order_cancel_reject(fix_str, source)
		else:
			print("{}: Not Implemented (Msg Type) - {}".format(source, msg_typ))
			return NotImplemented
		return


	def _genOrderID(self):
		self.orderID += 1
		timestamp = dt.datetime.timestamp(dt.datetime.utcnow())
		return str(self.orderID) + "-" + str(timestamp)


	def _handle_exec_report(self, ord_status, msg, source):
		# Handle execution reports from the FIX server
		tags = extract_tag_value_pair_from(msg)

		_id = tags.get(self._id_field, None)
		_timestamp = tags.get(self._sending_time_field, None)
		_ticker = tags.get(self._symbol_field, None)
		_side = tags.get(self._side_field, None)
		_qty = tags.get(self._last_filled_qty_field, 0)
		_price = tags.get(self._last_filled_price_field, 0.0)

		trade = Trade(_id, _timestamp, _ticker, _side, float(_qty), float(_price))
		order_event = OrderUpdateEvent(ordId=_id, timestamp=_timestamp, qty=float(_qty), price=float(_price),
									   status=ord_status, ticker=_ticker, side=_side)

		if ord_status == fix.OrdStatus_NEW:
			self.app_event_callbacks["update"](order_event)
		elif ord_status == fix.OrdStatus_PARTIALLY_FILLED:
			self.app_event_callbacks["add"](trade)
			self.app_event_callbacks["update"](order_event)
		elif (ord_status == fix.OrdStatus_FILLED):
			self.app_event_callbacks["add"](trade)
			self.app_event_callbacks["remove"](order_event)
		elif ord_status == fix.OrdStatus_REJECTED:
			self.app_event_callbacks["remove"](order_event)
		elif ord_status == fix.OrdStatus_CANCELED:
			self.app_event_callbacks["remove"](order_event)
		else:
			print("{}: Not Implemented (Order Status) - {}".format(source, ord_status))
			return NotImplemented

	def _handle_reject(self, msg, source):
		# Handle rejection reports from the FIX server
		tags = extract_tag_value_pair_from(msg)
		reject_msg = tags.get(self._msg_field, "Nil")
		print("{}: Reject - {}".format(source, reject_msg))


	def _handle_order_cancel_reject(self, msg, source):
		# Handle order cancel rejection reports from the FIX server
		tags = extract_tag_value_pair_from(msg)
		reject_msg = tags.get(self._msg_field, "Nil")
		reject_order = tags.get(self._orig_clorid_field, None)
		print("{}: Order ({}) Cancel Rejected - {}".format(source, reject_order, reject_msg))


	def _newMsg(self):
		# Initialise a new FIX message
		order_msg = fix.Message()
		order_msg.getHeader().setField(fix.BeginString())
		return order_msg


	def sendNewOrder(self, order_req):
		'''
		Send Buy orders to the FIX server in the form of a FIX message
		
		:param order_req: Order
		'''
		_ticker = order_req.ticker
		_side = order_req.side
		_order_type = order_req.ordtyp
		_qty = order_req.qty
		_security = order_req.security
		_price = order_req.price

		order_msg = self._newMsg()
		order_msg.getHeader().setField(fix.MsgType(fix.MsgType_NewOrderSingle))

		# Set content
		new_id = self._genOrderID()
		order_req.id = new_id
		order_msg.setField(fix.ClOrdID(new_id))
		order_msg.setField(fix.TimeInForce(fix.TimeInForce_GOOD_TILL_CANCEL))
		order_msg.setField(fix.SecurityType(_security))
		order_msg.setField(fix.Symbol(_ticker))
		order_msg.setField(fix.Side(_side))
		order_msg.setField(fix.OrdType(_order_type))
		order_msg.setField(fix.Price(_price))
		order_msg.setField(fix.OrderQty(_qty))
		order_msg.setField(fix.HandlInst(fix.HandlInst_AUTOMATED_EXECUTION_ORDER_PRIVATE_NO_BROKER_INTERVENTION))
		order_msg.setField(fix.StringField(self._transact_time_field,(dt.datetime.utcnow().strftime("%Y%m%d-%H:%M:%S.%f"))[:-3]))

		try:
			fix.Session.sendToTarget(order_msg, self.curr_sess)
			self.app_event_callbacks["add"](order_req)
		except fix.SessionNotFound as e:
			return


	def cancelOrder(self, fix_repr):
		'''
		Send Cancel orders to the FIX server in the form of a FIX message
		
		:param fix_repr: dict
		'''
		order_msg = self._newMsg()
		order_msg.getHeader().setField(fix.MsgType(fix.MsgType_OrderCancelRequest))

		order_msg.setField( fix.ClOrdID( self._genOrderID() ) )
		for tag, value in fix_repr.items():
			order_msg.setField(fix.StringField(int(tag), str(value)))
		order_msg.setField(fix.StringField(self._transact_time_field,(dt.datetime.utcnow().strftime("%Y%m%d-%H:%M:%S.%f"))[:-3]))

		try:
			fix.Session.sendToTarget(order_msg, self.curr_sess)
		except fix.SessionNotFound as e:
			return


	def register_app_event_callback(self, methods):
		"""
		Registers the necessary callbacks to add, remove and update ledgers
		within the trading book

		:param methods: dict{label: method}
		"""
		if isinstance(methods, dict):
			try:
				for label, method in methods.items(): 
					self.app_event_callbacks[label] = method
			except KeyError:
				print("Valid keys are 'add', 'remove' and 'update'")
		else:
			raise ValueError("Callback inputs should be a dictionary")


