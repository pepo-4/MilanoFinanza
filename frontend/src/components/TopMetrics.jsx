import React from 'react';
import {
  TrendingUp,
  Zap,
  ShieldAlert,
  BarChart2,
  ArrowUpRight,
  ArrowDownRight,
  Minus
} from 'lucide-react';

export default function TopMetrics({ metrics }) {
  const categories = [
    {
      key: 'keyData',
      title: metrics.keyData.title,
      icon: BarChart2,
      iconColor: 'text-trade-accent',
      borderColor: 'border-blue-500/20',
      data: metrics.keyData.items
    },
    {
      key: 'momentum',
      title: metrics.momentum.title,
      icon: Zap,
      iconColor: 'text-amber-400',
      borderColor: 'border-amber-500/20',
      data: metrics.momentum.items
    },
    {
      key: 'strength',
      title: metrics.strength.title,
      icon: TrendingUp,
      iconColor: 'text-emerald-400',
      borderColor: 'border-emerald-500/20',
      data: metrics.strength.items
    },
    {
      key: 'uncertainty',
      title: metrics.uncertainty.title,
      icon: ShieldAlert,
      iconColor: 'text-purple-400',
      borderColor: 'border-purple-500/20',
      data: metrics.uncertainty.items
    }
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 h-full">
      {categories.map((cat) => {
        const IconComponent = cat.icon;
        return (
          <div
            key={cat.key}
            className={`bg-dark-800/90 border border-dark-700/80 rounded-xl p-4 flex flex-col justify-between hover:border-dark-600 transition-all shadow-lg backdrop-blur-sm`}
          >
            {/* Header Categoria */}
            <div className="flex items-center justify-between pb-3 border-b border-dark-700/60 mb-3">
              <div className="flex items-center gap-2">
                <div className="p-1.5 rounded-lg bg-dark-900/80 border border-dark-700/50">
                  <IconComponent size={16} className={cat.iconColor} />
                </div>
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-200">
                  {cat.title}
                </h3>
              </div>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-dark-900 text-slate-400 border border-dark-700">
                LIVE
              </span>
            </div>

            {/* Lista Widget/Tabelle */}
            <div className="space-y-2.5">
              {cat.data.map((item, idx) => (
                <div
                  key={idx}
                  className="flex items-center justify-between text-xs py-1 px-1.5 rounded hover:bg-dark-750/50 transition-colors"
                >
                  <div className="flex flex-col">
                    <span className="text-slate-400 font-medium text-[11px]">{item.label}</span>
                    <span className="text-[10px] text-slate-500 font-mono">{item.sub}</span>
                  </div>

                  <div className="flex items-center gap-1.5 text-right">
                    <span className="font-mono font-semibold text-slate-100 text-xs">
                      {item.value}
                    </span>
                    {item.status === 'up' && (
                      <ArrowUpRight size={13} className="text-trade-up" />
                    )}
                    {item.status === 'down' && (
                      <ArrowDownRight size={13} className="text-trade-down" />
                    )}
                    {item.status === 'neutral' && (
                      <Minus size={11} className="text-slate-500" />
                    )}
                  </div>
                </div>
              ))}
            </div>

            {/* Mini barra di indicatore se presente level */}
            {cat.data[0]?.level !== undefined && (
              <div className="mt-3 pt-2 border-t border-dark-700/40">
                <div className="flex justify-between text-[10px] text-slate-400 mb-1 font-mono">
                  <span>Intensità Indicatore</span>
                  <span className="text-slate-200 font-semibold">{cat.data[0].level}%</span>
                </div>
                <div className="w-full h-1.5 bg-dark-900 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full ${
                      cat.data[0].level > 70
                        ? 'bg-gradient-to-r from-emerald-500 to-trade-up'
                        : cat.data[0].level > 40
                        ? 'bg-gradient-to-r from-blue-500 to-trade-accent'
                        : 'bg-gradient-to-r from-purple-500 to-indigo-500'
                    }`}
                    style={{ width: `${Math.min(cat.data[0].level, 100)}%` }}
                  />
                </div>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
