"""Generate local-only credentials once. Never overwrite existing configuration."""
from pathlib import Path
import secrets

root = Path(__file__).resolve().parents[1]
env = root / ".env"
if not env.exists():
    env.write_text(f"POSTGRES_PASSWORD={secrets.token_urlsafe(32)}\n")
    env.chmod(0o600)
values = dict(line.split("=", 1) for line in env.read_text().splitlines() if "=" in line and not line.startswith("#"))
password = values["POSTGRES_PASSWORD"]
url = f"postgresql://resolvedesk:{password}@127.0.0.1:55432/resolvedesk"
files = {
    root / "apps/web/.env.local": f"DATABASE_URL={url}\nBETTER_AUTH_SECRET={secrets.token_urlsafe(48)}\nBETTER_AUTH_URL=http://localhost:3000\nAPI_URL=http://127.0.0.1:8000\n",
    root / "apps/api/.env": f"DATABASE_URL={url.replace('postgresql://', 'postgresql+psycopg://')}\nAUTH_URL=http://localhost:3000\nAPP_ORIGIN=http://localhost:3000\nDEMO_ENABLED=true\n",
}
for path, contents in files.items():
    if not path.exists():
        path.write_text(contents)
        path.chmod(0o600)
print("Local environment files are ready; existing files preserved. No credentials printed.")
