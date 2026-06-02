export interface Property {
  id: string;
  lotId: string;
  code: string;
  title: string;
  address: string;
  neighborhood: string;
  city: string;
  price: number;
  area: number;
  type: string;
  status: string;
  formaPgto: string;
  propostaMAC: string;
  cash: number;
  permutaFisica: number;
  permutaFin: number;
  owner: { name: string; action: string };
}

export const properties: Property[] = [
  {
    id: '1', lotId: 'lot-f0088', code: '047.097.0088-5',
    title: 'Rua Maria Fagnani, 101', address: 'Rua Maria Fagnani, 101',
    neighborhood: 'Cid. Patriarca', city: 'São Paulo',
    price: 3_000_000, area: 150, type: 'casa',
    status: 'Em Negociação', formaPgto: 'Estuda % permuta',
    propostaMAC: 'R$ 450.000,00 Cash + 80m² residencial (R$ 1.040.000,00) = R$ 1.490.000,00',
    cash: 450_000, permutaFisica: 1_040_000, permutaFin: 0,
    owner: { name: 'DANILO', action: 'Contato realizado' },
  },
  {
    id: '2', lotId: 'lot-f0173', code: '047.097.0173-3',
    title: 'Rua Maria Fagnani, 121', address: 'Rua Maria Fagnani, 121',
    neighborhood: 'Cid. Patriarca', city: 'São Paulo',
    price: 3_000_000, area: 300, type: 'terreno',
    status: 'Em Negociação', formaPgto: '100% permuta finan.',
    propostaMAC: 'R$ 400.000,00 Cash + 125m² residencial (R$ 1.625.000,00) = R$ 2.025.000,00',
    cash: 400_000, permutaFisica: 1_625_000, permutaFin: 0,
    owner: { name: 'ROGERIO', action: 'Contato realizado' },
  },
  {
    id: '3', lotId: 'lot-f0089', code: '047.097.0089-3',
    title: 'Rua Maria Fagnani, 113', address: 'Rua Maria Fagnani, 113',
    neighborhood: 'Cid. Patriarca', city: 'São Paulo',
    price: 2_000_000, area: 160, type: 'casa',
    status: 'Em Negociação', formaPgto: '50% permuta aprox',
    propostaMAC: 'R$ 450.000,00 Cash + 80m² residencial (R$ 1.040.000,00) = R$ 1.490.000,00',
    cash: 450_000, permutaFisica: 1_040_000, permutaFin: 0,
    owner: { name: 'DANILO', action: 'Contato realizado' },
  },
  {
    id: '4', lotId: 'lot-f0172', code: '047.097.0172-5',
    title: 'Rua Maria Fagnani, 91', address: 'Rua Maria Fagnani, 91',
    neighborhood: 'Cid. Patriarca', city: 'São Paulo',
    price: 3_000_000, area: 300, type: 'casa',
    status: 'Em Negociação', formaPgto: 'Estuda % permuta',
    propostaMAC: 'R$ 500.000,00 + 155m² residencial (R$ 2.015.000,00) = R$ 2.515.000,00',
    cash: 500_000, permutaFisica: 2_015_000, permutaFin: 0,
    owner: { name: '?', action: 'Contato realizado' },
  },
  {
    id: '5', lotId: 'lot-f0090', code: '047.097.0090-7',
    title: 'Rua Maria Fagnani, 117', address: 'Rua Maria Fagnani, 117',
    neighborhood: 'Cid. Patriarca', city: 'São Paulo',
    price: 2_000_000, area: 170, type: 'casa',
    status: 'Em Negociação', formaPgto: 'Estuda % permuta',
    propostaMAC: 'R$ 450.000,00 Cash + 80m² residencial (R$ 1.040.000,00) = R$ 1.490.000,00',
    cash: 450_000, permutaFisica: 1_040_000, permutaFin: 0,
    owner: { name: 'DANILO', action: 'Contato realizado' },
  },
  {
    id: '6', lotId: 'lot-f0086', code: '047.097.0086-9',
    title: 'Rua Maria Fagnani, 85', address: 'Rua Maria Fagnani, 85',
    neighborhood: 'Cid. Patriarca', city: 'São Paulo',
    price: 1_800_000, area: 300, type: 'casa',
    status: 'Em Negociação', formaPgto: '100% permuta finan.',
    propostaMAC: 'R$ 400.000,00 Cash + 125m² residencial (R$ 1.625.000,00) = R$ 2.025.000,00',
    cash: 400_000, permutaFisica: 1_625_000, permutaFin: 0,
    owner: { name: 'ROGERIO', action: 'Contato realizado' },
  },
  {
    id: '7', lotId: 'lot-f0079', code: '047.097.0079-6',
    title: 'R. Aprígio Gonzaga, 342', address: 'R. Aprígio Gonzaga, 342',
    neighborhood: 'Cid. Patriarca', city: 'São Paulo',
    price: 1_800_000, area: 300, type: 'terreno',
    status: 'Sem Contato', formaPgto: '100% permuta finan.',
    propostaMAC: 'R$ 500.000,00 + 155m² residencial (R$ 2.015.000,00) = R$ 2.515.000,00',
    cash: 500_000, permutaFisica: 2_015_000, permutaFin: 0,
    owner: { name: 'ROGERIO', action: 'Informações Vizinho' },
  },
  {
    id: '8', lotId: 'lot-f0080', code: '047.097.0080-1',
    title: 'R. Aprígio Gonzaga, 330', address: 'R. Aprígio Gonzaga, 330',
    neighborhood: 'Cid. Patriarca', city: 'São Paulo',
    price: 2_500_000, area: 300, type: 'terreno',
    status: 'Sem Contato', formaPgto: 'Estuda % permuta',
    propostaMAC: 'R$ 500.000,00 + 155m² residencial (R$ 2.015.000,00) = R$ 2.515.000,00',
    cash: 500_000, permutaFisica: 2_015_000, permutaFin: 0,
    owner: { name: '?', action: 'Informações Vizinho' },
  },
  {
    id: '9', lotId: 'lot-f0081', code: '047.097.0081-0',
    title: 'R. Aprígio Gonzaga, 318', address: 'R. Aprígio Gonzaga, 318',
    neighborhood: 'Cid. Patriarca', city: 'São Paulo',
    price: 2_800_000, area: 300, type: 'terreno',
    status: 'Sem Contato', formaPgto: 'Estuda permuta parcial',
    propostaMAC: 'R$ 500.000,00 Cash + 125m² residencial (R$ 1.625.000,00) = R$ 2.125.000,00',
    cash: 500_000, permutaFisica: 1_625_000, permutaFin: 0,
    owner: { name: 'MARCOS', action: 'Vizinho sem telefone' },
  },
  {
    id: '10', lotId: 'lot-f0019', code: '047.097.0283-1',
    title: 'R. Aprígio Gonzaga, 344', address: 'R. Aprígio Gonzaga, 344',
    neighborhood: 'Cid. Patriarca', city: 'São Paulo',
    price: 3_000_000, area: 300, type: 'terreno',
    status: 'Sem Contato', formaPgto: 'Aceita composição flexível',
    propostaMAC: 'R$ 450.000,00 Cash + 125m² residencial (R$ 1.625.000,00) = R$ 2.075.000,00',
    cash: 450_000, permutaFisica: 1_625_000, permutaFin: 0,
    owner: { name: '?', action: 'Sem dados cadastrais' },
  },
  {
    id: '11', lotId: 'lot-f0071a', code: '047.097.0077-0',
    title: 'R. Aprígio Gonzaga, 358', address: 'R. Aprígio Gonzaga, 358',
    neighborhood: 'Cid. Patriarca', city: 'São Paulo',
    price: 2_700_000, area: 300, type: 'terreno',
    status: 'Em Negociação', formaPgto: 'Permuta com entrada reduzida',
    propostaMAC: 'R$ 450.000,00 Cash + 125m² residencial (R$ 1.625.000,00) = R$ 2.075.000,00',
    cash: 450_000, permutaFisica: 1_625_000, permutaFin: 0,
    owner: { name: 'DANILO', action: 'Contato em andamento' },
  },
  {
    id: '12', lotId: 'lot-f0076', code: '047.097.0076-1',
    title: 'R. Aprígio Gonzaga, 368', address: 'R. Aprígio Gonzaga, 368',
    neighborhood: 'Cid. Patriarca', city: 'São Paulo',
    price: 2_500_000, area: 300, type: 'terreno',
    status: 'Em Negociação', formaPgto: 'Permuta e caixa',
    propostaMAC: 'R$ 500.000,00 Cash + 125m² residencial (R$ 1.625.000,00) = R$ 2.125.000,00',
    cash: 500_000, permutaFisica: 1_625_000, permutaFin: 0,
    owner: { name: 'ROGERIO', action: 'Proprietário receptivo' },
  },
  {
    id: '13', lotId: 'lot-f0075', code: '047.097.0075-3',
    title: 'R. Aprígio Gonzaga, 378', address: 'R. Aprígio Gonzaga, 378',
    neighborhood: 'Cid. Patriarca', city: 'São Paulo',
    price: 3_000_000, area: 150, type: 'terreno',
    status: 'Em Negociação', formaPgto: 'Composição financeira flexível',
    propostaMAC: 'R$ 500.000,00 Cash + 125m² residencial (R$ 1.625.000,00) = R$ 2.125.000,00',
    cash: 500_000, permutaFisica: 1_625_000, permutaFin: 0,
    owner: { name: 'DANILO', action: 'Retorno aguardado' },
  },
];