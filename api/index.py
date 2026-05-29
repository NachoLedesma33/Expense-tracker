import os
import sys
import json

# Debug: write env vars (without secrets) to stderr for Vercel logs
print("[startup] DJANGO_SETTINGS_MODULE:", os.environ.get('DJANGO_SETTINGS_MODULE'), file=sys.stderr)
print("[startup] HAS_DJANGO_SECRET_KEY:", 'DJANGO_SECRET_KEY' in os.environ, file=sys.stderr)
print("[startup] HAS_DATABASE_URL:", 'DATABASE_URL' in os.environ, file=sys.stderr)
print("[startup] ALLOWED_HOSTS:", os.environ.get('DJANGO_ALLOWED_HOSTS'), file=sys.stderr)

try:
    from config.wsgi import application
    handler = application
    print("[startup] Django WSGI loaded successfully", file=sys.stderr)
except Exception as e:
    print(f"[startup] CRASH: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc(file=sys.stderr)

    def handler(environ, start_response):
        status = '500 Internal Server Error'
        headers = [('Content-Type', 'text/plain')]
        body = f"Startup Error: {e}\n\nCheck Vercel Function Logs for details.".encode()
        start_response(status, headers)
        return [body]
