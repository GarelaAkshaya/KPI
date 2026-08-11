import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Navbar from '../components/Navbar';
import DashboardCard from '../components/DashboardCard';
import ComingSoonModal from '../components/ComingSoonModal';
import { Users, UserCheck, Building2, LineChart, GraduationCap, Quote, ArrowUpRight, CheckCircle2 } from 'lucide-react';

export default function HomePage() {
  const navigate = useNavigate();
  const [modalState, setModalState] = useState({ isOpen: false, featureName: '' });

  const [stats, setStats] = useState({
    totalStudents: 12458,
    totalFaculty: 612,
    totalDepartments: 28,
    activeKPIs: 15,
    isLive: false,
  });

  useEffect(() => {
    async function fetchStats() {
      try {
        const res = await fetch('http://localhost:5000/api/stats');
        if (res.ok) {
          const data = await res.json();
          setStats(data);
        }
      } catch (e) {
        console.warn('Backend API offline or unreachable, using default DB baseline values.', e);
      }
    }
    fetchStats();
  }, []);

  const handleCardClick = (featureName, targetRoute) => {
    if (targetRoute) {
      navigate(targetRoute);
    } else {
      setModalState({ isOpen: true, featureName });
    }
  };

  const summaryCards = [
    {
      title: "Total Students",
      value: stats.totalStudents ? stats.totalStudents.toLocaleString() : "12,458",
      change: "↑ 8.2% from last year",
      icon: GraduationCap,
      iconBg: "bg-[#EFF6FF] text-[#2563EB]",
      badgeColor: "text-[#10B981]",
    },
    {
      title: "Total Faculty",
      value: stats.totalFaculty ? stats.totalFaculty.toLocaleString() : "612",
      change: "↑ 5.6% from last year",
      icon: UserCheck,
      iconBg: "bg-[#F3E8FF] text-[#9333EA]",
      badgeColor: "text-[#10B981]",
    },
    {
      title: "Departments",
      value: stats.totalDepartments ? stats.totalDepartments.toString() : "28",
      change: "No change",
      icon: Building2,
      iconBg: "bg-[#ECFDF5] text-[#059669]",
      badgeColor: "text-[#64748B]",
    },
    {
      title: "Active KPIs",
      value: stats.activeKPIs ? stats.activeKPIs.toString() : "15",
      change: "↑ 2 new this month",
      icon: LineChart,
      iconBg: "bg-[#FFFBEB] text-[#D97706]",
      badgeColor: "text-[#10B981]",
    },
  ];

  const dashboardModules = [
    {
      title: "Upload Student Data",
      description: "Import and manage student records, enrollment metrics, academic performance, and other related data.",
      icon: GraduationCap,
      badgeText: "Data Management",
      targetRoute: "/upload-students",
      iconBg: "bg-[#2563EB]/10",
      iconBorder: "border-[#2563EB]/30",
      iconColor: "text-[#2563EB]",
      iconShadow: "shadow-md shadow-[#2563EB]/20",
      buttonText: "Open Module",
      buttonBg: "bg-[#2563EB] hover:bg-[#1D4ED8]",
    },
    {
      title: "Upload Faculty Data",
      description: "Manage faculty profiles, research outputs, qualifications, workload, and performance metrics.",
      icon: UserCheck,
      badgeText: "Academic Ops",
      targetRoute: "/faculty",
      iconBg: "bg-[#9333EA]/10",
      iconBorder: "border-[#9333EA]/30",
      iconColor: "text-[#9333EA]",
      iconShadow: "shadow-md shadow-[#9333EA]/20",
      buttonText: "Open Module",
      buttonBg: "bg-[#9333EA] hover:bg-[#7E22CE]",
    },
    {
      title: "Upload Department Data",
      description: "Configure department structures, course mappings, resource allocations, and institutional parameters.",
      icon: Building2,
      badgeText: "Infrastructure",
      iconBg: "bg-[#10B981]/10",
      iconBorder: "border-[#10B981]/30",
      iconColor: "text-[#10B981]",
      iconShadow: "shadow-md shadow-[#10B981]/20",
      buttonText: "Open Module",
      buttonBg: "bg-[#059669] hover:bg-[#047857]",
    },
    {
      title: "KPI Dashboard",
      description: "View and analyze key performance indicators across academic years with interactive visualizations.",
      icon: LineChart,
      badgeText: "Analytics Portal",
      targetRoute: "/dashboard",
      iconBg: "bg-[#F59E0B]/10",
      iconBorder: "border-[#F59E0B]/30",
      iconColor: "text-[#F59E0B]",
      iconShadow: "shadow-md shadow-[#F59E0B]/20",
      buttonText: "Open Dashboard",
      buttonBg: "bg-[#EA580C] hover:bg-[#C2410C]",
    },
  ];

  return (
    <div className="min-h-screen bg-[#F8FAFC] text-[#1E293B] flex flex-col font-sans">
      {/* Header Navigation */}
      <Navbar />

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8 sm:space-y-10">
        
        {/* Administrator Welcome Banner with Campus Overlay */}
        <section className="relative overflow-hidden rounded-3xl shadow-xl border border-slate-700/30">
          {/* Background Image Layer */}
          <div 
            className="absolute inset-0 bg-cover bg-center filter brightness-[0.45] contrast-[1.1] transform scale-105 transition-transform duration-1000"
            style={{ backgroundImage: "url('/campus_banner.png')" }}
          />
          
          {/* Rich Gradient Overlay */}
          <div className="absolute inset-0 bg-gradient-to-r from-[#0F172A]/90 via-[#1E3A8A]/85 to-[#0F172A]/90" />

          {/* Decorative Subtle Glowing Elements */}
          <div className="absolute -top-24 -right-24 w-96 h-96 bg-blue-500/20 rounded-full blur-3xl pointer-events-none" />
          <div className="absolute -bottom-24 -left-24 w-96 h-96 bg-indigo-500/20 rounded-full blur-3xl pointer-events-none" />

          {/* Banner Content Container */}
          <div className="relative z-10 p-8 sm:p-12 text-white flex flex-col lg:flex-row items-start lg:items-center justify-between gap-8">
            <div className="max-w-2xl">
              <div className="flex items-center gap-2 mb-3">
                <span className="px-3.5 py-1 rounded-full bg-blue-500/20 backdrop-blur-md border border-blue-400/30 text-blue-200 text-xs font-semibold tracking-wide flex items-center gap-1.5 shadow-sm">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                  Authenticated Session
                </span>
                <span className="text-xs text-slate-300 font-medium hidden sm:inline">• Institutional System</span>
              </div>

              <h1 className="text-3xl sm:text-5xl font-black text-white tracking-tight">
                Welcome back,
              </h1>
              <p className="text-2xl sm:text-4xl font-extrabold text-blue-300 mt-1 drop-shadow-sm">
                Administrator <span className="inline-block animate-bounce text-xl sm:text-3xl">👋</span>
              </p>
              
              <p className="text-slate-200 text-sm sm:text-base mt-4 leading-relaxed font-normal opacity-95">
                Monitor, analyze, and improve institutional performance through data-driven insights.
              </p>
            </div>

            {/* Glassmorphic Peter Drucker Quote Card */}
            <div className="w-full lg:w-auto min-w-[300px] max-w-md bg-white/10 backdrop-blur-md border border-white/20 p-6 rounded-2xl shadow-2xl relative group hover:bg-white/15 transition-all">
              <Quote className="w-8 h-8 text-blue-300 opacity-60 mb-2 transform -rotate-18" />
              <blockquote className="text-white text-sm sm:text-base font-medium italic leading-snug">
                “What gets measured, gets improved.”
              </blockquote>
              <p className="text-right text-xs font-bold uppercase tracking-widest text-blue-200 mt-3">
                — Peter Drucker
              </p>
            </div>
          </div>
        </section>

        {/* 4 Dynamic Summary Cards Section */}
        <section className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-extrabold text-[#1E293B] tracking-tight flex items-center gap-2">
              <span>Institutional Highlights</span>
              {stats.isLive && (
                <span className="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-emerald-100 text-emerald-700 border border-emerald-300">
                  Live Database
                </span>
              )}
            </h2>
            <span className="text-xs font-semibold text-[#64748B]">Real-time Summary</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5 sm:gap-6">
            {summaryCards.map((card, idx) => {
              const Icon = card.icon;
              return (
                <div
                  key={idx}
                  className="bg-white border border-slate-200/80 rounded-2xl p-5 shadow-xs hover:shadow-md transition-all duration-300 flex flex-col justify-between group cursor-default"
                >
                  <div className="flex items-center justify-between mb-4">
                    <div className={`w-12 h-12 rounded-xl ${card.iconBg} flex items-center justify-center transition-transform group-hover:scale-105`}>
                      <Icon className="w-6 h-6" />
                    </div>
                    <ArrowUpRight className="w-4 h-4 text-slate-300 group-hover:text-slate-500 transition-colors" />
                  </div>

                  <div>
                    <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">
                      {card.title}
                    </p>
                    <h3 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
                      {card.value}
                    </h3>
                  </div>

                  <div className="mt-3 pt-3 border-t border-slate-100 flex items-center justify-between text-xs font-medium">
                    <span className={card.badgeColor}>{card.change}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </section>

        {/* Primary Operational Modules Grid Section */}
        <section className="space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1">
            <div>
              <h2 className="text-xl font-extrabold text-[#1E293B] tracking-tight">
                Primary Operational Modules
              </h2>
              <p className="text-xs text-[#64748B] mt-0.5">
                Select a module to manage institutional data and view analytics
              </p>
            </div>
            <span className="text-xs font-bold text-[#2563EB] bg-[#EFF6FF] px-3 py-1 rounded-full border border-[#DBEAFE] self-start sm:self-auto">
              4 Core Modules Ready
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {dashboardModules.map((module, index) => (
              <DashboardCard
                key={index}
                title={module.title}
                description={module.description}
                icon={module.icon}
                badgeText={module.badgeText}
                iconBg={module.iconBg}
                iconBorder={module.iconBorder}
                iconColor={module.iconColor}
                iconShadow={module.iconShadow}
                buttonText={module.buttonText}
                buttonBg={module.buttonBg}
                onClick={() => handleCardClick(module.title, module.targetRoute)}
              />
            ))}
          </div>
        </section>

      </main>

      {/* Footer */}
      <footer className="bg-[#FFFFFF] border-t border-[#E2E8F0] py-6 mt-12 text-center text-xs text-[#64748B]">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-4">
          <p>© 2025 IFHE KPI Portal. All rights reserved.</p>
          <div className="flex items-center gap-4 text-[#64748B]">
            <span>System Status: <strong className="text-[#10B981] font-semibold">Online</strong></span>
            <span>|</span>
            <span>Environment: <strong className="text-[#1E293B] font-semibold">Production</strong></span>
          </div>
        </div>
      </footer>

      {/* Coming Soon Modal */}
      <ComingSoonModal
        isOpen={modalState.isOpen}
        onClose={() => setModalState({ isOpen: false, featureName: '' })}
        featureName={modalState.featureName}
      />
    </div>
  );
}

