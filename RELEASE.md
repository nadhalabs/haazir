# Haazir release configuration

## Flutter API URL

Every release build must provide the public HTTPS API root explicitly:

```bash
flutter build apk --release \
  --dart-define=HAAZIR_API_URL=https://haazir-api.onrender.com/api/v1
```

The apps remove trailing slashes. Release startup fails clearly when the value is
missing, malformed, or not HTTPS. Debug builds may use the local development API.
Future WebSocket clients should derive `wss` from this HTTPS URL.

## Render backend

The root `render.yaml` provisions the Docker API, PostgreSQL, and a private Render
Key Value instance and runs `alembic upgrade head` before each deployment.

Required production variables:

- `DATABASE_URL`: Render PostgreSQL internal connection string.
- `REDIS_URL`: Render Key Value internal connection string.
- `SECRET_KEY`: generated or a random secret of at least 32 characters.
- `CORS_ORIGINS` (or legacy `BACKEND_CORS_ORIGINS`): JSON array of exact trusted web origins, for example
  `["https://admin.example.com"]`; never `*` in production.
- `ENVIRONMENT=production`.

The container binds `0.0.0.0` and respects Render's `PORT`. Do not seed an admin
password in deployment configuration; provision admin accounts out of band.

## Android signing

Current release APK builds use Flutter's local debug signing configuration only
for installable verification artifacts. Before Play distribution, create an upload
keystore outside Git, configure Gradle through an untracked `key.properties` or CI
secrets, and retain the application IDs permanently. Never commit `.jks` files or
passwords.
