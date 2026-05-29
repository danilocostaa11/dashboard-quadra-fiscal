export interface Lot {
  id: string; lote: string; numero: string; status: string;
  x: number; y: number; width: number; height: number;
  propertyId?: string; rotation?: number;
}
export interface Property {
  id: string; endereco: string; codigo: string; preco: number; area: number;
  tipo: string; cash: number; permutaFisica: number; permutaFinanceira: number;
  propostaMAC: number; situacao: string; proprietario: string; observacoes: string;
}
export interface Lead {
  id: string; nome: string; email: string; telefone: string;
  interesse: string; fonte: string; estagio: string;
  score: number; ultimoContato: string;
}
export interface PipelineStage {
  name: string; count: number; valor: number; color: string;
}
export type LotStatus = 'fechado' | 'negociando' | 'nao-vende' | 'sem-contato' | 'sem-dados';
