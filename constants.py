"""
Central constants for AnkiPH Addon
Single source of truth for version, URLs, and configuration
Version: 3.3.0 - Subscription-only model
"""

# Addon Info
ADDON_NAME = "AnkiPH"
ADDON_VERSION = "3.3.0"

# Base URLs - Use primary domain for all features
BASE_URL = "https://nottorney.com"

# Page URLs (derived from BASE_URL for consistency)
HOMEPAGE_URL = BASE_URL
REGISTER_URL = f"{BASE_URL}/register"
FORGOT_PASSWORD_URL = f"{BASE_URL}/forgot-password"
TERMS_URL = f"{BASE_URL}/terms"
PRIVACY_URL = f"{BASE_URL}/privacy"
PLANS_URL = f"{BASE_URL}/pricing"
DOCS_URL = f"{BASE_URL}/docs"
HELP_URL = f"{BASE_URL}/help"
CHANGELOG_URL = f"{BASE_URL}/changelog"
COMMUNITY_URL = f"{BASE_URL}/community"

# Subscription URLs (v3.3 - subscription-only model)
COLLECTION_URL = f"{BASE_URL}/collection"
PREMIUM_URL = f"{BASE_URL}/settings?tab=subscription"
SUBSCRIBE_URL = PREMIUM_URL  # Alias for subscription page

# Limits and Magic Numbers (v4.0 - centralized)
DEFAULT_BATCH_LIMIT = 20
MAX_BATCH_LIMIT = 100
BATCH_DOWNLOAD_MAX = 10
PAGINATION_LIMIT = 1000
SYNC_TIMEOUT_SECONDS = 30
DOWNLOAD_TIMEOUT_SECONDS = 120
TEMP_FILE_SUFFIX = ".apkg"

# Study Stats Constants
RETENTION_DAYS_LOOKBACK = 30
STREAK_GRACE_DAYS = 1
MIN_EASE_FACTOR = 1300  # Anki default in permille
LEARNING_CARD_TYPE = 1
REVIEW_CARD_TYPE = 2
RELEARNING_CARD_TYPE = 3

# Other Constants
CHUNK_SIZE = 500
SQLITE_MAX_VARIABLES = 999
API_BATCH_SIZE = 500
UI_PREVIEW_LIMIT = 100
