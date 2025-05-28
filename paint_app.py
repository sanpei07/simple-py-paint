#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
シンプルなペイントアプリケーションのメインクラス
"""

import tkinter as tk
from tkinter import colorchooser, filedialog, messagebox
import os
from PIL import Image, ImageDraw

# ストローク予測のインポート
from models.stroke_predictor import StrokePredictor

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
        
        # ストローク予測の設定
        self.stroke_prediction_enabled = False
        self.stroke_predictor = StrokePredictor()
        self.prediction_ids = []  # キャンバス上の予測線のID
        
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
        
        # キャンバスの初期表示を更新（境界線を表示するため）
        self.update_canvas_from_image()
        
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
        
        # ブラシプレビュー用のマウス移動イベントをバインド
        self.canvas.bind("<Motion>", self.show_brush_preview)
        self.canvas.bind("<Leave>", self.hide_brush_preview)
        
        # ブラシプレビュー用の変数
        self.brush_preview_id = None
        
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
        
        # ストローク予測フレーム
        prediction_frame = tk.Frame(top_frame, bg="#f0f0f0")
        prediction_frame.pack(side=tk.LEFT, padx=10)
        
        # ストローク予測チェックボックス
        self.prediction_var = tk.BooleanVar()
        self.prediction_var.set(self.stroke_prediction_enabled)
        self.prediction_checkbox = tk.Checkbutton(prediction_frame, text="ストローク予測", bg="#f0f0f0", 
                                                 variable=self.prediction_var, 
                                                 command=self.toggle_prediction)
        self.prediction_checkbox.pack(side=tk.LEFT, padx=5)
        
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
        
        # キャンバスサイズ変更フレーム
        canvas_size_frame = tk.Frame(bottom_frame, bg="#f0f0f0")
        canvas_size_frame.pack(side=tk.LEFT, padx=10)
        
        tk.Label(canvas_size_frame, text="サイズ:", bg="#f0f0f0").pack(side=tk.LEFT)
        
        # 幅入力
        tk.Label(canvas_size_frame, text="幅:", bg="#f0f0f0").pack(side=tk.LEFT, padx=(5,0))
        self.width_entry = tk.Entry(canvas_size_frame, width=6)
        self.width_entry.pack(side=tk.LEFT, padx=2)
        self.width_entry.insert(0, str(self.canvas_width))
        
        # 高さ入力
        tk.Label(canvas_size_frame, text="高さ:", bg="#f0f0f0").pack(side=tk.LEFT, padx=(5,0))
        self.height_entry = tk.Entry(canvas_size_frame, width=6)
        self.height_entry.pack(side=tk.LEFT, padx=2)
        self.height_entry.insert(0, str(self.canvas_height))
        
        # サイズ変更ボタン
        resize_button = tk.Button(canvas_size_frame, text="サイズ変更", bg="#e0e0e0", command=self.resize_canvas)
        resize_button.pack(side=tk.LEFT, padx=5)
        
        # 履歴操作フレーム
        history_frame = tk.Frame(bottom_frame, bg="#f0f0f0")
        history_frame.pack(side=tk.LEFT, padx=10)
        
        # 元に戻すボタン（アンドゥ）
        undo_button = tk.Button(history_frame, text="元に戻す", bg="#e0e0e0", command=self.undo)
        undo_button.pack(side=tk.LEFT, padx=2)
        
        # やり直しボタン（リドゥ）
        redo_button = tk.Button(history_frame, text="やり直し", bg="#e0e0e0", command=self.redo)
        redo_button.pack(side=tk.LEFT, padx=2)
        
    def toggle_prediction(self):
        """
        ストローク予測機能の有効/無効を切り替える
        """
        self.stroke_prediction_enabled = self.prediction_var.get()
        
        # 予測を非表示
        self.clear_predictions()
        
        if self.stroke_prediction_enabled:
            # 予測が有効になったらストローク履歴をクリア
            self.stroke_predictor.clear()
            print("ストローク予測が有効になりました")
        else:
            print("ストローク予測が無効になりました")
            
    def clear_predictions(self):
        """
        キャンバスから全ての予測を削除
        """
        for pred_id in self.prediction_ids:
            self.canvas.delete(pred_id)
        self.prediction_ids = []
        
    def show_predictions(self):
        """
        現在のストロークに基づいて予測を表示
        """
        if not self.stroke_prediction_enabled or self.tool != "pen":
            return
            
        # 現在の予測を削除
        self.clear_predictions()
        
        # 新しい予測を取得
        predicted_points = self.stroke_predictor.predict_next_points()
        
        if len(predicted_points) < 2:
            return
            
        # 予測線の色 (薄い青色)
        prediction_color = "#0078D7"
        
        # 予測線を描画（点線と半透明を表現）
        for i in range(len(predicted_points) - 1):
            x1, y1 = predicted_points[i]
            x2, y2 = predicted_points[i + 1]
            
            # 予測の確実性を表現するため、遠くなるほど線を薄くする
            opacity = max(10, 70 - i * 6)  # 70%から始めて徐々に薄く
            dash_pattern = (4, 2 + i // 2)  # 予測が遠くなるほど点線間隔を広げる
            
            # 予測線をキャンバスに追加して、IDを保存
            line_id = self.canvas.create_line(
                x1, y1, x2, y2,
                width=max(1, self.brush_size // 2),
                fill=prediction_color,
                dash=dash_pattern,
                stipple="gray50",  # 半透明効果
                capstyle=tk.ROUND,
            )
            self.prediction_ids.append(line_id)
            
    def start_draw(self, event):
        """
        描画開始時の処理
        
        Args:
            event: マウスイベント
        """
        # 描画中はプレビューを非表示にする
        if self.brush_preview_id:
            self.canvas.delete(self.brush_preview_id)
            self.brush_preview_id = None
            
        # 予測を消去
        self.clear_predictions()
        
        if self.tool == "fill":
            self.flood_fill(event.x, event.y)
        else:
            # キャンバス境界内に座標を制限
            x = max(0, min(event.x, self.canvas_width - 1))
            y = max(0, min(event.y, self.canvas_height - 1))
            self.prev_x = x
            self.prev_y = y
            
            # ストローク予測のためにポイントを記録
            if self.stroke_prediction_enabled and self.tool == "pen":
                self.stroke_predictor.add_point(x, y)
        
    def draw(self, event):
        """
        描画中の処理
        
        Args:
            event: マウスイベント
        """
        if self.prev_x and self.prev_y:
            # キャンバス境界内に座標を制限
            x = max(0, min(event.x, self.canvas_width - 1))
            y = max(0, min(event.y, self.canvas_height - 1))
            
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
                
                # ストローク予測のために点を記録
                if self.stroke_prediction_enabled:
                    self.stroke_predictor.add_point(x, y)
                    
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
                
                # 消しゴムで描画した場合、境界線を再描画
                self.draw_canvas_border()
            
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
            
        # ストローク予測が有効な場合、予測を表示
        if self.stroke_prediction_enabled and self.tool == "pen":
            self.show_predictions()
        
        # 描画終了後、再度プレビューを表示する
        self.show_brush_preview(event)
        
    def change_tool(self, tool):
        """
        描画ツールを変更する
        
        Args:
            tool: 選択するツール
        """
        self.tool = tool
        
        # 予測をクリア
        self.clear_predictions()
        
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
        x = max(0, min(x, self.canvas_width - 1))
        y = max(0, min(y, self.canvas_height - 1))
        
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
            
            # 予測をクリア
            self.prediction_ids = []
            
            # キャンバスの境界を描画
            self.draw_canvas_border()
            
        except Exception as e:
            print(f"キャンバス更新エラー: {e}")
            
    def draw_canvas_border(self):
        """
        キャンバスの境界線を描画する
        """
        # キャンバスの境界を可視化する（破線の長方形を描画）
        self.canvas.create_rectangle(
            0, 0, self.canvas_width - 1, self.canvas_height - 1,
            outline="#0078D7", dash=(4, 4), width=1, tags="canvas_border"
        )
        
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
                    # キャンバスサイズを読み込んだ画像に合わせるかユーザーに確認
                    result = messagebox.askyesnocancel(
                        "サイズ調整",
                        f"読み込んだ画像のサイズ ({loaded_image.width}x{loaded_image.height}) がキャンバスサイズ ({self.canvas_width}x{self.canvas_height}) と異なります。\n\n" +
                        "「はい」: キャンバスサイズを画像に合わせる\n" +
                        "「いいえ」: 画像をキャンバスサイズにリサイズする\n" +
                        "「キャンセル」: 読み込みを中止する"
                    )
                    
                    if result is None:  # キャンセル
                        return
                    elif result:  # はい - キャンバスサイズを画像に合わせる
                        self.canvas_width = loaded_image.width
                        self.canvas_height = loaded_image.height
                        
                        # エントリーフィールドを更新
                        self.width_entry.delete(0, tk.END)
                        self.width_entry.insert(0, str(self.canvas_width))
                        self.height_entry.delete(0, tk.END)
                        self.height_entry.insert(0, str(self.canvas_height))
                        
                        # キャンバスウィジェットのサイズを更新
                        self.canvas.config(width=self.canvas_width, height=self.canvas_height)
                    else:  # いいえ - 画像をリサイズ
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
        
        # ストローク予測データもクリア
        self.stroke_predictor.clear()
        self.clear_predictions()
        
        # キャンバスをクリアした後に境界線を再描画
        self.draw_canvas_border()
        
    def resize_canvas(self):
        """
        キャンバスのサイズを変更する
        """
        try:
            # 入力値を取得
            new_width = int(self.width_entry.get())
            new_height = int(self.height_entry.get())
            
            # 値の範囲チェック
            if new_width < 50 or new_width > 2000 or new_height < 50 or new_height > 2000:
                messagebox.showerror("サイズエラー", "キャンバスサイズは50から2000の範囲で設定してください")
                return
                
            # 現在のサイズと同じ場合は何もしない
            if new_width == self.canvas_width and new_height == self.canvas_height:
                return
                
            # 現在の状態を保存
            self.save_state()
            
            # 古い描画データを保存
            old_drawing_data = self.drawing_data.copy()
            
            # 新しいサイズを設定
            self.canvas_width = new_width
            self.canvas_height = new_height
            
            # 新しい描画データを作成
            self.drawing_data = Image.new("RGB", (self.canvas_width, self.canvas_height), "white")
            self.drawing_data_draw = ImageDraw.Draw(self.drawing_data)
            
            # 既存の描画内容を新しいキャンバスにコピー（可能な範囲で）
            paste_width = min(old_drawing_data.width, self.canvas_width)
            paste_height = min(old_drawing_data.height, self.canvas_height)
            
            if paste_width > 0 and paste_height > 0:
                # 既存の内容を左上から貼り付け
                crop_box = (0, 0, paste_width, paste_height)
                cropped_old_data = old_drawing_data.crop(crop_box)
                self.drawing_data.paste(cropped_old_data, (0, 0))
            
            # キャンバスウィジェットのサイズを更新
            self.canvas.config(width=self.canvas_width, height=self.canvas_height)
            
            # ストローク予測データをクリア
            self.stroke_predictor.clear()
            self.clear_predictions()
            
            # キャンバスの表示を更新
            self.update_canvas_from_image()
            
            messagebox.showinfo("サイズ変更完了", f"キャンバスサイズを {self.canvas_width}x{self.canvas_height} に変更しました")
            
        except ValueError:
            messagebox.showerror("入力エラー", "幅と高さには有効な数値を入力してください")
        except Exception as e:
            messagebox.showerror("サイズ変更エラー", f"キャンバスサイズの変更中にエラーが発生しました: {e}")
        
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
            
    def show_brush_preview(self, event):
        """
        マウス位置にブラシサイズのプレビューを表示
        
        Args:
            event: マウスイベント
        """
        # ツールが「塗りつぶし」の場合はプレビューを表示しない
        if self.tool == "fill":
            self.hide_brush_preview(None)
            return
            
        # キャンバス境界内に座標を制限
        x = max(0, min(event.x, self.canvas_width - 1))
        y = max(0, min(event.y, self.canvas_height - 1))
        
        # 以前のプレビューを削除
        if self.brush_preview_id:
            self.canvas.delete(self.brush_preview_id)
        
        # ツールに応じた色を設定
        preview_color = "#0078D7" if self.tool == "pen" else "#FF0000"
        
        # ブラシプレビューを描画（円または輪郭のみの円）
        if self.tool == "pen":
            # 塗りつぶしなしの輪郭のみの円（ペンツールの場合）
            self.brush_preview_id = self.canvas.create_oval(
                x - self.brush_size//2, y - self.brush_size//2,
                x + self.brush_size//2, y + self.brush_size//2,
                outline=preview_color, width=1
            )
        elif self.tool == "eraser":
            # 塗りつぶしなしの輪郭のみの円（消しゴムツールの場合）
            self.brush_preview_id = self.canvas.create_oval(
                x - self.brush_size//2, y - self.brush_size//2,
                x + self.brush_size//2, y + self.brush_size//2,
                outline=preview_color, width=1
            )
    
    def hide_brush_preview(self, event):
        """
        ブラシプレビューを非表示にする
        
        Args:
            event: マウスイベント
        """
        if self.brush_preview_id:
            self.canvas.delete(self.brush_preview_id)
            self.brush_preview_id = None