import { useMemo, useState } from "react";
import { useCasingHole, usePpfg, useDirectional } from "@/hooks/use-wells";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { formatNumber } from "@/lib/utils";
import type { Well, CasingHoleSection, PpfgRow, DirectionalRow } from "@shared/schema";

/** Interpolate TVD from MD using the survey */
function mdToTvd(md: number, survey: { md: number; tvd: number }[]): number {
  if (survey.length === 0) return md;
  if (md <= survey[0].md) return survey[0].tvd;
  if (md >= survey[survey.length - 1].md) return survey[survey.length - 1].tvd;
  for (let i = 1; i < survey.length; i++) {
    if (md <= survey[i].md) {
      const frac = (md - survey[i - 1].md) / (survey[i].md - survey[i - 1].md);
      return survey[i - 1].tvd + frac * (survey[i].tvd - survey[i - 1].tvd);
    }
  }
  return md;
}

/** Interpolate PPFG value at a given TVD */
function interpPpfg(
  tvd: number,
  ppfg: PpfgRow[],
  field: "ppShale" | "minFracExt" | "obg"
): number | null {
  const pts = ppfg
    .filter((p) => p.tvdRkb != null && p[field] != null)
    .sort((a, b) => a.tvdRkb - b.tvdRkb);
  if (pts.length === 0) return null;
  if (tvd <= pts[0].tvdRkb) return pts[0][field];
  if (tvd >= pts[pts.length - 1].tvdRkb) return pts[pts.length - 1][field];
  for (let i = 1; i < pts.length; i++) {
    if (tvd <= pts[i].tvdRkb) {
      const frac = (tvd - pts[i - 1].tvdRkb) / (pts[i].tvdRkb - pts[i - 1].tvdRkb);
      return pts[i - 1][field]! + frac * (pts[i][field]! - pts[i - 1][field]!);
    }
  }
  return null;
}

interface Tubular {
  od: number | null;
  weight: number | null;
  grade: string;
  burst: number | null;
  collapse: number | null;
  tension: number | null;
}

function parseTubulars(str: string | null): Tubular[] {
  const def: Tubular = { od: null, weight: null, grade: "", burst: null, collapse: null, tension: null };
  if (!str) return [def];
  try {
    const arr = JSON.parse(str);
    return Array.isArray(arr) && arr.length > 0 ? arr.map((t: any) => ({ ...def, ...t })) : [def];
  } catch {
    return [def];
  }
}

interface DesignResult {
  sectionName: string;
  sectionType: string;
  shoeMd: number | null;
  shoeTvd: number | null;
  mw: number | null;
  shoePp: number | null;
  shoeFg: number | null;
  shoeObg: number | null;
  mawpBsee: number | null;
  casingTestPressure: number | null;
  burstLoad: number | null;
  collapseLoad: number | null;
  tensionLoad: number | null;
  sfBurst: number | null;
  sfCollapse: number | null;
  sfTension: number | null;
  tubular: Tubular;
}

function computeDesign(
  section: CasingHoleSection,
  allSections: CasingHoleSection[],
  ppfg: PpfgRow[],
  survey: { md: number; tvd: number }[],
  waterDepth: number | null,
  swDensity: number | null
): DesignResult {
  const tub = parseTubulars(section.tubulars)[0];
  const shoeMd = section.baseMd;
  const shoeTvd = shoeMd != null ? mdToTvd(shoeMd, survey) : null;
  const mw = section.drillingFluidDensity;
  const shoePp = shoeTvd != null ? interpPpfg(shoeTvd, ppfg, "ppShale") : null;
  const shoeFg = shoeTvd != null ? interpPpfg(shoeTvd, ppfg, "minFracExt") : null;
  const shoeObg = shoeTvd != null ? interpPpfg(shoeTvd, ppfg, "obg") : null;
  const sw = swDensity ?? 8.6;
  const wd = waterDepth ?? 0;
  const aml = wd; // air gap / mudline at water depth

  // MAWP (BSEE-style): (FG - MW) * 0.052 * ShoeTVD
  const mawpBsee =
    shoeFg != null && mw != null && shoeTvd != null
      ? (shoeFg - mw) * 0.052 * shoeTvd
      : null;

  // Casing test pressure
  const isLiner = section.sectionType.toLowerCase().includes("liner");
  const isConductor =
    section.sectionType.toLowerCase().includes("conductor") ||
    section.sectionType.toLowerCase().includes("surface");

  let casingTestPressure: number | null = null;
  if (isConductor) {
    // No test for conductor/surface
  } else if (isLiner) {
    if (shoeFg != null && mw != null && shoeTvd != null) {
      casingTestPressure = 0.052 * shoeFg * shoeTvd - 0.052 * mw * shoeTvd;
    }
  } else {
    // Test to MAWP or 70% burst, whichever is less
    const tests: number[] = [];
    if (mawpBsee != null) tests.push(mawpBsee);
    if (tub.burst != null && mw != null && shoeTvd != null) {
      tests.push(0.7 * tub.burst - (mw - sw) * 0.052 * shoeTvd);
    }
    if (tests.length > 0) {
      casingTestPressure = Math.min(...tests.filter((v) => v > 0));
    }
  }

  // Gas gradient (0.1 psi/ft)
  const gasGrad = 0.1;

  // Burst load: gas kick at shoe
  let burstLoad: number | null = null;
  if (shoeFg != null && shoeTvd != null && mw != null) {
    const kickPressure = shoeFg * 0.052 * shoeTvd - gasGrad * (shoeTvd - aml);
    const hydrostatic = mw * 0.052 * shoeTvd;
    burstLoad = kickPressure - hydrostatic;
    if (burstLoad < 0) burstLoad = null;
  }

  // Collapse load: evacuation
  let collapseLoad: number | null = null;
  if (mw != null && shoeTvd != null) {
    const external = mw * 0.052 * shoeTvd;
    const internal = 0; // fully evacuated
    collapseLoad = external - internal;
  }

  // Tension load
  let tensionLoad: number | null = null;
  if (tub.weight != null && shoeMd != null && section.topMd != null && mw != null) {
    const length = shoeMd - section.topMd;
    const bf = (65.5 - (mw ?? 0)) / 65.5;
    tensionLoad = tub.weight * length * bf + 250000; // overpull
  }

  // Safety factors
  const sfBurst =
    tub.burst != null && burstLoad != null && burstLoad > 0
      ? tub.burst / burstLoad
      : null;
  const sfCollapse =
    tub.collapse != null && collapseLoad != null && collapseLoad > 0
      ? tub.collapse / collapseLoad
      : null;
  const sfTension =
    tub.tension != null && tensionLoad != null && tensionLoad > 0
      ? (tub.tension * 1000) / tensionLoad
      : null;

  return {
    sectionName: section.sectionName,
    sectionType: section.sectionType,
    shoeMd,
    shoeTvd,
    mw,
    shoePp,
    shoeFg,
    shoeObg,
    mawpBsee,
    casingTestPressure,
    burstLoad,
    collapseLoad,
    tensionLoad,
    sfBurst,
    sfCollapse,
    sfTension,
    tubular: tub,
  };
}

export default function CasingDesignTab({ wellId, well }: { wellId: number; well: Well }) {
  const { data: sections } = useCasingHole(wellId);
  const { data: ppfg } = usePpfg(wellId);
  const { data: directional } = useDirectional(wellId);
  const [selectedIdx, setSelectedIdx] = useState(0);

  const survey = useMemo(
    () =>
      (directional || [])
        .filter((d) => d.md != null && d.tvd != null)
        .map((d) => ({ md: d.md, tvd: d.tvd }))
        .sort((a, b) => a.md - b.md),
    [directional]
  );

  const sorted = useMemo(
    () =>
      [...(sections || [])].sort((a, b) => (a.sortOrder ?? 0) - (b.sortOrder ?? 0)),
    [sections]
  );

  const designs = useMemo(
    () =>
      sorted.map((s) =>
        computeDesign(s, sorted, ppfg || [], survey, well.waterDepth, well.seawaterDensity)
      ),
    [sorted, ppfg, survey, well.waterDepth, well.seawaterDensity]
  );

  if (!sections || sections.length === 0) {
    return (
      <Card>
        <CardContent className="py-8 text-center text-muted-foreground">
          Add casing sections in the Casing & Hole tab first to see design calculations.
        </CardContent>
      </Card>
    );
  }

  const d = designs[selectedIdx];

  return (
    <div className="space-y-4">
      {/* Section tabs */}
      <div className="flex gap-2 flex-wrap">
        {designs.map((design, i) => (
          <button
            key={i}
            onClick={() => setSelectedIdx(i)}
            className={`px-3 py-1.5 text-sm rounded-md border transition-colors ${
              i === selectedIdx
                ? "bg-primary text-primary-foreground border-primary"
                : "bg-background hover:bg-muted border-border"
            }`}
          >
            {design.sectionName}
          </button>
        ))}
      </div>

      {d && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {/* Tubular Info */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-base">Tubular & Hole</CardTitle>
            </CardHeader>
            <CardContent>
              <table className="w-full text-sm">
                <tbody>
                  <Row label="Section" value={d.sectionType} />
                  <Row label="OD" value={d.tubular.od != null ? `${d.tubular.od} in` : "-"} />
                  <Row label="Weight" value={d.tubular.weight != null ? `${d.tubular.weight} ppf` : "-"} />
                  <Row label="Grade" value={d.tubular.grade || "-"} />
                  <Row label="Shoe MD" value={d.shoeMd != null ? `${formatNumber(d.shoeMd, 0)} ft` : "-"} />
                  <Row label="Shoe TVD" value={d.shoeTvd != null ? `${formatNumber(d.shoeTvd, 0)} ft` : "-"} />
                  <Row label="MW" value={d.mw != null ? `${formatNumber(d.mw, 1)} ppg` : "-"} />
                </tbody>
              </table>
            </CardContent>
          </Card>

          {/* PPFG at Shoe */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-base">PPFG at Shoe</CardTitle>
            </CardHeader>
            <CardContent>
              <table className="w-full text-sm">
                <tbody>
                  <Row label="Pore Pressure" value={d.shoePp != null ? `${formatNumber(d.shoePp, 2)} ppg` : "-"} />
                  <Row label="Frac Gradient" value={d.shoeFg != null ? `${formatNumber(d.shoeFg, 2)} ppg` : "-"} />
                  <Row label="Overburden" value={d.shoeObg != null ? `${formatNumber(d.shoeObg, 2)} ppg` : "-"} />
                </tbody>
              </table>
            </CardContent>
          </Card>

          {/* Test Pressures */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-base">Test Pressures</CardTitle>
            </CardHeader>
            <CardContent>
              <table className="w-full text-sm">
                <tbody>
                  <Row label="MAWP (BSEE)" value={d.mawpBsee != null ? `${formatNumber(d.mawpBsee, 0)} psi` : "-"} />
                  <Row
                    label="Casing Test Pressure"
                    value={d.casingTestPressure != null ? `${formatNumber(d.casingTestPressure, 0)} psi` : "-"}
                  />
                </tbody>
              </table>
            </CardContent>
          </Card>

          {/* Design Loads & Safety Factors */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-base">Design Loads & Safety Factors</CardTitle>
            </CardHeader>
            <CardContent>
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-muted-foreground border-b">
                    <th className="text-left pb-1"></th>
                    <th className="text-right pb-1">Load</th>
                    <th className="text-right pb-1">Rating</th>
                    <th className="text-right pb-1">SF</th>
                  </tr>
                </thead>
                <tbody>
                  <tr className="border-b">
                    <td className="py-1">Burst</td>
                    <td className="text-right">{d.burstLoad != null ? `${formatNumber(d.burstLoad, 0)} psi` : "-"}</td>
                    <td className="text-right">{d.tubular.burst != null ? `${d.tubular.burst} psi` : "-"}</td>
                    <td className={`text-right font-medium ${sfColor(d.sfBurst)}`}>
                      {d.sfBurst != null ? formatNumber(d.sfBurst, 2) : "-"}
                    </td>
                  </tr>
                  <tr className="border-b">
                    <td className="py-1">Collapse</td>
                    <td className="text-right">{d.collapseLoad != null ? `${formatNumber(d.collapseLoad, 0)} psi` : "-"}</td>
                    <td className="text-right">{d.tubular.collapse != null ? `${d.tubular.collapse} psi` : "-"}</td>
                    <td className={`text-right font-medium ${sfColor(d.sfCollapse)}`}>
                      {d.sfCollapse != null ? formatNumber(d.sfCollapse, 2) : "-"}
                    </td>
                  </tr>
                  <tr>
                    <td className="py-1">Tension</td>
                    <td className="text-right">{d.tensionLoad != null ? `${formatNumber(d.tensionLoad / 1000, 0)} klb` : "-"}</td>
                    <td className="text-right">{d.tubular.tension != null ? `${d.tubular.tension} klb` : "-"}</td>
                    <td className={`text-right font-medium ${sfColor(d.sfTension)}`}>
                      {d.sfTension != null ? formatNumber(d.sfTension, 2) : "-"}
                    </td>
                  </tr>
                </tbody>
              </table>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <tr className="border-b last:border-0">
      <td className="py-1 text-muted-foreground">{label}</td>
      <td className="py-1 text-right font-medium">{value}</td>
    </tr>
  );
}

function sfColor(sf: number | null): string {
  if (sf == null) return "";
  if (sf >= 1.25) return "text-green-600";
  if (sf >= 1.0) return "text-yellow-600";
  return "text-red-600";
}
