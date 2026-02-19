import { useState, useMemo } from "react";
import { useDirectional, useBulkDirectional } from "@/hooks/use-wells";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Plus, Trash2, Save } from "lucide-react";
import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  LineChart,
  Line,
} from "recharts";

interface SurveyEntry {
  md: number | null;
  inc: number | null;
  azm: number | null;
  tvd: number | null;
  tvdss: number | null;
  vsec: number | null;
  ns: number | null;
  ew: number | null;
  dls: number | null;
}

const emptyRow: SurveyEntry = {
  md: null,
  inc: null,
  azm: null,
  tvd: null,
  tvdss: null,
  vsec: null,
  ns: null,
  ew: null,
  dls: null,
};

const mainCols: { key: keyof SurveyEntry; label: string }[] = [
  { key: "md", label: "MD (ft)" },
  { key: "inc", label: "Inc (\u00b0)" },
  { key: "azm", label: "Azm (\u00b0)" },
  { key: "tvd", label: "TVD (ft)" },
  { key: "tvdss", label: "TVDSS (ft)" },
  { key: "vsec", label: "VS (ft)" },
  { key: "ns", label: "N/S (ft)" },
  { key: "ew", label: "E/W (ft)" },
  { key: "dls", label: "DLS (\u00b0/100ft)" },
];

export default function DirectionalTab({ wellId }: { wellId: number }) {
  const { data: directional, isLoading } = useDirectional(wellId);
  const bulkSave = useBulkDirectional(wellId);
  const [editing, setEditing] = useState(false);
  const [rows, setRows] = useState<SurveyEntry[]>([]);

  const startEdit = () => {
    setRows(
      directional && directional.length > 0
        ? directional.map((d) => ({
            md: d.md,
            inc: d.inc,
            azm: d.azm,
            tvd: d.tvd,
            tvdss: d.tvdss,
            vsec: d.vsec,
            ns: d.ns,
            ew: d.ew,
            dls: d.dls,
          }))
        : [{ ...emptyRow }]
    );
    setEditing(true);
  };

  const handleSave = async () => {
    const valid = rows.filter((r) => r.md != null && r.tvd != null);
    await bulkSave.mutateAsync(
      valid.map((r) => ({
        ...r,
        md: r.md!,
        inc: r.inc ?? 0,
        azm: r.azm ?? 0,
        tvd: r.tvd!,
      }))
    );
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
    const parsed: SurveyEntry[] = lines.map((line) => {
      const vals = line.split(/\t|,/).map((v) => {
        const n = parseFloat(v.trim());
        return isNaN(n) ? null : n;
      });
      return {
        md: vals[0] ?? null,
        inc: vals[1] ?? null,
        azm: vals[2] ?? null,
        tvd: vals[3] ?? null,
        tvdss: vals[4] ?? null,
        vsec: vals[5] ?? null,
        ns: vals[6] ?? null,
        ew: vals[7] ?? null,
        dls: vals[8] ?? null,
      };
    });
    setRows(parsed);
  };

  const updateRow = (idx: number, key: keyof SurveyEntry, value: string) => {
    const next = [...rows];
    next[idx] = { ...next[idx], [key]: value ? Number(value) : null };
    setRows(next);
  };

  const chartData = useMemo(() => {
    const source = editing ? rows : directional || [];
    return source
      .filter((r) => r.md != null && r.tvd != null)
      .sort((a, b) => (a.md ?? 0) - (b.md ?? 0));
  }, [editing, rows, directional]);

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
        <h3 className="text-lg font-semibold">Directional Survey</h3>
        <div className="flex gap-2">
          {editing ? (
            <>
              <Button variant="outline" size="sm" onClick={() => setEditing(false)}>
                Cancel
              </Button>
              <Button size="sm" onClick={handleSave} disabled={bulkSave.isPending}>
                <Save className="h-4 w-4 mr-1" /> Save
              </Button>
            </>
          ) : (
            <Button size="sm" onClick={startEdit}>
              {directional && directional.length > 0 ? "Edit Data" : "Add Data"}
            </Button>
          )}
        </div>
      </div>

      {/* Charts */}
      {chartData.length > 1 && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-base">TVD vs Vertical Section</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <LineChart
                  data={chartData.filter((d) => d.vsec != null)}
                  margin={{ top: 5, right: 20, left: 10, bottom: 20 }}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis
                    dataKey="vsec"
                    type="number"
                    label={{ value: "VS (ft)", position: "insideBottom", offset: -10 }}
                  />
                  <YAxis
                    dataKey="tvd"
                    reversed
                    label={{ value: "TVD (ft)", angle: -90, position: "insideLeft" }}
                  />
                  <Tooltip />
                  <Line
                    type="monotone"
                    dataKey="tvd"
                    stroke="#3b82f6"
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-base">Plan View (N/S vs E/W)</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <ScatterChart margin={{ top: 5, right: 20, left: 10, bottom: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis
                    dataKey="ew"
                    type="number"
                    name="E/W"
                    label={{ value: "E/W (ft)", position: "insideBottom", offset: -10 }}
                  />
                  <YAxis
                    dataKey="ns"
                    type="number"
                    name="N/S"
                    label={{ value: "N/S (ft)", angle: -90, position: "insideLeft" }}
                  />
                  <Tooltip />
                  <Scatter
                    data={chartData.filter((d) => d.ns != null && d.ew != null)}
                    fill="#3b82f6"
                    line={{ stroke: "#3b82f6" }}
                  />
                </ScatterChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Data Table */}
      {editing ? (
        <Card>
          <CardContent className="pt-4" onPaste={handlePaste}>
            <p className="text-xs text-muted-foreground mb-2">
              Tip: Paste tab/comma-separated survey data from a spreadsheet.
            </p>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-muted-foreground">
                    {mainCols.map((c) => (
                      <th key={c.key} className="text-left pb-1 pr-2 text-xs whitespace-nowrap">
                        {c.label}
                      </th>
                    ))}
                    <th className="w-8"></th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((row, i) => (
                    <tr key={i} className="border-b last:border-0">
                      {mainCols.map((c) => (
                        <td key={c.key} className="py-1 pr-2">
                          <Input
                            type="number"
                            step="any"
                            className="h-8 text-xs w-20"
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
      ) : directional && directional.length > 0 ? (
        <Card>
          <CardContent className="pt-4">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-muted-foreground">
                    {mainCols.map((c) => (
                      <th key={c.key} className="text-left pb-1 pr-2 text-xs whitespace-nowrap">
                        {c.label}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {directional.map((row, i) => (
                    <tr key={i} className="border-b last:border-0">
                      {mainCols.map((c) => (
                        <td key={c.key} className="py-1 pr-2">
                          {row[c.key] != null
                            ? Number(row[c.key]).toFixed(c.key === "md" || c.key === "tvd" || c.key === "tvdss" ? 0 : 2)
                            : "-"}
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
            No directional survey data yet. Click "Add Data" to enter survey points.
          </CardContent>
        </Card>
      )}
    </div>
  );
}
