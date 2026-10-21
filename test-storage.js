import { S3Client, PutObjectCommand, GetObjectCommand, ListObjectsV2Command } from '@aws-sdk/client-s3';
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

const s3 = new S3Client({
  region: env.AWS_REGION || 'us-east-2',
  endpoint: env.AWS_ENDPOINT_URL_S3,
  credentials: {
    accessKeyId: env.AWS_ACCESS_KEY_ID,
    secretAccessKey: env.AWS_SECRET_ACCESS_KEY,
  },
  forcePathStyle: true,
});

async function main() {
  const bucketName = 'assets';
  const testKey = 'test/mobiuspilot-demo.txt';
  const testContent = `MobiusPilot Neon Object Storage Test - Timestamp: ${new Date().toISOString()}`;

  try {
    console.log(`Writing test object to bucket: ${bucketName}...`);
    await s3.send(new PutObjectCommand({
      Bucket: bucketName,
      Key: testKey,
      Body: testContent,
      ContentType: 'text/plain',
    }));
    console.log("PutObject successful!");

    console.log(`Listing objects in bucket: ${bucketName}...`);
    const listRes = await s3.send(new ListObjectsV2Command({
      Bucket: bucketName,
    }));
    console.log("Found objects:", listRes.Contents?.map(c => ({ key: c.Key, size: c.Size })));

    console.log(`Reading back test object: ${testKey}...`);
    const getRes = await s3.send(new GetObjectCommand({
      Bucket: bucketName,
      Key: testKey,
    }));
    const downloadedText = await getRes.Body.transformToString();
    console.log("Read object content successfully:", downloadedText);
  } catch (err) {
    console.error("Storage error:", err);
    process.exit(1);
  }
}

main();
