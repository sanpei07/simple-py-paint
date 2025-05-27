# simple-py-paint

シンプルなペイントソフト

## 概要
Pythonで作成されたシンプルなペイントソフトウェアです。基本的な描画機能とファイル操作を提供します。

## 機能
- 自由に描画できるペンツール
- 消しゴムツール
- 色の選択
- ブラシサイズの調整
- 画像の保存と読み込み
- キャンバスのクリア

## 必要条件
- Python 3.x
- Tkinter (通常はPythonに同梱されています)
  - Linux: `sudo apt-get install python3-tk` でインストール
  - Windows/Mac: 通常はPythonインストール時に含まれています
- Pillow (PIL): `pip install pillow` でインストール

## インストール方法
```bash
# リポジトリのクローン
git clone https://github.com/sanpei07/simple-py-paint.git
cd simple-py-paint

# 必要なパッケージのインストール
pip install pillow
```

## 使い方
```bash
# アプリケーションを起動
python main.py
```

## 操作方法
- **ペン**: ペンツールを選択し、キャンバスにマウスを押しながら描画
- **消しゴム**: 消しゴムツールを選択し、消したい部分をマウスで消去
- **色を選択**: クリックして描画色を変更
- **ブラシサイズ**: スライダーでペンと消しゴムの太さを変更
- **保存**: 画像をPNGまたはJPGとして保存
- **読み込み**: 既存の画像を読み込んで編集
- **クリア**: キャンバスを白紙に戻す