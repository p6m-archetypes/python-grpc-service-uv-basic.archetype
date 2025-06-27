#!/bin/bash

# Protocol Buffer Compiler Installation Script
# Supports Linux, macOS, and Windows (via WSL)

set -e

PROTOC_VERSION="25.1"
PROTOC_ZIP="protoc-${PROTOC_VERSION}-linux-x86_64.zip"
INSTALL_DIR="/usr/local"

echo "🔧 Installing Protocol Buffer Compiler (protoc) v${PROTOC_VERSION}..."

# Detect OS
OS=$(uname -s)
ARCH=$(uname -m)

case $OS in
    Linux*)
        if [[ "$ARCH" == "x86_64" ]]; then
            PROTOC_ZIP="protoc-${PROTOC_VERSION}-linux-x86_64.zip"
        elif [[ "$ARCH" == "aarch64" ]]; then
            PROTOC_ZIP="protoc-${PROTOC_VERSION}-linux-aarch_64.zip"
        else
            echo "❌ Unsupported Linux architecture: $ARCH"
            exit 1
        fi
        ;;
    Darwin*)
        if [[ "$ARCH" == "x86_64" ]]; then
            PROTOC_ZIP="protoc-${PROTOC_VERSION}-osx-x86_64.zip"
        elif [[ "$ARCH" == "arm64" ]]; then
            PROTOC_ZIP="protoc-${PROTOC_VERSION}-osx-aarch_64.zip"
        else
            echo "❌ Unsupported macOS architecture: $ARCH"
            exit 1
        fi
        ;;
    CYGWIN*|MINGW32*|MSYS*|MINGW*)
        PROTOC_ZIP="protoc-${PROTOC_VERSION}-win64.zip"
        ;;
    *)
        echo "❌ Unsupported operating system: $OS"
        exit 1
        ;;
esac

echo "📦 Detected OS: $OS, Architecture: $ARCH"
echo "📥 Will download: $PROTOC_ZIP"

# Check if running with appropriate permissions
if [[ "$INSTALL_DIR" == "/usr/local" ]] && [[ "$EUID" -ne 0 ]]; then
    echo "⚠️  Installing to /usr/local requires sudo privileges"
    echo "🔄 Re-running with sudo..."
    exec sudo "$0" "$@"
fi

# Create temporary directory
TEMP_DIR=$(mktemp -d)
cd "$TEMP_DIR"

echo "📥 Downloading protoc..."
curl -LO "https://github.com/protocolbuffers/protobuf/releases/download/v${PROTOC_VERSION}/${PROTOC_ZIP}"

if [[ ! -f "$PROTOC_ZIP" ]]; then
    echo "❌ Failed to download protoc"
    exit 1
fi

echo "📦 Extracting protoc..."
unzip -q "$PROTOC_ZIP"

echo "📁 Installing to $INSTALL_DIR..."
cp bin/protoc "$INSTALL_DIR/bin/"
cp -r include/* "$INSTALL_DIR/include/"

# Make sure protoc is executable
chmod +x "$INSTALL_DIR/bin/protoc"

# Cleanup
cd /
rm -rf "$TEMP_DIR"

# Verify installation
echo "✅ Installation complete!"
echo "🔍 Verifying installation..."

if command -v protoc >/dev/null 2>&1; then
    INSTALLED_VERSION=$(protoc --version)
    echo "✅ protoc is available: $INSTALLED_VERSION"
else
    echo "⚠️  protoc not found in PATH. You may need to add $INSTALL_DIR/bin to your PATH"
    echo "   Add this to your shell profile (.bashrc, .zshrc, etc.):"
    echo "   export PATH=\"$INSTALL_DIR/bin:\$PATH\""
fi

echo ""
echo "🎉 Protocol Buffer Compiler installation completed!"
echo ""
echo "📝 Next steps:"
echo "   1. Restart your terminal or source your shell profile"
echo "   2. Run 'protoc --version' to verify"
echo "   3. Generate Python gRPC code with './scripts/generate-grpc.sh'"