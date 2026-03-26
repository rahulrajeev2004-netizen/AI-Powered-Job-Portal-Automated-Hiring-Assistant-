"""
Unit tests for the centralized logging system.
"""
import unittest
import os
from utils.logger import get_logger

class TestLogger(unittest.TestCase):
    def test_logger_creation(self):
        log_file = 'logs/test_ai_system.log'
        logger = get_logger(name='test_logger', log_file=log_file)
        
        # Test if logger is created
        self.assertIsNotNone(logger)
        
        # Test if log file is created after logging a message
        logger.info('Test log message')
        self.assertTrue(os.path.exists(log_file))
        
        # Test if the file has content
        with open(log_file, 'r') as f:
            content = f.read()
            self.assertIn('Test log message', content)

if __name__ == '__main__':
    unittest.main()
