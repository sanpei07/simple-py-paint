#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
シンプルなペイントソフトのメインエントリーポイント
"""

import tkinter as tk
from paint_app import PaintApp

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Simple Paint - シンプルペイント")
    app = PaintApp(root)
    root.mainloop()