// Quadra Fiscal 047097 — Lote polygons (percent-based coordinates)
// All coordinates are percentages of canvas width/height
// Derived from the official cadastral map of Cid. Patriarca, São Paulo
// R. Prof. Aprígio Gonzaga (top), R. Maria Fagnani (bottom)
//
// GEOMETRIA FIDEDIGNA: Cada lote segue os limites reais do mapa cadastral
// - Lado esquerdo curvo (oscila entre x=0 e x=2)
// - Lado direito com degraus (reentrâncias em y=42 e y=55)
// - Fileira frontal mais estreita que a traseira
// - Linha divisória inclinada de y=47 (esquerda) a y=44 (direita)
// - Topo inclinado seguindo R. Prof. Aprígio Gonzaga
// - Base inclinada seguindo R. Maria Fagnani

export interface LotData {
  id: string;
  lote: string;
  numero: string;
  status: string;
  points: [number, number][]; // [x%, y%] — percentage of canvas dimensions
  row: 'top' | 'bottom';
  propertyId?: string;
}

// ============================================================
// BLOCK BOUNDARIES (from cadastral map)
// ============================================================

// Top edge: y = topYAt(x) — R. Prof. Aprígio Gonzaga
// Slopes from (6, 0) to (100, 11.5)
function topYAt(x: number): number {
  return 0 + (x - 6) * (11.5 / 94); // slope = 11.5/94 ≈ 0.1223
}

// Bottom edge: y = bottomYAt(x) — R. Maria Fagnani
// Slopes from (6, 80) to (0, 87), then curves
function bottomYAt(x: number): number {
  if (x >= 6) {
    return 80 + (x - 6) * 0.1; // gentle slope right
  } else {
    return 80 + (6 - x) * 1.17; // steep curve left
  }
}

// Dividing line between rows: y = divYAt(x)
// Slopes from (6, 47) to (94, 44)
function divYAt(x: number): number {
  return 47 + (x - 6) * (-3 / 88); // slope = -3/88 ≈ -0.0341
}

// Left boundary: x = leftXAt(y) — curved edge
// Oscillates between x=0 and x=2
function leftXAt(y: number): number {
  if (y < 10) return 0;
  if (y < 30) return 2;
  if (y < 50) return 0;
  if (y < 70) return 2;
  if (y < 85) return 0;
  return 3;
}

// Right boundary: stepped
// First step at y=42, second at y=55
function rightXAt(y: number): number {
  if (y < 42) return 100;
  if (y < 55) return 94;
  if (y < 100) return 97.5;
  return 97.5;
}

// ============================================================
// LOT GEOMETRY — 16 columns, 2 rows, FIDEL to cadastral map
// ============================================================

// Front row: narrower lots (3-4% width), from top edge to dividing line
// Back row: wider lots (5-6% width), from dividing line to bottom edge

export const lots: LotData[] = [
  // ===== TOP ROW (F 0082 → F 0070 → CD 08) =====
  // Front lots: narrower, following top edge slope

  // Col 0: F0082 (N.308) — leftmost, left edge follows curve
  {
    id: 'lot-f0082',
    lote: 'F 0082',
    numero: 'N. 308',
    status: 'Sem dados',
    row: 'top',
    points: [
      [leftXAt(10), 10],           // top-left (curved)
      [9, topYAt(9)],              // top-right
      [9, divYAt(9)],              // bottom-right (at dividing line)
      [leftXAt(47), 47],           // bottom-left (curved, at dividing line)
    ],
  },

  // Col 1: F0081 (N.318)
  {
    id: 'lot-f0081',
    lote: 'F 0081',
    numero: 'N. 318',
    status: 'Sem Contato',
    row: 'top',
    propertyId: '9',
    points: [
      [9, topYAt(9)],
      [14, topYAt(14)],
      [14, divYAt(14)],
      [9, divYAt(9)],
    ],
  },

  // Col 2: F0080 (N.330)
  {
    id: 'lot-f0080',
    lote: 'F 0080',
    numero: 'N. 330',
    status: 'Sem Contato',
    row: 'top',
    propertyId: '8',
    points: [
      [14, topYAt(14)],
      [19, topYAt(19)],
      [19, divYAt(19)],
      [14, divYAt(14)],
    ],
  },

  // Col 3: F0079 (N.342)
  {
    id: 'lot-f0079',
    lote: 'F 0079',
    numero: 'N. 342',
    status: 'Sem Contato',
    row: 'top',
    propertyId: '7',
    points: [
      [19, topYAt(19)],
      [24, topYAt(24)],
      [24, divYAt(24)],
      [19, divYAt(19)],
    ],
  },

  // Col 4: F0283 (N.344)
  {
    id: 'lot-f0283',
    lote: 'F 0283',
    numero: 'N. 344',
    status: 'Sem Contato',
    row: 'top',
    propertyId: '10',
    points: [
      [24, topYAt(24)],
      [29, topYAt(29)],
      [29, divYAt(29)],
      [24, divYAt(24)],
    ],
  },

  // Col 5: F0282 (N.350)
  {
    id: 'lot-f0282',
    lote: 'F 0282',
    numero: 'N. 350',
    status: 'Sem Contato',
    row: 'top',
    points: [
      [29, topYAt(29)],
      [34, topYAt(34)],
      [34, divYAt(34)],
      [29, divYAt(29)],
    ],
  },

  // Col 6: F0077 (N.358)
  {
    id: 'lot-f0077',
    lote: 'F 0077',
    numero: 'N. 358',
    status: 'Em Negociação',
    row: 'top',
    propertyId: '11',
    points: [
      [34, topYAt(34)],
      [39, topYAt(39)],
      [39, divYAt(39)],
      [34, divYAt(34)],
    ],
  },

  // Col 7: F0076 (N.368)
  {
    id: 'lot-f0076',
    lote: 'F 0076',
    numero: 'N. 368',
    status: 'Em Negociação',
    row: 'top',
    propertyId: '12',
    points: [
      [39, topYAt(39)],
      [44, topYAt(44)],
      [44, divYAt(44)],
      [39, divYAt(39)],
    ],
  },

  // Col 8: F0075 (N.378)
  {
    id: 'lot-f0075',
    lote: 'F 0075',
    numero: 'N. 378',
    status: 'Em Negociação',
    row: 'top',
    propertyId: '13',
    points: [
      [44, topYAt(44)],
      [49, topYAt(49)],
      [49, divYAt(49)],
      [44, divYAt(44)],
    ],
  },

  // Col 9: F0074 (N.384)
  {
    id: 'lot-f0074',
    lote: 'F 0074',
    numero: 'N. 384',
    status: 'Sem dados',
    row: 'top',
    points: [
      [49, topYAt(49)],
      [54, topYAt(54)],
      [54, divYAt(54)],
      [49, divYAt(49)],
    ],
  },

  // Col 10: F0073 (N.394)
  {
    id: 'lot-f0073',
    lote: 'F 0073',
    numero: 'N. 394',
    status: 'Sem dados',
    row: 'top',
    points: [
      [54, topYAt(54)],
      [59, topYAt(59)],
      [59, divYAt(59)],
      [54, divYAt(54)],
    ],
  },

  // Col 11: F0072 (N.400)
  {
    id: 'lot-f0072',
    lote: 'F 0072',
    numero: 'N. 400',
    status: 'Sem dados',
    row: 'top',
    points: [
      [59, topYAt(59)],
      [64, topYAt(64)],
      [64, divYAt(64)],
      [59, divYAt(59)],
    ],
  },

  // Col 12: F0071 (N.404)
  {
    id: 'lot-f0071',
    lote: 'F 0071',
    numero: 'N. 404',
    status: 'Sem dados',
    row: 'top',
    points: [
      [64, topYAt(64)],
      [69, topYAt(69)],
      [69, divYAt(69)],
      [64, divYAt(64)],
    ],
  },

  // Col 13: F0180 (N.408)
  {
    id: 'lot-f0180',
    lote: 'F 0180',
    numero: 'N. 408',
    status: 'Sem dados',
    row: 'top',
    points: [
      [69, topYAt(69)],
      [74, topYAt(74)],
      [74, divYAt(74)],
      [69, divYAt(69)],
    ],
  },

  // Col 14: F0070 (N.414)
  {
    id: 'lot-f0070',
    lote: 'F 0070',
    numero: 'N. 414',
    status: 'Sem dados',
    row: 'top',
    points: [
      [74, topYAt(74)],
      [79, topYAt(79)],
      [79, divYAt(79)],
      [74, divYAt(74)],
    ],
  },

  // Col 15: CD 08 (N.440) — far right, extends to right edge with steps
  {
    id: 'lot-cd08',
    lote: 'CD 08',
    numero: 'N. 440',
    status: 'Sem dados',
    row: 'top',
    points: [
      [79, topYAt(79)],
      [94, topYAt(94)],
      [94, divYAt(94)],
      [79, divYAt(79)],
    ],
  },

  // ===== BOTTOM ROW (F 0083 → F 0062) =====
  // Back lots: wider, from dividing line to bottom edge

  // Col 0: F0083 (N.31) — leftmost, left edge follows curve
  {
    id: 'lot-f0083',
    lote: 'F 0083',
    numero: 'N. 31',
    status: 'Sem dados',
    row: 'bottom',
    points: [
      [leftXAt(47), 47],           // top-left (curved, at dividing line)
      [9, divYAt(9)],              // top-right (at dividing line)
      [9, bottomYAt(9)],           // bottom-right
      [leftXAt(80), 80],           // bottom-left (curved)
    ],
  },

  // Col 1: F0084 (N.39)
  {
    id: 'lot-f0084',
    lote: 'F 0084',
    numero: 'N. 39',
    status: 'Sem dados',
    row: 'bottom',
    points: [
      [9, divYAt(9)],
      [14, divYAt(14)],
      [14, bottomYAt(14)],
      [9, bottomYAt(9)],
    ],
  },

  // Col 2: F0450 (N.47)
  {
    id: 'lot-f0450',
    lote: 'F 0450',
    numero: 'N. 47',
    status: 'Sem dados',
    row: 'bottom',
    points: [
      [14, divYAt(14)],
      [19, divYAt(19)],
      [19, bottomYAt(19)],
      [14, bottomYAt(14)],
    ],
  },

  // Col 3: F0451 (N.73)
  {
    id: 'lot-f0451',
    lote: 'F 0451',
    numero: 'N. 73',
    status: 'Sem dados',
    row: 'bottom',
    points: [
      [19, divYAt(19)],
      [24, divYAt(24)],
      [24, bottomYAt(24)],
      [19, bottomYAt(19)],
    ],
  },

  // Col 4: F0172 (N.91) — atrás de F0283 (N.344)
  {
    id: 'lot-f0172',
    lote: 'F 0172',
    numero: 'N. 91',
    status: 'Em Negociação',
    row: 'bottom',
    propertyId: '4',
    points: [
      [24, divYAt(24)],
      [29, divYAt(29)],
      [29, bottomYAt(29)],
      [24, bottomYAt(24)],
    ],
  },

  // Col 5: F0086 (N.85)
  {
    id: 'lot-f0086',
    lote: 'F 0086',
    numero: 'N. 85',
    status: 'Em Negociação',
    row: 'bottom',
    propertyId: '6',
    points: [
      [29, divYAt(29)],
      [34, divYAt(34)],
      [34, bottomYAt(34)],
      [29, bottomYAt(29)],
    ],
  },

  // Col 6: F0088 (N.101) — atrás de F0077 (N.358)
  {
    id: 'lot-f0088',
    lote: 'F 0088',
    numero: 'N. 101',
    status: 'Em Negociação',
    row: 'bottom',
    propertyId: '1',
    points: [
      [34, divYAt(34)],
      [39, divYAt(39)],
      [39, bottomYAt(39)],
      [34, bottomYAt(34)],
    ],
  },

  // Col 7: F0087 (N.85)
  {
    id: 'lot-f0087',
    lote: 'F 0087',
    numero: 'N. 85',
    status: 'Sem dados',
    row: 'bottom',
    points: [
      [39, divYAt(39)],
      [44, divYAt(44)],
      [44, bottomYAt(44)],
      [39, bottomYAt(39)],
    ],
  },

  // Col 8: F0089 (N.113)
  {
    id: 'lot-f0089',
    lote: 'F 0089',
    numero: 'N. 113',
    status: 'Em Negociação',
    row: 'bottom',
    propertyId: '3',
    points: [
      [44, divYAt(44)],
      [49, divYAt(49)],
      [49, bottomYAt(49)],
      [44, bottomYAt(44)],
    ],
  },

  // Col 9: F0090 (N.117)
  {
    id: 'lot-f0090',
    lote: 'F 0090',
    numero: 'N. 117',
    status: 'Em Negociação',
    row: 'bottom',
    propertyId: '5',
    points: [
      [49, divYAt(49)],
      [54, divYAt(54)],
      [54, bottomYAt(54)],
      [49, bottomYAt(49)],
    ],
  },

  // Col 10: F0173 (N.121)
  {
    id: 'lot-f0173',
    lote: 'F 0173',
    numero: 'N. 121',
    status: 'Em Negociação',
    row: 'bottom',
    propertyId: '2',
    points: [
      [54, divYAt(54)],
      [59, divYAt(59)],
      [59, bottomYAt(59)],
      [54, bottomYAt(54)],
    ],
  },

  // Col 11: F0091 (N.131)
  {
    id: 'lot-f0091',
    lote: 'F 0091',
    numero: 'N. 131',
    status: 'Sem dados',
    row: 'bottom',
    points: [
      [59, divYAt(59)],
      [64, divYAt(64)],
      [64, bottomYAt(64)],
      [59, bottomYAt(59)],
    ],
  },

  // Col 12: F0092 (N.137)
  {
    id: 'lot-f0092',
    lote: 'F 0092',
    numero: 'N. 137',
    status: 'Sem dados',
    row: 'bottom',
    points: [
      [64, divYAt(64)],
      [69, divYAt(69)],
      [69, bottomYAt(69)],
      [64, bottomYAt(64)],
    ],
  },

  // Col 13: F0093 (N.151)
  {
    id: 'lot-f0093',
    lote: 'F 0093',
    numero: 'N. 151',
    status: 'Sem dados',
    row: 'bottom',
    points: [
      [69, divYAt(69)],
      [74, divYAt(74)],
      [74, bottomYAt(74)],
      [69, bottomYAt(69)],
    ],
  },

  // Col 14: F0094 (N.155)
  {
    id: 'lot-f0094',
    lote: 'F 0094',
    numero: 'N. 155',
    status: 'Sem dados',
    row: 'bottom',
    points: [
      [74, divYAt(74)],
      [79, divYAt(79)],
      [79, bottomYAt(79)],
      [74, bottomYAt(74)],
    ],
  },

  // Col 15: F0062 (N.165) — far right, follows stepped right boundary
  {
    id: 'lot-f0062',
    lote: 'F 0062',
    numero: 'N. 165',
    status: 'Sem dados',
    row: 'bottom',
    points: [
      [79, divYAt(79)],
      [94, divYAt(94)],
      [97.5, 55],                // step at y=55
      [97.5, bottomYAt(97.5)],  // bottom-right
      [79, bottomYAt(79)],
    ],
  },
];

// ============================================================
// BLOCK OUTLINE (for background fill)
// ============================================================
export const blockOutline: [number, number][] = [
  // Top-left curve (R. Aprígio Gonzaga)
  [0, 2],
  [2.5, 0.5],
  [6, 0],
  // Top edge — straight along R. Aprígio Gonzaga (slopes down to right)
  [100, 11.5],
  // Right side — stepped descent
  [100, 42],
  [94, 42],
  [94, 48],
  [100, 48],
  [100, 55],
  [97.5, 55],
  [97.5, 100],
  [93, 100],
  // Bottom edge — R. Maria Fagnani
  [6, 80],
  [2.5, 83],
  [0, 87],
  // Left curve back to top
  [0, 2],
];

// ============================================================
// STREET LABELS
// ============================================================
export const streets = [
  { name: 'R. Prof. Aprígio Gonzaga', position: [50, -2] as [number, number], rotation: 0.5, row: 'top' },
  { name: 'R. Maria Fagnani', position: [50, 86] as [number, number], rotation: 0.3, row: 'bottom' },
];

// ============================================================
// STATUS COLORS
// ============================================================
export const statusColors: Record<string, string> = {
  'Em Negociação': '#f59e0b',
  'Sem Contato': '#6b7280',
  'Sem dados': '#374151',
};

export const statusHoverColors: Record<string, string> = {
  'Em Negociação': '#FF8C42',
  'Sem Contato': '#AAAAAA',
  'Sem dados': '#666666',
};
