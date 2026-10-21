import { neon } from '@neondatabase/serverless';
import fs from 'fs';

const envContent = fs.readFileSync('.env.local', 'utf-8');
const match = envContent.match(/DATABASE_URL="([^"]+)"/);
if (!match) {
  console.error("DATABASE_URL not found in .env.local");
  process.exit(1);
}

const sql = neon(match[1]);

async function main() {
  try {
    console.log("Connecting to Lakebase Postgres...");
    const result = await sql`SELECT NOW() as current_time, version() as pg_version;`;
    console.log("Success! Connected to Lakebase Postgres:");
    console.log(result);
  } catch (err) {
    console.error("Postgres error:", err);
    process.exit(1);
  }
}

main();
