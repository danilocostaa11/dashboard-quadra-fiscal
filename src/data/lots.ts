// Quadra Fiscal 047097 — Lote polygons (percent-based coordinates)
// All coordinates are percentages of canvas width/height
// Derived from the official cadastral map of Cid. Patriarca, São Paulo
// R. Prof. Aprígio Gonzaga (top), R. Maria Fagnani (bottom)
//
// GEOMETRIA FIDEDIGNA 5ª REESCRITA:
// - Lado esquerdo curvo (x oscila entre 0 e 3)
// - Lado direito com degraus (y=42→94, y=55→97.5)
// - Fileira frontal (top): 16 lotes com LARGURAS VARIANTES
//   (CD 08 enorme à direita, F0283/F0282 estreitos no meio)
// - Fileira traseira (bottom):
//   CANTO INFERIOR ESQUERDO = 3 faixas HORIZONTAIS:
//     Faixa 1 (topo): F0083 — mais alta
//     Faixa 2 (meio): F0084 — intermediária
//     Faixa 3 (base): F0450 e F0451 LADO A LADO — mais curta
//   RESTANTE = lotes verticais, F0090/F0089 EMPILHADOS
// - Linha divisória desce à direita (y=42 esq → y=48 dir)
// - Colunas NÃO se alinham (staggered)

export interface LotData {
  id: string;
  lote: string;
  numero: string;
  status: string;
  points: [number, number][];
  row: 'top' | 'bottom';
  propertyId?: string;
}

// ============================================================
// BLOCK BOUNDARIES (from cadastral map)
// ============================================================

function topYAt(x: number): number {
  // R. Prof. Aprígio Gonzaga runs roughly horizontal
  // Very slight slope: y≈3 on left, y≈6 on right
  return 3 + x * 0.03;
}

function bottomYAt(x: number): number {
  if (x >= 6) return 80 + (x - 6) * 0.1;
  return 80 + (6 - x) * 1.17;
}

function leftXAt(y: number): number {
  if (y < 10) return 0;
  if (y < 30) return 2;
  if (y < 50) return 0;
  if (y < 70) return 2;
  if (y < 85) return 0;
  return 3;
}

function rightXAt(y: number): number {
  if (y < 42) return 100;
  if (y < 55) return 94;
  return 97.5;
}

// ============================================================
// HORIZONTAL LOT ZONE (lower-left: x = 0 to 24)
// ============================================================

const hzRight = 6; // right edge of horizontal lots (aligned with top row start)

// 3 horizontal bands (NOT 4)
// Band 1: F0083 — TALLEST (top of zone to mid)
// Band 2: F0084 — MEDIUM (mid to lower)
// Band 3: F0450 + F0451 SIDE BY SIDE (bottom, shortest)
const hzTop = 47;       // top of zone
const hzMid1 = 58;      // bottom of F0083 / top of F0450
const hzMid2 = 68;      // bottom of F0084 / top of F0451
const hzBottom = 80;    // bottom of zone
const hzMidX = 12;      // x-divider between F0450 and F0451

// ============================================================
// VERTICAL LOT ZONE DIVIDER
// ============================================================
// Divides top and bottom rows — DESCENDS from left to right
function vDivYAt(x: number): number {
  // y = 42 at left (x=24), y = 48 at right (x=100)
  return 42 + (x - hzRight) * (6 / 76);
}

// ============================================================
// TOP ROW — 16 lots with VARIED widths
// ============================================================
// Column positions calibrated from cadastral map:
// Wider: F0082, F0077, F0070, CD 08
// Narrower: F0283, F0282, F0074, F0073, F0072, F0071

// Top row: 16 lots, more uniform widths like the cadastral map
// Total span: x=6 (left edge at top) to x=100 (right edge)
// Average lot width ~5.5%, CD 08 slightly wider at ~8%
const topCols = [
  { id: 'lot-f0082', lote: 'F 0082', numero: 'N. 308', status: 'Sem dados', x1: 6, x2: 12 },
  { id: 'lot-f0081', lote: 'F 0081', numero: 'N. 318', status: 'Sem Contato', x1: 12, x2: 17, propertyId: '9' },
  { id: 'lot-f0080', lote: 'F 0080', numero: 'N. 330', status: 'Sem Contato', x1: 17, x2: 22, propertyId: '8' },
  { id: 'lot-f0079', lote: 'F 0079', numero: 'N. 342', status: 'Sem Contato', x1: 22, x2: 27, propertyId: '7' },
  { id: 'lot-f0283', lote: 'F 0283', numero: 'N. 344', status: 'Sem Contato', x1: 27, x2: 31, propertyId: '10' },
  { id: 'lot-f0282', lote: 'F 0282', numero: 'N. 350', status: 'Sem Contato', x1: 31, x2: 35 },
  { id: 'lot-f0077', lote: 'F 0077', numero: 'N. 358', status: 'Em Negociação', x1: 35, x2: 41, propertyId: '11' },
  { id: 'lot-f0076', lote: 'F 0076', numero: 'N. 368', status: 'Em Negociação', x1: 41, x2: 47, propertyId: '12' },
  { id: 'lot-f0075', lote: 'F 0075', numero: 'N. 378', status: 'Em Negociação', x1: 47, x2: 53, propertyId: '13' },
  { id: 'lot-f0074', lote: 'F 0074', numero: 'N. 384', status: 'Sem dados', x1: 53, x2: 58 },
  { id: 'lot-f0073', lote: 'F 0073', numero: 'N. 394', status: 'Sem dados', x1: 58, x2: 63 },
  { id: 'lot-f0072', lote: 'F 0072', numero: 'N. 400', status: 'Sem dados', x1: 63, x2: 68 },
  { id: 'lot-f0071', lote: 'F 0071', numero: 'N. 404', status: 'Sem dados', x1: 68, x2: 73 },
  { id: 'lot-f0160', lote: 'F 0160', numero: 'N. 408', status: 'Sem dados', x1: 73, x2: 78 },
  { id: 'lot-f0070', lote: 'F 0070', numero: 'N. 414', status: 'Sem dados', x1: 78, x2: 85 },
  { id: 'lot-cd08',  lote: 'CD 08',  numero: 'N. 444', status: 'Sem dados', x1: 85, x2: 100 },
];

export const lots: LotData[] = [
  // ============================================================
  // TOP ROW
  // ============================================================
  ...topCols.map(col => ({
    id: col.id,
    lote: col.lote,
    numero: col.numero,
    status: col.status,
    row: 'top' as const,
    propertyId: col.propertyId,
    points: [
      [col.x1, topYAt(col.x1)] as [number, number],
      [col.x2, topYAt(col.x2)] as [number, number],
      [col.x2, vDivYAt(col.x2)] as [number, number],
      [col.x1, vDivYAt(col.x1)] as [number, number],
    ],
  })),

  // ============================================================
  // BOTTOM ROW — HORIZONTAL LOTS (lower-left)
  // ============================================================

  // F0083 (N.31) — TALLEST horizontal band
  {
    id: 'lot-f0083', lote: 'F 0083', numero: 'N. 31', status: 'Sem dados', row: 'bottom',
    points: [
      [leftXAt(hzTop), hzTop],
      [hzRight, hzTop],
      [hzRight, hzMid1],
      [leftXAt(hzMid1), hzMid1],
    ],
  },

  // F0084 (N.39) — MEDIUM horizontal band
  {
    id: 'lot-f0084', lote: 'F 0084', numero: 'N. 39', status: 'Sem dados', row: 'bottom',
    points: [
      [leftXAt(hzMid1), hzMid1],
      [hzRight, hzMid1],
      [hzRight, hzMid2],
      [leftXAt(hzMid2), hzMid2],
    ],
  },

  // F0450 (N.47) — SHORT band, LEFT HALF
  {
    id: 'lot-f0450', lote: 'F 0450', numero: 'N. 47', status: 'Sem dados', row: 'bottom',
    points: [
      [leftXAt(hzMid2), hzMid2],
      [hzMidX, hzMid2],
      [hzMidX, hzBottom],
      [leftXAt(hzBottom), hzBottom],
    ],
  },

  // F0451 (N.73) — SHORT band, RIGHT HALF (side-by-side with F0450)
  {
    id: 'lot-f0451', lote: 'F 0451', numero: 'N. 73', status: 'Sem dados', row: 'bottom',
    points: [
      [hzMidX, hzMid2],
      [hzRight, hzMid2],
      [hzRight, bottomYAt(hzRight)],
      [hzMidX, bottomYAt(hzMidX)],
    ],
  },

  // ============================================================
  // BOTTOM ROW — VERTICAL LOTS (aligned with top row columns)
  // ============================================================

  // Each bottom lot is directly below its corresponding top lot
  // x-coordinates match the topCols positions

  // F0087 (N.85) — below F0082 (col 1: x=6-12)
  {
    id: 'lot-f0087', lote: 'F 0087', numero: 'N. 85', status: 'Sem dados', row: 'bottom',
    points: [
      [6, vDivYAt(6)], [12, vDivYAt(12)], [12, bottomYAt(12)], [6, bottomYAt(6)],
    ],
  },

  // F0086 (N.85) — below F0081 (col 2: x=12-17)
  {
    id: 'lot-f0086', lote: 'F 0086', numero: 'N. 85', status: 'Em Negociação', row: 'bottom', propertyId: '6',
    points: [
      [12, vDivYAt(12)], [17, vDivYAt(17)], [17, bottomYAt(17)], [12, bottomYAt(12)],
    ],
  },

  // F0172 (N.91) — below F0080 (col 3: x=17-22)
  {
    id: 'lot-f0172', lote: 'F 0172', numero: 'N. 91', status: 'Em Negociação', row: 'bottom', propertyId: '4',
    points: [
      [17, vDivYAt(17)], [22, vDivYAt(22)], [22, bottomYAt(22)], [17, bottomYAt(17)],
    ],
  },

  // F0088 (N.101) — below F0079 (col 4: x=22-27)
  {
    id: 'lot-f0088', lote: 'F 0088', numero: 'N. 101', status: 'Em Negociação', row: 'bottom', propertyId: '1',
    points: [
      [22, vDivYAt(22)], [27, vDivYAt(27)], [27, bottomYAt(27)], [22, bottomYAt(22)],
    ],
  },

  // F0090 (N.117) — below F0283 (col 5: x=27-31), TOP of stacked pair
  {
    id: 'lot-f0090', lote: 'F 0090', numero: 'N. 117', status: 'Em Negociação', row: 'bottom', propertyId: '5',
    points: [
      [27, vDivYAt(27)], [31, vDivYAt(31)], [31, vDivYAt(31) + 8], [27, vDivYAt(27) + 8],
    ],
  },

  // F0089 (N.113) — below F0283 (col 5: x=27-31), BOTTOM of stacked pair
  {
    id: 'lot-f0089', lote: 'F 0089', numero: 'N. 113', status: 'Em Negociação', row: 'bottom', propertyId: '3',
    points: [
      [27, vDivYAt(27) + 8], [31, vDivYAt(31) + 8], [31, bottomYAt(31)], [27, bottomYAt(27)],
    ],
  },

  // F0173 (N.121) — below F0282 (col 6: x=31-35)
  {
    id: 'lot-f0173', lote: 'F 0173', numero: 'N. 121', status: 'Em Negociação', row: 'bottom', propertyId: '2',
    points: [
      [31, vDivYAt(31)], [35, vDivYAt(35)], [35, bottomYAt(35)], [31, bottomYAt(31)],
    ],
  },

  // F0091 (N.131) — below F0077 (col 7: x=35-41)
  {
    id: 'lot-f0091', lote: 'F 0091', numero: 'N. 131', status: 'Sem dados', row: 'bottom',
    points: [
      [35, vDivYAt(35)], [41, vDivYAt(41)], [41, bottomYAt(41)], [35, bottomYAt(35)],
    ],
  },

  // F0092 (N.137) — below F0076 (col 8: x=41-47)
  {
    id: 'lot-f0092', lote: 'F 0092', numero: 'N. 137', status: 'Sem dados', row: 'bottom',
    points: [
      [41, vDivYAt(41)], [47, vDivYAt(47)], [47, bottomYAt(47)], [41, bottomYAt(41)],
    ],
  },

  // F0093 (N.151) — below F0075 (col 9: x=47-53)
  {
    id: 'lot-f0093', lote: 'F 0093', numero: 'N. 151', status: 'Sem dados', row: 'bottom',
    points: [
      [47, vDivYAt(47)], [53, vDivYAt(53)], [53, bottomYAt(53)], [47, bottomYAt(47)],
    ],
  },

  // F0094 (N.155) — below F0074 (col 10: x=53-58)
  {
    id: 'lot-f0094', lote: 'F 0094', numero: 'N. 155', status: 'Sem dados', row: 'bottom',
    points: [
      [53, vDivYAt(53)], [58, vDivYAt(58)], [58, bottomYAt(58)], [53, bottomYAt(53)],
    ],
  },

  // F0062 (N.165) — below F0073+F0072+F0071+F0160+F0070 (cols 11-15: x=58-85)
  {
    id: 'lot-f0062', lote: 'F 0062', numero: 'N. 165', status: 'Sem dados', row: 'bottom',
    points: [
      [58, vDivYAt(58)], [85, vDivYAt(85)],
      [85, bottomYAt(85)], [58, bottomYAt(58)],
    ],
  },
];

// ============================================================
// BLOCK OUTLINE
// ============================================================
export const blockOutline: [number, number][] = [
  [0, 3], [0, 3],
  [100, 6],
  [100, 42], [94, 42], [94, 55], [97.5, 55], [97.5, 100], [93, 100],
  [6, 80], [2.5, 83], [0, 87],
  [0, 3],
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
