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
        
        # 操作履歴の管理（アンドゥ/リドゥ用）
        self.history = []
        self.history_index = -1
        self.max_history = 20  # 履歴の最大数
        
        # 初期状態を履歴に保存
        self.save_state()
        
    def setup_ui(self):
        """
        UIコンポーネントの設定
        """
        # フレームの設定
        top_frame = tk.Frame(self.root, bg="#f0f0f0", pady=10)
        top_frame.pack(side=tk.TOP, fill=tk.X)
        
        bottom_frame = tk.Frame(self.root, bg="#f0f0f0", pady=10)
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        # キャンバスの設定
        canvas_frame = tk.Frame(self.root)
        canvas_frame.pack(expand=tk.YES, fill=tk.BOTH, padx=10, pady=10)
        
        self.canvas = tk.Canvas(canvas_frame, width=self.canvas_width, height=self.canvas_height, 
                                bg="white", relief=tk.SUNKEN, bd=2)
        self.canvas.pack(expand=tk.YES, fill=tk.BOTH)
        
        # マウスイベントのバインド
        self.canvas.bind("<Button-1>", self.start_draw)
        self.canvas.bind("<B1-Motion>", self.draw)
        self.canvas.bind("<ButtonRelease-1>", self.stop_draw)
        
        # ツールフレーム
        tools_frame = tk.Frame(top_frame, bg="#f0f0f0")
        tools_frame.pack(side=tk.LEFT, padx=10)
        
        tk.Label(tools_frame, text="ツール:", bg="#f0f0f0").pack(side=tk.LEFT, padx=5)
        
        # ツールバーボタンの設定
        # ペンツール
        self.pen_button = tk.Button(tools_frame, text="ペン", 
                             bg="#e0e0e0", relief=tk.SUNKEN,
                             command=lambda: self.change_tool("pen"))
        self.pen_button.pack(side=tk.LEFT, padx=2)
        
        # 消しゴムツール
        self.eraser_button = tk.Button(tools_frame, text="消しゴム", 
                                bg="#e0e0e0", relief=tk.RAISED,
                                command=lambda: self.change_tool("eraser"))
        self.eraser_button.pack(side=tk.LEFT, padx=2)
        
        # 塗りつぶしツール
        self.fill_button = tk.Button(tools_frame, text="塗りつぶし", 
                              bg="#e0e0e0", relief=tk.RAISED,
                              command=lambda: self.change_tool("fill"))
        self.fill_button.pack(side=tk.LEFT, padx=2)
        
        # 色を選択するフレーム
        color_frame = tk.Frame(top_frame, bg="#f0f0f0")
        color_frame.pack(side=tk.LEFT, padx=10)
        
        # 色を選択するボタン
        color_button = tk.Button(color_frame, text="色を選択", bg="#e0e0e0", command=self.choose_color)
        color_button.pack(side=tk.LEFT, padx=2)
        
        # 現在の色を表示するラベル
        self.color_display = tk.Label(color_frame, bg=self.current_color, width=3, height=1, relief=tk.SUNKEN, bd=2)
        self.color_display.pack(side=tk.LEFT, padx=5)
        
        # ブラシサイズフレーム
        brush_frame = tk.Frame(top_frame, bg="#f0f0f0")
        brush_frame.pack(side=tk.LEFT, padx=10)
        
        # ブラシサイズの選択
        tk.Label(brush_frame, text="ブラシサイズ:", bg="#f0f0f0").pack(side=tk.LEFT)
        self.size_slider = tk.Scale(brush_frame, from_=1, to=50, orient=tk.HORIZONTAL, 
                                   bg="#f0f0f0", command=self.change_brush_size)
        self.size_slider.set(self.brush_size)
        self.size_slider.pack(side=tk.LEFT, padx=5)
        
        # ファイル操作フレーム
        file_frame = tk.Frame(bottom_frame, bg="#f0f0f0")
        file_frame.pack(side=tk.LEFT, padx=10)
        
        # 保存ボタン
        save_button = tk.Button(file_frame, text="保存", bg="#e0e0e0", command=self.save_image)
        save_button.pack(side=tk.LEFT, padx=2)
        
        # 読み込みボタン
        load_button = tk.Button(file_frame, text="読み込み", bg="#e0e0e0", command=self.load_image)
        load_button.pack(side=tk.LEFT, padx=2)
        
        # キャンバス操作フレーム
        canvas_ops_frame = tk.Frame(bottom_frame, bg="#f0f0f0")
        canvas_ops_frame.pack(side=tk.LEFT, padx=10)
        
        # キャンバスをクリアするボタン
        clear_button = tk.Button(canvas_ops_frame, text="クリア", bg="#e0e0e0", command=self.clear_canvas)
        clear_button.pack(side=tk.LEFT, padx=2)
        
        # 履歴操作フレーム
        history_frame = tk.Frame(bottom_frame, bg="#f0f0f0")
        history_frame.pack(side=tk.LEFT, padx=10)
        
        # 元に戻すボタン（アンドゥ）
        undo_button = tk.Button(history_frame, text="元に戻す", bg="#e0e0e0", command=self.undo)
        undo_button.pack(side=tk.LEFT, padx=2)
        
        # やり直しボタン（リドゥ）
        redo_button = tk.Button(history_frame, text="やり直し", bg="#e0e0e0", command=self.redo)
        redo_button.pack(side=tk.LEFT, padx=2)
        
    def start_draw(self, event):
        """
        描画開始時の処理
        
        Args:
            event: マウスイベント
        """
        if self.tool == "fill":
            self.flood_fill(event.x, event.y)
        else:
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
        
        # 描画が終わったら状態を保存
        if self.tool != "fill":  # 塗りつぶしは別で処理
            self.save_state()
        
    def change_tool(self, tool):
        """
        描画ツールを変更する
        
        Args:
            tool: 選択するツール
        """
        self.tool = tool
        
        # ボタンの見た目を更新
        self.pen_button.config(relief=tk.SUNKEN if tool == "pen" else tk.RAISED)
        self.eraser_button.config(relief=tk.SUNKEN if tool == "eraser" else tk.RAISED)
        self.fill_button.config(relief=tk.SUNKEN if tool == "fill" else tk.RAISED)
        
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
        
    def flood_fill(self, x, y):
        """
        指定された位置から塗りつぶしを行う
        
        Args:
            x: X座標
            y: Y座標
        """
        # 座標が画像範囲内かチェック
        if x < 0 or x >= self.canvas_width or y < 0 or y >= self.canvas_height:
            return
            
        # 現在の色をRGBタプルに変換
        fill_color = self.hex_to_rgb(self.current_color)
        
        # クリックした位置の色を取得
        target_color = self.drawing_data.getpixel((x, y))
        
        # 塗りつぶす色と同じ場合は何もしない
        if target_color == fill_color:
            return
            
        # PILのImageDrawを使って塗りつぶし
        try:
            from PIL import ImageDraw
            # PIL 10.0.0以降ではfloodfill関数を使用
            ImageDraw.floodfill(self.drawing_data, (x, y), fill_color)
            
            # キャンバスを更新
            self.update_canvas_from_image()
            self.save_state()  # 状態を保存
            
        except Exception as e:
            # フォールバック: 独自の塗りつぶしアルゴリズム
            self.custom_flood_fill(x, y, target_color, fill_color)
            
    def hex_to_rgb(self, hex_color):
        """
        16進数カラーコードをRGBタプルに変換
        
        Args:
            hex_color: #RRGGBBの形式の色
            
        Returns:
            (R, G, B)のタプル
        """
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        
    def custom_flood_fill(self, x, y, target_color, fill_color):
        """
        カスタム塗りつぶしアルゴリズム（フォールバック用）
        
        Args:
            x, y: 開始座標
            target_color: 置き換え対象の色
            fill_color: 塗りつぶす色
        """
        if target_color == fill_color:
            return
            
        # スタックベースの塗りつぶしアルゴリズム
        stack = [(x, y)]
        pixels = self.drawing_data.load()
        
        while stack:
            current_x, current_y = stack.pop()
            
            if (current_x < 0 or current_x >= self.canvas_width or 
                current_y < 0 or current_y >= self.canvas_height):
                continue
                
            if pixels[current_x, current_y] != target_color:
                continue
                
            pixels[current_x, current_y] = fill_color
            
            # 隣接する4方向のピクセルをスタックに追加
            stack.append((current_x + 1, current_y))
            stack.append((current_x - 1, current_y))
            stack.append((current_x, current_y + 1))
            stack.append((current_x, current_y - 1))
            
        # キャンバスを更新
        self.update_canvas_from_image()
        self.save_state()  # 状態を保存
        
    def update_canvas_from_image(self):
        """
        PIL Imageデータからキャンバスを更新
        """
        try:
            from PIL import ImageTk
            # 現在のキャンバスをクリア
            self.canvas.delete("all")
            
            # PIL ImageをTkinter用に変換して表示
            self.photo = ImageTk.PhotoImage(self.drawing_data)
            self.canvas.create_image(0, 0, image=self.photo, anchor=tk.NW)
            
        except Exception as e:
            print(f"キャンバス更新エラー: {e}")
        
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
                
                # 状態を履歴に保存
                self.save_state()
                
                messagebox.showinfo("読み込み成功", f"画像を読み込みました: {file_path}")
                
            except Exception as e:
                messagebox.showerror("読み込みエラー", f"画像の読み込み中にエラーが発生しました: {e}")
                
    def clear_canvas(self):
        """
        キャンバスをクリアする
        """
        self.save_state()  # 現在の状態を保存してからクリア
        self.canvas.delete("all")
        self.drawing_data = Image.new("RGB", (self.canvas_width, self.canvas_height), "white")
        self.drawing_data_draw = ImageDraw.Draw(self.drawing_data)
        
    def save_state(self):
        """
        現在のキャンバスの状態を履歴に保存する
        """
        # 履歴に新しい状態を追加すると、それより後の履歴は破棄される
        if self.history_index < len(self.history) - 1:
            self.history = self.history[:self.history_index + 1]
            
        # 現在の描画データをコピーして保存
        current_state = self.drawing_data.copy()
        
        # 履歴の上限を超える場合、最も古い履歴を削除
        if len(self.history) >= self.max_history:
            self.history.pop(0)
            # インデックスを調整（先頭を削除したので1つ減らす）
            # ただしインデックスは増加させる必要がある（新しい状態を追加するため）
            # 結果として相殺されてインデックスは変わらない
        else:
            self.history_index += 1
            
        self.history.append(current_state)
        
    def undo(self):
        """
        1つ前の状態に戻す
        """
        if self.history_index > 0:
            self.history_index -= 1
            self.drawing_data = self.history[self.history_index].copy()
            self.drawing_data_draw = ImageDraw.Draw(self.drawing_data)
            self.update_canvas_from_image()
            
    def redo(self):
        """
        取り消した操作をやり直す
        """
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            self.drawing_data = self.history[self.history_index].copy()
            self.drawing_data_draw = ImageDraw.Draw(self.drawing_data)
            self.update_canvas_from_image()