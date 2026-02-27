import { useAuth0 as useAuth0Base } from '@auth0/auth0-react';
import { useState, useCallback, useEffect } from 'react';

/**
 * Wraps @auth0/auth0-react's useAuth0 and exposes a shape compatible with the
 * previous useKeycloak hook for minimal component changes.
 */
export const useAuth0 = () => {
  const {
    user: auth0User,
    isAuthenticated,
    isLoading: auth0Loading,
    error: auth0Error,
    loginWithRedirect,
    logout: auth0Logout,
    getAccessTokenSilently,
    getIdTokenClaims,
  } = useAuth0Base();

  const [tokenCache, setTokenCache] = useState({ accessToken: null, idToken: null });
  const [mappedUser, setMappedUser] = useState(null);

  // Map Auth0 user to keycloak-compatible shape
  useEffect(() => {
    if (!auth0User) {
      setMappedUser(null);
      return;
    }

    const nameParts = (auth0User.name || '').split(' ');
    const firstName = auth0User.given_name || nameParts[0] || '';
    const lastName = auth0User.family_name || nameParts.slice(1).join(' ') || '';

    setMappedUser({
      id: auth0User.sub,
      username: auth0User.nickname || auth0User.name || auth0User.sub,
      email: auth0User.email,
      firstName,
      lastName,
      fullName: auth0User.name || `${firstName} ${lastName}`.trim() || auth0User.sub,
      roles: auth0User['https://your-app/roles'] || auth0User.roles || [],
    });
  }, [auth0User]);

  const login = useCallback(() => {
    loginWithRedirect();
  }, [loginWithRedirect]);

  const logout = useCallback(() => {
    auth0Logout({
      logoutParams: {
        returnTo: window.location.origin,
      },
    });
  }, [auth0Logout]);

  const refreshToken = useCallback(async () => {
    try {
      const accessToken = await getAccessTokenSilently();
      const idTokenClaims = await getIdTokenClaims();
      setTokenCache({
        accessToken,
        idToken: idTokenClaims ? idTokenClaims.__raw : null,
      });
      return true;
    } catch (err) {
      console.error('Token refresh failed:', err);
      return false;
    }
  }, [getAccessTokenSilently, getIdTokenClaims]);

  // Cache tokens when authenticated
  useEffect(() => {
    if (!isAuthenticated || !auth0User) {
      setTokenCache({ accessToken: null, idToken: null });
      return;
    }

    let cancelled = false;
    const load = async () => {
      try {
        const accessToken = await getAccessTokenSilently();
        const idTokenClaims = await getIdTokenClaims();
        if (!cancelled) {
          setTokenCache({
            accessToken,
            idToken: idTokenClaims ? idTokenClaims.__raw : null,
          });
        }
      } catch (e) {
        if (!cancelled) setTokenCache({ accessToken: null, idToken: null });
      }
    };
    load();
    return () => { cancelled = true; };
  }, [isAuthenticated, auth0User, getAccessTokenSilently, getIdTokenClaims]);

  // Decode access token for AuthTokensDialog (exp, iat, sub, iss, aud)
  const parseToken = (token) => {
    if (!token) return null;
    try {
      const base64 = token.split('.')[1];
      if (!base64) return null;
      const json = atob(base64.replace(/-/g, '+').replace(/_/g, '/'));
      return JSON.parse(json);
    } catch {
      return null;
    }
  };

  const tokenParsed = tokenCache.accessToken ? parseToken(tokenCache.accessToken) : null;

  // Auth object compatible with keycloak prop (token, idToken, tokenParsed, realm, subject)
  const auth = {
    token: tokenCache.accessToken,
    idToken: tokenCache.idToken,
    tokenParsed,
    realm: 'Auth0',
    subject: auth0User?.sub,
    authenticated: isAuthenticated,
    updateToken: refreshToken,
  };

  return {
    user: mappedUser,
    isLoading: auth0Loading,
    isAuthenticated,
    error: auth0Error ? (auth0Error.message || 'Authentication error') : null,
    login,
    logout,
    refreshToken,
    clearError: () => {},
    auth0: auth,
  };
};
