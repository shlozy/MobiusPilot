import http from 'http';
import fs from 'fs';
import { 
  initDatabase, 
  getAllMembers, 
  insertMember, 
  getAllTasks, 
  insertTask, 
  updateTask, 
  getAllProjects, 
  insertProject 
} from './src/backend/db.js';
import { INITIAL_MEMBERS, INITIAL_TASKS, INITIAL_BUSINESS_PROJECTS } from './src/data/mockData.js';

const PORT = process.env.PORT || 4000;

// Initialize and seed database on startup
await initDatabase(INITIAL_MEMBERS, INITIAL_TASKS, INITIAL_BUSINESS_PROJECTS);

const server = http.createServer(async (req, res) => {
  // CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PATCH, DELETE, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');

  if (req.method === 'OPTIONS') {
    res.writeHead(204);
    res.end();
    return;
  }

  res.setHeader('Content-Type', 'application/json');
  const url = req.url.split('?')[0];

  try {
    if (url === '/api/health') {
      res.end(JSON.stringify({ status: 'ok', time: new Date().toISOString() }));
      return;
    }

    if (url === '/api/members') {
      if (req.method === 'GET') {
        const members = await getAllMembers();
        res.end(JSON.stringify(members));
        return;
      }
      if (req.method === 'POST') {
        let body = '';
        req.on('data', c => body += c);
        req.on('end', async () => {
          const m = await insertMember(JSON.parse(body || '{}'));
          res.end(JSON.stringify(m));
        });
        return;
      }
    }

    if (url === '/api/tasks') {
      if (req.method === 'GET') {
        const tasks = await getAllTasks();
        res.end(JSON.stringify(tasks));
        return;
      }
      if (req.method === 'POST') {
        let body = '';
        req.on('data', c => body += c);
        req.on('end', async () => {
          const t = await insertTask(JSON.parse(body || '{}'));
          res.end(JSON.stringify(t));
        });
        return;
      }
      if (req.method === 'PATCH') {
        let body = '';
        req.on('data', c => body += c);
        req.on('end', async () => {
          const { id, ...updates } = JSON.parse(body || '{}');
          const updated = await updateTask(id, updates);
          res.end(JSON.stringify(updated));
        });
        return;
      }
    }

    if (url === '/api/projects') {
      if (req.method === 'GET') {
        const projs = await getAllProjects();
        res.end(JSON.stringify(projs));
        return;
      }
      if (req.method === 'POST') {
        let body = '';
        req.on('data', c => body += c);
        req.on('end', async () => {
          const p = await insertProject(JSON.parse(body || '{}'));
          res.end(JSON.stringify(p));
        });
        return;
      }
    }

    res.statusCode = 404;
    res.end(JSON.stringify({ error: 'Not found' }));
  } catch (err) {
    res.statusCode = 500;
    res.end(JSON.stringify({ error: err.message }));
  }
});

server.listen(PORT, () => {
  console.log(`🚀 MobiusPilot Neon Backend Server running on http://localhost:${PORT}`);
});
