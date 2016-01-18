#!/usr/bin/env python3
"""
Meerkat API Tests

Unit tests for the Meerkat frontend
"""
import json
import unittest
from datetime import datetime
from datetime import timedelta
from sqlalchemy import extract

import meerkat_api
import meerkat_abacus.manage as manage
import meerkat_abacus.config as config
import meerkat_abacus.model as model




class MeerkatHermesTestCase(unittest.TestCase):

    def setUp(self):
        """Setup for testing"""
        meerkat_api.app.config['TESTING'] = True
        manage.set_up_everything(
            config.DATABASE_URL,
            True, True, N=500)

        self.app = meerkat_api.app.test_client()
        self.locations = {1: {"name": "Demo"}}
        self.variables = {1: {"name": "Total"}}
    def tearDown(self):
        pass
        
if __name__ == '__main__':
    unittest.main()
