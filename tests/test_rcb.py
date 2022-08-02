"""

Tests for the RCB management system

"""
import unittest
import torch
from src import rcb

class integration_rcb(unittest.TestCase):
    """
    Tests rcb creation, and proper functionality
    with torch.

    It also verifies that it is the case that I can
    simply tweak the rcb callback to allow torch
    to compile a rebuilt function.
    """
    def test_basic(self):
        erp = 3
        bop = 4
        deep = {}

        env = rcb.makeEnvFromFrame(0)
        callback = rcb.createCallbackfromEnv(env)

        self.assertTrue(callback('erp') == erp)
        self.assertTrue(callback('bop') == bop)
        self.assertTrue(callback('deep') is deep)
    def test_torch_integration(self):
        """Tests the callback still is usable by torch"""
        def erp():
            deeper = 3
            return deeper

        def func():
            return erp()

        env = rcb.makeEnvFromFrame()
        print(env.locals)
        callback = rcb.createCallbackfromEnv(env)
        func = torch.jit.script(func, _rcb=callback)
        self.assertTrue(func() == 3)
    def test_env_modified_integration(self):
        """Test the ability of the function to correct issues"""
        def func():
            return erp()

        env = rcb.makeEnvFromFrame()

        def erp():
            return 4

        env.locals['erp'] = erp
        callback = rcb.createCallbackfromEnv(env)
        func = torch.jit.script(func, _rcb=callback)
        self.assertTrue(func() == 4)