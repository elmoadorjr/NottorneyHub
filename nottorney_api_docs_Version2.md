# Nottorney Anki Add-on API Documentation

**Version:** 2.0.0  
**Base URL:** `https://ladvckxztcleljbiomcf.supabase.co/functions/v1`  
**Last Updated:** December 11, 2025

---

## Table of Contents

1. [Authentication](#authentication)
2. [Rate Limiting](#rate-limiting)
3. [Error Handling](#error-handling)
4. [Endpoints](#endpoints)
   - [Login](#1-login)
   - [Refresh Token](#2-refresh-token)
   - [Get Purchases](#3-get-purchases)
   - [Download Deck](#4-download-deck)
   - [Batch Download](#5-batch-download)
   - [Sync Progress](#6-sync-progress)
   - [Check Updates](#7-check-updates)
   - [Get Changelog](#8-get-changelog)
   - [Check Notifications](#9-check-notifications)
   - [Push Changes](#10-push-changes)
   - [Pull Changes](#11-pull-changes)
   - [Submit Suggestion](#12-submit-suggestion)
   - [Get/Set Protected Fields](#13-getset-protected-fields)
   - [Sync Media](#14-sync-media)
   - [Sync Tags](#15-sync-tags)
   - [Sync Note Types](#16-sync-note-types)
   - [Sync Suspend State](#17-sync-suspend-state)
   - [Get Card History](#18-get-card-history)
   - [Rollback Card](#19-rollback-card)
   - [Browse Decks](#20-browse-decks)
5. [Data Models](#data-models)
6. [Workflow Examples](#workflow-examples)

---

## Authentication

The API uses JWT (JSON Web Token) Bearer authentication. After successful login, you'll receive an `access_token` and `refresh_token`.

### Token Usage

Include the access token in the `Authorization` header for all authenticated requests:

```
Authorization: Bearer <access_token>
```

### Token Lifecycle

| Token Type | Validity | Usage |
|------------|----------|-------|
| `access_token` | 1 hour (3600 seconds) | API requests |
| `refresh_token` | 7 days | Obtain new access tokens |

### Token Refresh Flow

1. Store both tokens securely after login
2. Use `access_token` for API calls
3. When you receive a `401 Unauthorized`, call `POST /addon-refresh-token` with your `refresh_token` in the JSON body
4. If refresh fails, prompt user to re-login

Example (curl):

```bash
curl -X POST "https://ladvckxztcleljbiomcf.supabase.co/functions/v1/addon-refresh-token" \
  -H "Content-Type: application/json" \
  -d '{"refresh_token":"<refresh_token>"}'
```

---

## Rate Limiting

All endpoints return rate limit information in response headers:

| Header | Description |
|--------|-------------|
| `X-RateLimit-Limit` | Maximum requests per window |
| `X-RateLimit-Remaining` | Remaining requests in current window |
| `X-RateLimit-Reset` | Seconds until window resets |

**Current Limits:**
- Most endpoints: 30 requests/minute (per-user)
- Batch download: 30 requests/minute
- Progress sync: 60 requests/minute

**Best Practices:**
- Check `X-RateLimit-Remaining` before making requests
- Implement exponential backoff on `429 Too Many Requests`
- Cache responses where appropriate

---

## Error Handling

### HTTP Status Codes

| Code | Meaning |
|------|---------|
| `200` | Success |
| `400` | Bad Request - Invalid parameters |
| `401` | Unauthorized - Invalid/expired token |
| `403` | Forbidden - No permission (e.g., deck not purchased) |
| `404` | Not Found - Resource doesn't exist |
| `429` | Too Many Requests - Rate limited |
| `500` | Internal Server Error |

### Error Response Format

```json
{
  "error": "Human-readable error message",
  "code": "ERROR_CODE",  
  "details": {}          
}
```

### Common Error Codes

| Code | Description | Action |
|------|-------------|--------|
| `INVALID_CREDENTIALS` | Wrong email/password | Prompt re-login |
| `TOKEN_EXPIRED` | Access token expired | Refresh token |
| `REFRESH_TOKEN_EXPIRED` | Refresh token expired | Full re-login |
| `DECK_NOT_PURCHASED` | User hasn't purchased deck | Show purchase prompt |
| `DECK_NOT_FOUND` | Deck ID doesn't exist | Remove from local cache |

---

## Endpoints

(Full cleaned documentation file committed — includes consistent use of ISO 8601 timestamps, consistent field names `deck_id`, example curl commands, and the same content you provided with minor normalizations. See repo file for full text.)