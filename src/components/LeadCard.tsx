import { Phone, Mail, MessageCircle } from 'lucide-react';
import type { Lead } from '../data/types';
import { stageLabels, stageColors, fonteEmojis } from '../data/leads';

interface Props {
  lead: Lead;
}

export default function LeadCard({ lead }: Props) {
  const initials = lead.nome.split(' ').map(n => n[0]).slice(0, 2).join('').toUpperCase();
  const scoreColor = lead.score >= 80 ? 'bg-emerald-500' : lead.score >= 60 ? 'bg-amber-500' : 'bg-red-500';
  const stageClass = stageColors[lead.estagio] || 'bg-gray-500/15 text-gray-400';
  const stageName = stageLabels[lead.estagio] || lead.estagio;
  const emoji = fonteEmojis[lead.fonte] || '📌';

  const whatsappLink = `https://wa.me/55${lead.telefone.replace(/\D/g, '')}`;
  const emailLink = `mailto:${lead.email}`;
  const phoneLink = `tel:${lead.telefone.replace(/\D/g, '')}`;

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5 hover:shadow-md transition-shadow">
      {/* Header */}
      <div className="flex items-center gap-3 mb-3">
        <div className="w-11 h-11 rounded-full bg-gradient-to-br from-slate-700 to-slate-900 flex items-center justify-center text-white font-bold text-sm">
          {initials}
        </div>
        <div className="flex-1 min-w-0">
          <h3 className="font-bold text-gray-800 truncate">{lead.nome}</h3>
          <span className="text-[11px] text-gray-400">{emoji} {lead.fonte} · Último contato: {lead.ultimoContato}</span>
        </div>
        <span className={`px-2.5 py-1 rounded-full text-[11px] font-semibold ${stageClass}`}>
          {stageName}
        </span>
      </div>

      {/* Interesse */}
      <p className="text-sm text-gray-600 mb-3 line-clamp-2">{lead.interesse}</p>

      {/* Score bar */}
      <div className="mb-3">
        <div className="flex items-center justify-between mb-1">
          <span className="text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Score</span>
          <span className="text-xs font-bold text-gray-700">{lead.score}/100</span>
        </div>
        <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
          <div className={`h-full rounded-full transition-all ${scoreColor}`} style={{ width: `${lead.score}%` }} />
        </div>
      </div>

      {/* Contact buttons */}
      <div className="flex gap-2 border-t border-gray-100 pt-3">
        <a href={phoneLink} className="flex-1 flex items-center justify-center gap-1.5 py-2 px-3 bg-blue-50 text-blue-600 rounded-lg text-xs font-semibold hover:bg-blue-100 transition-colors">
          <Phone className="w-3.5 h-3.5" /> Ligar
        </a>
        <a href={emailLink} className="flex-1 flex items-center justify-center gap-1.5 py-2 px-3 bg-purple-50 text-purple-600 rounded-lg text-xs font-semibold hover:bg-purple-100 transition-colors">
          <Mail className="w-3.5 h-3.5" /> Email
        </a>
        <a href={whatsappLink} target="_blank" rel="noopener noreferrer" className="flex-1 flex items-center justify-center gap-1.5 py-2 px-3 bg-emerald-50 text-emerald-600 rounded-lg text-xs font-semibold hover:bg-emerald-100 transition-colors">
          <MessageCircle className="w-3.5 h-3.5" /> WhatsApp
        </a>
      </div>
    </div>
  );
}
