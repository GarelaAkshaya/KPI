import React from 'react';
import { ArrowRight, Sparkles } from 'lucide-react';

export default function DashboardCard({
  title,
  description,
  icon: Icon,
  gradient,
  accentColor,
  badgeText = "System Feature",
  onClick,
}) {
  return (
    <div
      onClick={onClick}
      className={`group relative overflow-hidden rounded-3xl p-7 bg-slate-900/90 border border-slate-800/80 shadow-xl shadow-slate-950/50 hover:shadow-2xl hover:shadow-${accentColor}/20 transition-all duration-300 transform hover:-translate-y-2 cursor-pointer flex flex-col justify-between`}
    >
      {/* Dynamic Background Mesh Gradient on Hover */}
      <div
        className={`absolute -top-24 -right-24 w-60 h-60 rounded-full bg-gradient-to-br ${gradient} opacity-15 group-hover:opacity-35 blur-3xl transition-opacity duration-500 pointer-events-none`}
      />

      <div>
        {/* Header & Icon */}
        <div className="flex items-center justify-between mb-6">
          <div
            className={`w-14 h-14 rounded-2xl bg-gradient-to-br ${gradient} p-0.5 shadow-lg shadow-indigo-500/10 group-hover:scale-110 transition-transform duration-300`}
          >
            <div className="w-full h-full bg-slate-950/80 backdrop-blur-sm rounded-[14px] flex items-center justify-center">
              <Icon className={`w-7 h-7 text-white group-hover:rotate-6 transition-transform duration-300`} />
            </div>
          </div>

          <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-semibold bg-slate-800/80 text-slate-300 border border-slate-700/60 shadow-inner">
            <Sparkles className="w-3 h-3 text-amber-400" />
            {badgeText}
          </span>
        </div>

        {/* Title & Description */}
        <h3 className="text-xl font-bold text-slate-100 group-hover:text-white mb-2 tracking-wide transition-colors">
          {title}
        </h3>
        <p className="text-slate-400 text-sm leading-relaxed mb-6">
          {description}
        </p>
      </div>

      {/* Action Footer Button */}
      <div className="pt-4 border-t border-slate-800/80 flex items-center justify-between">
        <span className="text-xs font-bold uppercase tracking-wider text-slate-400 group-hover:text-slate-200 transition-colors">
          Open Feature
        </span>
        <div className={`w-9 h-9 rounded-full bg-slate-800 group-hover:bg-gradient-to-r ${gradient} flex items-center justify-center text-slate-300 group-hover:text-white transition-all duration-300 shadow-md`}>
          <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
        </div>
      </div>
    </div>
  );
}
