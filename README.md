# not-so-smart-contract

## Set up bot to update ethereum price hourly [crontab]

- In terminal use the following command to access *crontab* config file
```
crontab -e
```
- Insert the following line
```
0 * * * * /usr/bin/python3 <path-to-EthPrice.py> set ETH
```
The above crontab will execute the EthPrice.py with *set* method hourly.
- And to query for its price, simply use this command
```
/usr/bin/python3 <path-to-EthPrice.py> get ETH
```