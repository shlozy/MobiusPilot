async function runE2ETests() {
  const baseUrl = 'http://localhost:5174';

  console.log("=== 1. TESTING /api/neon/health (All 4 Services Health Check) ===");
  const healthRes = await fetch(`${baseUrl}/api/neon/health`);
  const health = await healthRes.json();
  console.log("Health Status:", JSON.stringify(health, null, 2));

  console.log("\n=== 2. TESTING /api/neon/query (Lakebase Postgres Query) ===");
  const queryRes = await fetch(`${baseUrl}/api/neon/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query: 'SELECT count(*) as row_count FROM system_telemetry;' })
  });
  const queryData = await queryRes.json();
  console.log("Postgres Query Response:", JSON.stringify(queryData, null, 2));

  console.log("\n=== 3. TESTING /api/neon/storage (Object Storage Put in 'assets' bucket) ===");
  const storageRes = await fetch(`${baseUrl}/api/neon/storage`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      key: `e2e/test-proof-${Date.now()}.txt`,
      content: 'Proving Neon Object Storage integration in MobiusPilot',
      contentType: 'text/plain'
    })
  });
  const storageData = await storageRes.json();
  console.log("Storage Put Response:", JSON.stringify(storageData, null, 2));

  console.log("\n=== 4. TESTING /api/neon/function (Neon Function 'hello' Call) ===");
  const fnRes = await fetch(`${baseUrl}/api/neon/function`);
  const fnData = await fnRes.json();
  console.log("Neon Function Ping Response:", JSON.stringify(fnData, null, 2));
}

runE2ETests().catch(err => {
  console.error("E2E Test Failed:", err);
  process.exit(1);
});
