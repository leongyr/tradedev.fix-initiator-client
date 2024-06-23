from abc import ABC, abstractmethod
import quickfix as fix

from app.client.fix_client import (FixClient)


class _BaseSession(ABC):
	def __init__(self, args):
		self.args = args
		self.config_file = args.config
		self.settings = fix.SessionSettings(self.config_file)
		self.application = FixClient()
		self.storeFactory = fix.FileStoreFactory(self.settings)
		self.logFactory = fix.FileLogFactory(self.settings)
		self.initiator = fix.SocketInitiator(self.application,
											 self.storeFactory,
											 self.settings,
											 self.logFactory)

	@abstractmethod
	def start(self):
		pass