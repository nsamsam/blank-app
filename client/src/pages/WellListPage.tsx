import { useState } from "react";
import { useLocation } from "wouter";
import { useWells, useCreateWell, useDeleteWell } from "@/hooks/use-wells";
import { useAuth } from "@/hooks/use-auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Plus, Trash2, LogOut } from "lucide-react";

export default function WellListPage() {
  const [, navigate] = useLocation();
  const { data: wells, isLoading } = useWells();
  const createWell = useCreateWell();
  const deleteWell = useDeleteWell();
  const { logout } = useAuth();
  const [open, setOpen] = useState(false);
  const [wellName, setWellName] = useState("");
  const [operator, setOperator] = useState("");
  const [waterDepth, setWaterDepth] = useState("");
  const [seawaterDensity, setSeawaterDensity] = useState("8.6");

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!wellName.trim()) return;
    await createWell.mutateAsync({
      name: wellName,
      operator: operator || null,
      waterDepth: waterDepth ? Number(waterDepth) : null,
      seawaterDensity: seawaterDensity ? Number(seawaterDensity) : null,
    });
    setWellName("");
    setOperator("");
    setWaterDepth("");
    setSeawaterDensity("8.6");
    setOpen(false);
  };

  const handleDelete = async (e: React.MouseEvent, id: number) => {
    e.stopPropagation();
    if (confirm("Are you sure you want to delete this well?")) {
      await deleteWell.mutateAsync(id);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Wells</h2>
        <div className="flex gap-2">
          <Dialog open={open} onOpenChange={setOpen}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="h-4 w-4 mr-2" /> New Well
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Create New Well</DialogTitle>
              </DialogHeader>
              <form onSubmit={handleCreate} className="space-y-4">
                <div className="space-y-2">
                  <Label>Well Name</Label>
                  <Input
                    value={wellName}
                    onChange={(e) => setWellName(e.target.value)}
                    placeholder="Enter well name"
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label>Operator</Label>
                  <Input
                    value={operator}
                    onChange={(e) => setOperator(e.target.value)}
                    placeholder="Operator name"
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Water Depth (ft)</Label>
                    <Input
                      type="number"
                      step="any"
                      value={waterDepth}
                      onChange={(e) => setWaterDepth(e.target.value)}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Seawater Density (ppg)</Label>
                    <Input
                      type="number"
                      step="any"
                      value={seawaterDensity}
                      onChange={(e) => setSeawaterDensity(e.target.value)}
                    />
                  </div>
                </div>
                <Button type="submit" className="w-full" disabled={createWell.isPending}>
                  Create Well
                </Button>
              </form>
            </DialogContent>
          </Dialog>
          <Button variant="ghost" size="icon" onClick={() => logout.mutate()}>
            <LogOut className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {!wells || wells.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12 text-center">
            <p className="text-muted-foreground mb-4">
              No wells yet. Create your first well to get started.
            </p>
            <Button onClick={() => setOpen(true)}>
              <Plus className="h-4 w-4 mr-2" /> Create Well
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {wells.map((well) => (
            <Card
              key={well.id}
              className="cursor-pointer hover:shadow-md transition-shadow"
              onClick={() => navigate(`/wells/${well.id}`)}
            >
              <CardHeader className="pb-2">
                <div className="flex items-start justify-between">
                  <CardTitle className="text-lg">{well.name}</CardTitle>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8 text-muted-foreground hover:text-destructive"
                    onClick={(e) => handleDelete(e, well.id)}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <div className="text-sm text-muted-foreground space-y-1">
                  {well.operator && <p>Operator: {well.operator}</p>}
                  {well.waterDepth != null && <p>Water Depth: {well.waterDepth} ft</p>}
                  {well.field && <p>Field: {well.field}</p>}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
