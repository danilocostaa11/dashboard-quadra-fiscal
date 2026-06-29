import { useEffect, useRef, useState, useCallback } from 'react';
import { Canvas, Point, Polygon, Text, Rect } from 'fabric';
import { lots, statusColors, statusHoverColors, streets } from '../data/lots';
import { Property } from '../data/properties';

interface QuadraMapProps {
  selectedLot: string | null;
  onSelectLot: (lotId: string | null) => void;
  properties: Property[];
}

// Normalize lotId — handles 'F0088', 'lot-f0088', 'f0088' etc
const norm = (id: string) => id.replace(/^lot-/i, '').toUpperCase();

const ALL_STATUSES = [
  { key: 'Em Negociação', color: '#f59e0b' },
  { key: 'Sem Contato', color: '#6b7280' },
  { key: 'Fechado', color: '#22c55e' },
  { key: 'Não Vende', color: '#ef4444' },
  { key: 'Sem dados', color: '#374151' },
];

export default function QuadraMap({ selectedLot, onSelectLot, properties }: QuadraMapProps) {
  const wrapRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const fabricRef = useRef<Canvas | null>(null);
  const lotShapesRef = useRef<Map<string, Polygon>>(new Map());
  const propsRef = useRef(properties);
  const selectedRef = useRef(selectedLot);
  const [resizeKey, setResizeKey] = useState(0);

  // Keep refs in sync
  propsRef.current = properties;
  selectedRef.current = selectedLot;

  const getProperty = useCallback((lotId: string) => {
    const n = norm(lotId);
    return propsRef.current.find(p => norm(p.lotId) === n);
  }, []);

  const getColor = useCallback((lotId: string): string => {
    const prop = getProperty(lotId);
    const status = prop?.status || 'Sem dados';
    return statusColors[status] || '#374151';
  }, [getProperty]);

  const getHoverColor = useCallback((lotId: string): string => {
    const prop = getProperty(lotId);
    const status = prop?.status || 'Sem dados';
    return statusHoverColors[status] || '#4b5563';
  }, [getProperty]);

  // --- Main canvas setup (re-runs on resizeKey change) ---
  useEffect(() => {
    if (!canvasRef.current || !wrapRef.current) return;

    const wrap = wrapRef.current;
    const wrapWidth = Math.max(320, wrap.clientWidth - 4);
    const aspect = 500 / 1200;
    const CW = wrapWidth;
    const CH = Math.round(wrapWidth * aspect);

    const px = (xPct: number) => (xPct / 100) * CW;
    const py = (yPct: number) => (yPct / 100) * CH;

    const canvas = new Canvas(canvasRef.current, {
      width: CW,
      height: CH,
      backgroundColor: '#0d1117',
      selection: false,
      stopContextMenu: true,
    });
    fabricRef.current = canvas;

    // --- ZOOM & PAN ---
    let isDragging = false;
    let lastPosX = 0;
    let lastPosY = 0;

    canvas.on('mouse:wheel', (opt) => {
      const e = opt.e as WheelEvent;
      let zoom = canvas.getZoom();
      zoom *= 0.999 ** e.deltaY;
      zoom = Math.min(Math.max(0.5, zoom), 5);
      canvas.zoomToPoint(new Point(e.offsetX, e.offsetY), zoom);
      e.preventDefault();
      e.stopPropagation();
    });

    canvas.on('mouse:down', (opt) => {
      const evt = opt.e as MouseEvent;
      if (evt.button === 1) {
        isDragging = true;
        lastPosX = evt.clientX;
        lastPosY = evt.clientY;
        canvas.selection = false;
        return;
      }
      const obj = opt.target as any;
      if (obj?._lotId) {
        onSelectLot(obj._lotId === selectedRef.current ? null : obj._lotId);
      } else {
        isDragging = true;
        lastPosX = evt.clientX;
        lastPosY = evt.clientY;
        canvas.selection = false;
        onSelectLot(null);
      }
    });

    canvas.on('mouse:move', (opt) => {
      if (!isDragging) return;
      const evt = opt.e as MouseEvent;
      const vpt = canvas.viewportTransform;
      if (!vpt) return;
      vpt[4] += evt.clientX - lastPosX;
      vpt[5] += evt.clientY - lastPosY;
      lastPosX = evt.clientX;
      lastPosY = evt.clientY;
      canvas.requestRenderAll();
    });

    canvas.on('mouse:up', () => {
      isDragging = false;
      canvas.selection = false;
    });

    // --- TOUCH: pinch zoom ---
    let pinchDist = 0;
    let pinchZoomStart = 1;
    const touchEl = canvas.getSelectionElement().parentElement;
    if (touchEl) {
      const onTouchStart = (e: TouchEvent) => {
        if (e.touches.length === 2) {
          const dx = e.touches[0].clientX - e.touches[1].clientX;
          const dy = e.touches[0].clientY - e.touches[1].clientY;
          pinchDist = Math.hypot(dx, dy);
          pinchZoomStart = canvas.getZoom();
          e.preventDefault();
        }
      };
      const onTouchMove = (e: TouchEvent) => {
        if (e.touches.length === 2 && pinchDist > 0) {
          const dx = e.touches[0].clientX - e.touches[1].clientX;
          const dy = e.touches[0].clientY - e.touches[1].clientY;
          const dist = Math.hypot(dx, dy);
          let zoom = pinchZoomStart * (dist / pinchDist);
          zoom = Math.min(Math.max(0.5, zoom), 5);
          const rect = touchEl.getBoundingClientRect();
          canvas.zoomToPoint(new Point(rect.width / 2, rect.height / 2), zoom);
          e.preventDefault();
        }
      };
      const onTouchEnd = () => { pinchDist = 0; };

      touchEl.addEventListener('touchstart', onTouchStart, { passive: false });
      touchEl.addEventListener('touchmove', onTouchMove, { passive: false });
      touchEl.addEventListener('touchend', onTouchEnd);
    }

    // --- DRAW LOTS ---
    const lotShapes = new Map<string, Polygon>();
    const labelScale = Math.max(0.65, CW / 1200);

    lots.forEach((lot) => {
      const color = getColor(lot.id);
      const hoverColor = getHoverColor(lot.id);
      const isSelected = selectedRef.current === lot.id;
      const points = lot.points.map(([x, y]) => ({ x: px(x), y: py(y) }));

      const polygon = new Polygon(points, {
        fill: isSelected ? '#3b82f6' : color,
        stroke: isSelected ? '#60a5fa' : '#1a1f2e',
        strokeWidth: isSelected ? 2.5 : 1,
        selectable: false,
        evented: true,
        hasControls: false,
        hasBorders: false,
        hoverCursor: 'pointer',
      });

      (polygon as any)._lotId = lot.id;
      (polygon as any)._fillColor = color;
      (polygon as any)._hoverColor = hoverColor;

      canvas.add(polygon);
      lotShapes.set(lot.id, polygon);

      // Labels at centroid
      const cx = points.reduce((s, p) => s + p.x, 0) / points.length;
      const cy = points.reduce((s, p) => s + p.y, 0) / points.length;

      const fLabel = new Text(`F ${lot.numero}`, {
        left: cx, top: cy - 5 * labelScale,
        fontSize: 8 * labelScale,
        fontFamily: 'Inter, system-ui, sans-serif',
        fill: '#d1d5db',
        originX: 'center', originY: 'center',
        selectable: false, evented: false,
      });
      canvas.add(fLabel);

      if (lot.numImovel) {
        const nLabel = new Text(`N. ${lot.numImovel}`, {
          left: cx, top: cy + 6 * labelScale,
          fontSize: 7 * labelScale,
          fontFamily: 'Inter, system-ui, sans-serif',
          fill: '#9ca3af',
          originX: 'center', originY: 'center',
          selectable: false, evented: false,
        });
        canvas.add(nLabel);
      }
    });

    lotShapesRef.current = lotShapes;

    // --- STREET LABELS ---
    streets.forEach((street) => {
      const label = new Text(street.name, {
        left: px(street.position[0]), top: py(street.position[1]),
        fontSize: 12 * labelScale,
        fontFamily: 'Inter, system-ui, sans-serif',
        fill: '#6b7280', fontWeight: '600',
        originX: 'center', originY: 'center',
        angle: street.rotation,
        selectable: false, evented: false,
      });
      canvas.add(label);
    });

    // --- DYNAMIC LEGEND with counts ---
    const legendY = CH - 14;
    let legendX = 10;
    const matchedLotIds = new Set(propsRef.current.map(p => norm(p.lotId)));

    ALL_STATUSES.forEach((s) => {
      const count = s.key === 'Sem dados'
        ? lots.filter(l => !matchedLotIds.has(norm(l.id))).length
        : propsRef.current.filter(p => p.status === s.key).length;

      const rect = new Rect({
        left: legendX, top: legendY - 6,
        width: 10, height: 10,
        fill: s.color, stroke: '#0d1117', strokeWidth: 1,
        selectable: false, evented: false,
      });
      const text = new Text(`${s.key} (${count})`, {
        left: legendX + 15, top: legendY,
        fontSize: 9 * labelScale,
        fontFamily: 'Inter, system-ui, sans-serif',
        fill: '#9ca3af',
        selectable: false, evented: false,
        originY: 'center',
      });
      canvas.add(rect);
      canvas.add(text);
      legendX += 115 * labelScale;
    });

    // Source label
    const srcLabel = new Text('GeoSampa WFS', {
      left: CW - 8, top: CH - 14,
      fontSize: 9 * labelScale,
      fontFamily: 'Inter, system-ui, sans-serif',
      fill: '#374151',
      originX: 'right', originY: 'center',
      selectable: false, evented: false,
    });
    canvas.add(srcLabel);

    // --- HOVER ---
    canvas.on('mouse:over', (e) => {
      const obj = e.target as any;
      if (obj?._lotId && selectedRef.current !== obj._lotId && !isDragging) {
        obj.set('fill', obj._hoverColor);
        obj.set('strokeWidth', 2.5);
        obj.set('stroke', '#f59e0b');
        canvas.requestRenderAll();
      }
    });

    canvas.on('mouse:out', (e) => {
      const obj = e.target as any;
      if (obj?._lotId && selectedRef.current !== obj._lotId) {
        obj.set('fill', obj._fillColor);
        obj.set('strokeWidth', 1);
        obj.set('stroke', '#1a1f2e');
        canvas.requestRenderAll();
      }
    });

    // --- RESIZE OBSERVER ---
    let resizeTimer: ReturnType<typeof setTimeout>;
    const ro = new ResizeObserver(() => {
      clearTimeout(resizeTimer);
      resizeTimer = setTimeout(() => {
        const newW = Math.max(320, wrap.clientWidth - 4);
        if (Math.abs(newW - CW) > 40) {
          setResizeKey(k => k + 1);
        }
      }, 200);
    });
    ro.observe(wrap);

    return () => {
      clearTimeout(resizeTimer);
      ro.disconnect();
      canvas.dispose();
      fabricRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [resizeKey]);

  // --- UPDATE COLORS WHEN PROPERTIES CHANGE ---
  useEffect(() => {
    const canvas = fabricRef.current;
    if (!canvas) return;

    lotShapesRef.current.forEach((shape, lotId) => {
      const obj = shape as any;
      const isSelected = selectedLot === lotId;
      const color = getColor(lotId);
      const hoverColor = getHoverColor(lotId);

      obj._fillColor = color;
      obj._hoverColor = hoverColor;

      if (isSelected) {
        shape.set('fill', '#3b82f6');
        shape.set('stroke', '#60a5fa');
        shape.set('strokeWidth', 3);
      } else {
        shape.set('fill', color);
        shape.set('stroke', '#1a1f2e');
        shape.set('strokeWidth', 1);
      }
    });
    canvas.requestRenderAll();
  }, [properties, selectedLot, getColor, getHoverColor]);

  return (
    <div className="quadra-map-wrapper" ref={wrapRef}>
      <div className="zoom-hint">🔍 Scroll/pinch para zoom · Arrastar para mover</div>
      <canvas ref={canvasRef} />
    </div>
  );
}
