import type { Property } from './types';

const STORAGE_KEY = 'dashboard-prospeccao-properties';

const defaultProperties: Property[] = [
  { id: "1", endereco: "R. Maria Fagnani, 426", codigo: "047.097.014-4", preco: 2800000, area: 280, tipo: "Sobrado", cash: 1800000, permutaFisica: 600000, permutaFinanceira: 400000, propostaMAC: 2600000, situacao: "Em negociação", proprietario: "José Silva", observacoes: "Proprietário aceita permuta por apto na região" },
  { id: "2", endereco: "R. Maria Fagnani, 416", codigo: "047.097.015-2", preco: 3200000, area: 320, tipo: "Terreno", cash: 2800000, permutaFisica: 300000, permutaFinanceira: 100000, propostaMAC: 3000000, situacao: "Fechado", proprietario: "Maria Santos", observacoes: "Escriturado, documentação em dia" },
  { id: "3", endereco: "R. Prof. Aprígio Gonzaga, 406", codigo: "047.097.016-1", preco: 4500000, area: 380, tipo: "Prédio Comercial", cash: 3500000, permutaFisica: 700000, permutaFinanceira: 300000, propostaMAC: 4200000, situacao: "Fechado", proprietario: "Construtora ABC", observacoes: "Área com potencial construtivo alto" },
  { id: "4", endereco: "R. Prof. Aprígio Gonzaga, 382", codigo: "047.097.017-9", preco: 1800000, area: 250, tipo: "Sobrado", cash: 1200000, permutaFisica: 400000, permutaFinanceira: 200000, propostaMAC: 1600000, situacao: "Não vende", proprietario: "Herdeiros Costa", observacoes: "Inventário em andamento, indisponível" },
  { id: "5", endereco: "R. Maria Fagnani, 372", codigo: "047.097.018-7", preco: 2500000, area: 290, tipo: "Casa", cash: 2000000, permutaFisica: 350000, permutaFinanceira: 150000, propostaMAC: 2300000, situacao: "Em contato", proprietario: "Ana Paula Lima", observacoes: "Interessada, quer prazo de 6 meses" },
  { id: "6", endereco: "R. Prof. Aprígio Gonzaga, 362", codigo: "047.097.019-5", preco: 3800000, area: 340, tipo: "Terreno + Casa", cash: 3000000, permutaFisica: 500000, permutaFinanceira: 300000, propostaMAC: 3500000, situacao: "Em negociação", proprietario: "Carlos Mendes", observacoes: "Aceita proposta com 20% de entrada" },
  { id: "7", endereco: "R. Prof. Aprígio Gonzaga, 352", codigo: "047.097.020-3", preco: 5200000, area: 410, tipo: "Prédio Misto", cash: 4000000, permutaFisica: 800000, permutaFinanceira: 400000, propostaMAC: 4800000, situacao: "Fechado", proprietario: "Imobiliária Central", observacoes: "Contrato assinado, aguardando registro" },
  { id: "8", endereco: "R. Maria Fagnani, 330", codigo: "047.097.021-1", preco: 2100000, area: 260, tipo: "Sobrado", cash: 1500000, permutaFisica: 400000, permutaFinanceira: 200000, propostaMAC: 1900000, situacao: "Em contato", proprietario: "Roberto Dias", observacoes: "Visita agendada para semana que vem" },
  { id: "9", endereco: "R. Maria Fagnani, 318", codigo: "047.097.022-9", preco: 1950000, area: 240, tipo: "Casa", cash: 1400000, permutaFisica: 350000, permutaFinanceira: 200000, propostaMAC: 1800000, situacao: "Em contato", proprietario: "Sandra Oliveira", observacoes: "Quer trocar por apto maior na mesma região" },
  { id: "10", endereco: "R. Maria Fagnani, 348", codigo: "047.097.023-7", preco: 2650000, area: 300, tipo: "Casa", cash: 2100000, permutaFisica: 350000, permutaFinanceira: 200000, propostaMAC: 2400000, situacao: "Em contato", proprietario: "Fernando Alves", observacoes: "Disponível, preço firme" },
  { id: "11", endereco: "R. Maria Fagnani, 338", codigo: "047.097.024-5", preco: 3100000, area: 310, tipo: "Sobrado", cash: 2500000, permutaFisica: 400000, permutaFinanceira: 200000, propostaMAC: 2900000, situacao: "Fechado", proprietario: "Lucia Ferreira", observacoes: "Negócio fechado, escrituração em curso" },
  { id: "12", endereco: "R. Maria Fagnani, 316", codigo: "047.097.025-3", preco: 2350000, area: 270, tipo: "Casa", cash: 1800000, permutaFisica: 350000, permutaFinanceira: 200000, propostaMAC: 2200000, situacao: "Em negociação", proprietario: "Marcos Tavares", observacoes: "Contraproposta enviada, aguardando" },
  { id: "13", endereco: "R. Maria Fagnani, 306", codigo: "047.097.026-1", preco: 1750000, area: 230, tipo: "Casa", cash: 1200000, permutaFisica: 350000, permutaFinanceira: 200000, propostaMAC: 1600000, situacao: "Em contato", proprietario: "Patricia Ramos", observacoes: "Primeiro contato realizado por WhatsApp" },
];

export function getProperties(): Property[] {
  const stored = localStorage.getItem(STORAGE_KEY);
  if (stored) {
    try { return JSON.parse(stored); } catch { /* ignore */ }
  }
  return defaultProperties;
}

export function saveProperties(props: Property[]) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(props));
}

export { defaultProperties };
