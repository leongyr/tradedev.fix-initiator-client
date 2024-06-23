import argparse

from app.user_sessions.demo_session import (DemoSession)

def main():
	parser = argparse.ArgumentParser(description='FIX Client')
	parser.add_argument('-cfg', '--config', type=str, help='Configuration filename')
	parser.add_argument('-o', '--order', type=int, nargs='?', default=10, help='Number of orders to send')
	parser.add_argument('-t', '--threshold', type=float, nargs='?', default=0.8, help='Threshold for send order frequency')
	args = parser.parse_args()

	app = DemoSession(args)
	app.start()

if __name__ == "__main__":
	main()