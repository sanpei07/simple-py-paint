#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
シンプルなペイントアプリケーションのメインクラス
"""

import tkinter as tk
from tkinter import colorchooser, filedialog, messagebox
import os
from PIL import Image, ImageDraw

class PaintApp:
    def __init__(self, root):
        """
        ペイントアプリケーションの初期化
        
        Args:
            root: tkinterのルートウィンドウ
        """
        self.root = root
        
        # キャンバスのサイズ
        self.canvas_width = 800
        self.canvas_height = 600
        
        # 線の色とサイズの初期値
        self.current_color = "#000000"  # 黒
        self.brush_size = 3
        self.tool = "pen"  # 初期ツールはペン
        
        # UIの設定
        self.setup_ui()
        
        # キャンバスの描画データ
        self.drawing_data = Image.new("RGB", (self.canvas_width, self.canvas_height), "white")
        self.drawing_data_draw = ImageDraw.Draw(self.drawing_data)
        
        # マウスのイベントを追跡するための変数
        self.prev_x = None
        self.prev_y = None
        
    def setup_ui(self):
        """
        UIコンポーネントの設定
        """
        # フレームの設定
        top_frame = tk.Frame(self.root)
        top_frame.pack(side=tk.TOP, fill=tk.X)
        
        bottom_frame = tk.Frame(self.root)
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        # キャンバスの設定
        self.canvas = tk.Canvas(self.root, width=self.canvas_width, height=self.canvas_height, bg="white")
        self.canvas.pack(expand=tk.YES, fill=tk.BOTH)
        
        # マウスイベントのバインド
        self.canvas.bind("<Button-1>", self.start_draw)
        self.canvas.bind("<B1-Motion>", self.draw)
        self.canvas.bind("<ButtonRelease-1>", self.stop_draw)
        
        # ツールバーボタンの設定
        # ペンツール
        pen_button = tk.Button(top_frame, text="ペン", command=lambda: self.change_tool("pen"))
        pen_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        # 消しゴムツール
        eraser_button = tk.Button(top_frame, text="消しゴム", command=lambda: self.change_tool("eraser"))
        eraser_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        # 色を選択するボタン
        color_button = tk.Button(top_frame, text="色を選択", command=self.choose_color)
        color_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        # 現在の色を表示するラベル
        self.color_display = tk.Label(top_frame, bg=self.current_color, width=3)
        self.color_display.pack(side=tk.LEFT, padx=5, pady=5)
        
        # ブラシサイズの選択
        tk.Label(top_frame, text="ブラシサイズ:").pack(side=tk.LEFT, padx=5, pady=5)
        self.size_slider = tk.Scale(top_frame, from_=1, to=50, orient=tk.HORIZONTAL, command=self.change_brush_size)
        self.size_slider.set(self.brush_size)
        self.size_slider.pack(side=tk.LEFT, padx=5, pady=5)
        
        # 保存ボタン
        save_button = tk.Button(bottom_frame, text="保存", command=self.save_image)
        save_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        # 読み込みボタン
        load_button = tk.Button(bottom_frame, text="読み込み", command=self.load_image)
        load_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        # キャンバスをクリアするボタン
        clear_button = tk.Button(bottom_frame, text="クリア", command=self.clear_canvas)
        clear_button.pack(side=tk.LEFT, padx=5, pady=5)
        
    def start_draw(self, event):
        """
        描画開始時の処理
        
        Args:
            event: マウスイベント
        """
        self.prev_x = event.x
        self.prev_y = event.y
        
    def draw(self, event):
        """
        描画中の処理
        
        Args:
            event: マウスイベント
        """
        if self.prev_x and self.prev_y:
            x, y = event.x, event.y
            
            # キャンバスに描画
            if self.tool == "pen":
                self.canvas.create_line(
                    self.prev_x, self.prev_y, x, y,
                    width=self.brush_size,
                    fill=self.current_color,
                    capstyle=tk.ROUND,
                    smooth=tk.TRUE
                )
                # 描画データにも保存
                self.drawing_data_draw.line(
                    (self.prev_x, self.prev_y, x, y),
                    fill=self.current_color,
                    width=self.brush_size
                )
            elif self.tool == "eraser":
                self.canvas.create_line(
                    self.prev_x, self.prev_y, x, y,
                    width=self.brush_size,
                    fill="white",
                    capstyle=tk.ROUND,
                    smooth=tk.TRUE
                )
                # 描画データにも保存
                self.drawing_data_draw.line(
                    (self.prev_x, self.prev_y, x, y),
                    fill="white",
                    width=self.brush_size
                )
            
            self.prev_x = x
            self.prev_y = y
            
    def stop_draw(self, event):
        """
        描画終了時の処理
        
        Args:
            event: マウスイベント
        """
        self.prev_x = None
        self.prev_y = None
        
    def change_tool(self, tool):
        """
        描画ツールを変更する
        
        Args:
            tool: 選択するツール
        """
        self.tool = tool
        
    def choose_color(self):
        """
        色選択ダイアログを表示して色を選択する
        """
        color = colorchooser.askcolor(initialcolor=self.current_color)[1]
        if color:
            self.current_color = color
            self.color_display.config(bg=color)
            
    def change_brush_size(self, size):
        """
        ブラシサイズを変更する
        
        Args:
            size: 新しいブラシサイズ
        """
        self.brush_size = int(size)
        
    def save_image(self):
        """
        描画した画像を保存する
        """
        file_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("JPEG files", "*.jpg"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                self.drawing_data.save(file_path)
                messagebox.showinfo("保存成功", f"画像が保存されました: {file_path}")
            except Exception as e:
                messagebox.showerror("保存エラー", f"画像の保存中にエラーが発生しました: {e}")
                
    def load_image(self):
        """
        画像をロードして表示する
        """
        file_path = filedialog.askopenfilename(
            filetypes=[("PNG files", "*.png"), ("JPEG files", "*.jpg"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                # キャンバスをクリア
                self.clear_canvas()
                
                # 画像を読み込む
                loaded_image = Image.open(file_path)
                
                # リサイズが必要な場合はリサイズする
                if loaded_image.width != self.canvas_width or loaded_image.height != self.canvas_height:
                    loaded_image = loaded_image.resize((self.canvas_width, self.canvas_height))
                
                # 描画データを更新
                self.drawing_data = loaded_image
                self.drawing_data_draw = ImageDraw.Draw(self.drawing_data)
                
                # キャンバスに表示
                from PIL import ImageTk
                self.photo = ImageTk.PhotoImage(loaded_image)
                self.canvas.create_image(0, 0, image=self.photo, anchor=tk.NW)
                
                messagebox.showinfo("読み込み成功", f"画像を読み込みました: {file_path}")
                
            except Exception as e:
                messagebox.showerror("読み込みエラー", f"画像の読み込み中にエラーが発生しました: {e}")
                
    def clear_canvas(self):
        """
        キャンバスをクリアする
        """
        self.canvas.delete("all")
        self.drawing_data = Image.new("RGB", (self.canvas_width, self.canvas_height), "white")
        self.drawing_data_draw = ImageDraw.Draw(self.drawing_data)