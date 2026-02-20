import passport from "passport";
import { Strategy as LocalStrategy } from "passport-local";
import bcrypt from "bcryptjs";
import { db } from "./db.js";
import { users } from "../shared/schema.js";
import { eq } from "drizzle-orm";
import type { Express, Request } from "express";
import session from "express-session";
import connectPgSimple from "connect-pg-simple";
import { Pool } from "pg";

declare global {
  namespace Express {
    interface User {
      id: number;
      username: string;
    }
  }
}

export function setupAuth(app: Express) {
  const PgSession = connectPgSimple(session);
  const dbUrl = process.env.DATABASE_URL || "";
  const useSSL = dbUrl.includes("rlwy.net") ? { rejectUnauthorized: false } : false;

  const pool = new Pool({
    connectionString: process.env.DATABASE_URL,
    ssl: useSSL,
    connectionTimeoutMillis: 10000,
    idleTimeoutMillis: 30000,
  });

  app.use(
    session({
      store: new PgSession({ pool, createTableIfMissing: true }),
      secret: process.env.SESSION_SECRET || "engineering-workbook-secret",
      resave: false,
      saveUninitialized: false,
      cookie: {
        maxAge: 30 * 24 * 60 * 60 * 1000, // 30 days
        httpOnly: true,
        secure: process.env.NODE_ENV === "production",
      },
    })
  );

  app.use(passport.initialize());
  app.use(passport.session());

  passport.use(
    new LocalStrategy(async (username, password, done) => {
      try {
        const [user] = await db
          .select()
          .from(users)
          .where(eq(users.username, username));
        if (!user) return done(null, false, { message: "Invalid credentials" });

        const isValid = await bcrypt.compare(password, user.passwordHash);
        if (!isValid)
          return done(null, false, { message: "Invalid credentials" });

        return done(null, { id: user.id, username: user.username });
      } catch (err) {
        return done(err);
      }
    })
  );

  passport.serializeUser((user, done) => done(null, user.id));

  passport.deserializeUser(async (id: number, done) => {
    try {
      const [user] = await db
        .select()
        .from(users)
        .where(eq(users.id, id));
      if (!user) return done(null, false);
      done(null, { id: user.id, username: user.username });
    } catch (err) {
      done(err);
    }
  });

  // Auth routes
  app.post("/api/auth/login", (req, res, next) => {
    passport.authenticate(
      "local",
      (err: any, user: Express.User | false, info: any) => {
        if (err) return next(err);
        if (!user) return res.status(401).json({ message: info?.message || "Invalid credentials" });
        req.logIn(user, (err) => {
          if (err) return next(err);
          res.json({ id: user.id, username: user.username });
        });
      }
    )(req, res, next);
  });

  app.post("/api/auth/logout", (req, res) => {
    req.logout(() => {
      res.json({ message: "Logged out" });
    });
  });

  app.get("/api/auth/me", (req, res) => {
    if (!req.isAuthenticated()) return res.status(401).json({ message: "Not authenticated" });
    res.json({ id: req.user!.id, username: req.user!.username });
  });

  // Register route (for initial setup)
  app.post("/api/auth/register", async (req, res) => {
    try {
      const { username, password } = req.body;
      if (!username || !password) {
        return res.status(400).json({ message: "Username and password required" });
      }

      const existing = await db
        .select()
        .from(users)
        .where(eq(users.username, username));
      if (existing.length > 0) {
        return res.status(409).json({ message: "Username already taken" });
      }

      const passwordHash = await bcrypt.hash(password, 10);
      const [user] = await db
        .insert(users)
        .values({ username, passwordHash })
        .returning();

      req.logIn({ id: user.id, username: user.username }, (err) => {
        if (err) return res.status(500).json({ message: "Login failed after registration" });
        res.status(201).json({ id: user.id, username: user.username });
      });
    } catch (err) {
      res.status(500).json({ message: "Registration failed" });
    }
  });
}

export function requireAuth(req: Request, res: any, next: any) {
  if (!req.isAuthenticated()) {
    return res.status(401).json({ message: "Authentication required" });
  }
  next();
}
