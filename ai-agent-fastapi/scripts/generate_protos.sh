#!/usr/bin/env bash
set -e

# Define directories
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SHARED_PROTO_DIR="$PROJECT_ROOT/../shared-proto"
OUTPUT_DIR="$PROJECT_ROOT/src/generated"

echo "🛠️  Generating Python gRPC Stubs..."

# Ensure output directory exists
mkdir -p "$OUTPUT_DIR"
touch "$OUTPUT_DIR/__init__.py"

# Run the compiler
poetry run python -m grpc_tools.protoc \
    -I"$SHARED_PROTO_DIR" \
    --python_out="$OUTPUT_DIR" \
    --grpc_python_out="$OUTPUT_DIR" \
    "$SHARED_PROTO_DIR"/*.proto

# Fix relative imports in the generated _grpc.py files (Python 3 issue)
# grpc_tools generates imports like `import itinerary_pb2` instead of `from . import itinerary_pb2`
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS requires an empty string for the -i flag
    sed -i '' 's/import \([a-z_]*\)_pb2/from . import \1_pb2/g' "$OUTPUT_DIR"/*_grpc.py
else
    # Linux
    sed -i 's/import \([a-z_]*\)_pb2/from . import \1_pb2/g' "$OUTPUT_DIR"/*_grpc.py
fi

echo "✅ Protobuf stubs successfully generated in $OUTPUT_DIR"
