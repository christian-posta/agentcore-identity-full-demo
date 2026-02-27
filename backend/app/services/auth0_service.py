import requests
import jwt
from jwt import PyJWKClient
from typing import Optional, Dict
from app.config import settings


class Auth0Service:
    def __init__(self):
        self.domain = settings.auth0_domain
        self.audience = settings.auth0_audience or None
        self.issuer = f"https://{self.domain}/" if self.domain else None
        self.jwks_client: Optional[PyJWKClient] = None
        self.jwks_uri: Optional[str] = None
        self._init_jwks()

    def _init_jwks(self):
        """Fetch JWKS URI from Auth0 discovery and create JWKS client"""
        if not self.domain:
            print("AUTH0_DOMAIN not configured")
            return
        try:
            discovery_url = f"https://{self.domain}/.well-known/openid-configuration"
            response = requests.get(discovery_url, timeout=10)
            response.raise_for_status()
            discovery = response.json()
            self.jwks_uri = discovery.get("jwks_uri")
            if not self.jwks_uri:
                print("No jwks_uri in Auth0 discovery")
                return
            self.jwks_client = PyJWKClient(self.jwks_uri)
            print(f"Loaded Auth0 JWKS for domain: {self.domain}")
        except Exception as e:
            print(f"Failed to load Auth0 JWKS: {e}")

    def verify_token(self, token: str) -> Optional[Dict]:
        """Verify JWT token from Auth0"""
        try:
            if not self.jwks_client:
                print("No JWKS client available for token verification")
                return None

            signing_key = self.jwks_client.get_signing_key_from_jwt(token)

            options = {"verify_signature": True}
            if self.audience:
                options["verify_aud"] = True
            else:
                options["verify_aud"] = False

            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience=self.audience if self.audience else None,
                issuer=self.issuer,
                options=options,
            )

            username = payload.get("nickname") or payload.get("name") or payload.get("sub", "unknown")
            print(f"Token verified successfully for user: {username}")
            return payload

        except jwt.ExpiredSignatureError:
            print("Token has expired")
            return None
        except jwt.InvalidTokenError as e:
            print(f"Invalid token: {e}")
            return None
        except Exception as e:
            print(f"Token verification failed: {e}")
            import traceback
            traceback.print_exc()
            return None

    def get_user_info(self, token: str) -> Optional[Dict]:
        """Get user info from Auth0"""
        if not self.domain:
            return None
        try:
            url = f"https://{self.domain}/userinfo"
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            user_info = response.json()
            username = user_info.get("nickname") or user_info.get("name") or user_info.get("sub", "unknown")
            print(f"Retrieved user info for: {username}")
            return user_info
        except Exception as e:
            print(f"Failed to get user info: {e}")
            return None

    def _map_to_user_response(self, payload: Dict, user_info: Optional[Dict] = None) -> Dict:
        """Map Auth0 claims to UserResponse-compatible dict"""
        source = user_info if user_info else payload
        username = (
            source.get("nickname")
            or source.get("preferred_username")
            or source.get("name")
            or source.get("sub", "")
        )
        return {
            "sub": payload.get("sub"),
            "preferred_username": username,
            "username": username,
            "email": source.get("email", ""),
            "name": source.get("name"),
            "nickname": source.get("nickname"),
            "role": source.get("role", "User"),
        }


auth0_service = Auth0Service()
