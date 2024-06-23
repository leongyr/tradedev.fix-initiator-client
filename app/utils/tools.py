import random
import quickfix as fix

from app.common.interface_order import (Order)


def unicode_fix(string: str) -> str: 
   """
   Replace FIX unicode characters with '|'

   :param string: str
   """ 
   bar_in_unicode = "\x01" 
   new_str = string.replace(bar_in_unicode, '|') 
   return new_str


def gen_synthetic_orders(tickers: list[str]) -> dict:
   """
   Generate random orders for sending to server

   :param tickers: list[str]
   """
   sides = [fix.Side_BUY, fix.Side_SELL, fix.Side_SELL_SHORT]
   order_types = [fix.OrdType_LIMIT, fix.OrdType_MARKET]

   ticker = random.choice(tickers)
   side = random.choice(sides)
   order_type = random.choice(order_types)
   qty = random.randrange(1,11)
   security_type = fix.SecurityType_COMMON_STOCK

   syn_order = Order(ticker=ticker,
                     side=side,
                     qty=qty,
                     security=security_type,
                     ordtyp=order_type
                    )

   if order_type == fix.OrdType_LIMIT:
      syn_order.price = round(random.random() * 100, 2)
   return syn_order


def extract_tag_value_pair_from(msg: str) -> dict:
   """
   Extract tag-value pairs from string representation 
   of fix messages

   :param msg: str
   """
   tag_dict = {}
   tag_value_pairs = msg.split("|")[:-1]
   for pair in tag_value_pairs:
      tag, val = pair.split("=")
      tag_dict[int(tag)] = val
   return tag_dict


# For testing purposes
if __name__ == "__main__":
   for i in range(10):
      print(gen_synthetic_orders())