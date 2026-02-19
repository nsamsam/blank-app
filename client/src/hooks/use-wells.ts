import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import type { Well, CasingHoleSection, PpfgRow, DirectionalRow } from "@shared/schema";

async function api(url: string, options?: RequestInit) {
  const res = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({ message: "Request failed" }));
    throw new Error(body.message || "Request failed");
  }
  return res.json();
}

// Wells
export function useWells() {
  return useQuery<Well[]>({
    queryKey: ["wells"],
    queryFn: () => api("/api/wells"),
  });
}

export function useWell(id: number) {
  return useQuery<Well>({
    queryKey: ["wells", id],
    queryFn: () => api(`/api/wells/${id}`),
    enabled: !!id,
  });
}

export function useCreateWell() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: Partial<Well>) =>
      api("/api/wells", { method: "POST", body: JSON.stringify(data) }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["wells"] }),
  });
}

export function useUpdateWell() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, ...data }: Partial<Well> & { id: number }) =>
      api(`/api/wells/${id}`, { method: "PUT", body: JSON.stringify(data) }),
    onSuccess: (_, vars) => {
      qc.invalidateQueries({ queryKey: ["wells"] });
      qc.invalidateQueries({ queryKey: ["wells", vars.id] });
    },
  });
}

export function useDeleteWell() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => api(`/api/wells/${id}`, { method: "DELETE" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["wells"] }),
  });
}

// Casing & Hole
export function useCasingHole(wellId: number) {
  return useQuery<CasingHoleSection[]>({
    queryKey: ["casing-hole", wellId],
    queryFn: () => api(`/api/wells/${wellId}/casing-hole`),
    enabled: !!wellId,
  });
}

export function useCreateCasingHole(wellId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: Partial<CasingHoleSection>) =>
      api(`/api/wells/${wellId}/casing-hole`, {
        method: "POST",
        body: JSON.stringify(data),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["casing-hole", wellId] }),
  });
}

export function useUpdateCasingHole(wellId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, ...data }: Partial<CasingHoleSection> & { id: number }) =>
      api(`/api/wells/${wellId}/casing-hole/${id}`, {
        method: "PATCH",
        body: JSON.stringify(data),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["casing-hole", wellId] }),
  });
}

export function useDeleteCasingHole(wellId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) =>
      api(`/api/wells/${wellId}/casing-hole/${id}`, { method: "DELETE" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["casing-hole", wellId] }),
  });
}

// PPFG
export function usePpfg(wellId: number) {
  return useQuery<PpfgRow[]>({
    queryKey: ["ppfg", wellId],
    queryFn: () => api(`/api/wells/${wellId}/ppfg`),
    enabled: !!wellId,
  });
}

export function useBulkPpfg(wellId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: Partial<PpfgRow>[]) =>
      api(`/api/wells/${wellId}/ppfg/bulk`, {
        method: "POST",
        body: JSON.stringify({ data }),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["ppfg", wellId] }),
  });
}

// Directional Survey
export function useDirectional(wellId: number) {
  return useQuery<DirectionalRow[]>({
    queryKey: ["directional", wellId],
    queryFn: () => api(`/api/wells/${wellId}/directional`),
    enabled: !!wellId,
  });
}

export function useBulkDirectional(wellId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: Partial<DirectionalRow>[]) =>
      api(`/api/wells/${wellId}/directional/bulk`, {
        method: "POST",
        body: JSON.stringify({ data }),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["directional", wellId] }),
  });
}
