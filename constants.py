"""
Central constants for AnkiPH Addon
Single source of truth for version, URLs, and configuration
Version: 4.0.0 - Subscription-only model
"""

# Addon Info
ADDON_NAME = "AnkiPH"
ADDON_VERSION = "4.0.0"

# Base URLs - Use primary domain for all features
BASE_URL = "https://ankiph.lovable.app"

# Page URLs (derived from BASE_URL for consistency)
HOMEPAGE_URL = BASE_URL
REGISTER_URL = f"{BASE_URL}/auth"
FORGOT_PASSWORD_URL = f"{BASE_URL}/auth"
TERMS_URL = f"{BASE_URL}/terms"
PRIVACY_URL = f"{BASE_URL}/privacy"
PLANS_URL = f"{BASE_URL}/subscription"
DOCS_URL = f"{BASE_URL}/ankiph"
HELP_URL = f"{BASE_URL}/help"
CHANGELOG_URL = f"{BASE_URL}/help"
COMMUNITY_URL = f"{BASE_URL}/help"

# Subscription URLs (v3.3 - subscription-only model)
COLLECTION_URL = f"{BASE_URL}/collection"
PREMIUM_URL = f"{BASE_URL}/subscription"
SUBSCRIBE_URL = PREMIUM_URL  # Alias for subscription page

# Limits and Magic Numbers (v4.0 - centralized)

SQLITE_MAX_VARIABLES = 999
API_BATCH_SIZE = 1000
API_MAX_BATCH_SIZE = 5000
API_MIN_BATCH_SIZE = 200

# Timing Constants
SYNC_TIMEOUT_SECONDS = 30
DOWNLOAD_TIMEOUT_SECONDS = 120
TARGET_REQUEST_DURATION_MIN = 2.0
TARGET_REQUEST_DURATION_MAX = 5.0
DEFAULT_MAX_RETRIES = 3

# Token Validation
MIN_TOKEN_LENGTH = 20

# Study Stats Constants
RETENTION_DAYS_LOOKBACK = 30
LEARNING_CARD_TYPE = 1
REVIEW_CARD_TYPE = 2
RELEARNING_CARD_TYPE = 3

# Support & Contact
SUPPORT_EMAIL = "nottorney@gmail.com"
FEEDBACK_URL = f"{BASE_URL}/help"