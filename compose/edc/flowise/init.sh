#!/bin/sh

MARKER_FILE="/data/.user_created"

if [ -f "$MARKER_FILE" ]; then
    echo "User already created, skipping registration and import"
    exit 0
fi

echo "Registering user..."
RESPONSE=$(curl -s -w "\n%{http_code}" --location 'http://flowise:3000/api/v1/account/register' \
    --header 'Content-Type: application/json' \
    --data-raw "{\"user\":{\"name\":\"admin\",\"email\":\"${FLOWISE_EMAIL}\",\"type\":\"pro\",\"credential\":\"${FLOWISE_PASSWORD}\"}}")

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)

BODY=$(echo "$RESPONSE" | sed '$d')

echo "HTTP Status: $HTTP_CODE"
echo "Response: $BODY"

if [ "$HTTP_CODE" != "201" ]; then
    echo "User was already created"
else
    echo "User successfully registered"
fi

echo "Logging in..."
LOGIN_RESPONSE=$(curl -s -w "\n%{http_code}" 'http://flowise:3000/api/v1/auth/login' \
  -X POST \
  -c /tmp/cookies.txt \
  -H 'Content-Type: application/json' \
  --data-raw "{\"email\":\"${FLOWISE_EMAIL}\",\"password\":\"${FLOWISE_PASSWORD}\"}")

LOGIN_CODE=$(echo "$LOGIN_RESPONSE" | tail -n1)
LOGIN_BODY=$(echo "$LOGIN_RESPONSE" | sed '$d')

echo "Login HTTP Status: $LOGIN_CODE"
echo "Login Response: $LOGIN_BODY"

if [ "$LOGIN_CODE" != "200" ]; then
    echo "Failed to login"
    exit 1
fi

echo "Login successful"

echo "Importing flows from ExportData.json..."
IMPORT_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST 'http://flowise:3000/api/v1/export-import/import' \
     -b /tmp/cookies.txt \
     -H "Content-Type: application/json" \
     -H "x-request-from: internal" \
     -d @/data/ExportData.json)

IMPORT_CODE=$(echo "$IMPORT_RESPONSE" | tail -n1)
IMPORT_BODY=$(echo "$IMPORT_RESPONSE" | sed '$d')

echo "Import HTTP Status: $IMPORT_CODE"
echo "Import Response: $IMPORT_BODY"

if [ "$IMPORT_CODE" = "200" ] || [ "$IMPORT_CODE" = "201" ]; then
    echo "Flows imported successfully"
    touch "$MARKER_FILE"
    echo "Marker file created at $MARKER_FILE"
    exit 0
else
    echo "Failed to import flows"
    exit 1
fi