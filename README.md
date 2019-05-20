# Pytrader Custom

## Disclaimer
This project aim to simulate and analyse the crypto market by allowing to run transaction on python based simulator.

This project is composed by 2 projects :
- a data loader
- a pytrader simulator

## Project data-loader
This project aims to help analysis of cryptocurrencies data. This use an elasticsearch database and python script to load extracted data.

## Project simulator
This project give an overview of a basic python simulator. With some parameters, the simulator is able to perform basic trading operations with a success rate of 1. 

## Install notes
# MAC osX
Follow the steps :
1. install python3.7+ (using Homebrew eg.)
2. install `pew` (advised)
3. install virtual environment and dependencies using 
> `pew new NEW_ENV_NAME -p /usr/local/Cellar/python/3.7.3/bin/python3.7 -r requirements.txt`