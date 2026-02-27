# Auth0 Setup Guide

This document describes how to configure Auth0 for the supply-chain-ui and backend.

## 1. Auth0 Dashboard Configuration

### Create Application

1. Log in to [Auth0 Dashboard](https://manage.auth0.com/)
2. Go to **Applications** → **Applications** → **Create Application**
3. Select **Single Page Application** → **Create**
4. Note your **Domain** (e.g. `your-tenant.auth0.com`) and **Client ID**

### Application URIs

In your application's **Settings**:

| Setting | Value |
|---------|-------|
| **Allowed Callback URLs** | `http://localhost:3050`, `http://localhost:3000` (add your production URL when deploying) |
| **Allowed Logout URLs** | Same as callback URLs |
| **Allowed Web Origins** | Same as callback URLs |

### API (Optional)

To validate `aud` on access tokens:

1. Go to **Applications** → **APIs** → **Create API**
2. Set **Identifier** (e.g. `https://api.yourapp.com` or `urn:supply-chain-api`)
3. Use this identifier as `REACT_APP_AUTH0_AUDIENCE` (frontend) and `AUTH0_AUDIENCE` (backend)

### Algorithms

Ensure RS256 is used (Auth0 default).

## 2. Auth0 Endpoints

| Endpoint | URL |
|----------|-----|
| Discovery | `https://{AUTH0_DOMAIN}/.well-known/openid-configuration` |
| JWKS | `https://{AUTH0_DOMAIN}/.well-known/jwks.json` |
| Userinfo | `https://{AUTH0_DOMAIN}/userinfo` |
| Issuer | `https://{AUTH0_DOMAIN}/` |

## 3. Environment Variables

### supply-chain-ui

Copy `supply-chain-ui/env.template` to `supply-chain-ui/.env` and set:

| Variable | Description |
|----------|-------------|
| `REACT_APP_AUTH0_DOMAIN` | Your Auth0 tenant domain (e.g. `your-tenant.auth0.com`) |
| `REACT_APP_AUTH0_CLIENT_ID` | SPA application Client ID |
| `REACT_APP_AUTH0_AUDIENCE` | Optional: API identifier for access token audience |
| `REACT_APP_API_BASE_URL` | Backend API base URL (e.g. `http://localhost:8000`) |

### backend

Set in `.env` or deployment environment:

| Variable | Description |
|----------|-------------|
| `AUTH0_DOMAIN` | Same Auth0 tenant domain |
| `AUTH0_AUDIENCE` | Optional: API identifier for JWT `aud` validation |
