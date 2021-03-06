#! python
#-*- coding: utf-8 -*-
#
# Copyright 2013-2014 European Commission (JRC);
# Licensed under the EUPL (the 'Licence');
# You may not use this work except in compliance with the Licence.
# You may obtain a copy of the Licence at: http://ec.europa.eu/idabc/eupl

from __future__ import division, unicode_literals

import unittest

import six

from pandalone import utils


try:
    from pandalone.pandui import TkPandalone
    import tkinter as tk
except (ImportError, NotImplementedError):
    pass


class TkUiTest(unittest.TestCase):

    @unittest.skipIf(utils.is_travis() or six.PY2, "TravisCI has no XServer!")
    def test_smoke_test_no_event_loop(self):
        root = tk.Tk()
        try:
            app = TkPandalone(root)
            app.master.quit()
        finally:
            root.destroy()

    @unittest.skipIf(utils.is_travis() or six.PY2, "TravisCI has no XServer!")
    def test_smoke_test_with_event_loop(self):
        root = tk.Tk()
        try:
            app = TkPandalone(root)
            root.after_idle(app._do_about)
            root.after_idle(app._do_reset)
            root.after(3000, root.quit)
            app.mainloop()
        finally:
            try:
                root.destroy()
            except tk.TclError:
                pass


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
