#!/bin/bash

# OPA Policy Testing Script
# This script helps test various authorization scenarios

OPA_URL="http://localhost:8181"

echo "OPA Policy Testing Script"
echo "========================="

# Test 1: Basic read access for alice
echo "Test 1: Alice reading data"
curl -s -X POST "$OPA_URL/v1/data/authz/allow" \
  -H 'Content-Type: application/json' \
  -d '{"input": {"user": "alice", "action": "read", "resource": "data"}}' | jq .

# Test 2: Admin access
echo -e "\nTest 2: Admin delete access"
curl -s -X POST "$OPA_URL/v1/data/authz/allow" \
  -H 'Content-Type: application/json' \
  -d '{"input": {"user": "admin", "action": "delete", "resource": "data"}}' | jq .

# Test 3: Bob reading reports
echo -e "\nTest 3: Bob reading reports"
curl -s -X POST "$OPA_URL/v1/data/authz/allow" \
  -H 'Content-Type: application/json' \
  -d '{"input": {"user": "bob", "action": "read", "resource": "reports"}}' | jq .

# Test 4: Non-admin accessing sensitive data
echo -e "\nTest 4: Non-admin accessing sensitive data"
curl -s -X POST "$OPA_URL/v1/data/authz/allow" \
  -H 'Content-Type: application/json' \
  -d '{"input": {"user": "alice", "action": "read", "resource": "sensitive"}}' | jq .

# Test 5: Unknown user
echo -e "\nTest 5: Unknown user"
curl -s -X POST "$OPA_URL/v1/data/authz/allow" \
  -H 'Content-Type: application/json' \
  -d '{"input": {"user": "unknown", "action": "read", "resource": "data"}}' | jq .

# Test 6: Write access for alice
echo -e "\nTest 6: Alice writing data"
curl -s -X POST "$OPA_URL/v1/data/authz/allow" \
  -H 'Content-Type: application/json' \
  -d '{"input": {"user": "alice", "action": "write", "resource": "data"}}' | jq .

echo -e "\nTesting completed!"
