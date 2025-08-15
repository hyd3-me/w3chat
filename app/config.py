# app/config.py
import os
from app import utils

class Config:
    """Base configuration class."""
    LOG_LEVEL = 'INFO'
    LOG_FORMAT = '%(asctime)s [%(levelname)s] %(message)s'
    LOG_DATEFMT = '%Y-%m-%d %H:%M:%S'
    LOG_MAX_BYTES = 1_000_000  # 1 MB
    LOG_BACKUP_COUNT = 3  # 3 backup files

    @staticmethod
    def init_logging():
        pass

class DevelopmentConfig(Config):
    """Development configuration."""
    LOG_LEVEL = 'DEBUG'
    LOG_FORMAT = '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    LOG_TO_CONSOLE = True
    LOG_TO_FILE = True
    LOG_FILE = utils.join_paths(utils.get_data_path(), 'logs', 'dev.log')

    @staticmethod
    def init_logging():
        Config.init_logging()

class TestingConfig(Config):
    """Testing configuration."""
    LOG_LEVEL = 'ERROR'
    LOG_TO_CONSOLE = False
    LOG_TO_FILE = True
    LOG_FILE = utils.join_paths(utils.get_data_path(), 'logs', 'test.log')

    @staticmethod
    def init_logging():
        Config.init_logging()

class ProductionConfig(Config):
    """Production configuration."""
    LOG_LEVEL = 'INFO'
    LOG_TO_CONSOLE = False
    LOG_TO_FILE = True
    LOG_FILE = utils.join_paths(utils.get_data_path(), 'logs', 'prod.log')

    @staticmethod
    def init_logging():
        Config.init_logging()

config_map = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}