import type { Lot } from './types';

// Lotes da QUADRA FISCAL 047097 — R. Maria Fagnani / R. Prof. Aprígio Gonzaga
// Geometria baseada no mapa cadastral real (2 fileiras, 26 lotes)

export interface CadastralLot {
  id: string;
  lote: string;
  numero: string;
  status: string;
  propertyId?: string;
  row: 'top' | 'bottom';
  index: number; // posição na fileira (0-based)
}

export const cadastralLots: CadastralLot[] = [
  // === FILEIRA SUPERIOR (13 lotes) — topo da quadra ===
  { id: "f0082", lote: "F 0082", numero: "N. 308", status: "Sem dados", row: "top", index: 0 },
  { id: "f0081", lote: "F 0081", numero: "N. 318", status: "Sem Contato", propertyId: "9", row: "top", index: 1 },
  { id: "f0080", lote: "F 0080", numero: "N. 330", status: "Sem Contato", propertyId: "8", row: "top", index: 2 },
  { id: "f0079", lote: "F 0079", numero: "N. 342", status: "Sem dados", row: "top", index: 3 },
  { id: "f0283", lote: "F 0283", numero: "N. 344", status: "Sem dados", row: "top", index: 4 },
  { id: "f0282", lote: "F 0282", numero: "N. 358", status: "Fechado", propertyId: "7", row: "top", index: 5 },
  { id: "f0077", lote: "F 0077", numero: "N. 368", status: "Negociando", propertyId: "6", row: "top", index: 6 },
  { id: "f0076", lote: "F 0076", numero: "N. 378", status: "Sem Contato", propertyId: "5", row: "top", index: 7 },
  { id: "f0075", lote: "F 0075", numero: "N. 384", status: "Não Vende", propertyId: "4", row: "top", index: 8 },
  { id: "f0074", lote: "F 0074", numero: "N. 394", status: "Sem dados", row: "top", index: 9 },
  { id: "f0073", lote: "F 0073", numero: "N. 394", status: "Fechado", propertyId: "3", row: "top", index: 10 },
  { id: "f0072", lote: "F 0072", numero: "N. 394", status: "Negociando", propertyId: "2", row: "top", index: 11 },
  { id: "f0071", lote: "F 0071", numero: "N. 394", status: "Sem Contato", propertyId: "1", row: "top", index: 12 },

  // === FILEIRA INFERIOR (13 lotes) — base da quadra (3 primeiros recuam = degraus) ===
  { id: "f0083", lote: "F 0083", numero: "N. 31", status: "Sem Contato", propertyId: "13", row: "bottom", index: 0 },
  { id: "f0084", lote: "F 0084", numero: "N. 39", status: "Negociando", propertyId: "12", row: "bottom", index: 1 },
  { id: "f0450", lote: "F 0450", numero: "N. 47", status: "Sem dados", row: "bottom", index: 2 },
  { id: "f0451", lote: "F 0451", numero: "N. 73", status: "Fechado", propertyId: "11", row: "bottom", index: 3 },
  { id: "f0087", lote: "F 0087", numero: "N. 85", status: "Sem Contato", propertyId: "10", row: "bottom", index: 4 },
  { id: "f0086", lote: "F 0086", numero: "N. 85", status: "Sem dados", row: "bottom", index: 5 },
  { id: "f0172", lote: "F 0172", numero: "N. 91", status: "Negociando", row: "bottom", index: 6 },
  { id: "f0088", lote: "F 0088", numero: "N. 101", status: "Sem dados", row: "bottom", index: 7 },
  { id: "f0090", lote: "F 0090", numero: "N. 117", status: "Fechado", row: "bottom", index: 8 },
  { id: "f0089", lote: "F 0089", numero: "N. 113", status: "Sem Contato", row: "bottom", index: 9 },
  { id: "f0173", lote: "F 0173", numero: "N. 121", status: "Sem dados", row: "bottom", index: 10 },
  { id: "f0091", lote: "F 0091", numero: "N. 131", status: "Sem dados", row: "bottom", index: 11 },
  { id: "f0092", lote: "F 0092", numero: "N. 137", status: "Sem dados", row: "bottom", index: 12 },
];

// Manter compatibilidade com o tipo Lot existente
export const lots: Lot[] = cadastralLots.map(l => ({
  id: `lot-${l.id}`,
  lote: l.lote,
  numero: l.numero,
  status: l.status,
  x: 0, y: 0, width: 0, height: 0, // positions handled by SVG layout
  propertyId: l.propertyId,
  rotation: 0,
}));
