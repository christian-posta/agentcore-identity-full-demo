#!/usr/bin/env bash
# Export current AWS SSO (or profile) credentials to a file that can be sourced
# before starting agentgateway. Agentgateway uses the default credential chain,
# which reads AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_SESSION_TOKEN from
# the environment when using implicit AWS backend auth.
#
# Usage:
#   ./export-aws-sso-creds.sh [--profile PROFILE] [OUTPUT_FILE]
#
# Then start agentgateway with credentials in the environment:
#   source ./aws-creds.env   # or whatever OUTPUT_FILE you used
#   agentgateway --config config.yaml
#
# Credentials are short-lived (e.g. 8–12 hours); re-run this script and
# restart agentgateway when they expire.

set -e

PROFILE=""
while [[ $# -gt 0 ]]; do
  case $1 in
    --profile)
      PROFILE="$2"
      shift 2
      ;;
    *)
      break
      ;;
  esac
done

OUTPUT_FILE="${1:-aws-creds.env}"

if [[ -n "$PROFILE" ]]; then
  aws configure export-credentials --profile "$PROFILE" --format env > "$OUTPUT_FILE"
else
  aws configure export-credentials --format env > "$OUTPUT_FILE"
fi

# Optionally append default region from profile so agentgateway can resolve region
if [[ -n "$PROFILE" ]]; then
  REGION=$(aws configure get region --profile "$PROFILE" 2>/dev/null || true)
else
  REGION=$(aws configure get region 2>/dev/null || true)
fi
if [[ -n "$REGION" ]]; then
  echo "export AWS_DEFAULT_REGION=$REGION" >> "$OUTPUT_FILE"
  echo "export AWS_REGION=$REGION" >> "$OUTPUT_FILE"
fi

echo "Wrote credentials to $OUTPUT_FILE"
echo "Source it before starting agentgateway:  source $OUTPUT_FILE"
