import fs from 'fs';

const envContent = fs.readFileSync('.env.local', 'utf-8');
const env = {};
envContent.split('\n').forEach(line => {
  const parts = line.split('=');
  if (parts.length >= 2) {
    const key = parts[0].trim();
    let val = parts.slice(1).join('=').trim();
    if (val.startsWith('"') && val.endsWith('"')) {
      val = val.slice(1, -1);
    }
    env[key] = val;
  }
});

async function main() {
  console.log("Checking Neon Auth Endpoint:", env.NEON_AUTH_BASE_URL);
  try {
    const res = await fetch(env.NEON_AUTH_JWKS_URL);
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}: ${res.statusText}`);
    }
    const data = await res.json();
    console.log("Neon Auth JWKS response verified:", data);
  } catch (err) {
    console.error("Neon Auth error:", err);
    process.exit(1);
  }
}

main();
