import { useState } from "react";
import { useLocation } from "wouter";
import { useWell, useUpdateWell } from "@/hooks/use-wells";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ArrowLeft, Save } from "lucide-react";
import CasingHoleTab from "@/components/CasingHoleTab";
import CasingDesignTab from "@/components/CasingDesignTab";
import PpfgTab from "@/components/PpfgTab";
import DirectionalTab from "@/components/DirectionalTab";

export default function WellDetailPage({ wellId }: { wellId: number }) {
  const [, navigate] = useLocation();
  const { data: well, isLoading } = useWell(wellId);
  const updateWell = useUpdateWell();
  const [editWell, setEditWell] = useState<Record<string, any> | null>(null);

  if (isLoading || !well) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
      </div>
    );
  }

  const startEdit = () => {
    setEditWell({
      name: well.name,
      operator: well.operator || "",
      field: well.field || "",
      area: well.area || "",
      block: well.block || "",
      slot: well.slot || "",
      latitude: well.latitude ?? "",
      longitude: well.longitude ?? "",
      waterDepth: well.waterDepth ?? "",
      seawaterDensity: well.seawaterDensity ?? "",
    });
  };

  const handleSave = async () => {
    if (!editWell) return;
    await updateWell.mutateAsync({
      id: wellId,
      name: editWell.name,
      operator: editWell.operator || null,
      field: editWell.field || null,
      area: editWell.area || null,
      block: editWell.block || null,
      slot: editWell.slot || null,
      latitude: editWell.latitude !== "" ? Number(editWell.latitude) : null,
      longitude: editWell.longitude !== "" ? Number(editWell.longitude) : null,
      waterDepth: editWell.waterDepth !== "" ? Number(editWell.waterDepth) : null,
      seawaterDensity: editWell.seawaterDensity !== "" ? Number(editWell.seawaterDensity) : null,
    });
    setEditWell(null);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => navigate("/")}>
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <h2 className="text-2xl font-bold">{well.name}</h2>
      </div>

      <Tabs defaultValue="info">
        <TabsList className="flex-wrap">
          <TabsTrigger value="info">Well Info</TabsTrigger>
          <TabsTrigger value="casing-hole">Casing & Hole</TabsTrigger>
          <TabsTrigger value="casing-design">Casing Design</TabsTrigger>
          <TabsTrigger value="ppfg">PPFG</TabsTrigger>
          <TabsTrigger value="directional">Directional</TabsTrigger>
        </TabsList>

        <TabsContent value="info">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Well Information</CardTitle>
                {editWell ? (
                  <div className="flex gap-2">
                    <Button size="sm" variant="outline" onClick={() => setEditWell(null)}>
                      Cancel
                    </Button>
                    <Button size="sm" onClick={handleSave} disabled={updateWell.isPending}>
                      <Save className="h-4 w-4 mr-1" /> Save
                    </Button>
                  </div>
                ) : (
                  <Button size="sm" variant="outline" onClick={startEdit}>
                    Edit
                  </Button>
                )}
              </div>
            </CardHeader>
            <CardContent>
              {editWell ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {[
                    { label: "Well Name", key: "name" },
                    { label: "Operator", key: "operator" },
                    { label: "Field", key: "field" },
                    { label: "Area", key: "area" },
                    { label: "Block", key: "block" },
                    { label: "Slot", key: "slot" },
                    { label: "Latitude", key: "latitude", type: "number" },
                    { label: "Longitude", key: "longitude", type: "number" },
                    { label: "Water Depth (ft)", key: "waterDepth", type: "number" },
                    { label: "Seawater Density (ppg)", key: "seawaterDensity", type: "number" },
                  ].map(({ label, key, type }) => (
                    <div key={key} className="space-y-1">
                      <Label>{label}</Label>
                      <Input
                        type={type || "text"}
                        step="any"
                        value={editWell[key]}
                        onChange={(e) =>
                          setEditWell({ ...editWell, [key]: e.target.value })
                        }
                      />
                    </div>
                  ))}
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {[
                    { label: "Well Name", value: well.name },
                    { label: "Operator", value: well.operator },
                    { label: "Field", value: well.field },
                    { label: "Area", value: well.area },
                    { label: "Block", value: well.block },
                    { label: "Slot", value: well.slot },
                    { label: "Latitude", value: well.latitude != null ? `${well.latitude}\u00b0` : null },
                    { label: "Longitude", value: well.longitude != null ? `${well.longitude}\u00b0` : null },
                    { label: "Water Depth", value: well.waterDepth != null ? `${well.waterDepth} ft` : null },
                    { label: "Seawater Density", value: well.seawaterDensity != null ? `${well.seawaterDensity} ppg` : null },
                  ].map(({ label, value }) => (
                    <div key={label}>
                      <p className="text-sm text-muted-foreground">{label}</p>
                      <p className="font-medium">{value || "-"}</p>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="casing-hole">
          <CasingHoleTab wellId={wellId} />
        </TabsContent>

        <TabsContent value="casing-design">
          <CasingDesignTab wellId={wellId} well={well} />
        </TabsContent>

        <TabsContent value="ppfg">
          <PpfgTab wellId={wellId} />
        </TabsContent>

        <TabsContent value="directional">
          <DirectionalTab wellId={wellId} />
        </TabsContent>
      </Tabs>
    </div>
  );
}
