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
  const url = env.NEON_FUNCTION_HELLO_BASE_URL;
  console.log("Calling Neon Function at:", url);
  try {
    const res = await fetch(url);
    console.log("Status:", res.status, res.statusText);
    const text = await res.text();
    console.log("Function response body:", text);
  } catch (err) {
    console.error("Neon Function error:", err);
    process.exit(1);
  }
}

main();
