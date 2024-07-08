#!/usr/bin/python3

import logging
import os

class logem:
    
    def __init__(self, log=None, message=None, level=None):
        
        self.log = log
        self.message = message
        self.level = level
        self.check_exists()
        self.write_log()
        
    def check_exists(self):
        
        absFilePath = os.path.abspath(self.log)
        directory = os.path.dirname(absFilePath)
        
        if not os.path.exists(directory):
            os.makedirs(directory)
            
    def write_log(self):
        
        logger = logging.getLogger(f'{self.log}')
        logger.setLevel(logging.DEBUG)
        
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        if self.level == "info":
            
            info_handler = logging.FileHandler(self.log)
            info_handler.setLevel(logging.INFO)
            info_handler.setFormatter(formatter)
            logger.addHandler(info_handler)
            logger.info(self.message)
            
        elif self.level == "error":
            
            error_handler = logging.FileHandler(self.log)
            error_handler.setLevel(logging.ERROR)
            error_handler.setFormatter(formatter)
            logger.addHandler(error_handler)
            logger.error(self.message)
            
        else:
            
            print("Logging error")
