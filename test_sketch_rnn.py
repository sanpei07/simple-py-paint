#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
sketch-rnnの動作確認テスト
"""

from models.stroke_predictor import StrokePredictor, SKETCH_RNN_AVAILABLE

def test_sketch_rnn_availability():
    print(f"sketch-rnnが利用可能かどうか: {SKETCH_RNN_AVAILABLE}")
    
    # 通常モード
    predictor = StrokePredictor(use_sketch_rnn=False)
    print(f"通常モードでのuse_sketch_rnn: {predictor.use_sketch_rnn}")
    
    # sketch-rnnモード（利用可能かどうかに関わらず）
    predictor = StrokePredictor(use_sketch_rnn=True)
    print(f"sketch-rnnモードでのuse_sketch_rnn: {predictor.use_sketch_rnn}")
    print(f"モデルがロードされているか: {predictor.model_loaded}")
    
    # 予測テスト
    predictor.add_point(100, 100)
    predictor.add_point(110, 110) 
    predictor.add_point(120, 120)
    predictor.add_point(130, 130)
    predictor.add_point(140, 140)
    
    points = predictor.predict_next_points()
    print(f"予測された点の数: {len(points)}")
    if len(points) > 0:
        print(f"最初の予測点: {points[0]}")
    
if __name__ == "__main__":
    test_sketch_rnn_availability()