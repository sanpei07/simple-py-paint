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
    root.configure(bg="#f0f0f0")  # 背景色の設定
    
    # ウィンドウアイコンを設定（iconphotoを使用）
    # アプリケーションアイコンが必要な場合は追加実装が必要
    
    app = PaintApp(root)
    root.mainloop()