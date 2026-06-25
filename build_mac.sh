#!/bin/bash
# ──────────────────────────────────────────────────────────
# ListeningTrainer — macOS 构建脚本
# 在 macOS 上运行此脚本以构建 .app 安装包
# ──────────────────────────────────────────────────────────
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "  ListeningTrainer macOS Build"
echo "=========================================="

# ── Step 1: 检查环境 ──────────────────────────
echo ""
echo "[1/4] 检查环境..."

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 未找到 python3，请先安装 Python 3.10+"
    exit 1
fi
echo "  ✓ Python $(python3 --version)"

# 检查 pip
if ! command -v pip3 &> /dev/null; then
    echo "❌ 未找到 pip3"
    exit 1
fi

# ── Step 2: 安装依赖 ──────────────────────────
echo ""
echo "[2/4] 安装 Python 依赖..."
pip3 install --upgrade pip
pip3 install -r requirements_mac.txt

# ── Step 3: 生成 .icns 图标 ──────────────────
echo ""
echo "[3/4] 生成 macOS 图标..."

ICON_SRC="pic.png"
ICON_DST="app_icon.icns"

if [ ! -f "$ICON_DST" ]; then
    if command -v sips &> /dev/null && command -v iconutil &> /dev/null; then
        # 用系统工具从 png 生成 icns
        mkdir -p AppIcon.iconset
        for size in 16 32 64 128 256 512 1024; do
            case $size in
                16)  sips -z 16 16   "$ICON_SRC" --out AppIcon.iconset/icon_16x16.png 2>/dev/null ;;
                32)  sips -z 32 32   "$ICON_SRC" --out AppIcon.iconset/icon_32x32.png 2>/dev/null
                     sips -z 32 32   "$ICON_SRC" --out AppIcon.iconset/icon_16x16@2x.png 2>/dev/null ;;
                64)  sips -z 64 64   "$ICON_SRC" --out AppIcon.iconset/icon_32x32@2x.png 2>/dev/null ;;
                128) sips -z 128 128 "$ICON_SRC" --out AppIcon.iconset/icon_128x128.png 2>/dev/null ;;
                256) sips -z 256 256 "$ICON_SRC" --out AppIcon.iconset/icon_256x256.png 2>/dev/null
                     sips -z 256 256 "$ICON_SRC" --out AppIcon.iconset/icon_128x128@2x.png 2>/dev/null ;;
                512) sips -z 512 512 "$ICON_SRC" --out AppIcon.iconset/icon_512x512.png 2>/dev/null
                     sips -z 512 512 "$ICON_SRC" --out AppIcon.iconset/icon_256x256@2x.png 2>/dev/null ;;
                1024) sips -z 1024 1024 "$ICON_SRC" --out AppIcon.iconset/icon_512x512@2x.png 2>/dev/null ;;
            esac
        done
        iconutil -c icns AppIcon.iconset
        mv AppIcon.icns "$ICON_DST"
        rm -rf AppIcon.iconset
        echo "  ✓ 已生成 $ICON_DST"
    else
        echo "  ⚠ 无法自动生成 .icns，使用 .ico 替代"
    fi
else
    echo "  ✓ $ICON_DST 已存在"
fi

# ── Step 4: PyInstaller 构建 ─────────────────
echo ""
echo "[4/4] PyInstaller 构建 .app..."
python3 -m PyInstaller --noconfirm build_mac.spec

# ── 完成 ──────────────────────────────────────
echo ""
echo "=========================================="
echo "  ✅ 构建完成！"
echo ""
APP_PATH="dist/ListeningTrainer.app"
if [ -d "$APP_PATH" ]; then
    echo "  .app 位于: $SCRIPT_DIR/$APP_PATH"
    echo ""
    echo "  打开方式: open $APP_PATH"
    echo "  或: cp -r $APP_PATH /Applications/"
else
    echo "  ⚠ 构建可能失败，请检查上方输出"
fi
echo "=========================================="
