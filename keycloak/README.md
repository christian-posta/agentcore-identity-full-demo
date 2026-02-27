# Publish Keycloak JWKS to S3

**NOTE: At the moment we are not going to use Keycloak. We'll use Auth0 for this demo. Keycloak in my demos issues from `http://`  when the spec requires `https://` and public services honor this. **

This guide shows how to publish your Keycloak realm's **discovery document** and **JWKS** to Amazon S3 so they can be used when a verifier (e.g. Microsoft Entra, an API gateway) cannot reach Keycloak directly. The discovery document declares the **real token issuer** (Keycloak at localhost) and points **jwks_uri** at S3, so token `iss` validation and key fetching both work.

```bash

curl https://keycloak-jwks-2ebe2847.s3.us-west-2.amazonaws.com/jwks
curl https://keycloak-jwks-2ebe2847.s3.us-west-2.amazonaws.com/.well-known/openid-configuration
```

## Architecture

```
Verifier (Entra / API Gateway)              S3 Bucket
┌─────────────────────────────┐             ┌─────────────────────────────────────┐
│ 1. GET discovery URL        │ ──────────► │ oidc/.well-known/openid-configuration │
│    (S3)                     │             │   issuer: http://localhost:8080/... │
│                             │             │   jwks_uri: https://...s3.../oidc/jwks
│ 2. Validate token iss       │             ├─────────────────────────────────────┤
│    matches issuer (localhost)│             │ oidc/jwks (keycloak-openid.json)     │
│                             │ ◀────────── │   public keys for signature verify   │
│ 3. GET jwks_uri (S3)        │             └─────────────────────────────────────┘
└─────────────────────────────┘
```

**Token issuer = localhost:** The discovery doc’s `issuer` is set to your Keycloak realm URL (e.g. `http://localhost:8080/realms/mcp-realm`). Verifiers that fetch discovery from S3 will still validate the JWT’s `iss` claim against that value, so Keycloak-issued tokens remain valid.

**Resulting URLs (after setup):**

| Purpose | URL |
|--------|-----|
| **Discovery** (use this as the discovery URL in your verifier) | `https://YOUR-BUCKET.s3.YOUR-REGION.amazonaws.com/oidc/.well-known/openid-configuration` |
| **JWKS** | `https://YOUR-BUCKET.s3.YOUR-REGION.amazonaws.com/oidc/jwks` |

---

## Prerequisites

- **AWS CLI** installed and configured (`aws configure`)
- **jq** (optional, for verifying JSON)

```bash
aws --version   # 2.x
```

---

## 1. Set variables

```bash
# Choose a globally unique bucket name (lowercase, no underscores)
export AWS_REGION="us-west-2"
export BUCKET_NAME="keycloak-jwks-$(openssl rand -hex 4)"

# Prefix under which discovery + JWKS live (gives you a clean "base" URL)
export OIDC_PREFIX="oidc"

# The real token issuer — Keycloak realm URL (must match iss in JWTs)
export KEYCLOAK_ISSUER_URL="http://localhost:8080/realms/mcp-realm"

# S3 URLs (derived)
export DISCOVERY_URL="https://${BUCKET_NAME}.s3.${AWS_REGION}.amazonaws.com/${OIDC_PREFIX}/.well-known/openid-configuration"
export JWKS_URL="https://${BUCKET_NAME}.s3.${AWS_REGION}.amazonaws.com/${OIDC_PREFIX}/jwks"

echo "Discovery URL: $DISCOVERY_URL"
echo "JWKS URL:      $JWKS_URL"
echo "Issuer (in discovery): $KEYCLOAK_ISSUER_URL"
```

---

## 2. Create the S3 bucket

For **us-east-1** do not use `LocationConstraint`. For any other region you must specify it:

```bash
if [ "$AWS_REGION" = "us-east-1" ]; then
  aws s3api create-bucket \
    --bucket "$BUCKET_NAME" \
    --region "$AWS_REGION"
else
  aws s3api create-bucket \
    --bucket "$BUCKET_NAME" \
    --region "$AWS_REGION" \
    --create-bucket-configuration LocationConstraint="$AWS_REGION"
fi
```

Example response:

```json
{
  "Location": "http://keycloak-jwks-xxxx.s3.amazonaws.com/",
  "BucketArn": "arn:aws:s3:::keycloak-jwks-xxxx"
}
```

---

## 3. Block public access (we'll allow it only for OIDC objects via policy)

By default S3 blocks public access. We'll enable public read only for the discovery document and JWKS using a bucket policy.

```bash
aws s3api put-public-access-block \
  --bucket "$BUCKET_NAME" \
  --public-access-block-configuration \
    "BlockPublicAcls=false,IgnorePublicAcls=false,BlockPublicPolicy=false,RestrictPublicBuckets=false"
```

---

## 4. Bucket policy (public read only for discovery + JWKS)

```bash
cat > /tmp/jwks-bucket-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadOIDC",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": [
        "arn:aws:s3:::${BUCKET_NAME}/${OIDC_PREFIX}/.well-known/openid-configuration",
        "arn:aws:s3:::${BUCKET_NAME}/${OIDC_PREFIX}/jwks"
      ]
    }
  ]
}
EOF

aws s3api put-bucket-policy \
  --bucket "$BUCKET_NAME" \
  --policy file:///tmp/jwks-bucket-policy.json
```

---

## 5. Create the discovery document

The discovery document uses the **Keycloak issuer** (localhost) so token `iss` validation matches. The **jwks_uri** points to S3 so verifiers can fetch keys without reaching Keycloak.

```bash
cd "$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

cat > openid-configuration.json << EOF
{
  "issuer": "${KEYCLOAK_ISSUER_URL}",
  "jwks_uri": "${JWKS_URL}",
  "response_types_supported": ["id_token", "token"],
  "subject_types_supported": ["public"],
  "id_token_signing_alg_values_supported": ["RS256"]
}
EOF

echo "✅ Created openid-configuration.json"
cat openid-configuration.json | jq .
```

---

## 6. Upload discovery and JWKS to S3

```bash
# Upload discovery document
aws s3 cp openid-configuration.json \
  "s3://${BUCKET_NAME}/${OIDC_PREFIX}/.well-known/openid-configuration" \
  --content-type "application/json" \
  --cache-control "public, max-age=300"

# Upload JWKS (keycloak-openid.json)
aws s3 cp keycloak-openid.json \
  "s3://${BUCKET_NAME}/${OIDC_PREFIX}/jwks" \
  --content-type "application/json" \
  --cache-control "public, max-age=300"

echo "✅ Uploaded discovery and JWKS"
```

---

## 7. Verify

```bash
echo "Discovery (issuer = Keycloak, jwks_uri = S3):"
curl -s "$DISCOVERY_URL" | jq .

echo ""
echo "JWKS:"
curl -s "$JWKS_URL" | jq .
```

Discovery should show `issuer` = your Keycloak URL and `jwks_uri` = the S3 JWKS URL. JWKS should show a `keys` array.

---

## Summary: URLs to use

| What | URL |
|------|-----|
| **Discovery URL** (give this to your verifier as the discovery endpoint) | `https://YOUR-BUCKET.s3.YOUR-REGION.amazonaws.com/oidc/.well-known/openid-configuration` |
| **JWKS URI** (also in discovery; use if you only need keys) | `https://YOUR-BUCKET.s3.YOUR-REGION.amazonaws.com/oidc/jwks` |

Verifier flow: GET discovery from S3 → read `issuer` (localhost) and `jwks_uri` (S3) → validate token `iss` against issuer, verify signature using keys from `jwks_uri`. Token issuer being localhost does not matter as long as the discovery document declares that same issuer.

---

## Refreshing the JWKS

When Keycloak rotates keys, re-export the JWKS and re-upload:

```bash
# 1. Replace keycloak-openid.json with the new JWKS from Keycloak:
#    GET http://localhost:8080/realms/mcp-realm/protocol/openid-connect/certs

# 2. Re-upload
aws s3 cp keycloak-openid.json \
  "s3://${BUCKET_NAME}/${OIDC_PREFIX}/jwks" \
  --content-type "application/json" \
  --cache-control "public, max-age=300"
```

The discovery document only needs to be re-uploaded if you change `KEYCLOAK_ISSUER_URL` or bucket/region.

---

## Optional: use a custom domain (CloudFront)

For a shorter URL or custom domain, put CloudFront in front of the bucket and use the CloudFront base URL in place of `https://BUCKET.s3.REGION.amazonaws.com/oidc` for both the discovery and JWKS URLs.
