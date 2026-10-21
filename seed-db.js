import { initDatabase, getAllMembers, getAllTasks } from './src/backend/db.js';
import { INITIAL_MEMBERS, INITIAL_TASKS, INITIAL_BUSINESS_PROJECTS } from './src/data/mockData.js';

async function main() {
  console.log("Seeding and verifying database in Neon Postgres...");
  await initDatabase(INITIAL_MEMBERS, INITIAL_TASKS, INITIAL_BUSINESS_PROJECTS);
  const members = await getAllMembers();
  const tasks = await getAllTasks();
  console.log(`Neon Database ready! Members: ${members.length}, Tasks: ${tasks.length}`);
}

main().catch(console.error);
