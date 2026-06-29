# Dashboard Quadra Fiscal — Contexto

## Visão Geral
Dashboard de Prospecção Imobiliária — Quadra Fiscal 047097 (R. Maria Fagnani / R. Prof. Aprígio Gonzaga, Cid. Patriarca, SP).

## Stack
- **React 19** + **Vite 8** + **TypeScript 6**
- **Tailwind CSS v4** (via @tailwindcss/vite)
- **Fabric.js** — canvas para polígonos interativos
- **lucide-react** para ícones
- Build output: ~224KB JS + ~27KB CSS

## Infraestrutura
- **GitHub:** github.com/danilocostaa11/dashboard-quadra-fiscal
- **Vercel:** dash-quadra-fiscal.vercel.app (auto-deploy conectado)
- **Local:** /docker/hermes/projetos/dashboard-quadra-fiscal/

## Estrutura de Arquivos
```
src/
├── data/
│   ├── types.ts          — Interfaces (Lot, Property, Lead, PipelineStage)
│   ├── lots.ts           — 63 lotes com polígonos reais do GeoSampa WFS
│   ├── properties.ts     — imóveis + localStorage persistence
│   ├── leads.ts          — leads + stage labels/colors
│   └── pipeline.ts       — 5 estágios do funil + formatters BRL
├── components/
│   ├── QuadraMap.tsx     — Canvas Fabric.js com polígonos reais
│   ├── PropertyCard.tsx  — Card de imóvel (preço, composição, MAC)
│   ├── LeadCard.tsx      — Card de lead (score, estágio, botões)
│   ├── KPICards.tsx      — KPIs (Valor, Metragem, Cash, Permutas, Total)
│   ├── PipelineWidget.tsx — Funil visual com barras horizontais
│   └── AppLayout.tsx     — Sidebar + header + content area
├── App.tsx               — 4 abas: Dashboard, Quadra, Imóveis, Leads
├── main.tsx
└── index.css             — @import "tailwindcss"
```

## Dados da Quadra
- **Quadra Fiscal:** 047097
- **Ruas:** R. Maria Fagnani (base) / R. Prof. Aprígio Gonzaga (topo)
- **Bairro:** Cid. Patriarca, São Paulo
- **Área total:** 3.480 m²
- **Lotes:** 63 (polígonos reais do GeoSampa WFS)
- **Fonte geográfica:** GeoSampa WFS (servicos.spurbanismo.sp.gov.br)
- **Coordenadas:** UTM EPSG:31983 normalizadas para canvas %

## Status dos Lotes (cores)
- 🟢 Fechado (#22c55e)
- 🟡 Negociando (#eab308)
- 🔴 Não Vende (#ef4444)
- ⚪ Sem Contato (#94a3b8)
- 🟠 Sem dados (#f97316)

## Features
- Mapa visual com polígonos reais do GeoSampa (Canvas Fabric.js)
- Cada lote é um polígono interativo com hover + seleção
- Labels de rua posicionados no canvas
- Popup ao clicar no lote
- Filtros por status + busca textual em Imóveis e Leads
- localStorage persistence (`dashboard-prospeccao-properties`)
- Formatação BRL via Intl.NumberFormat
- Pipeline visual com 5 estágios

## Git History
- `611b639` — feat: polígonos reais do GeoSampa WFS — geometria fidedigna
- `81b83ae` — Rebuild completo (Vite/React/TS + todos componentes)
- `f48db05` — Initial commit from Vercel deployment

## Status
- ✅ Source completo e versionado
- ✅ Build funcionando (pnpm build)
- ✅ Push pro GitHub feito
- ✅ Vercel auto-deploy conectado
- ✅ Polígonos reais do GeoSampa implementados

## Próximos passos
- Melhorias na Dashboard (aguardando direção do Danilo)
