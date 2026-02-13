#!/bin/bash

# Configuration
WEBUI_URL="http://localhost:3000"
FUNCTIONS_DIR="$(pwd)/openwebui/functions"
EMAIL="admin@localhost"
PASSWORD=""

echo "=== Open WebUI Function Importer ==="
echo ""

# Check if functions directory exists
if [ ! -d "$FUNCTIONS_DIR" ]; then
    echo "✗ Error: Functions directory not found: $FUNCTIONS_DIR"
    exit 1
fi

# Check if credentials are provided
if [ -z "$EMAIL" ]; then
    echo "✗ Error: EMAIL not set"
    exit 1
fi

echo "Authenticating with Open WebUI..."

# Get JWT token
JWT_TOKEN=$(curl -s -X POST "${WEBUI_URL}/api/v1/auths/signin" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"${EMAIL}\",\"password\":\"${PASSWORD}\"}" 2>/dev/null | jq -r '.token')

if [ "$JWT_TOKEN" == "null" ] || [ -z "$JWT_TOKEN" ]; then
    echo "✗ Failed to authenticate"
    echo "Please check your credentials (EMAIL and PASSWORD)"
    exit 1
fi

echo "✓ Authenticated successfully"
echo ""

# Find all JSON files in functions directory
FILES=$(find "$FUNCTIONS_DIR" -maxdepth 1 -name "*.json" -type f)

if [ -z "$FILES" ]; then
    echo "✗ No JSON files found in $FUNCTIONS_DIR"
    exit 1
fi

# Count files
FILE_COUNT=$(echo "$FILES" | wc -l)
echo "Found $FILE_COUNT function file(s) to import"
echo ""

SUCCESS_COUNT=0
FAIL_COUNT=0

# Process each file
while IFS= read -r FUNCTION_JSON; do
    echo "────────────────────────────────────────"
    echo "Processing: $(basename "$FUNCTION_JSON")"
    
    # Check if it's valid JSON
    if ! jq empty "$FUNCTION_JSON" 2>/dev/null; then
        echo "✗ Invalid JSON file: $FUNCTION_JSON"
        FAIL_COUNT=$((FAIL_COUNT + 1))
        continue
    fi
    
    # Extract payload (handle array or object)
    PAYLOAD=$(cat "$FUNCTION_JSON" | jq 'if type == "array" then .[0] else . end')
    
    # Get function details
    FUNCTION_NAME=$(echo "$PAYLOAD" | jq -r '.name // "Unknown"')
    FUNCTION_ID=$(echo "$PAYLOAD" | jq -r '.id // "unknown"')
    
    echo "  Name: $FUNCTION_NAME"
    echo "  ID: $FUNCTION_ID"
    
    # Import function
    echo "  Importing..."
    RESPONSE=$(curl -s -X POST "${WEBUI_URL}/api/v1/functions/create" \
      -H "Authorization: Bearer ${JWT_TOKEN}" \
      -H "Content-Type: application/json" \
      -d "$PAYLOAD")
    
    if echo "$RESPONSE" | jq -e '.id' > /dev/null 2>&1; then
        CREATED_ID=$(echo "$RESPONSE" | jq -r '.id')
        echo "  ✓ Created successfully (ID: $CREATED_ID)"
        
        # Toggle to activate
        echo "  Activating..."
        TOGGLE_RESPONSE=$(curl -s -X POST "${WEBUI_URL}/api/v1/functions/id/${CREATED_ID}/toggle" \
          -H "Authorization: Bearer ${JWT_TOKEN}" \
          -H "Content-Type: application/json")
        
        if echo "$TOGGLE_RESPONSE" | jq -e '.is_active' > /dev/null 2>&1; then
            IS_ACTIVE=$(echo "$TOGGLE_RESPONSE" | jq -r '.is_active')
            if [ "$IS_ACTIVE" == "true" ]; then
                echo "  ✓ Activated successfully"
                SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
            else
                # Toggle again if not active
                curl -s -X POST "${WEBUI_URL}/api/v1/functions/id/${CREATED_ID}/toggle" \
                  -H "Authorization: Bearer ${JWT_TOKEN}" \
                  -H "Content-Type: application/json" > /dev/null
                echo "  ✓ Activated (toggled twice)"
                SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
            fi
        else
            echo "  ⚠ Created but could not activate"
            echo "  Response: $TOGGLE_RESPONSE"
            SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
        fi
    else
        echo "  ✗ Failed to import"
        ERROR_MSG=$(echo "$RESPONSE" | jq -r '.detail // .message // "Unknown error"')
        echo "  Error: $ERROR_MSG"
        FAIL_COUNT=$((FAIL_COUNT + 1))
    fi
    
done <<< "$FILES"

echo ""
echo "════════════════════════════════════════"
echo "Import Summary:"
echo "  Total: $FILE_COUNT"
echo "  Success: $SUCCESS_COUNT"
echo "  Failed: $FAIL_COUNT"
echo "════════════════════════════════════════"

if [ $FAIL_COUNT -gt 0 ]; then
    exit 1
fi
