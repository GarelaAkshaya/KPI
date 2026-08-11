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
  buttonText = "Open Module",
  buttonBg = "bg-[#2563EB] hover:bg-[#1D4ED8]",
}) {
  return (
    <div
      onClick={onClick}
      className="group relative overflow-hidden rounded-3xl p-6 sm:p-7 bg-[#FFFFFF] border border-[#E2E8F0] shadow-sm hover:shadow-xl hover:border-[#2563EB]/30 transition-all duration-300 transform hover:-translate-y-1.5 cursor-pointer flex flex-col justify-between"
    >
      {/* Background Subtle Gradient Glow */}
      <div
        className="absolute -top-24 -right-24 w-60 h-60 rounded-full bg-gradient-to-br from-[#DBEAFE]/50 to-[#EFF6FF]/20 opacity-0 group-hover:opacity-100 blur-3xl transition-opacity duration-500 pointer-events-none"
      />

      <div>
        {/* Header Icon */}
        <div className="flex items-center justify-between mb-5">
          <div
            className={`w-14 h-14 rounded-2xl ${iconBg} border ${iconBorder} ${iconShadow} flex items-center justify-center group-hover:scale-105 transition-transform duration-300`}
          >
            <Icon className={`w-7 h-7 ${iconColor} group-hover:rotate-3 transition-transform duration-300`} />
          </div>

          {badgeText && (
            <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-semibold bg-[#F8FAFC] text-[#64748B] border border-[#E2E8F0] shadow-2xs">
              <Sparkles className="w-3 h-3 text-[#F59E0B]" />
              {badgeText}
            </span>
          )}
        </div>

        {/* Title & Description */}
        <h3 className="text-lg font-extrabold text-[#1E293B] group-hover:text-[#2563EB] mb-2.5 tracking-tight transition-colors">
          {title}
        </h3>
        <p className="text-[#64748B] text-xs sm:text-sm leading-relaxed mb-6">
          {description}
        </p>
      </div>

      {/* Primary Action Button */}
      <div className="pt-2">
        <button
          type="button"
          className={`w-full py-3 px-4 rounded-xl text-white font-semibold text-xs sm:text-sm shadow-md transition-all duration-300 flex items-center justify-between group-hover:shadow-lg ${buttonBg}`}
        >
          <span>{buttonText}</span>
          <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
        </button>
      </div>
    </div>
  );
}
