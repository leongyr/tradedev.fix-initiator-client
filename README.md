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
Command to run the program is as follows:
```
python main.py [-cfg CONFIG] [-o [ORDER]] [-t [THRESHOLD]]
```
-cfg: required configuration file for the FIX server, and is stored under the config directory
-o: number of random orders to send to the FIX server, default value of 10
-t: threshold to determine send order frequencies, value between 0.0 and 1.0, with a higher value indicating higher likelihood of buy orders being sent compared to cancel orders

## 4. Mini-Project
For the purpose of the project, please run the command as follows:
```
python main.py -cfg=config/fixapp.cfg -o=1000
```

