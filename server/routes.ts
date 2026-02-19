import { Express } from "express";
import { db } from "./db.js";
import { requireAuth } from "./auth.js";
import {
  wells,
  casingHoleData,
  ppfgData,
  directionalData,
} from "../shared/schema.js";
import { eq, and, asc } from "drizzle-orm";

export function setupRoutes(app: Express) {
  // ── Wells ──────────────────────────────────────────────────

  app.get("/api/wells", requireAuth, async (req, res) => {
    const data = await db
      .select()
      .from(wells)
      .where(eq(wells.userId, req.user!.id))
      .orderBy(asc(wells.name));
    res.json(data);
  });

  app.post("/api/wells", requireAuth, async (req, res) => {
    const [well] = await db
      .insert(wells)
      .values({ ...req.body, userId: req.user!.id })
      .returning();
    res.status(201).json(well);
  });

  app.get("/api/wells/:id", requireAuth, async (req, res) => {
    const [well] = await db
      .select()
      .from(wells)
      .where(
        and(eq(wells.id, Number(req.params.id)), eq(wells.userId, req.user!.id))
      );
    if (!well) return res.status(404).json({ message: "Well not found" });
    res.json(well);
  });

  app.put("/api/wells/:id", requireAuth, async (req, res) => {
    const { userId, id, createdAt, ...updates } = req.body;
    const [well] = await db
      .update(wells)
      .set({ ...updates, updatedAt: new Date() })
      .where(
        and(eq(wells.id, Number(req.params.id)), eq(wells.userId, req.user!.id))
      )
      .returning();
    if (!well) return res.status(404).json({ message: "Well not found" });
    res.json(well);
  });

  app.delete("/api/wells/:id", requireAuth, async (req, res) => {
    const [well] = await db
      .delete(wells)
      .where(
        and(eq(wells.id, Number(req.params.id)), eq(wells.userId, req.user!.id))
      )
      .returning();
    if (!well) return res.status(404).json({ message: "Well not found" });
    res.json({ message: "Well deleted" });
  });

  // ── Casing & Hole ─────────────────────────────────────────

  app.get("/api/wells/:wellId/casing-hole", requireAuth, async (req, res) => {
    const wellId = Number(req.params.wellId);
    const data = await db
      .select()
      .from(casingHoleData)
      .where(eq(casingHoleData.wellId, wellId))
      .orderBy(asc(casingHoleData.sortOrder));
    res.json(data);
  });

  app.post("/api/wells/:wellId/casing-hole", requireAuth, async (req, res) => {
    const wellId = Number(req.params.wellId);
    const [section] = await db
      .insert(casingHoleData)
      .values({ ...req.body, wellId })
      .returning();
    res.status(201).json(section);
  });

  app.patch(
    "/api/wells/:wellId/casing-hole/:id",
    requireAuth,
    async (req, res) => {
      const { wellId: _w, id: _i, ...updates } = req.body;
      const [section] = await db
        .update(casingHoleData)
        .set(updates)
        .where(eq(casingHoleData.id, Number(req.params.id)))
        .returning();
      if (!section) return res.status(404).json({ message: "Section not found" });
      res.json(section);
    }
  );

  app.delete(
    "/api/wells/:wellId/casing-hole/:id",
    requireAuth,
    async (req, res) => {
      const [section] = await db
        .delete(casingHoleData)
        .where(eq(casingHoleData.id, Number(req.params.id)))
        .returning();
      if (!section) return res.status(404).json({ message: "Section not found" });
      res.json({ message: "Section deleted" });
    }
  );

  // ── PPFG ──────────────────────────────────────────────────

  app.get("/api/wells/:wellId/ppfg", requireAuth, async (req, res) => {
    const wellId = Number(req.params.wellId);
    const data = await db
      .select()
      .from(ppfgData)
      .where(eq(ppfgData.wellId, wellId))
      .orderBy(asc(ppfgData.tvdRkb));
    res.json(data);
  });

  app.post("/api/wells/:wellId/ppfg/bulk", requireAuth, async (req, res) => {
    const wellId = Number(req.params.wellId);
    const { data } = req.body;

    // Delete existing data
    await db.delete(ppfgData).where(eq(ppfgData.wellId, wellId));

    if (data && data.length > 0) {
      const rows = data.map((row: any) => ({ ...row, wellId }));
      await db.insert(ppfgData).values(rows);
    }

    const result = await db
      .select()
      .from(ppfgData)
      .where(eq(ppfgData.wellId, wellId))
      .orderBy(asc(ppfgData.tvdRkb));
    res.json(result);
  });

  // ── Directional Survey ────────────────────────────────────

  app.get("/api/wells/:wellId/directional", requireAuth, async (req, res) => {
    const wellId = Number(req.params.wellId);
    const data = await db
      .select()
      .from(directionalData)
      .where(eq(directionalData.wellId, wellId))
      .orderBy(asc(directionalData.md));
    res.json(data);
  });

  app.post(
    "/api/wells/:wellId/directional/bulk",
    requireAuth,
    async (req, res) => {
      const wellId = Number(req.params.wellId);
      const { data } = req.body;

      // Delete existing data
      await db
        .delete(directionalData)
        .where(eq(directionalData.wellId, wellId));

      if (data && data.length > 0) {
        const rows = data.map((row: any) => ({ ...row, wellId }));
        await db.insert(directionalData).values(rows);
      }

      const result = await db
        .select()
        .from(directionalData)
        .where(eq(directionalData.wellId, wellId))
        .orderBy(asc(directionalData.md));
      res.json(result);
    }
  );
}
