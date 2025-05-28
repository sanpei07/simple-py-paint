#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ストローク予測のためのシンプルな予測モジュール
Googleのmagentaのsketch-rnnを利用したストローク予測もサポート
"""

from typing import List, Tuple, Optional
import os
import numpy as np

try:
    import tensorflow as tf
    from magenta.models.sketch_rnn import model as sketch_rnn_model
    from magenta.models.sketch_rnn import utils as sketch_rnn_utils
    SKETCH_RNN_AVAILABLE = True
except ImportError:
    SKETCH_RNN_AVAILABLE = False

class StrokePredictor:
    """
    ストロークの予測を行うクラス
    """
    def __init__(self, points_to_consider: int = 5, prediction_steps: int = 10, smoothing_factor: float = 0.8, 
                 use_sketch_rnn: bool = False, model_path: str = None):
        """
        ストローク予測機能の初期化
        
        Args:
            points_to_consider: 予測に使用する過去のポイント数
            prediction_steps: 予測するポイント数
            smoothing_factor: 予測の滑らかさを調整する係数 (0.0〜1.0)
            use_sketch_rnn: sketch-rnnモデルを使用するかどうか
            model_path: sketch-rnnモデルのパス（Noneの場合はデフォルトモデルを使用）
        """
        self.points_to_consider = points_to_consider
        self.prediction_steps = prediction_steps
        self.smoothing_factor = smoothing_factor
        self.stroke_history: List[Tuple[int, int]] = []
        self.predicted_points: List[Tuple[int, int]] = []
        
        # sketch-rnn関連の設定
        self.use_sketch_rnn = use_sketch_rnn and SKETCH_RNN_AVAILABLE
        self.model_path = model_path
        self.sketch_rnn_model = None
        self.model_loaded = False
        
        # sketch-rnnモデルを読み込む
        if self.use_sketch_rnn:
            self.load_sketch_rnn_model()
        
    def load_sketch_rnn_model(self) -> bool:
        """
        sketch-rnnモデルを読み込む
        
        Returns:
            モデル読み込みの成否
        """
        if not SKETCH_RNN_AVAILABLE:
            print("警告: magentaまたはtensorflowがインストールされていないため、sketch-rnnは利用できません")
            return False
        
        try:
            # デフォルトのモデルパスを設定（モデルパスが指定されていない場合）
            if self.model_path is None:
                self.model_path = "https://storage.googleapis.com/quickdraw-models/sketchRNN/large_models/cat.gen.h5"
            
            # モデルの設定
            model_dir = os.path.dirname(self.model_path)
            model_name = os.path.basename(self.model_path).split('.')[0]
            
            # モデルのハイパーパラメータ読み込み
            # sketch-rnn用のモデル設定
            model_params = sketch_rnn_model.get_default_hparams()
            model_params.data_set = model_name
            
            # sketch-rnnモデルの初期化
            self.sketch_rnn_model = sketch_rnn_model.Model(model_params)
            
            # モデルを読み込む
            self.sketch_rnn_model.load_model(self.model_path)
            self.model_loaded = True
            print(f"sketch-rnnモデルの読み込み成功: {self.model_path}")
            return True
        except Exception as e:
            print(f"sketch-rnnモデルの読み込み失敗: {str(e)}")
            self.model_loaded = False
            self.use_sketch_rnn = False
            return False
    
    def _convert_points_to_sketch_rnn_format(self) -> np.ndarray:
        """
        ストローク履歴をsketch-rnn形式に変換
        
        Returns:
            sketch-rnn形式のストロークデータ
        """
        if len(self.stroke_history) < 2:
            return np.zeros((1, 5))
        
        # sketch-rnnの形式に変換 (dx, dy, p1, p2, p3)
        # p1, p2, p3は各ペンの状態（線を描いている、ペンを上げる、スケッチ終了）
        strokes = []
        prev_x, prev_y = self.stroke_history[0]
        
        for i in range(1, len(self.stroke_history)):
            x, y = self.stroke_history[i]
            dx = x - prev_x
            dy = y - prev_y
            
            # 最後の点以外はペンダウン(線を描いている)状態
            if i < len(self.stroke_history) - 1:
                strokes.append([dx, dy, 1, 0, 0])  # ペンダウン
            else:
                strokes.append([dx, dy, 0, 1, 0])  # ペンアップ
            
            prev_x, prev_y = x, y
            
        return np.array(strokes)
            
    def add_point(self, x: int, y: int) -> None:
        """
        ストロークの点を追加
        
        Args:
            x: X座標
            y: Y座標
        """
        self.stroke_history.append((x, y))
        if len(self.stroke_history) > 100:  # 履歴は100点に制限
            self.stroke_history = self.stroke_history[-100:]
            
    def predict_next_points(self) -> List[Tuple[int, int]]:
        """
        次のストロークポイントを予測
        
        Returns:
            予測されたポイントのリスト
        """
        if len(self.stroke_history) < self.points_to_consider:
            return []
        
        # sketch-rnnモデルが有効な場合はそれを使用
        if self.use_sketch_rnn and self.model_loaded:
            return self._predict_with_sketch_rnn()
        else:
            # 従来の予測手法を使用
            return self._predict_with_simple_model()
            
    def _predict_with_sketch_rnn(self) -> List[Tuple[int, int]]:
        """
        sketch-rnnモデルを使用して次のストロークポイントを予測
        
        Returns:
            予測されたポイントのリスト
        """
        if not self.model_loaded or len(self.stroke_history) < 2:
            return []
            
        try:
            # 現在のストロークをsketch-rnn形式に変換
            strokes = self._convert_points_to_sketch_rnn_format()
            
            # モデルの状態を初期化
            prev_state = self.sketch_rnn_model.zero_state(batch_size=1)
            
            # ストロークをエンコード
            prev_x = np.zeros((1, 5))
            for i in range(len(strokes)):
                enc_out, prev_state = self.sketch_rnn_model.encode(prev_x, strokes[i:i+1], prev_state)
                prev_x = strokes[i:i+1]
            
            # 予測結果を保存するリスト
            predicted = []
            
            # 最後の点を開始点として設定
            curr_x, curr_y = self.stroke_history[-1]
            
            # 予測を実行
            for _ in range(self.prediction_steps):
                # 次のストロークを予測
                next_stroke, prev_state = self.sketch_rnn_model.decode(prev_x, prev_state)
                
                # 予測結果から次の座標を計算
                dx, dy = next_stroke[0, 0], next_stroke[0, 1]
                next_x = round(curr_x + dx)
                next_y = round(curr_y + dy)
                
                predicted.append((next_x, next_y))
                
                # 次のステップのためにcurrent pointとprev_xを更新
                curr_x, curr_y = next_x, next_y
                prev_x = next_stroke
                
            self.predicted_points = predicted
            return predicted
            
        except Exception as e:
            print(f"sketch-rnn予測エラー: {str(e)}")
            # エラーが発生した場合はシンプルなモデルにフォールバック
            return self._predict_with_simple_model()
            
    def _predict_with_simple_model(self) -> List[Tuple[int, int]]:
    def _predict_with_simple_model(self) -> List[Tuple[int, int]]:
        """
        シンプルな予測モデルを使用して次のストロークポイントを予測
        
        Returns:
            予測されたポイントのリスト
        """
        # 予測のために最新のポイントを取得
        recent_points = self.stroke_history[-self.points_to_consider:]
        
        # ポイント間の差分を計算
        dx_list = []
        dy_list = []
        for i in range(1, len(recent_points)):
            dx = recent_points[i][0] - recent_points[i-1][0]
            dy = recent_points[i][1] - recent_points[i-1][1]
            dx_list.append(dx)
            dy_list.append(dy)
            
        if not dx_list or not dy_list:
            return []
            
        # 平均移動方向を計算
        avg_dx = sum(dx_list) / len(dx_list)
        avg_dy = sum(dy_list) / len(dy_list)
        
        # 最近の動きの加速度を考慮
        if len(dx_list) >= 2:
            accel_x = dx_list[-1] - dx_list[0]
            accel_y = dy_list[-1] - dy_list[0]
            
            # 加速度を平滑化
            accel_x *= self.smoothing_factor
            accel_y *= self.smoothing_factor
        else:
            accel_x = 0
            accel_y = 0
        
        # 予測ポイントを生成
        last_point = recent_points[-1]
        predicted = []
        
        curr_x, curr_y = last_point
        curr_dx, curr_dy = avg_dx, avg_dy
        
        for _ in range(self.prediction_steps):
            # 加速度を考慮して移動方向を更新
            curr_dx += accel_x / self.prediction_steps
            curr_dy += accel_y / self.prediction_steps
            
            # 次のポイントを計算
            next_x = round(curr_x + curr_dx)
            next_y = round(curr_y + curr_dy)
            
            predicted.append((next_x, next_y))
            
            # 次のステップのためにcurrent pointを更新
            curr_x, curr_y = next_x, next_y
            
        self.predicted_points = predicted
        return predicted

    def clear(self) -> None:
        """
        ストローク履歴と予測をクリア
        """
        self.stroke_history = []
        self.predicted_points = []