import { useState, useMemo } from "react";
import { usePpfg, useBulkPpfg } from "@/hooks/use-wells";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Plus, Trash2, Upload, Save } from "lucide-react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

interface PpfgEntry {
  tvdRkb: number | null;
  ppShale: number | null;
  mwBreakout: number | null;
  minHStress: number | null;
  minFracExt: number | null;
  fracInit: number | null;
  obg: number | null;
}

const emptyRow: PpfgEntry = {
  tvdRkb: null,
  ppShale: null,
  mwBreakout: null,
  minHStress: null,
  minFracExt: null,
  fracInit: null,
  obg: null,
};

const columns: { key: keyof PpfgEntry; label: string; color: string }[] = [
  { key: "tvdRkb", label: "TVD RKB (ft)", color: "" },
  { key: "ppShale", label: "PP Shale (ppg)", color: "#ef4444" },
  { key: "mwBreakout", label: "MW Breakout (ppg)", color: "#f97316" },
  { key: "minHStress", label: "Min H Stress (ppg)", color: "#eab308" },
  { key: "minFracExt", label: "Min Frac Ext (ppg)", color: "#22c55e" },
  { key: "fracInit", label: "Frac Init (ppg)", color: "#3b82f6" },
  { key: "obg", label: "OBG (ppg)", color: "#8b5cf6" },
];

export default function PpfgTab({ wellId }: { wellId: number }) {
  const { data: ppfgData, isLoading } = usePpfg(wellId);
  const bulkSave = useBulkPpfg(wellId);
  const [editing, setEditing] = useState(false);
  const [rows, setRows] = useState<PpfgEntry[]>([]);

  const startEdit = () => {
    setRows(
      ppfgData && ppfgData.length > 0
        ? ppfgData.map((p) => ({
            tvdRkb: p.tvdRkb,
            ppShale: p.ppShale,
            mwBreakout: p.mwBreakout,
            minHStress: p.minHStress,
            minFracExt: p.minFracExt,
            fracInit: p.fracInit,
            obg: p.obg,
          }))
        : [{ ...emptyRow }]
    );
    setEditing(true);
  };

  const handleSave = async () => {
    const valid = rows
      .filter((r): r is PpfgEntry & { tvdRkb: number } => r.tvdRkb != null)
      .map(({ tvdRkb, ppShale, mwBreakout, minHStress, minFracExt, fracInit, obg }) => ({
        tvdRkb,
        ppShale: ppShale ?? undefined,
        mwBreakout: mwBreakout ?? undefined,
        minHStress: minHStress ?? undefined,
        minFracExt: minFracExt ?? undefined,
        fracInit: fracInit ?? undefined,
        obg: obg ?? undefined,
      }));
    await bulkSave.mutateAsync(valid);
    setEditing(false);
  };

  const handlePaste = (e: React.ClipboardEvent) => {
    const text = e.clipboardData.getData("text");
    const lines = text
      .split("\n")
      .map((l) => l.trim())
      .filter(Boolean);
    if (lines.length < 2) return;

    e.preventDefault();
    const parsed: PpfgEntry[] = lines.map((line) => {
      const vals = line.split(/\t|,/).map((v) => {
        const n = parseFloat(v.trim());
        return isNaN(n) ? null : n;
      });
      return {
        tvdRkb: vals[0] ?? null,
        ppShale: vals[1] ?? null,
        mwBreakout: vals[2] ?? null,
        minHStress: vals[3] ?? null,
        minFracExt: vals[4] ?? null,
        fracInit: vals[5] ?? null,
        obg: vals[6] ?? null,
      };
    });
    setRows(parsed);
  };

  const updateRow = (idx: number, key: keyof PpfgEntry, value: string) => {
    const next = [...rows];
    next[idx] = { ...next[idx], [key]: value ? Number(value) : null };
    setRows(next);
  };

  const chartData = useMemo(() => {
    const source = editing ? rows : ppfgData || [];
    return source
      .filter((r) => r.tvdRkb != null)
      .sort((a, b) => (a.tvdRkb ?? 0) - (b.tvdRkb ?? 0));
  }, [editing, rows, ppfgData]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-32">
        <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary" />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">PPFG Data</h3>
        <div className="flex gap-2">
          {editing ? (
            <>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setEditing(false)}
              >
                Cancel
              </Button>
              <Button size="sm" onClick={handleSave} disabled={bulkSave.isPending}>
                <Save className="h-4 w-4 mr-1" /> Save
              </Button>
            </>
          ) : (
            <Button size="sm" onClick={startEdit}>
              {ppfgData && ppfgData.length > 0 ? "Edit Data" : "Add Data"}
            </Button>
          )}
        </div>
      </div>

      {/* Chart */}
      {chartData.length > 0 && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">PPFG Plot</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={500}>
              <LineChart
                data={chartData}
                layout="vertical"
                margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  type="number"
                  domain={["auto", "auto"]}
                  label={{ value: "EMW (ppg)", position: "insideBottom", offset: -5 }}
                />
                <YAxis
                  type="number"
                  dataKey="tvdRkb"
                  reversed
                  domain={["auto", "auto"]}
                  label={{ value: "TVD RKB (ft)", angle: -90, position: "insideLeft" }}
                />
                <Tooltip />
                <Legend />
                {columns.slice(1).map((col) => (
                  <Line
                    key={col.key}
                    type="monotone"
                    dataKey={col.key}
                    stroke={col.color}
                    name={col.label.replace(" (ppg)", "")}
                    dot={false}
                    connectNulls
                  />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      )}

      {/* Data Table */}
      {editing ? (
        <Card>
          <CardContent className="pt-4" onPaste={handlePaste}>
            <p className="text-xs text-muted-foreground mb-2">
              Tip: Paste tab/comma-separated data from a spreadsheet.
            </p>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-muted-foreground">
                    {columns.map((c) => (
                      <th key={c.key} className="text-left pb-1 pr-2 text-xs">
                        {c.label}
                      </th>
                    ))}
                    <th className="w-8"></th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((row, i) => (
                    <tr key={i} className="border-b last:border-0">
                      {columns.map((c) => (
                        <td key={c.key} className="py-1 pr-2">
                          <Input
                            type="number"
                            step="any"
                            className="h-8 text-xs"
                            value={row[c.key] ?? ""}
                            onChange={(e) => updateRow(i, c.key, e.target.value)}
                          />
                        </td>
                      ))}
                      <td className="py-1">
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8"
                          onClick={() => setRows(rows.filter((_, j) => j !== i))}
                        >
                          <Trash2 className="h-3 w-3" />
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <Button
              variant="outline"
              size="sm"
              className="mt-2"
              onClick={() => setRows([...rows, { ...emptyRow }])}
            >
              <Plus className="h-3 w-3 mr-1" /> Add Row
            </Button>
          </CardContent>
        </Card>
      ) : ppfgData && ppfgData.length > 0 ? (
        <Card>
          <CardContent className="pt-4">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-muted-foreground">
                    {columns.map((c) => (
                      <th key={c.key} className="text-left pb-1 pr-2 text-xs">
                        {c.label}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {ppfgData.map((row, i) => (
                    <tr key={i} className="border-b last:border-0">
                      {columns.map((c) => (
                        <td key={c.key} className="py-1 pr-2">
                          {row[c.key] != null ? Number(row[c.key]).toFixed(c.key === "tvdRkb" ? 0 : 2) : "-"}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardContent className="py-8 text-center text-muted-foreground">
            No PPFG data yet. Click "Add Data" to enter pore pressure and fracture gradient values.
          </CardContent>
        </Card>
      )}
    </div>
  );
}
