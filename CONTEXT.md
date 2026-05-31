# Dashboard Quadra Fiscal — Contexto

## Visão Geral
Dashboard de Prospecção Imobiliária — Quadra Fiscal 047097 (R. Maria Fagnani / R. Prof. Aprígio Gonzaga, Cid. Patriarca, SP).

## Stack
- **React 19** + **Vite 8** + **TypeScript 6**
- **Tailwind CSS v4** (via @tailwindcss/vite)
- **Leaflet 1.9.4** + react-leaflet 5 (CSS via CDN no index.html)
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
│   ├── lots.ts           — 32 lotes com coord % (F0082→F0057)
│   ├── properties.ts     — 13 imóveis + localStorage persistence
│   ├── leads.ts          — 10 leads + stage labels/colors
│   └── pipeline.ts       — 5 estágios do funil + formatters BRL
├── components/
│   ├── QuadraMap.tsx     — Mapa visual (lotes posicionados por %)
│   ├── PropertyCard.tsx  — Card de imóvel (preço, composição, MAC)
│   ├── LeadCard.tsx      — Card de lead (score, estágio, botões)
│   ├── KPICards.tsx      — 6 KPIs (Valor, Metragem, Cash, Permutas, Total)
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
- **Lotes:** 32 (17 primeira fileira + 15 segunda fileira)
- **Imóveis:** 13 cadastrados
- **Leads:** 10 ativos

## Status dos Lotes (cores)
- 🟢 Fechado (#22c55e)
- 🟡 Negociando (#eab308)
- 🔴 Não Vende (#ef4444)
- ⚪ Sem Contato (#94a3b8)
- 🟠 Sem dados (#f97316)

## Features
- Mapa visual com lotes posicionados por % (absolute positioning)
- Cutouts de escada (4 degraus) + recorte de rua
- Popup ao clicar no lote
- Filtros por status + busca textual em Imóveis e Leads
- localStorage persistence (`dashboard-prospeccao-properties`)
- Formatação BRL via Intl.NumberFormat
- Pipeline visual com 5 estágios

## Git History
- `81b83ae` — Rebuild completo (Vite/React/TS + todos componentes)
- `f48db05` — Initial commit from Vercel deployment

## Status
- ✅ Source completo e versionado
- ✅ Build funcionando (pnpm build)
- ✅ Push pro GitHub feito
- ✅ Vercel auto-deploy conectado

## Próximos passos
- TBD (aguardando direção do Danilo)
