"""
ClaWin1Click - Configuracoes
Variaveis de ambiente e configuracoes globais
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ============================================
# API KEYS
# ============================================
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")  # Para STT (Whisper) e TTS

# ============================================
# DATABASE
# ============================================
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost/clawin1click")

# ============================================
# REDIS
# ============================================
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# ============================================
# SECURITY
# ============================================
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("CRITICAL: SECRET_KEY not set. Set it in .env")

# ENCRYPTION_KEY - CRITICO: Esta chave NUNCA pode mudar ou os dados serao perdidos!
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")

if not ENCRYPTION_KEY:
    raise RuntimeError(
        "[CRITICAL] ENCRYPTION_KEY nao configurada! "
        "Esta variavel e OBRIGATORIA para criptografia de dados. "
        "Configure no .env ou variaveis de ambiente antes de iniciar."
    )

JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_HOURS = 1
JWT_REFRESH_TOKEN_DAYS = 30

# ============================================
# APP SETTINGS
# ============================================
APP_NAME = "OpenClaw"
APP_VERSION = "1.0.0"
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

MAINTENANCE_MODE = os.getenv("MAINTENANCE_MODE", "False").lower() == "true"

# ============================================
# AI SETTINGS
# ============================================
# Provider: "proxy" (Codex via Railway) | "openai" (GPT direto) | "anthropic" (Claude direto)
AI_PROVIDER = os.getenv("AI_PROVIDER", "proxy")

# AI models — Codex (GPT-5.2) via Railway proxy (principal)
AI_MODEL_PRIMARY = os.getenv("CLAUDE_MODEL", "gpt-5.2-codex")
AI_MODEL_FALLBACK = os.getenv("CLAUDE_MODEL_FALLBACK", "gpt-5.2-codex")
AI_MODEL_EXTRACTION = os.getenv("CLAUDE_MODEL_EXTRACTION", "gpt-5.2-codex")

# OpenAI models (fallback direto quando provider=openai)
OPENAI_MODEL_PRIMARY = "gpt-4o-mini"
OPENAI_MODEL_EXTRACTION = "gpt-4o-mini"

# Proxy settings (Codex via Railway — ChatGPT Plus OAuth)
PROXY_URL = os.getenv("CLAUDE_PROXY_URL", "https://codex-chatgpt-proxy-production.up.railway.app/v1")

# Proxy model aliases (resolvidos do env, default = Codex)
PROXY_MODEL_PRIMARY    = AI_MODEL_PRIMARY
PROXY_MODEL_EXTRACTION = AI_MODEL_EXTRACTION

MAX_TOKENS_RESPONSE = 2000
MAX_CONTEXT_TOKENS = 4000

# Social Module — Worker API Key
SOCIAL_WORKER_API_KEY = os.getenv("SOCIAL_WORKER_API_KEY", "")

# Voice Settings
VOICE_ENABLED = os.getenv("VOICE_ENABLED", "True").lower() == "true"
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
STT_PROVIDER = os.getenv("STT_PROVIDER", "groq")  # "groq" (free) or "openai"
STT_MODEL = "whisper-1"
STT_MODEL_GROQ = "whisper-large-v3-turbo"
STT_MAX_FILE_SIZE = 25 * 1024 * 1024
TTS_MODEL = "tts-1-hd"
TTS_VOICE = "nova"
TTS_SPEED = 1.0

# Edge TTS (free) — default voices per language
EDGE_TTS_VOICE_PT = os.getenv("EDGE_TTS_VOICE_PT", "pt-BR-FranciscaNeural")
EDGE_TTS_VOICE_EN = os.getenv("EDGE_TTS_VOICE_EN", "en-US-JennyNeural")
EDGE_TTS_VOICE_ES = os.getenv("EDGE_TTS_VOICE_ES", "es-MX-DaliaNeural")

# TTS Provider: "edge" (free) or "openai" ($15/1M chars)
TTS_PROVIDER = os.getenv("TTS_PROVIDER", "edge")

# ============================================
# PRICING
# ============================================
PLAN_PRICE_USD = 29.90    # Plano unico

# ============================================
# AFFILIATES
# ============================================
AFFILIATE_DEFAULT_COMMISSION_RATE = 0.30    # 30% do liquido = $8.62/mes por referido
AFFILIATE_COOKIE_DAYS = 30
AFFILIATE_AUTO_PAYOUT_THRESHOLD = float(os.getenv("AFFILIATE_AUTO_PAYOUT_THRESHOLD", "25.00"))
AFFILIATE_MIN_MONTHLY_PAYOUT = float(os.getenv("AFFILIATE_MIN_MONTHLY_PAYOUT", "10.00"))
AFFILIATE_DEFAULT_TOKEN = os.getenv("AFFILIATE_DEFAULT_TOKEN", "USDT")
AFFILIATE_DEFAULT_NETWORK = os.getenv("AFFILIATE_DEFAULT_NETWORK", "bep20")

# ============================================
# STRIPE
# ============================================
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
STRIPE_PRICE_ID = os.getenv("STRIPE_PRICE_ID", "")  # Stripe Price ID for $29.90/month (individual)
STRIPE_BUSINESS_PRICE_ID = os.getenv("STRIPE_BUSINESS_PRICE_ID", "")  # Stripe Price ID for business plan (legacy)
STRIPE_SETUP_PRICE_ID = os.getenv("STRIPE_SETUP_PRICE_ID", "price_1TAOKeP8Hos97mNkANWMYkjt")  # $200 one-time setup
STRIPE_MONTHLY_PRICE_ID = os.getenv("STRIPE_MONTHLY_PRICE_ID", "price_1T98fsP8Hos97mNkyplI6yUU")  # $199/mo recurring

# ============================================
# INSTANCE PROVISIONING (Hostinger VPS API)
# ============================================
HOSTINGER_API_TOKEN = os.getenv("HOSTINGER_API_TOKEN", "")
HOSTINGER_API_BASE = "https://developers.hostinger.com"
HOSTINGER_DATACENTER = os.getenv("HOSTINGER_DATACENTER", "us-central-1")
HOSTINGER_DOCKER_PROJECT_NAME = os.getenv("HOSTINGER_DOCKER_PROJECT_NAME", "openclaw")
HOSTINGER_PROVISION_TIMEOUT = int(os.getenv("HOSTINGER_PROVISION_TIMEOUT", "300"))  # seconds

# ============================================
# OAUTH SETTINGS
# ============================================
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8002/auth/google/callback")

GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID", "")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET", "")
GITHUB_REDIRECT_URI = os.getenv("GITHUB_REDIRECT_URI", "http://localhost:8002/auth/github/callback")

# ============================================
# CORS SETTINGS
# ============================================
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
CORS_ALLOW_HEADERS = ["*"]

PRODUCTION_ORIGINS = [
    "https://clawin1click.com",
    "https://www.clawin1click.com",
    "https://primerstarcorp.com",
    "https://www.primerstarcorp.com",
    "https://clawtobusiness.com",
    "https://www.clawtobusiness.com",
]

# ============================================
# EMAIL SETTINGS (Resend)
# ============================================
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
EMAIL_FROM = os.getenv("EMAIL_FROM", "OpenClaw to Business <noreply@clawtobusiness.com>")
EMAIL_REPLY_TO = os.getenv("EMAIL_REPLY_TO", "contact@clawtobusiness.com")
APP_URL = os.getenv("APP_URL", "https://clawtobusiness.com")

# ============================================
# ADMIN SETTINGS
# ============================================
ADMIN_EMAILS = os.getenv("ADMIN_EMAILS", "root@clawtobusiness.com,admin@clawin1click.com").split(",")

# ============================================
# MODERATION (OpenAI)
# ============================================
MODERATION_MODEL = "omni-moderation-latest"
MODERATION_ENABLED = os.getenv("MODERATION_ENABLED", "True").lower() == "true"

# ============================================
# TELEGRAM — sales bot channel
# ============================================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_WEBHOOK_SECRET = os.getenv("TELEGRAM_WEBHOOK_SECRET", "")  # optional header secret

# ============================================
# WHATSAPP (Evolution API) — for sales bot
# ============================================
EVOLUTION_API_URL = os.getenv("EVOLUTION_API_URL", "")
EVOLUTION_API_KEY = os.getenv("EVOLUTION_API_KEY", "")
EVOLUTION_WEBHOOK_SECRET = os.getenv("EVOLUTION_WEBHOOK_SECRET", "")

# ============================================
# RAILWAY (site deployment — legacy)
# ============================================
RAILWAY_API_TOKEN = os.getenv("RAILWAY_API_TOKEN", "")

# ============================================
# CLOUDFLARE (site deployment — primary)
# ============================================
CLOUDFLARE_ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID", "")
CLOUDFLARE_API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN", "")

# ============================================
# PUSH NOTIFICATIONS (VAPID)
# ============================================
VAPID_PUBLIC_KEY = os.getenv("VAPID_PUBLIC_KEY", "")
VAPID_PRIVATE_KEY = os.getenv("VAPID_PRIVATE_KEY", "")
VAPID_CLAIMS_EMAIL = os.getenv("VAPID_CLAIMS_EMAIL", "suporte@clawin1click.com")

# ============================================
# TWILIO (SMS for Xcleaners notifications)
# ============================================
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER", "")

# ============================================
# XCLEANERS MODULE
# ============================================
XCLEANERS_DEFAULT_PLAN = os.getenv("XCLEANERS_DEFAULT_PLAN", "basic")
XCLEANERS_AUTO_SCHEDULE_TIME = os.getenv("XCLEANERS_AUTO_SCHEDULE_TIME", "18:00")
VAPID_SUBJECT = os.getenv("VAPID_SUBJECT", "mailto:suporte@xcleaners.com")
