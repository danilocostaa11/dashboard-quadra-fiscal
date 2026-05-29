import type { Lead } from './types';

export const leads: Lead[] = [
  { id: "lead-1", nome: "Ricardo Almeida", email: "ricardo@email.com", telefone: "(11) 99876-5432", interesse: "Terreno comercial Cid. Patriarca", fonte: "site", estagio: "novo", score: 85, ultimoContato: "2026-05-28" },
  { id: "lead-2", nome: "Fernanda Costa", email: "fernanda.costa@gmail.com", telefone: "(11) 98765-4321", interesse: "Sobrado na R. Maria Fagnani", fonte: "indicacao", estagio: "contato", score: 72, ultimoContato: "2026-05-27" },
  { id: "lead-3", nome: "Paulo Henrique", email: "ph.negocios@yahoo.com", telefone: "(11) 97654-3210", interesse: "Prédio comercial zona leste", fonte: "anuncio", estagio: "visita", score: 91, ultimoContato: "2026-05-26" },
  { id: "lead-4", nome: "Camila Santos", email: "camila.s@outlook.com", telefone: "(11) 96543-2109", interesse: "Área para incorporação", fonte: "site", estagio: "proposta", score: 68, ultimoContato: "2026-05-25" },
  { id: "lead-5", nome: "Roberto Nunes", email: "roberto.n@email.com", telefone: "(11) 95432-1098", interesse: "Casa com terreno grande", fonte: "indicacao", estagio: "novo", score: 77, ultimoContato: "2026-05-28" },
  { id: "lead-6", nome: "Juliana Martins", email: "ju.martins@gmail.com", telefone: "(11) 94321-0987", interesse: "Investimento imobiliário SP", fonte: "anuncio", estagio: "contato", score: 63, ultimoContato: "2026-05-24" },
  { id: "lead-7", nome: "André Luiz", email: "andre.luiz@empresa.com", telefone: "(11) 93210-9876", interesse: "Permuta de imóveis comerciais", fonte: "site", estagio: "proposta", score: 88, ultimoContato: "2026-05-27" },
  { id: "lead-8", nome: "Mariana Oliveira", email: "mari.oliveira@hotmail.com", telefone: "(11) 92109-8765", interesse: "Casa em Cid. Patriarca", fonte: "indicacao", estagio: "visita", score: 55, ultimoContato: "2026-05-22" },
  { id: "lead-9", nome: "Lucas Ferreira", email: "lucas.f@email.com", telefone: "(11) 91098-7654", interesse: "Área + prédio para retrofit", fonte: "anuncio", estagio: "novo", score: 82, ultimoContato: "2026-05-28" },
  { id: "lead-10", nome: "Beatriz Araújo", email: "bia.araujo@gmail.com", telefone: "(11) 90987-6543", interesse: "Terreno zona leste SP", fonte: "site", estagio: "contato", score: 70, ultimoContato: "2026-05-26" },
];

export const stageLabels: Record<string, string> = {
  novo: "Novo",
  contato: "Em Contato",
  visita: "Visita Agendada",
  proposta: "Proposta",
  fechado: "Fechado",
  perdido: "Perdido",
};

export const stageColors: Record<string, string> = {
  novo: "bg-blue-500/15 text-blue-400",
  contato: "bg-purple-500/15 text-purple-400",
  visita: "bg-amber-500/15 text-amber-400",
  proposta: "bg-orange-500/15 text-orange-400",
  fechado: "bg-emerald-500/15 text-emerald-400",
  perdido: "bg-red-500/15 text-red-400",
};

export const fonteEmojis: Record<string, string> = {
  site: "🌐",
  indicacao: "🤝",
  anuncio: "📢",
  rede_social: "📱",
  evento: "🎪",
  outro: "📌",
};
