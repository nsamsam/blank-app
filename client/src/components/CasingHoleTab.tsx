import { useState, useCallback } from "react";
import {
  useCasingHole,
  useCreateCasingHole,
  useUpdateCasingHole,
  useDeleteCasingHole,
} from "@/hooks/use-wells";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Plus, Pencil, Trash2, ChevronUp, ChevronDown, X, Check } from "lucide-react";
import type { CasingHoleSection } from "@shared/schema";

interface Tubular {
  od: number | null;
  weight: number | null;
  grade: string;
  burst: number | null;
  collapse: number | null;
  tension: number | null;
}

const SECTION_TYPES = [
  "Conductor",
  "Surface Casing",
  "Intermediate Casing",
  "Production Casing",
  "Production Liner",
  "Tieback",
  "Open Hole",
];

const emptyForm = {
  sectionName: "",
  sectionType: "",
  tubulars: [{ od: null, weight: null, grade: "", burst: null, collapse: null, tension: null }] as Tubular[],
  casingSize: null as number | null,
  holeSize: null as number | null,
  topMd: null as number | null,
  baseMd: null as number | null,
  sectionTdMd: null as number | null,
  topOfCementMd: null as number | null,
  cementType: "",
  leadCementSlurryDensity: null as number | null,
  tailCementSlurryDensity: null as number | null,
  tailCementLength: null as number | null,
  drillingFluid: "",
  drillingFluidDensity: null as number | null,
  displacementFluidDensity: null as number | null,
  drillingEcd: null as number | null,
};

function parseTubulars(str: string | null): Tubular[] {
  const def = { od: null, weight: null, grade: "", burst: null, collapse: null, tension: null };
  if (!str) return [def];
  try {
    const arr = JSON.parse(str);
    return Array.isArray(arr) && arr.length > 0 ? arr.map((t: any) => ({ ...def, ...t })) : [def];
  } catch {
    return [def];
  }
}

export default function CasingHoleTab({ wellId }: { wellId: number }) {
  const { data: sections, isLoading } = useCasingHole(wellId);
  const createSection = useCreateCasingHole(wellId);
  const updateSection = useUpdateCasingHole(wellId);
  const deleteSection = useDeleteCasingHole(wellId);

  const [editId, setEditId] = useState<number | null>(null);
  const [form, setForm] = useState(emptyForm);
  const [showForm, setShowForm] = useState(false);

  const startNew = () => {
    setEditId(null);
    setForm({ ...emptyForm, tubulars: [{ od: null, weight: null, grade: "", burst: null, collapse: null, tension: null }] });
    setShowForm(true);
  };

  const startEdit = (s: CasingHoleSection) => {
    setEditId(s.id);
    setForm({
      sectionName: s.sectionName,
      sectionType: s.sectionType,
      tubulars: parseTubulars(s.tubulars),
      casingSize: s.casingSize,
      holeSize: s.holeSize,
      topMd: s.topMd,
      baseMd: s.baseMd,
      sectionTdMd: s.sectionTdMd,
      topOfCementMd: s.topOfCementMd,
      cementType: s.cementType || "",
      leadCementSlurryDensity: s.leadCementSlurryDensity,
      tailCementSlurryDensity: s.tailCementSlurryDensity,
      tailCementLength: s.tailCementLength,
      drillingFluid: s.drillingFluid || "",
      drillingFluidDensity: s.drillingFluidDensity,
      displacementFluidDensity: s.displacementFluidDensity,
      drillingEcd: s.drillingEcd,
    });
    setShowForm(true);
  };

  const cancel = () => {
    setEditId(null);
    setShowForm(false);
    setForm(emptyForm);
  };

  const handleSave = async () => {
    if (!form.sectionName.trim() || !form.sectionType) return;
    const hasTubular = form.tubulars.some(
      (t) => t.od != null || t.weight != null || t.grade || t.burst != null || t.collapse != null || t.tension != null
    );
    const payload: any = {
      sectionName: form.sectionName,
      sectionType: form.sectionType,
      tubulars: hasTubular ? JSON.stringify(form.tubulars) : null,
      casingSize: form.casingSize,
      holeSize: form.holeSize,
      topMd: form.topMd,
      baseMd: form.baseMd,
      sectionTdMd: form.sectionTdMd,
      topOfCementMd: form.topOfCementMd,
      lengthOfCementMd:
        form.baseMd != null && form.topOfCementMd != null
          ? form.baseMd - form.topOfCementMd
          : null,
      cementType: form.cementType || null,
      leadCementSlurryDensity: form.leadCementSlurryDensity,
      tailCementSlurryDensity: form.tailCementSlurryDensity,
      tailCementLength: form.tailCementLength,
      drillingFluid: form.drillingFluid || null,
      drillingFluidDensity: form.drillingFluidDensity,
      displacementFluidDensity: form.displacementFluidDensity,
      drillingEcd: form.drillingEcd,
    };

    if (editId != null) {
      await updateSection.mutateAsync({ id: editId, ...payload });
    } else {
      payload.sortOrder = (sections?.length ?? 0);
      await createSection.mutateAsync(payload);
    }
    cancel();
  };

  const handleDelete = async (id: number) => {
    if (confirm("Delete this section?")) {
      await deleteSection.mutateAsync(id);
    }
  };

  const numField = (value: number | null, onChange: (v: number | null) => void) => (
    <Input
      type="number"
      step="any"
      value={value ?? ""}
      onChange={(e) => onChange(e.target.value ? Number(e.target.value) : null)}
    />
  );

  const updateTubular = (idx: number, field: keyof Tubular, value: any) => {
    const next = [...form.tubulars];
    next[idx] = { ...next[idx], [field]: value };
    setForm({ ...form, tubulars: next });
  };

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
        <h3 className="text-lg font-semibold">Casing & Hole Sections</h3>
        {!showForm && (
          <Button onClick={startNew} size="sm">
            <Plus className="h-4 w-4 mr-1" /> Add Section
          </Button>
        )}
      </div>

      {/* Existing sections */}
      {sections && sections.length > 0 && (
        <div className="space-y-2">
          {sections.map((s) => (
            <Card key={s.id} className="hover:shadow-sm transition-shadow">
              <CardContent className="py-3 px-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">{s.sectionName}</p>
                    <p className="text-sm text-muted-foreground">{s.sectionType}</p>
                  </div>
                  <div className="flex items-center gap-1 text-sm text-muted-foreground">
                    {s.topMd != null && s.baseMd != null && (
                      <span className="mr-3">
                        {s.topMd} - {s.baseMd} ft MD
                      </span>
                    )}
                    <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => startEdit(s)}>
                      <Pencil className="h-3.5 w-3.5" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8 text-destructive"
                      onClick={() => handleDelete(s.id)}
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {sections?.length === 0 && !showForm && (
        <Card>
          <CardContent className="py-8 text-center text-muted-foreground">
            Add casing and hole sections to define the well construction.
          </CardContent>
        </Card>
      )}

      {/* Add/Edit Form */}
      {showForm && (
        <Card>
          <CardHeader className="pb-4">
            <CardTitle className="text-base">
              {editId != null ? "Edit Section" : "New Section"}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-1">
                <Label>Section Name</Label>
                <Input
                  value={form.sectionName}
                  onChange={(e) => setForm({ ...form, sectionName: e.target.value })}
                  placeholder="e.g. 20in Conductor"
                />
              </div>
              <div className="space-y-1">
                <Label>Section Type</Label>
                <Select
                  value={form.sectionType}
                  onValueChange={(v) => setForm({ ...form, sectionType: v })}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select type" />
                  </SelectTrigger>
                  <SelectContent>
                    {SECTION_TYPES.map((t) => (
                      <SelectItem key={t} value={t}>
                        {t}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* Depths */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="space-y-1">
                <Label>Top MD (ft)</Label>
                {numField(form.topMd, (v) => setForm({ ...form, topMd: v }))}
              </div>
              <div className="space-y-1">
                <Label>Base MD (ft)</Label>
                {numField(form.baseMd, (v) => setForm({ ...form, baseMd: v }))}
              </div>
              <div className="space-y-1">
                <Label>Section TD MD (ft)</Label>
                {numField(form.sectionTdMd, (v) => setForm({ ...form, sectionTdMd: v }))}
              </div>
              <div className="space-y-1">
                <Label>Hole Size (in)</Label>
                {numField(form.holeSize, (v) => setForm({ ...form, holeSize: v }))}
              </div>
            </div>

            {/* Tubulars */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <Label>Tubulars</Label>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() =>
                    setForm({
                      ...form,
                      tubulars: [
                        ...form.tubulars,
                        { od: null, weight: null, grade: "", burst: null, collapse: null, tension: null },
                      ],
                    })
                  }
                >
                  <Plus className="h-3 w-3 mr-1" /> Row
                </Button>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left text-muted-foreground border-b">
                      <th className="pb-1 pr-2">OD (in)</th>
                      <th className="pb-1 pr-2">Weight (ppf)</th>
                      <th className="pb-1 pr-2">Grade</th>
                      <th className="pb-1 pr-2">Burst (psi)</th>
                      <th className="pb-1 pr-2">Collapse (psi)</th>
                      <th className="pb-1 pr-2">Tension (klb)</th>
                      <th className="pb-1 w-8"></th>
                    </tr>
                  </thead>
                  <tbody>
                    {form.tubulars.map((t, i) => (
                      <tr key={i} className="border-b last:border-0">
                        <td className="py-1 pr-2">
                          <Input
                            type="number"
                            step="any"
                            className="h-8"
                            value={t.od ?? ""}
                            onChange={(e) =>
                              updateTubular(i, "od", e.target.value ? Number(e.target.value) : null)
                            }
                          />
                        </td>
                        <td className="py-1 pr-2">
                          <Input
                            type="number"
                            step="any"
                            className="h-8"
                            value={t.weight ?? ""}
                            onChange={(e) =>
                              updateTubular(i, "weight", e.target.value ? Number(e.target.value) : null)
                            }
                          />
                        </td>
                        <td className="py-1 pr-2">
                          <Input
                            className="h-8"
                            value={t.grade}
                            onChange={(e) => updateTubular(i, "grade", e.target.value)}
                          />
                        </td>
                        <td className="py-1 pr-2">
                          <Input
                            type="number"
                            step="any"
                            className="h-8"
                            value={t.burst ?? ""}
                            onChange={(e) =>
                              updateTubular(i, "burst", e.target.value ? Number(e.target.value) : null)
                            }
                          />
                        </td>
                        <td className="py-1 pr-2">
                          <Input
                            type="number"
                            step="any"
                            className="h-8"
                            value={t.collapse ?? ""}
                            onChange={(e) =>
                              updateTubular(i, "collapse", e.target.value ? Number(e.target.value) : null)
                            }
                          />
                        </td>
                        <td className="py-1 pr-2">
                          <Input
                            type="number"
                            step="any"
                            className="h-8"
                            value={t.tension ?? ""}
                            onChange={(e) =>
                              updateTubular(i, "tension", e.target.value ? Number(e.target.value) : null)
                            }
                          />
                        </td>
                        <td className="py-1">
                          {form.tubulars.length > 1 && (
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-8 w-8"
                              onClick={() =>
                                setForm({
                                  ...form,
                                  tubulars: form.tubulars.filter((_, j) => j !== i),
                                })
                              }
                            >
                              <X className="h-3 w-3" />
                            </Button>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Cement */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="space-y-1">
                <Label>TOC MD (ft)</Label>
                {numField(form.topOfCementMd, (v) => setForm({ ...form, topOfCementMd: v }))}
              </div>
              <div className="space-y-1">
                <Label>Lead Slurry (ppg)</Label>
                {numField(form.leadCementSlurryDensity, (v) =>
                  setForm({ ...form, leadCementSlurryDensity: v })
                )}
              </div>
              <div className="space-y-1">
                <Label>Tail Slurry (ppg)</Label>
                {numField(form.tailCementSlurryDensity, (v) =>
                  setForm({ ...form, tailCementSlurryDensity: v })
                )}
              </div>
              <div className="space-y-1">
                <Label>Tail Length (ft)</Label>
                {numField(form.tailCementLength, (v) => setForm({ ...form, tailCementLength: v }))}
              </div>
            </div>

            {/* Fluids */}
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              <div className="space-y-1">
                <Label>Drilling Fluid</Label>
                <Input
                  value={form.drillingFluid}
                  onChange={(e) => setForm({ ...form, drillingFluid: e.target.value })}
                />
              </div>
              <div className="space-y-1">
                <Label>Drilling Fluid Density (ppg)</Label>
                {numField(form.drillingFluidDensity, (v) =>
                  setForm({ ...form, drillingFluidDensity: v })
                )}
              </div>
              <div className="space-y-1">
                <Label>Drilling ECD (ppg)</Label>
                {numField(form.drillingEcd, (v) => setForm({ ...form, drillingEcd: v }))}
              </div>
            </div>

            <div className="flex gap-2 justify-end">
              <Button variant="outline" onClick={cancel}>
                Cancel
              </Button>
              <Button
                onClick={handleSave}
                disabled={
                  !form.sectionName.trim() ||
                  !form.sectionType ||
                  createSection.isPending ||
                  updateSection.isPending
                }
              >
                <Check className="h-4 w-4 mr-1" /> Save
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
