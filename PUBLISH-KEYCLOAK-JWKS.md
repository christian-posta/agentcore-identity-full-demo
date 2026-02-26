# Publish Keycloak JWKS to S3

This guide shows how to publish your Keycloak realm's public keys (JWKS) to Amazon S3 so they can be used as a **JWKS endpoint** for JWT verification. Use this when a verifier (e.g. Microsoft Entra, an API gateway, or another service) cannot reach Keycloak directly but needs the public keys—configure the verifier with **issuer** = your Keycloak realm URL (e.g. `http://localhost:8080/realms/mcp-realm`) and **jwks_uri** = the S3 URL below.

```bash
# JWKS URL: https://keycloak-jwks-2ebe2847.s3.us-west-2.amazonaws.com/jwks
curl https://keycloak-jwks-2ebe2847.s3.us-west-2.amazonaws.com/jwks | jq
```

## Architecture

```
Your app / Entra / API Gateway          S3 Bucket
┌─────────────────────────┐            ┌──────────────────┐
│ JWT verification        │            │ jwks             │
│                         │  ────────►  │ (keycloak-openid │
│ issuer: Keycloak URL    │   HTTPS     │  .json)           │
│ jwks_uri: S3 URL below  │             └──────────────────┘
└─────────────────────────┘
```

**Resulting URL (after setup):**

| Purpose | URL |
|--------|-----|
| **JWKS (public keys)** | `https://YOUR-BUCKET.s3.YOUR-REGION.amazonaws.com/jwks` |

Use this URL as **jwks_uri** in your verifier. Keep **issuer** as your Keycloak realm URL so token `iss` validation matches.

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

# Object key for the JWKS file (URL path)
export JWKS_KEY="jwks"

export JWKS_URL="https://${BUCKET_NAME}.s3.${AWS_REGION}.amazonaws.com/${JWKS_KEY}"
echo "JWKS URL: $JWKS_URL"
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

## 3. Block public access (we'll allow it only for the JWKS object via policy)

By default S3 blocks public access. We'll enable public read only for the JWKS object using a bucket policy.

```bash
# Remove the default "Block all public access" so the bucket policy can allow reads
aws s3api put-public-access-block \
  --bucket "$BUCKET_NAME" \
  --public-access-block-configuration \
    "BlockPublicAcls=false,IgnorePublicAcls=false,BlockPublicPolicy=false,RestrictPublicBuckets=false"
```

---

## 4. Bucket policy (public read only for JWKS)

Create a policy that allows public `GetObject` only for the JWKS file:

```bash
cat > /tmp/jwks-bucket-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadJWKS",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::${BUCKET_NAME}/${JWKS_KEY}"
    }
  ]
}
EOF

aws s3api put-bucket-policy \
  --bucket "$BUCKET_NAME" \
  --policy file:///tmp/jwks-bucket-policy.json
```

---

## 5. Upload JWKS to S3

From the directory that contains `keycloak-openid.json`:

```bash
cd "$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

aws s3 cp keycloak-openid.json \
  "s3://${BUCKET_NAME}/${JWKS_KEY}" \
  --content-type "application/json" \
  --cache-control "public, max-age=300"

echo "✅ Uploaded JWKS"
```

---

## 6. Verify

```bash
curl -s "$JWKS_URL" | jq .
```

You should see JSON with a `keys` array.

---

## Summary: URL to use

After running the steps above:

| What | URL |
|------|-----|
| **JWKS URI** (for JWT verification) | `https://YOUR-BUCKET.s3.YOUR-REGION.amazonaws.com/jwks` |

Configure your verifier with **issuer** = Keycloak realm URL (e.g. `http://localhost:8080/realms/mcp-realm`) and **jwks_uri** = this S3 URL.

---

## Refreshing the JWKS

When Keycloak rotates keys (e.g. after realm key settings change), re-export the JWKS from Keycloak and re-upload:

```bash
# 1. Replace keycloak-openid.json with the new JWKS from Keycloak:
#    GET http://localhost:8080/realms/mcp-realm/protocol/openid-connect/certs

# 2. Re-upload
aws s3 cp keycloak-openid.json \
  "s3://${BUCKET_NAME}/${JWKS_KEY}" \
  --content-type "application/json" \
  --cache-control "public, max-age=300"
```

---

## Optional: use a custom domain (CloudFront)

For a shorter URL or custom domain (e.g. `jwks.example.com`), put CloudFront in front of the S3 bucket and use that URL as **jwks_uri**.
