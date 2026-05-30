import { useState } from 'react';
import { cadastralLots } from '../data/lots';
import type { CadastralLot } from '../data/lots';

// --- Muted / Cadastral Status Colors ---
const STATUS_COLORS: Record<string, string> = {
  'Fechado':      '#8fbc8f',   // muted sage green
  'Negociando':   '#e6c88a',   // muted amber
  'Não Vende':    '#cd8c8c',   // muted rose
  'Sem Contato':  '#b0b8b8',   // muted gray
  'Sem dados':    '#d4b896',   // muted tan
};

// --- SVG Layout Constants (landscape, cadastral proportions) ---
const VB_W = 1400;
const VB_H = 500;

// Margins
const M = { top: 55, bottom: 55, left: 20, right: 20 };

// Block area
const BLOCK_Y = M.top;
const BLOCK_H = VB_H - M.top - M.bottom;
const BLOCK_X = M.left;
const BLOCK_END_X = VB_W - M.right;
const BLOCK_W = BLOCK_END_X - BLOCK_X;

// Top row: 13 equal-width vertical lots
const TOP_ROW_H = BLOCK_H * 0.52;
const LOT_W = BLOCK_W / 13;
const TOP_Y = BLOCK_Y;

// Bottom row
const BOT_ROW_H = BLOCK_H * 0.48;
const BOT_Y = BLOCK_Y + TOP_ROW_H;
const BOT_GAP = 15; // horizontal gap between staircase area and regular lots

// Bottom row regular lots (index 3..12) — 10 lots, equal width
const BOT_REGULAR_COUNT = 10;
const BOT_REGULAR_W = (BLOCK_W - BOT_GAP) / BOT_REGULAR_COUNT;

// Bottom row staircase lots (index 0,1,2) — staggered horizontally
// Each step recedes further to the right
const BOT_STEPS = [
  { x: BLOCK_X + LOT_W * 2 + 20,            w: LOT_W * 0.85 }, // i=0  (F0083, most recessed)
  { x: BLOCK_X + LOT_W * 1 + 10,            w: LOT_W * 0.9  }, // i=1  (F0084)
  { x: BLOCK_X,                              w: LOT_W * 0.9  }, // i=2  (F0450, closest to edge)
];
const STEP_HEIGHTS = [
  TOP_ROW_H * 0.55,  // i=0 shorter
  TOP_ROW_H * 0.75,  // i=1 medium
  TOP_ROW_H * 0.92,  // i=2 almost full height
];

function getBottomLotPos(index: number): { x: number; y: number; w: number; h: number } {
  if (index < 3) {
    return {
      x: BOT_STEPS[index].x,
      y: BOT_Y + (BLOCK_H * 0.48 - STEP_HEIGHTS[index]),
      w: BOT_STEPS[index].w,
      h: STEP_HEIGHTS[index],
    };
  }
  const xi = index - 3;
  return {
    x: BLOCK_X + BOT_GAP + xi * BOT_REGULAR_W,
    y: BOT_Y,
    w: BOT_REGULAR_W,
    h: BOT_ROW_H,
  };
}

// --- Muted palette ---
const COLORS = {
  bg:         '#FDF6E3',   // Solarized light — parchment
  border:     '#6B5B47',   // dark brown ink
  borderLight:'#A89880',   // lighter ink
  text:       '#3E3225',   // dark brown text
  textLight:  '#8B7D6B',   // muted label
  gridLine:   '#C8BBA8',   // grid separator
  lotDefault: '#F5DEB3',   // wheat
  titleBar:   '#EDE0CC',   // header bg
  streetBg:   '#E8DCC8',   // street label bg
};

// --- Outline polygon of the block (clockwise from top-left) ---
function buildOutlinePath(): string {
  const pts: [number, number][] = [];

  // Top-left corner
  pts.push([BLOCK_X, TOP_Y]);
  // Top-right corner
  pts.push([BLOCK_END_X, TOP_Y]);

  // Right edge down to bottom-right
  pts.push([BLOCK_END_X, BLOCK_Y + BLOCK_H]);

  // Bottom edge leftward to first regular lot left edge
  pts.push([BLOCK_X + BOT_GAP, BLOCK_Y + BLOCK_H]);

  // Staircase: step 0 (most recessed, right side)
  const s0 = getBottomLotPos(0);
  const s1 = getBottomLotPos(1);
  const s2 = getBottomLotPos(2);

  // Step 0 bottom
  pts.push([s0.x, s0.y + s0.h]);
  // Step 0 → step 1
  pts.push([s0.x, s1.y + s1.h]);
  // Step 1 → step 2
  pts.push([s1.x, s2.y + s2.h]);
  // Step 2 top
  pts.push([s2.x, s2.y]);
  // Step 2 left → top row left edge
  pts.push([BLOCK_X, BOT_Y]);
  // Up to top-left
  pts.push([BLOCK_X, TOP_Y]);

  return pts.map(p => p.join(',')).join(' ');
}

// --- Lot rectangle ---
function LotRect({
  lot, x, y, w, h, isSelected, isHovered, onSelect, onHover,
}: {
  lot: CadastralLot;
  x: number; y: number; w: number; h: number;
  isSelected: boolean; isHovered: boolean;
  onSelect: (id: string) => void; onHover: (id: string | null) => void;
}) {
  const fillColor = STATUS_COLORS[lot.status] || COLORS.lotDefault;
  const strokeColor = isSelected ? '#1E5C3A' : isHovered ? COLORS.text : COLORS.border;
  const strokeW = isSelected ? 2.5 : isHovered ? 1.5 : 1;

  // Adjust font size based on lot width
  const labelSize = w < 48 ? 9 : w < 60 ? 10 : 11;
  const subLabelSize = labelSize - 1;

  return (
    <g
      className="cursor-pointer"
      onClick={() => onSelect(lot.id)}
      onMouseEnter={() => onHover(lot.id)}
      onMouseLeave={() => onHover(null)}
    >
      <rect
        x={x} y={y} width={w} height={h}
        fill={fillColor}
        stroke={strokeColor}
        strokeWidth={strokeW}
        rx={0}
        opacity={isHovered ? 0.82 : 1}
      />
      {/* Label F XXXX — rotated vertically for narrow lots */}
      {h > w * 2.5 ? (
        <>
          <text
            x={x + w / 2} y={y + h / 2 - 6}
            textAnchor="middle"
            fontSize={labelSize}
            fontFamily="'Courier New', monospace"
            fontWeight="bold"
            fill={COLORS.text}
            fillOpacity={0.8}
            style={{ pointerEvents: 'none' }}
          >
            {lot.lote}
          </text>
          <text
            x={x + w / 2} y={y + h / 2 + 10}
            textAnchor="middle"
            fontSize={subLabelSize}
            fontFamily="'Courier New', monospace"
            fill={COLORS.textLight}
            fillOpacity={0.7}
            style={{ pointerEvents: 'none' }}
          >
            {lot.numero}
          </text>
        </>
      ) : (
        <>
          <text
            x={x + w / 2} y={y + h / 2 - 4}
            textAnchor="middle"
            fontSize={labelSize - 1}
            fontFamily="'Courier New', monospace"
            fontWeight="bold"
            fill={COLORS.text}
            fillOpacity={0.8}
            style={{ pointerEvents: 'none' }}
          >
            {lot.lote}
          </text>
          <text
            x={x + w / 2} y={y + h / 2 + 10}
            textAnchor="middle"
            fontSize={subLabelSize - 1}
            fontFamily="'Courier New', monospace"
            fill={COLORS.textLight}
            fillOpacity={0.7}
            style={{ pointerEvents: 'none' }}
          >
            {lot.numero}
          </text>
        </>
      )}
    </g>
  );
}

// --- Main component ---
export default function QuadraMap() {
  const [selected, setSelected] = useState<string | null>(null);
  const [hovered, setHovered] = useState<string | null>(null);

  const topLots = cadastralLots.filter(l => l.row === 'top');
  const bottomLots = cadastralLots.filter(l => l.row === 'bottom');
  const selectedLot = cadastralLots.find(l => l.id === selected);

  const outlinePath = buildOutlinePath();

  return (
    <div className="w-full">
      {/* ── Street label: top ── */}
      <div className="text-center mb-1">
        <span
          className="inline-block px-4 py-1 text-[11px] font-bold tracking-[0.18em] uppercase rounded-sm"
          style={{ color: COLORS.text, backgroundColor: COLORS.streetBg, border: `1px solid ${COLORS.borderLight}`, fontFamily: "'Courier New', monospace" }}
        >
          R. Prof. Aprígio Gonzaga
        </span>
      </div>

      {/* ── SVG Map ── */}
      <div
        className="relative w-full overflow-hidden"
        style={{
          backgroundColor: COLORS.bg,
          border: `1.5px solid ${COLORS.border}`,
        }}
      >
        <svg
          viewBox={`0 0 ${VB_W} ${VB_H}`}
          className="w-full"
          style={{ aspectRatio: `${VB_W}/${VB_H}` }}
        >
          {/* Parchment background */}
          <defs>
            <pattern id="parchment" patternUnits="userSpaceOnUse" width="4" height="4">
              <rect width="4" height="4" fill={COLORS.bg} />
              <circle cx="1" cy="1" r="0.3" fill={COLORS.borderLight} opacity="0.15" />
              <circle cx="3" cy="3" r="0.2" fill={COLORS.borderLight} opacity="0.1" />
            </pattern>
          </defs>
          <rect width={VB_W} height={VB_H} fill="url(#parchment)" />

          {/* Subtle grid / crosshatch in block area */}
          {[...Array(27)].map((_, i) => (
            <line
              key={`vg-${i}`}
              x1={BLOCK_X + i * (BLOCK_W / 26)} y1={BLOCK_Y}
              x2={BLOCK_X + i * (BLOCK_W / 26)} y2={BLOCK_Y + BLOCK_H}
              stroke={COLORS.gridLine} strokeWidth={0.3} opacity={0.4}
            />
          ))}

          {/* Block outline polygon */}
          <polygon
            points={outlinePath}
            fill="none"
            stroke={COLORS.border}
            strokeWidth={2}
            strokeLinejoin="miter"
          />

          {/* Horizontal dividing line between rows (top row bottom edge) */}
          <line
            x1={BLOCK_X} y1={BOT_Y}
            x2={BLOCK_END_X} y2={BOT_Y}
            stroke={COLORS.border}
            strokeWidth={1.2}
            strokeDasharray="8 4"
            opacity={0.5}
          />

          {/* ── Top row: 13 vertical lots ── */}
          {topLots.map(lot => {
            const x = BLOCK_X + lot.index * LOT_W;
            return (
              <LotRect
                key={lot.id}
                lot={lot}
                x={x}
                y={TOP_Y}
                w={LOT_W}
                h={TOP_ROW_H}
                isSelected={selected === lot.id}
                isHovered={hovered === lot.id}
                onSelect={setSelected}
                onHover={setHovered}
              />
            );
          })}

          {/* ── Bottom row: 13 lots with staircase on left ── */}
          {bottomLots.map(lot => {
            const pos = getBottomLotPos(lot.index);
            return (
              <LotRect
                key={lot.id}
                lot={lot}
                x={pos.x}
                y={pos.y}
                w={pos.w}
                h={pos.h}
                isSelected={selected === lot.id}
                isHovered={hovered === lot.id}
                onSelect={setSelected}
                onHover={setHovered}
              />
            );
          })}

          {/* ── Title: Quadra Fiscal label ── */}
          <text
            x={VB_W / 2} y={BLOCK_Y - 14}
            textAnchor="middle"
            fontSize="14"
            fontFamily="'Courier New', monospace"
            fontWeight="bold"
            fill={COLORS.text}
            fillOpacity={0.7}
            letterSpacing={2}
          >
            QUADRA FISCAL 047097
          </text>

          {/* ── Area label ── */}
          <text
            x={VB_W - M.right} y={BLOCK_Y + BLOCK_H + 22}
            textAnchor="end"
            fontSize="11"
            fontFamily="'Courier New', monospace"
            fill={COLORS.textLight}
          >
            Área: 3.480 m²
          </text>

          {/* ── Street label: bottom ── */}
          <text
            x={VB_W / 2} y={VB_H - 10}
            textAnchor="middle"
            fontSize="13"
            fontFamily="'Courier New', monospace"
            fontWeight="bold"
            fill={COLORS.text}
            fillOpacity={0.55}
            letterSpacing={4}
          >
            R. MARIA FAGNANI
          </text>

          {/* ── North arrow (simple) ── */}
          <g transform={`translate(${VB_W - M.right - 20}, ${BLOCK_Y + 20})`} opacity={0.4}>
            <line x1="0" y1="20" x2="0" y2="0" stroke={COLORS.text} strokeWidth="1.5" />
            <polygon points="-4,4 0,0 4,4" fill={COLORS.text} />
            <text x="0" y="28" textAnchor="middle" fontSize="8" fontFamily="'Courier New', monospace" fill={COLORS.text}>
              N
            </text>
          </g>

          {/* ── Scale bar (decorative) ── */}
          <g transform={`translate(${M.left + 10}, ${VB_H - 18})`} opacity={0.35}>
            <line x1="0" y1="0" x2="60" y2="0" stroke={COLORS.text} strokeWidth="1" />
            <line x1="0" y1="-3" x2="0" y2="3" stroke={COLORS.text} strokeWidth="1" />
            <line x1="30" y1="-2" x2="30" y2="2" stroke={COLORS.text} strokeWidth="0.5" />
            <line x1="60" y1="-3" x2="60" y2="3" stroke={COLORS.text} strokeWidth="1" />
            <text x="30" y="10" textAnchor="middle" fontSize="7" fontFamily="'Courier New', monospace" fill={COLORS.text}>
              50 m
            </text>
          </g>
        </svg>
      </div>

      {/* ── Street label: bottom ── */}
      <div className="text-center mt-1">
        <span
          className="inline-block px-4 py-1 text-[11px] font-bold tracking-[0.18em] uppercase rounded-sm"
          style={{ color: COLORS.text, backgroundColor: COLORS.streetBg, border: `1px solid ${COLORS.borderLight}`, fontFamily: "'Courier New', monospace" }}
        >
          R. Maria Fagnani
        </span>
      </div>

      {/* ── Popup do lote selecionado ── */}
      {selectedLot && (
        <div
          className="mt-3 p-4 rounded-sm"
          style={{
            backgroundColor: COLORS.bg,
            border: `1px solid ${COLORS.border}`,
            boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
          }}
        >
          <div className="flex items-center justify-between mb-2">
            <h3
              className="font-bold text-base"
              style={{ color: COLORS.text, fontFamily: "'Courier New', monospace" }}
            >
              {selectedLot.lote} — {selectedLot.numero}
            </h3>
            <button
              onClick={() => setSelected(null)}
              className="text-gray-400 hover:text-gray-700 text-lg"
            >
              ✕
            </button>
          </div>
          <span
            className="inline-block px-3 py-1 rounded-sm text-xs font-medium text-white"
            style={{ backgroundColor: STATUS_COLORS[selectedLot.status] }}
          >
            {selectedLot.status}
          </span>
          {selectedLot.propertyId && (
            <p className="mt-2 text-xs" style={{ color: COLORS.textLight, fontFamily: "'Courier New', monospace" }}>
              Imóvel vinculado: #{selectedLot.propertyId}
            </p>
          )}
          <p className="mt-1 text-xs" style={{ color: COLORS.textLight, fontFamily: "'Courier New', monospace" }}>
            Fileira {selectedLot.row === 'top' ? 'superior' : 'inferior'} · Posição {selectedLot.index + 1}/13
          </p>
        </div>
      )}

      {/* ── Legenda ── */}
      <div
        className="flex flex-wrap gap-4 mt-3 justify-center px-4 py-3 rounded-sm"
        style={{ backgroundColor: COLORS.titleBar, border: `1px solid ${COLORS.borderLight}` }}
      >
        {Object.entries(STATUS_COLORS).map(([label, color]) => (
          <div key={label} className="flex items-center gap-1.5">
            <div
              className="w-3.5 h-3.5 rounded-none border"
              style={{ backgroundColor: color, borderColor: COLORS.border }}
            />
            <span className="text-xs font-medium" style={{ color: COLORS.text, fontFamily: "'Courier New', monospace" }}>
              {label}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
