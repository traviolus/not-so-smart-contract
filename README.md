# not-so-smart-contract

## Install libraries & dependencies

This repository uses ```pipenv``` library to manage python packages.
To initialize and install python packages specified in ```Pipfile```, run the following command in the project directory.
```
pipenv install
pipenv shell
```

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