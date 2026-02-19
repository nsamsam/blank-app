import express from "express";
import path from "path";
import { fileURLToPath } from "url";
import { setupAuth } from "./auth.js";
import { setupRoutes } from "./routes.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const app = express();
const PORT = Number(process.env.PORT) || 3000;

// Trust Railway's reverse proxy (needed for secure cookies)
if (process.env.NODE_ENV === "production") {
  app.set("trust proxy", 1);
}

app.use(express.json({ limit: "10mb" }));
app.use(express.urlencoded({ extended: true }));

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

app.listen(PORT, "0.0.0.0", () => {
  console.log(`Server running on port ${PORT}`);
});
