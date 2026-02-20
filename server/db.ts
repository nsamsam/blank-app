import { Pool } from "pg";
import { drizzle } from "drizzle-orm/node-postgres";
import * as schema from "../shared/schema.js";

if (!process.env.DATABASE_URL) {
  console.error(
    "ERROR: DATABASE_URL is not set. Please add a PostgreSQL database and set the DATABASE_URL environment variable."
  );
}

// Railway private networking (.railway.internal) does NOT support SSL.
// Railway public URLs (rlwy.net) require SSL.
const dbUrl = process.env.DATABASE_URL || "";
const useSSL = dbUrl.includes("rlwy.net") ? { rejectUnauthorized: false } : false;

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: useSSL,
  connectionTimeoutMillis: 10000,
  idleTimeoutMillis: 30000,
});

// Test connection on startup
pool.query("SELECT 1").then(() => {
  console.log("Database connected successfully");
}).catch((err) => {
  console.error("Database connection failed:", err.message);
});

export const db = drizzle(pool, { schema });
