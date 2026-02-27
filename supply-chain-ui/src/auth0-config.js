// Auth0 configuration - used by Auth0Provider and components
export const auth0Config = {
  domain: process.env.REACT_APP_AUTH0_DOMAIN || '',
  clientId: process.env.REACT_APP_AUTH0_CLIENT_ID || '',
  authorizationParams: {
    redirect_uri: typeof window !== 'undefined' ? window.location.origin : '',
    audience: process.env.REACT_APP_AUTH0_AUDIENCE || undefined,
  },
};
