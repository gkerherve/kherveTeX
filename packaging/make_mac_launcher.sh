#!/bin/bash
# Build a double-clickable "KherveTeX Dev.app" that runs this checkout's
# source with the repo's .venv, so the icon always starts the latest code.
# Usage: packaging/make_mac_launcher.sh [destination-dir]   (default: ~/Desktop)
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
DEST="${1:-$HOME/Desktop}"
APP="$DEST/KherveTeX Dev.app"
PY="$REPO/.venv/bin/python"

[ -x "$PY" ] || { echo "missing $PY — create the venv first" >&2; exit 1; }

rm -rf "$APP"
mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources"

cat > "$APP/Contents/MacOS/KherveTeX" <<EOF
#!/bin/bash
cd "$REPO"
export PATH="\$HOME/bin:/opt/homebrew/bin:/usr/local/bin:\$PATH"
exec "$PY" kherveDOC.py "\$@" >>"\$HOME/Library/Logs/KherveTeX-dev.log" 2>&1
EOF
chmod +x "$APP/Contents/MacOS/KherveTeX"

cat > "$APP/Contents/Info.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
	<key>CFBundleExecutable</key><string>KherveTeX</string>
	<key>CFBundleIdentifier</key><string>io.github.gkerherve.khervetex.dev</string>
	<key>CFBundleName</key><string>KherveTeX Dev</string>
	<key>CFBundleIconFile</key><string>KherveTeX</string>
	<key>CFBundlePackageType</key><string>APPL</string>
	<key>CFBundleInfoDictionaryVersion</key><string>6.0</string>
	<key>NSHighResolutionCapable</key><true/>
</dict>
</plist>
EOF

ICONSET="$(mktemp -d)/KherveTeX.iconset"
mkdir -p "$ICONSET"
SRC="$REPO/khervetex_logo_256.png"
for s in 16 32 128 256; do
  sips -z $s $s "$SRC" --out "$ICONSET/icon_${s}x${s}.png" >/dev/null
  sips -z $((s*2)) $((s*2)) "$SRC" --out "$ICONSET/icon_${s}x${s}@2x.png" >/dev/null
done
iconutil -c icns "$ICONSET" -o "$APP/Contents/Resources/KherveTeX.icns"

codesign --force --sign - "$APP" >/dev/null 2>&1 || true
touch "$APP"
echo "Created $APP"
