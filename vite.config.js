import react from '@vitejs/plugin-react'
import { defineConfig, loadEnv } from 'vite'
import { neon } from '@neondatabase/serverless'
import { S3Client, PutObjectCommand, ListObjectsV2Command } from '@aws-sdk/client-s3'
import fs from 'fs'
import { 
  getAllMembers, 
  insertMember, 
  getAllTasks, 
  insertTask, 
  updateTask, 
  getAllProjects, 
  insertProject 
} from './src/backend/db.js'

function neonDevPlugin() {
  let env = {}
  return {
    name: 'neon-dev-plugin',
    configResolved(config) {
      env = loadEnv(config.mode, process.cwd(), '')
      if (fs.existsSync('.env.local')) {
        const local = fs.readFileSync('.env.local', 'utf-8')
        local.split('\n').forEach(line => {
          const parts = line.split('=')
          if (parts.length >= 2) {
            const key = parts[0].trim()
            let val = parts.slice(1).join('=').trim()
            if (val.startsWith('"') && val.endsWith('"')) val = val.slice(1, -1)
            env[key] = val
          }
        })
      }
    },
    configureServer(server) {
      server.middlewares.use(async (req, res, next) => {
        if (!req.url.startsWith('/api/')) {
          return next()
        }

        res.setHeader('Content-Type', 'application/json')
        const url = req.url.split('?')[0]

        try {
          // --- 1. NEON DIAGNOSTIC APIS ---
          if (url === '/api/neon/health') {
            const status = {
              postgres: { status: 'checking' },
              auth: { status: 'checking' },
              storage: { status: 'checking' },
              functions: { status: 'checking' },
              branch: env.NEON_BRANCH || 'production',
              timestamp: new Date().toISOString()
            }

            try {
              const sql = neon(env.DATABASE_URL)
              const [row] = await sql`SELECT NOW() as current_time, version() as pg_version;`
              status.postgres = { status: 'healthy', version: row.pg_version, time: row.current_time }
            } catch (err) {
              status.postgres = { status: 'error', error: err.message }
            }

            try {
              const authRes = await fetch(env.NEON_AUTH_JWKS_URL)
              if (authRes.ok) {
                const jwks = await authRes.json()
                status.auth = { status: 'healthy', endpoint: env.NEON_AUTH_BASE_URL, keys: jwks.keys?.length }
              } else {
                status.auth = { status: 'error', error: `HTTP ${authRes.status}` }
              }
            } catch (err) {
              status.auth = { status: 'error', error: err.message }
            }

            try {
              const s3 = new S3Client({
                region: env.AWS_REGION || 'us-east-2',
                endpoint: env.AWS_ENDPOINT_URL_S3,
                credentials: {
                  accessKeyId: env.AWS_ACCESS_KEY_ID,
                  secretAccessKey: env.AWS_SECRET_ACCESS_KEY,
                },
                forcePathStyle: true,
              })
              const listRes = await s3.send(new ListObjectsV2Command({ Bucket: 'assets' }))
              status.storage = { status: 'healthy', bucket: 'assets', objectCount: listRes.KeyCount || 0 }
            } catch (err) {
              status.storage = { status: 'error', error: err.message }
            }

            try {
              const fnRes = await fetch(env.NEON_FUNCTION_HELLO_BASE_URL)
              const body = await fnRes.text()
              status.functions = { status: 'healthy', endpoint: env.NEON_FUNCTION_HELLO_BASE_URL, response: body }
            } catch (err) {
              status.functions = { status: 'error', error: err.message }
            }

            res.end(JSON.stringify(status))
            return
          }

          if (url === '/api/neon/query' && req.method === 'POST') {
            let body = ''
            req.on('data', chunk => { body += chunk })
            req.on('end', async () => {
              try {
                const { query } = JSON.parse(body || '{}')
                const sql = neon(env.DATABASE_URL)
                const rows = await sql.query(query || 'SELECT NOW() as current_time, version() as pg_version;')
                res.end(JSON.stringify({ success: true, rows }))
              } catch (err) {
                res.statusCode = 500
                res.end(JSON.stringify({ success: false, error: err.message }))
              }
            })
            return
          }

          if (url === '/api/neon/storage' && req.method === 'POST') {
            let body = ''
            req.on('data', chunk => { body += chunk })
            req.on('end', async () => {
              try {
                const { key, content, contentType } = JSON.parse(body || '{}')
                const s3 = new S3Client({
                  region: env.AWS_REGION || 'us-east-2',
                  endpoint: env.AWS_ENDPOINT_URL_S3,
                  credentials: {
                    accessKeyId: env.AWS_ACCESS_KEY_ID,
                    secretAccessKey: env.AWS_SECRET_ACCESS_KEY,
                  },
                  forcePathStyle: true,
                })
                await s3.send(new PutObjectCommand({
                  Bucket: 'assets',
                  Key: key || `uploads/note-${Date.now()}.txt`,
                  Body: content || 'MobiusPilot Neon asset payload',
                  ContentType: contentType || 'text/plain',
                }))
                res.end(JSON.stringify({ success: true, message: 'Object stored in Neon assets bucket' }))
              } catch (err) {
                res.statusCode = 500
                res.end(JSON.stringify({ success: false, error: err.message }))
              }
            })
            return
          }

          if (url === '/api/neon/function') {
            const fnRes = await fetch(env.NEON_FUNCTION_HELLO_BASE_URL)
            const text = await fnRes.text()
            res.end(JSON.stringify({ success: true, response: text }))
            return
          }

          // --- 2. APPLICATION BACKEND REST ENDPOINTS ---

          // Members
          if (url === '/api/members') {
            if (req.method === 'GET') {
              const members = await getAllMembers()
              res.end(JSON.stringify(members))
              return
            }
            if (req.method === 'POST') {
              let body = ''
              req.on('data', c => body += c)
              req.on('end', async () => {
                const data = JSON.parse(body || '{}')
                const member = await insertMember(data)
                res.end(JSON.stringify(member))
              })
              return
            }
          }

          // Tasks
          if (url === '/api/tasks') {
            if (req.method === 'GET') {
              const tasks = await getAllTasks()
              res.end(JSON.stringify(tasks))
              return
            }
            if (req.method === 'POST') {
              let body = ''
              req.on('data', c => body += c)
              req.on('end', async () => {
                const data = JSON.parse(body || '{}')
                const task = await insertTask(data)
                res.end(JSON.stringify(task))
              })
              return
            }
            if (req.method === 'PATCH') {
              let body = ''
              req.on('data', c => body += c)
              req.on('end', async () => {
                const { id, ...updates } = JSON.parse(body || '{}')
                const updated = await updateTask(id, updates)
                res.end(JSON.stringify(updated))
              })
              return
            }
          }

          // Projects
          if (url === '/api/projects') {
            if (req.method === 'GET') {
              const projects = await getAllProjects()
              res.end(JSON.stringify(projects))
              return
            }
            if (req.method === 'POST') {
              let body = ''
              req.on('data', c => body += c)
              req.on('end', async () => {
                const data = JSON.parse(body || '{}')
                const project = await insertProject(data)
                res.end(JSON.stringify(project))
              })
              return
            }
          }

          // AI Agent Task Distribution
          if (url === '/api/ai/distribute' && req.method === 'POST') {
            let body = ''
            req.on('data', c => body += c)
            req.on('end', async () => {
              const { prompt, tasks: distributedTasks } = JSON.parse(body || '{}')
              const saved = []
              if (Array.isArray(distributedTasks)) {
                for (const t of distributedTasks) {
                  const created = await insertTask(t)
                  saved.push(created)
                }
              }
              res.end(JSON.stringify({ success: true, count: saved.length, tasks: saved }))
            })
            return
          }

          res.statusCode = 404
          res.end(JSON.stringify({ error: 'Endpoint not found' }))
        } catch (err) {
          res.statusCode = 500
          res.end(JSON.stringify({ error: err.message }))
        }
      })
    }
  }
}

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), neonDevPlugin()],
})
