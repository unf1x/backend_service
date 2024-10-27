import yaml


class Config:
    def __init__(self):
        with open("config.yaml", 'r') as file:
            config = yaml.safe_load(file)

        self.private_key = config['blockchain']['private_key']
        self.infura_url = config['blockchain']['infura_url']
        self.contract_address = config['blockchain']['contract_address']
        self.contract_abi = config['blockchain']['contract_abi']
