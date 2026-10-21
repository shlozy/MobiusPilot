import { neon } from '@neondatabase/serverless';
import fs from 'fs';

const envContent = fs.readFileSync('.env.local', 'utf-8');
const match = envContent.match(/DATABASE_URL="([^"]+)"/);
const sql = neon(match[1]);

async function main() {
  console.log("Setting up tables in Lakebase Postgres...");
  await sql`
    CREATE TABLE IF NOT EXISTS system_telemetry (
      id SERIAL PRIMARY KEY,
      service VARCHAR(50) NOT NULL,
      status VARCHAR(20) NOT NULL,
      payload JSONB,
      created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
  `;
  console.log("Table system_telemetry verified/created.");

  const insertRes = await sql`
    INSERT INTO system_telemetry (service, status, payload)
    VALUES ('Neon Postgres', 'healthy', '{"app": "MobiusPilot", "version": "1.0.0"}'::jsonb)
    RETURNING *;
  `;
  console.log("Inserted row:", insertRes[0]);

  const countRes = await sql`SELECT count(*) as total FROM system_telemetry;`;
  console.log("Total telemetry rows:", countRes[0].total);
}

main().catch(err => {
  console.error("Migration error:", err);
  process.exit(1);
});
