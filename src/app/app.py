"""ScoutCloud - NBA intelligence platform Flask application.

Six routes (/, /health, /players, /scores, /analytics, /metrics) driven entirely
by environment variables. The app runs on first deploy with placeholder data;
each AWS chapter swaps one env var to wire up a real backend.
"""
import json
import os
import random
import re
import time
from datetime import datetime, timezone
from urllib.parse import quote_plus

import requests
from flask import Flask, Response, jsonify, render_template, request

try:
    import boto3
    from botocore.exceptions import BotoCoreError, ClientError
except Exception:
    boto3 = None
    BotoCoreError = ClientError = Exception

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except Exception:
    psycopg2 = None
    RealDictCursor = None

from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)

try:
    from jose import jwt
    from jose.utils import base64url_decode
except Exception:
    jwt = None
    base64url_decode = None


APP_VERSION = "1.0.0"
START_TIME = time.time()

DATABASE_URL = os.environ.get("DATABASE_URL", "placeholder")
DYNAMODB_TABLE = os.environ.get("DYNAMODB_TABLE", "placeholder")
COGNITO_USER_POOL_ID = os.environ.get("COGNITO_USER_POOL_ID", "")
COGNITO_CLIENT_ID = os.environ.get("COGNITO_CLIENT_ID", "")
COGNITO_DOMAIN = os.environ.get("COGNITO_DOMAIN", "scoutcloud-auth")
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
SECRET_ARN = os.environ.get("SECRET_ARN", "")


def _load_password_from_secrets_manager():
    """If SECRET_ARN is set, fetch password and rewrite DATABASE_URL."""
    global DATABASE_URL
    if not SECRET_ARN or boto3 is None:
        return
    try:
        client = boto3.client("secretsmanager", region_name=AWS_REGION)
        resp = client.get_secret_value(SecretId=SECRET_ARN)
        secret = json.loads(resp["SecretString"])
        password = secret["password"]
        # Replace password in DATABASE_URL: postgresql://user[:old]@host:5432/db
        m = re.match(
            r"^(?P<scheme>postgresql)://(?P<user>[^:@]+)(?::[^@]*)?@(?P<rest>.+)$",
            DATABASE_URL,
        )
        if m:
            DATABASE_URL = (
                f"{m.group('scheme')}://{m.group('user')}:"
                f"{quote_plus(password)}@{m.group('rest')}"
            )
            print("[STARTUP] Database password loaded from Secrets Manager", flush=True)
    except (BotoCoreError, ClientError, KeyError, json.JSONDecodeError) as e:
        print(f"[STARTUP] WARNING: failed to load secret {SECRET_ARN}: {e}", flush=True)


def _fetch_instance_id():
    try:
        r = requests.get(
            "http://169.254.169.254/latest/meta-data/instance-id", timeout=0.5
        )
        if r.status_code == 200 and r.text.strip():
            return r.text.strip()
    except requests.RequestException:
        pass
    return "local-dev"


_load_password_from_secrets_manager()
INSTANCE_ID = _fetch_instance_id()

if DATABASE_URL != "placeholder":
    print("[STARTUP] Database: CONNECTED (RDS)", flush=True)
else:
    print("[STARTUP] Database: PLACEHOLDER - connect RDS in Chapter 7", flush=True)
if DYNAMODB_TABLE != "placeholder":
    print("[STARTUP] DynamoDB: CONNECTED", flush=True)
else:
    print("[STARTUP] DynamoDB: PLACEHOLDER - connect Lambda in Chapter 8", flush=True)


REQUESTS_COUNTER = Counter(
    "scoutcloud_requests_total",
    "Total requests",
    ["endpoint", "method", "status"],
)
LATENCY = Histogram(
    "scoutcloud_request_duration_seconds",
    "Request duration",
    ["endpoint"],
)
DB_CONNECTED = Gauge(
    "scoutcloud_database_connected", "1 if RDS connected, 0 if placeholder"
)
DDB_CONNECTED = Gauge(
    "scoutcloud_dynamodb_connected", "1 if DynamoDB connected, 0 if placeholder"
)
ACTIVE_USERS = Gauge("scoutcloud_active_users", "Simulated active users")


app = Flask(__name__)


def build_cognito_url():
    if not COGNITO_USER_POOL_ID or not COGNITO_CLIENT_ID:
        return ""
    return (
        f"https://{COGNITO_DOMAIN}.auth.{AWS_REGION}.amazoncognito.com/login"
        f"?client_id={COGNITO_CLIENT_ID}"
        f"&response_type=code"
        f"&scope=email+openid+profile"
        f"&redirect_uri=https://scoutcloud.dev"
    )


@app.before_request
def _start_timer():
    request._sc_start = time.time()


@app.after_request
def _record_metrics(response):
    endpoint = request.path
    duration = time.time() - getattr(request, "_sc_start", time.time())
    LATENCY.labels(endpoint=endpoint).observe(duration)
    REQUESTS_COUNTER.labels(
        endpoint=endpoint, method=request.method, status=str(response.status_code)
    ).inc()
    DB_CONNECTED.set(0 if DATABASE_URL == "placeholder" else 1)
    DDB_CONNECTED.set(0 if DYNAMODB_TABLE == "placeholder" else 1)
    ACTIVE_USERS.set(random.randint(1200, 1800))
    return response


@app.route("/")
def index():
    return render_template(
        "index.html",
        instance_id=INSTANCE_ID,
        aws_region=AWS_REGION,
        database_connected=DATABASE_URL != "placeholder",
        dynamodb_connected=DYNAMODB_TABLE != "placeholder",
        cognito_enabled=bool(COGNITO_USER_POOL_ID),
        cognito_hosted_ui_url=build_cognito_url(),
    )


@app.route("/health")
def health():
    return jsonify(
        {
            "status": "ok",
            "instance_id": INSTANCE_ID,
            "uptime_seconds": int(time.time() - START_TIME),
            "current_time": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "database": "connected" if DATABASE_URL != "placeholder" else "placeholder",
            "dynamodb": "connected"
            if DYNAMODB_TABLE != "placeholder"
            else "placeholder",
            "version": APP_VERSION,
        }
    )


@app.route("/players")
def players():
    if DATABASE_URL == "placeholder":
        return jsonify(
            {
                "players": [],
                "source": "placeholder",
                "message": "Connect RDS in Chapter 7 - set DATABASE_URL env var",
            }
        )
    if psycopg2 is None:
        return (
            jsonify(
                {
                    "players": [],
                    "source": "error",
                    "message": "psycopg2 not installed",
                }
            ),
            500,
        )
    try:
        conn = psycopg2.connect(DATABASE_URL, connect_timeout=5)
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT p.name, t.name AS team, p.position,
                           p.ppg, p.apg, p.rpg, p.fg_pct
                    FROM players p
                    JOIN teams t ON p.team_id = t.team_id
                    ORDER BY p.ppg DESC
                    """
                )
                rows = [dict(r) for r in cur.fetchall()]
        finally:
            conn.close()
        return jsonify({"players": rows, "source": "rds", "count": len(rows)})
    except Exception as e:
        return (
            jsonify({"players": [], "source": "error", "message": str(e)}),
            500,
        )


@app.route("/scores")
def scores():
    if DYNAMODB_TABLE == "placeholder":
        return jsonify(
            {
                "games": [
                    {
                        "game_id": "NYK-BOS",
                        "home_team": "Knicks",
                        "away_team": "Celtics",
                        "home_score": 0,
                        "away_score": 0,
                        "status": "Scheduled",
                        "venue": "Madison Square Garden",
                        "updated_at": None,
                    },
                    {
                        "game_id": "LAL-GSW",
                        "home_team": "Lakers",
                        "away_team": "Warriors",
                        "home_score": 0,
                        "away_score": 0,
                        "status": "Scheduled",
                        "venue": "Crypto.com Arena",
                        "updated_at": None,
                    },
                    {
                        "game_id": "MIL-MIA",
                        "home_team": "Bucks",
                        "away_team": "Heat",
                        "home_score": 0,
                        "away_score": 0,
                        "status": "Scheduled",
                        "venue": "Fiserv Forum",
                        "updated_at": None,
                    },
                ],
                "source": "placeholder",
                "message": "Connect Lambda + DynamoDB in Chapter 8",
            }
        )
    if boto3 is None:
        return (
            jsonify(
                {"games": [], "source": "error", "message": "boto3 not installed"}
            ),
            500,
        )
    try:
        dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
        table = dynamodb.Table(DYNAMODB_TABLE)
        response = table.scan()
        return jsonify(
            {
                "games": response.get("Items", []),
                "source": "dynamodb",
                "count": response.get("Count", 0),
            }
        )
    except Exception as e:
        return jsonify({"games": [], "source": "error", "message": str(e)}), 500


_ANALYTICS_PAYLOAD = {
    "player": "Jalen Brunson",
    "team": "New York Knicks",
    "shot_zones": [
        {"zone": "Paint", "attempts": 142, "made": 87, "pct": 61.3},
        {"zone": "Mid-range", "attempts": 89, "made": 43, "pct": 48.3},
        {"zone": "Left corner 3", "attempts": 47, "made": 16, "pct": 34.0},
        {"zone": "Top of key 3", "attempts": 112, "made": 61, "pct": 54.5},
        {"zone": "Right wing 3", "attempts": 67, "made": 29, "pct": 43.3},
    ],
    "recent_alerts": [
        {
            "type": "milestone",
            "message": "Brunson 30+ pts - Knicks vs Celtics",
            "time_ago": "2h ago",
        },
        {
            "type": "live",
            "message": "Curry shooting 6-for-8 from 3 - live now",
            "time_ago": "now",
        },
        {
            "type": "report",
            "message": "Weekly shot chart export ready",
            "time_ago": "1d ago",
        },
    ],
    "source": "static",
}


_jwks_cache = {}


def _get_jwks():
    if not COGNITO_USER_POOL_ID:
        return None
    if COGNITO_USER_POOL_ID in _jwks_cache:
        return _jwks_cache[COGNITO_USER_POOL_ID]
    url = (
        f"https://cognito-idp.{AWS_REGION}.amazonaws.com/"
        f"{COGNITO_USER_POOL_ID}/.well-known/jwks.json"
    )
    try:
        r = requests.get(url, timeout=3)
        r.raise_for_status()
        _jwks_cache[COGNITO_USER_POOL_ID] = r.json()
        return _jwks_cache[COGNITO_USER_POOL_ID]
    except Exception:
        return None


def _validate_token(token):
    if jwt is None:
        return None, "python-jose not installed"
    jwks = _get_jwks()
    if not jwks:
        return None, "JWKS unavailable"
    try:
        headers = jwt.get_unverified_header(token)
        kid = headers.get("kid")
        key = next((k for k in jwks.get("keys", []) if k.get("kid") == kid), None)
        if not key:
            return None, "Signing key not found"
        claims = jwt.decode(
            token,
            key,
            algorithms=[key.get("alg", "RS256")],
            options={"verify_aud": False},
        )
        return claims, None
    except Exception as e:
        return None, str(e)


@app.route("/analytics")
def analytics():
    if not COGNITO_USER_POOL_ID:
        return jsonify(_ANALYTICS_PAYLOAD)
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return (
            jsonify({"error": "Authentication required", "login_url": "/"}),
            401,
        )
    token = auth[len("Bearer ") :].strip()
    claims, err = _validate_token(token)
    if claims is None:
        return jsonify({"error": "Invalid or expired token", "detail": err}), 401
    payload = dict(_ANALYTICS_PAYLOAD)
    payload["user_email"] = claims.get("email", "")
    return jsonify(payload)


@app.route("/metrics")
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "8080")))
