# not-so-smart-contract

## Set up bot to update the price hourly [crontab]

- In terminal use the following command to access *crontab* config file
```
crontab -e
```
- Insert the following line
```
0 * * * * /usr/bin/python3 <path-to-EthPrice.py> set
```
The above crontab will execute the EthPrice.py with *set* method hourly.