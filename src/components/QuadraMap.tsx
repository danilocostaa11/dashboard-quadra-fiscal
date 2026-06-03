import { useEffect, useRef } from 'react';
import { Canvas, Polygon, Text, Rect } from 'fabric';
import { lots, statusColors, statusHoverColors, streets } from '../data/lots';
import { properties } from '../data/properties';

interface QuadraMapProps {
  selectedLot: string | null;
  onSelectLot: (lotId: string | null) => void;
}

export default function QuadraMap({ selectedLot, onSelectLot }: QuadraMapProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const fabricRef = useRef<Canvas | null>(null);
  const lotShapesRef = useRef<Map<string, Polygon>>(new Map());

  const CANVAS_W = 1200;
  const CANVAS_H = 500;

  // Convert percentage coords to pixel coords
  const px = (xPct: number) => (xPct / 100) * CANVAS_W;
  const py = (yPct: number) => (yPct / 100) * CANVAS_H;

  const getProperty = (lotId: string) => properties.find(p => p.lotId === lotId);

  useEffect(() => {
    if (!canvasRef.current) return;
    
    const canvas = new Canvas(canvasRef.current, {
      width: CANVAS_W,
      height: CANVAS_H,
      backgroundColor: '#0d1117',
      selection: false,
    });
    fabricRef.current = canvas;

    // Draw lots as real polygons from GeoSampa
    const lotShapes = new Map<string, Polygon>();

    lots.forEach((lot) => {
      const prop = getProperty(lot.id);
      const status = prop?.status || lot.status;
      const color = statusColors[status] || '#374151';
      const hoverColor = statusHoverColors[status] || '#4b5563';
      const isSelected = selectedLot === lot.id;

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

      // Store original colors for hover
      (polygon as any)._lotId = lot.id;
      (polygon as any)._fillColor = color;
      (polygon as any)._hoverColor = hoverColor;
      (polygon as any)._selectedFill = '#3b82f6';
      (polygon as any)._selectedStroke = '#60a5fa';

      canvas.add(polygon);
      lotShapes.set(lot.id, polygon);

      // Add lot label at centroid
      const centerX = points.reduce((s, p) => s + p.x, 0) / points.length;
      const centerY = points.reduce((s, p) => s + p.y, 0) / points.length;

      // Lot number label
      const labelText = new Text(lot.numero, {
        left: centerX,
        top: centerY - 5,
        fontSize: 8,
        fontFamily: 'Inter, system-ui, sans-serif',
        fill: '#d1d5db',
        originX: 'center',
        originY: 'center',
        selectable: false,
        evented: false,
      });

      // Lote code label
      const loteText = new Text(lot.lote, {
        left: centerX,
        top: centerY + 6,
        fontSize: 6,
        fontFamily: 'Inter, system-ui, sans-serif',
        fill: '#6b7280',
        originX: 'center',
        originY: 'center',
        selectable: false,
        evented: false,
      });

      canvas.add(labelText);
      canvas.add(loteText);
    });

    lotShapesRef.current = lotShapes;

    // Draw street labels
    streets.forEach((street) => {
      const streetLabel = new Text(street.name, {
        left: px(street.position[0]),
        top: py(street.position[1]),
        fontSize: 12,
        fontFamily: 'Inter, system-ui, sans-serif',
        fill: '#6b7280',
        fontWeight: '600',
        originX: 'center',
        originY: 'center',
        angle: street.rotation,
        selectable: false,
        evented: false,
      });
      canvas.add(streetLabel);
    });

    // Legend labels
    const legendY = CANVAS_H - 18;
    const legendItems = [
      { label: 'Em Negociação', color: '#f59e0b' },
      { label: 'Sem Contato', color: '#6b7280' },
      { label: 'Sem dados', color: '#374151' },
    ];

    legendItems.forEach((item, i) => {
      const x = 10 + i * 140;
      const rect = new Rect({
        left: x,
        top: legendY - 6,
        width: 10,
        height: 10,
        fill: item.color,
        stroke: '#0d1117',
        strokeWidth: 1,
        selectable: false,
        evented: false,
      });
      const text = new Text(item.label, {
        left: x + 15,
        top: legendY,
        fontSize: 10,
        fontFamily: 'Inter, system-ui, sans-serif',
        fill: '#9ca3af',
        selectable: false,
        evented: false,
        originY: 'center',
      });
      canvas.add(rect);
      canvas.add(text);
    });

    // Quadra label
    const quadraLabel = new Text('Quadra Fiscal 047097 — Cid. Patriarca (GeoSampa)', {
      left: CANVAS_W - 10,
      top: CANVAS_H - 18,
      fontSize: 10,
      fontFamily: 'Inter, system-ui, sans-serif',
      fill: '#4b5563',
      originX: 'right',
      originY: 'center',
      selectable: false,
      evented: false,
    });
    canvas.add(quadraLabel);

    // Data source label
    const sourceLabel = new Text('Fonte: GeoSampa WFS — polígonos reais', {
      left: 10,
      top: CANVAS_H - 18,
      fontSize: 9,
      fontFamily: 'Inter, system-ui, sans-serif',
      fill: '#374151',
      selectable: false,
      evented: false,
      originY: 'center',
    });
    canvas.add(sourceLabel);

    // Mouse events
    canvas.on('mouse:over', (e) => {
      const obj = e.target as any;
      if (obj?._lotId && selectedLot !== obj._lotId) {
        obj.set('fill', obj._hoverColor);
        obj.set('strokeWidth', 2.5);
        obj.set('stroke', '#f59e0b');
        canvas.requestRenderAll();
      }
    });

    canvas.on('mouse:out', (e) => {
      const obj = e.target as any;
      if (obj?._lotId && selectedLot !== obj._lotId) {
        obj.set('fill', obj._fillColor);
        obj.set('strokeWidth', 1);
        obj.set('stroke', '#1a1f2e');
        canvas.requestRenderAll();
      }
    });

    canvas.on('mouse:down', (e) => {
      const obj = e.target as any;
      if (obj?._lotId) {
        onSelectLot(obj._lotId === selectedLot ? null : obj._lotId);
      } else {
        onSelectLot(null);
      }
    });

    return () => {
      canvas.dispose();
      fabricRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Update selection highlighting
  useEffect(() => {
    const canvas = fabricRef.current;
    if (!canvas) return;

    lotShapesRef.current.forEach((shape, lotId) => {
      const isSelected = selectedLot === lotId;
      const obj = shape as any;
      if (isSelected) {
        shape.set('fill', '#3b82f6');
        shape.set('stroke', '#60a5fa');
        shape.set('strokeWidth', 3);
      } else {
        shape.set('fill', obj._fillColor);
        shape.set('stroke', '#1a1f2e');
        shape.set('strokeWidth', 1);
      }
    });
    canvas.requestRenderAll();
  }, [selectedLot]);

  return (
    <div className="quadra-map-wrapper">
      <canvas ref={canvasRef} />
    </div>
  );
}
