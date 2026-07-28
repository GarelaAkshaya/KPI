import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Navbar from '../components/Navbar';
import DashboardCard from '../components/DashboardCard';
import ComingSoonModal from '../components/ComingSoonModal';
import { Users, UserCheck, Building2, LineChart, Shield, LayoutDashboard } from 'lucide-react';

export default function HomePage() {
  const navigate = useNavigate();
  const [modalState, setModalState] = useState({ isOpen: false, featureName: '' });

  const handleCardClick = (featureName, targetRoute) => {
    if (targetRoute) {
      navigate(targetRoute);
    } else {
      setModalState({ isOpen: true, featureName });
    }
  };

  const dashboardModules = [
    {
      title: "Upload Student Data",
      description: "Import, parse, and synchronize comprehensive student records, enrollment metrics, and performance metrics.",
      icon: Users,
      gradient: "from-blue-600 to-indigo-600",
      accentColor: "indigo-500",
      badgeText: "Data Management",
      targetRoute: "/upload-students",
    },
    {
      title: "Upload Faculty Data",
      description: "Manage faculty profiles, research outputs, qualification ratios, and academic workload metrics.",
      icon: UserCheck,
      gradient: "from-purple-600 to-pink-600",
      accentColor: "purple-500",
      badgeText: "Academic Ops",
    },
    {
      title: "Upload Department Data",
      description: "Configure department structures, course mappings, resource allocations, and institutional key parameters.",
      icon: Building2,
      gradient: "from-emerald-600 to-teal-600",
      accentColor: "emerald-500",
      badgeText: "Infrastructure",
    },
    {
      title: "KPI Dashboard",
      description: "Interactive analytics engine to visualize, filter, and review institutional performance indicators across academic years.",
      icon: LineChart,
      gradient: "from-amber-500 via-orange-600 to-red-600",
      accentColor: "amber-500",
      badgeText: "Analytics Portal",
      targetRoute: "/dashboard",
    },
  ];

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      {/* Header Navigation */}
      <Navbar />

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12">
        
        {/* Administrator Welcome Banner */}
        <section className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-slate-900 via-indigo-950/70 to-slate-900 border border-slate-800 p-8 sm:p-10 mb-10 shadow-2xl">
          <div className="absolute top-0 right-0 -mt-10 -mr-10 w-96 h-96 bg-indigo-600/10 rounded-full blur-3xl pointer-events-none" />
          <div className="absolute bottom-0 left-1/3 -mb-10 w-72 h-72 bg-purple-600/10 rounded-full blur-3xl pointer-events-none" />

          <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
            <div>
              <div className="flex items-center gap-2 mb-3">
                <span className="px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-xs font-bold uppercase tracking-widest flex items-center gap-1.5">
                  <Shield className="w-3.5 h-3.5" />
                  Authenticated Session
                </span>
                <span className="text-xs text-slate-400">• Institutional System</span>
              </div>
              <h1 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
                IFHE KPI
              </h1>
              <p className="text-xl sm:text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-indigo-300 via-purple-300 to-pink-300 mt-1">
                Welcome Administrator
              </p>
              <p className="text-slate-400 text-sm max-w-2xl mt-2 leading-relaxed">
                Select an operational task below to upload data metrics or navigate straight to the analytics visualization dashboard.
              </p>
            </div>

            {/* Metric pill */}
            <div className="flex items-center gap-4 bg-slate-950/70 border border-slate-800 p-4 rounded-2xl self-start md:self-auto shadow-inner">
              <div className="w-12 h-12 rounded-xl bg-indigo-500/10 flex items-center justify-center text-indigo-400">
                <LayoutDashboard className="w-6 h-6" />
              </div>
              <div>
                <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Active Workspace</p>
                <p className="text-sm font-bold text-slate-200">Main Administrative Desk</p>
              </div>
            </div>
          </div>
        </section>

        {/* 4 Large Dashboard Cards Grid */}
        <section className="space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-extrabold text-white tracking-wide flex items-center gap-2">
              <span>Primary Operational Modules</span>
            </h2>
            <span className="text-xs text-slate-400">4 Core Tools Available</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 sm:gap-8">
            {dashboardModules.map((module, index) => (
              <DashboardCard
                key={index}
                title={module.title}
                description={module.description}
                icon={module.icon}
                gradient={module.gradient}
                accentColor={module.accentColor}
                badgeText={module.badgeText}
                onClick={() => handleCardClick(module.title, module.targetRoute)}
              />
            ))}
          </div>
        </section>

      </main>

      {/* Footer */}
      <footer className="bg-slate-900/50 border-t border-slate-800/80 py-6 mt-12 text-center text-xs text-slate-400">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-4">
          <p>© IFHE KPI - Institutional KPI Monitoring System. All rights reserved.</p>
          <div className="flex items-center gap-4 text-slate-400">
            <span>System Status: <strong className="text-emerald-400 font-semibold">Online</strong></span>
            <span>|</span>
            <span>Role: <strong className="text-slate-300 font-semibold">Administrator</strong></span>
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
