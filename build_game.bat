@echo off
:: 文字化け対策（UTF-8設定）
chcp 65001 >nul
set PYTHONUTF8=1

echo ======================================================
echo   強力クリーンアップ ＆ アプリ再作成を開始します
echo ======================================================

cd /d %~dp0

echo [1/5] もし古いゲームが起動していたら強制終了させます...
taskkill /f /im main.exe >nul 2>&1

echo [2/5] 前回の作成データ（キャッシュ）を完全に削除しています...
if exist dist rd /s /q dist
if exist build rd /s /q build
if exist main.spec del /q main.spec

echo [3/5] 素材ファイルの有無を確認しています...
set "ADD_DATA="
if exist "levelup.wav" (
    set "ADD_DATA=--add-data "levelup.wav;.""
    echo  - levelup.wav をパッケージに含めます
)
if exist "select.wav" (
    set "ADD_DATA=%ADD_DATA% --add-data "select.wav;.""
    echo  - select.wav をパッケージに含めます
)

echo [4/5] 必要なライブラリの最新版を確認しています...
pip install pygame pyinstaller --upgrade

echo [5/5] アプリを「新規」作成中です。これには1-2分かかります...
python -m PyInstaller --onefile --noconsole --clean %ADD_DATA% main.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ------------------------------------------------------
    echo   完了しました！「dist」フォルダの「main.exe」が最新です。
    echo   この「main.exe」を友達に渡してください。
    echo ------------------------------------------------------
) else (
    echo.
    echo ######################################################
    echo   ビルドに失敗しました。
    echo   エラー内容を確認し、問題があれば教えてください。
    echo ######################################################
)
echo.
pause