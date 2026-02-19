import express from "express";
import path from "path";
import { fileURLToPath } from "url";
import { setupAuth } from "./auth.js";
import { setupRoutes } from "./routes.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const app = express();
const PORT = Number(process.env.PORT) || 3000;

// Trust reverse proxy (needed for secure cookies behind load balancers)
if (process.env.NODE_ENV === "production") {
  app.set("trust proxy", 1);
}

app.use(express.json({ limit: "10mb" }));
app.use(express.urlencoded({ extended: true }));

if (!process.env.DATABASE_URL) {
  // No database configured — serve a setup message instead of crashing
  app.use((_req, res) => {
    res.status(503).send(`
      <html>
        <head><title>Setup Required</title></head>
        <body style="font-family:system-ui;max-width:600px;margin:80px auto;padding:0 20px">
          <h1>Database Setup Required</h1>
          <p>The <code>DATABASE_URL</code> environment variable is not set.</p>
          <p>To fix this:</p>
          <ol>
            <li>Provision a PostgreSQL database</li>
            <li>Set the <code>DATABASE_URL</code> environment variable (secret) to the connection string</li>
            <li>Restart the application</li>
          </ol>
          <p>Example format: <code>postgresql://user:password@host:5432/dbname</code></p>
        </body>
      </html>
    `);
  });
} else {
  setupAuth(app);
  setupRoutes(app);

  // Serve static files in production
  if (process.env.NODE_ENV === "production") {
    const publicDir = path.join(__dirname, "../../public");
    app.use(express.static(publicDir));
    app.get("*", (_req, res) => {
      res.sendFile(path.join(publicDir, "index.html"));
    });
  }
}

app.listen(PORT, "0.0.0.0", () => {
  if (!process.env.DATABASE_URL) {
    console.log(`Server running on port ${PORT} — DATABASE_URL not set, showing setup page`);
  } else {
    console.log(`Server running on port ${PORT}`);
  }
});
