import React from 'react';
import { ArrowRight, Sparkles } from 'lucide-react';

export default function DashboardCard({
  title,
  description,
  icon: Icon,
  badgeText = "System Feature",
  onClick,
  iconBg = "bg-[#2563EB]/10",
  iconBorder = "border-[#2563EB]/30",
  iconColor = "text-[#2563EB]",
  iconShadow = "shadow-md shadow-[#2563EB]/20",
}) {
  return (
    <div
      onClick={onClick}
      className="group relative overflow-hidden rounded-3xl p-7 bg-[#FFFFFF] border border-[#E2E8F0] shadow-sm hover:shadow-md hover:border-[#2563EB]/40 transition-all duration-300 transform hover:-translate-y-2 cursor-pointer flex flex-col justify-between"
    >
      {/* Dynamic Background Mesh Gradient on Hover */}
      <div
        className="absolute -top-24 -right-24 w-60 h-60 rounded-full bg-gradient-to-br from-[#DBEAFE] to-[#EFF6FF] opacity-40 group-hover:opacity-80 blur-3xl transition-opacity duration-500 pointer-events-none"
      />

      <div>
        {/* Header & Icon */}
        <div className="flex items-center justify-between mb-6">
          <div
            className={`w-14 h-14 rounded-2xl ${iconBg} border ${iconBorder} ${iconShadow} flex items-center justify-center group-hover:scale-110 transition-transform duration-300`}
          >
            <Icon className={`w-7 h-7 ${iconColor} group-hover:rotate-6 transition-transform duration-300`} />
          </div>

          <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-semibold bg-[#EFF6FF] text-[#2563EB] border border-[#DBEAFE] shadow-inner">
            <Sparkles className="w-3 h-3 text-[#F59E0B]" />
            {badgeText}
          </span>
        </div>

        {/* Title & Description */}
        <h3 className="text-xl font-bold text-[#1E293B] group-hover:text-[#2563EB] mb-2 tracking-wide transition-colors">
          {title}
        </h3>
        <p className="text-[#64748B] text-sm leading-relaxed mb-6">
          {description}
        </p>
      </div>

      {/* Action Footer Button */}
      <div className="pt-4 border-t border-[#E2E8F0] flex items-center justify-between">
        <span className="text-xs font-bold uppercase tracking-wider text-[#64748B] group-hover:text-[#2563EB] transition-colors">
          Open Feature
        </span>
        <div className="w-9 h-9 rounded-full bg-[#EFF6FF] text-[#2563EB] group-hover:bg-[#2563EB] group-hover:text-white flex items-center justify-center transition-all duration-300 shadow-sm">
          <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
        </div>
      </div>
    </div>
  );
}
