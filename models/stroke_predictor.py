#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ストローク予測のためのシンプルな予測モジュール
"""

from typing import List, Tuple, Optional

class StrokePredictor:
    """
    ストロークの予測を行うクラス
    """
    def __init__(self, points_to_consider: int = 5, prediction_steps: int = 10, smoothing_factor: float = 0.8):
        """
        ストローク予測機能の初期化
        
        Args:
            points_to_consider: 予測に使用する過去のポイント数
            prediction_steps: 予測するポイント数
            smoothing_factor: 予測の滑らかさを調整する係数 (0.0〜1.0)
        """
        self.points_to_consider = points_to_consider
        self.prediction_steps = prediction_steps
        self.smoothing_factor = smoothing_factor
        self.stroke_history: List[Tuple[int, int]] = []
        self.predicted_points: List[Tuple[int, int]] = []
        
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