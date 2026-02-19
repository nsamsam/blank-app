import {
  pgTable,
  serial,
  text,
  integer,
  real,
  boolean,
  timestamp,
} from "drizzle-orm/pg-core";

export const users = pgTable("users", {
  id: serial("id").primaryKey(),
  username: text("username").notNull().unique(),
  passwordHash: text("password_hash").notNull(),
  createdAt: timestamp("created_at").defaultNow(),
});

export const wells = pgTable("wells", {
  id: serial("id").primaryKey(),
  userId: integer("user_id")
    .notNull()
    .references(() => users.id),
  name: text("name").notNull(),
  operator: text("operator"),
  field: text("field"),
  area: text("area"),
  block: text("block"),
  slot: text("slot"),
  latitude: real("latitude"),
  longitude: real("longitude"),
  waterDepth: real("water_depth"),
  seawaterDensity: real("seawater_density"),
  status: text("status"),
  createdAt: timestamp("created_at").defaultNow(),
  updatedAt: timestamp("updated_at").defaultNow(),
});

export const casingHoleData = pgTable("casing_hole_data", {
  id: serial("id").primaryKey(),
  wellId: integer("well_id")
    .notNull()
    .references(() => wells.id, { onDelete: "cascade" }),
  sectionName: text("section_name").notNull(),
  sectionType: text("section_type").notNull(),
  tubularType: text("tubular_type"),
  tubulars: text("tubulars"),
  casingSize: real("casing_size"),
  casingSizeUnit: text("casing_size_unit"),
  holeSize: real("hole_size"),
  holeSizeUnit: text("hole_size_unit"),
  topMd: real("top_md"),
  baseMd: real("base_md"),
  sectionTdMd: real("section_td_md"),
  topOfCementMd: real("top_of_cement_md"),
  lengthOfCementMd: real("length_of_cement_md"),
  cementType: text("cement_type"),
  leadCementSlurryDensity: real("lead_cement_slurry_density"),
  tailCementSlurryDensity: real("tail_cement_slurry_density"),
  tailCementLength: real("tail_cement_length"),
  drillingFluid: text("drilling_fluid"),
  drillingFluidDensity: real("drilling_fluid_density"),
  displacementFluidDensity: real("displacement_fluid_density"),
  casingRunningFluid: text("casing_running_fluid"),
  drillingEcd: real("drilling_ecd"),
  sortOrder: integer("sort_order").default(0),
});

export const ppfgData = pgTable("ppfg_data", {
  id: serial("id").primaryKey(),
  wellId: integer("well_id")
    .notNull()
    .references(() => wells.id, { onDelete: "cascade" }),
  tvdRkb: real("tvd_rkb").notNull(),
  ppShale: real("pp_shale"),
  mwBreakout: real("mw_breakout"),
  minHStress: real("min_h_stress"),
  minFracExt: real("min_frac_ext"),
  fracInit: real("frac_init"),
  obg: real("obg"),
});

export const directionalData = pgTable("directional_data", {
  id: serial("id").primaryKey(),
  wellId: integer("well_id")
    .notNull()
    .references(() => wells.id, { onDelete: "cascade" }),
  md: real("md").notNull(),
  inc: real("inc").notNull(),
  azm: real("azm").notNull(),
  tvd: real("tvd").notNull(),
  tvdss: real("tvdss"),
  vsec: real("vsec"),
  ns: real("ns"),
  ew: real("ew"),
  northing: real("northing"),
  easting: real("easting"),
  latitude: real("latitude"),
  longitude: real("longitude"),
  dls: real("dls"),
  br: real("br"),
  tr: real("tr"),
});

export type User = typeof users.$inferSelect;
export type InsertUser = typeof users.$inferInsert;
export type Well = typeof wells.$inferSelect;
export type InsertWell = typeof wells.$inferInsert;
export type CasingHoleSection = typeof casingHoleData.$inferSelect;
export type InsertCasingHoleSection = typeof casingHoleData.$inferInsert;
export type PpfgRow = typeof ppfgData.$inferSelect;
export type InsertPpfgRow = typeof ppfgData.$inferInsert;
export type DirectionalRow = typeof directionalData.$inferSelect;
export type InsertDirectionalRow = typeof directionalData.$inferInsert;
