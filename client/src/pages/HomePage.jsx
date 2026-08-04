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
      badgeText: "Data Management",
      targetRoute: "/upload-students",
      iconBg: "bg-[#2563EB]/10",
      iconBorder: "border-[#2563EB]/30",
      iconColor: "text-[#2563EB]",
      iconShadow: "shadow-md shadow-[#2563EB]/20",
    },
    {
      title: "Upload Faculty Data",
      description: "Manage faculty profiles, research outputs, qualification ratios, and academic workload metrics.",
      icon: UserCheck,
      badgeText: "Academic Ops",
      iconBg: "bg-[#9333EA]/10",
      iconBorder: "border-[#9333EA]/30",
      iconColor: "text-[#9333EA]",
      iconShadow: "shadow-md shadow-[#9333EA]/20",
    },
    {
      title: "Upload Department Data",
      description: "Configure department structures, course mappings, resource allocations, and institutional key parameters.",
      icon: Building2,
      badgeText: "Infrastructure",
      iconBg: "bg-[#10B981]/10",
      iconBorder: "border-[#10B981]/30",
      iconColor: "text-[#10B981]",
      iconShadow: "shadow-md shadow-[#10B981]/20",
    },
    {
      title: "KPI Dashboard",
      description: "Interactive analytics engine to visualize, filter, and review institutional performance indicators across academic years.",
      icon: LineChart,
      badgeText: "Analytics Portal",
      targetRoute: "/dashboard",
      iconBg: "bg-[#F59E0B]/10",
      iconBorder: "border-[#F59E0B]/30",
      iconColor: "text-[#F59E0B]",
      iconShadow: "shadow-md shadow-[#F59E0B]/20",
    },
  ];

  return (
    <div className="min-h-screen bg-[#F8FAFC] text-[#1E293B] flex flex-col">
      {/* Header Navigation */}
      <Navbar />

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12">
        
        {/* Administrator Welcome Banner */}
        <section className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-[#FFFFFF] via-[#EFF6FF] to-[#FFFFFF] border border-[#E2E8F0] p-8 sm:p-10 mb-10 shadow-sm">
          <div className="absolute top-0 right-0 -mt-10 -mr-10 w-96 h-96 bg-[#2563EB]/10 rounded-full blur-3xl pointer-events-none" />
          <div className="absolute bottom-0 left-1/3 -mb-10 w-72 h-72 bg-[#DBEAFE]/40 rounded-full blur-3xl pointer-events-none" />

          <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
            <div>
              <div className="flex items-center gap-2 mb-3">
                <span className="px-3 py-1 rounded-full bg-[#DBEAFE] border border-[#2563EB]/20 text-[#2563EB] text-xs font-bold uppercase tracking-widest flex items-center gap-1.5">
                  <Shield className="w-3.5 h-3.5 text-[#2563EB]" />
                  Authenticated Session
                </span>
                <span className="text-xs text-[#64748B]">• Institutional System</span>
              </div>
              <h1 className="text-3xl sm:text-4xl font-extrabold text-[#1E293B] tracking-tight">
                IFHE KPI
              </h1>
              <p className="text-xl sm:text-2xl font-bold text-[#2563EB] mt-1">
                Welcome Administrator
              </p>
              <p className="text-[#64748B] text-sm max-w-2xl mt-2 leading-relaxed">
                Select an operational task below to upload data metrics or navigate straight to the analytics visualization dashboard.
              </p>
            </div>

            {/* Metric pill */}
            <div className="flex items-center gap-4 bg-[#FFFFFF] border border-[#E2E8F0] p-4 rounded-2xl self-start md:self-auto shadow-sm">
              <div className="w-12 h-12 rounded-xl bg-[#EFF6FF] flex items-center justify-center text-[#2563EB]">
                <LayoutDashboard className="w-6 h-6" />
              </div>
              <div>
                <p className="text-xs font-semibold text-[#64748B] uppercase tracking-wider">Active Workspace</p>
                <p className="text-sm font-bold text-[#1E293B]">Main Administrative Desk</p>
              </div>
            </div>
          </div>
        </section>

        {/* 4 Large Dashboard Cards Grid */}
        <section className="space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-extrabold text-[#1E293B] tracking-wide flex items-center gap-2">
              <span>Primary Operational Modules</span>
            </h2>
            <span className="text-xs text-[#64748B]">4 Core Tools Available</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 sm:gap-8">
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
                onClick={() => handleCardClick(module.title, module.targetRoute)}
              />
            ))}
          </div>
        </section>

      </main>

      {/* Footer */}
      <footer className="bg-[#FFFFFF] border-t border-[#E2E8F0] py-6 mt-12 text-center text-xs text-[#64748B]">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-4">
          <p>© IFHE KPI - Institutional KPI Monitoring System. All rights reserved.</p>
          <div className="flex items-center gap-4 text-[#64748B]">
            <span>System Status: <strong className="text-[#10B981] font-semibold">Online</strong></span>
            <span>|</span>
            <span>Role: <strong className="text-[#1E293B] font-semibold">Administrator</strong></span>
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
