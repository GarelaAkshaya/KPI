import React, { useState } from 'react';
import Navbar from '../components/Navbar';
import { BarChart3, Calendar, Filter, AreaChart, PieChart, Layers, ArrowUpRight, Info } from 'lucide-react';

export default function KPIDashboardPage() {
  const [selectedKPI, setSelectedKPI] = useState('Student-Faculty Ratio');
  const [selectedAcademicYear, setSelectedAcademicYear] = useState('2024-25');

  const kpiOptions = [
    'Student-Faculty Ratio',
    'Pass Percentage',
  ];

  const yearOptions = [
    '2022-23',
    '2023-24',
    '2024-25',
    '2025-26',
  ];

  return (
    <div className="min-h-screen bg-[#F8FAFC] text-[#1E293B] flex flex-col">
      {/* Navbar Header */}
      <Navbar />

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12">
        
        {/* Page Title & Context Header */}
        <section className="mb-8">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-[#E2E8F0]">
            <div>
              <div className="flex items-center gap-2 mb-2">
                <span className="px-3 py-1 rounded-full bg-[#DBEAFE] text-[#2563EB] border border-[#2563EB]/20 text-xs font-bold uppercase tracking-wider flex items-center gap-1.5">
                  <BarChart3 className="w-3.5 h-3.5 text-[#2563EB]" />
                  Analytics Center
                </span>
                <span className="text-xs text-[#64748B]">• Institutional KPI Monitoring</span>
              </div>
              <h1 className="text-3xl sm:text-4xl font-extrabold text-[#1E293B] tracking-tight">
                IFHE KPI
              </h1>
              <p className="text-[#64748B] text-sm mt-1">
                Institutional Performance & Quality Benchmark Dashboard
              </p>
            </div>

            {/* Selected Active Filters Badge */}
            <div className="flex items-center gap-3 bg-[#FFFFFF] border border-[#E2E8F0] rounded-2xl p-3.5 shadow-sm">
              <div className="w-10 h-10 rounded-xl bg-[#2563EB] flex items-center justify-center text-white font-bold">
                <Filter className="w-5 h-5" />
              </div>
              <div className="text-xs">
                <p className="text-[#64748B] font-medium">Current View Filter</p>
                <p className="font-bold text-[#1E293B]">
                  {selectedKPI} <span className="text-[#2563EB]">({selectedAcademicYear})</span>
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* Dropdowns Control Panel */}
        <section className="mb-8">
          <div className="bg-[#FFFFFF] border border-[#E2E8F0] rounded-3xl p-6 sm:p-8 shadow-sm">
            <h2 className="text-base font-bold text-[#1E293B] mb-4 flex items-center gap-2">
              <Layers className="w-4 h-4 text-[#2563EB]" />
              <span>Select Indicator & Academic Session</span>
            </h2>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              
              {/* Dropdown 1: KPI */}
              <div className="space-y-2">
                <label htmlFor="kpi-select" className="block text-xs font-bold uppercase tracking-wider text-[#1E293B] flex items-center gap-2">
                  <BarChart3 className="w-4 h-4 text-[#2563EB]" />
                  KPI
                </label>
                <div className="relative">
                  <select
                    id="kpi-select"
                    value={selectedKPI}
                    onChange={(e) => setSelectedKPI(e.target.value)}
                    className="w-full appearance-none bg-[#F8FAFC] border border-[#E2E8F0] rounded-2xl px-4 py-3.5 pr-10 text-[#1E293B] text-sm font-semibold focus:outline-none focus:ring-2 focus:ring-[#2563EB]/40 focus:border-[#2563EB] focus:bg-[#FFFFFF] transition-all cursor-pointer shadow-inner"
                  >
                    {kpiOptions.map((option) => (
                      <option key={option} value={option} className="bg-white text-[#1E293B] py-2">
                        {option}
                      </option>
                    ))}
                  </select>
                  <div className="absolute inset-y-0 right-0 flex items-center px-4 pointer-events-none text-[#64748B]">
                    <svg className="w-4 h-4 fill-current" viewBox="0 0 20 20">
                      <path d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" />
                    </svg>
                  </div>
                </div>
              </div>

              {/* Dropdown 2: Academic Year */}
              <div className="space-y-2">
                <label htmlFor="year-select" className="block text-xs font-bold uppercase tracking-wider text-[#1E293B] flex items-center gap-2">
                  <Calendar className="w-4 h-4 text-[#2563EB]" />
                  Academic Year
                </label>
                <div className="relative">
                  <select
                    id="year-select"
                    value={selectedAcademicYear}
                    onChange={(e) => setSelectedAcademicYear(e.target.value)}
                    className="w-full appearance-none bg-[#F8FAFC] border border-[#E2E8F0] rounded-2xl px-4 py-3.5 pr-10 text-[#1E293B] text-sm font-semibold focus:outline-none focus:ring-2 focus:ring-[#2563EB]/40 focus:border-[#2563EB] focus:bg-[#FFFFFF] transition-all cursor-pointer shadow-inner"
                  >
                    {yearOptions.map((year) => (
                      <option key={year} value={year} className="bg-white text-[#1E293B] py-2">
                        {year}
                      </option>
                    ))}
                  </select>
                  <div className="absolute inset-y-0 right-0 flex items-center px-4 pointer-events-none text-[#64748B]">
                    <svg className="w-4 h-4 fill-current" viewBox="0 0 20 20">
                      <path d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" />
                    </svg>
                  </div>
                </div>
              </div>

            </div>
          </div>
        </section>

        {/* Large Graph Placeholder Section */}
        <section>
          <div className="relative overflow-hidden bg-[#FFFFFF] border border-[#E2E8F0] rounded-3xl p-8 sm:p-12 shadow-sm min-h-[420px] flex flex-col items-center justify-center text-center">
            
            {/* Background Decorative Chart Mesh / Wireframe */}
            <div className="absolute inset-0 opacity-20 pointer-events-none flex items-center justify-center">
              <svg className="w-full h-full text-[#2563EB]" viewBox="0 0 800 400" fill="none" stroke="currentColor">
                <path d="M 50 350 Q 200 200 350 280 T 650 100 T 750 150" strokeWidth="4" fill="none" />
                <path d="M 50 350 L 750 350" strokeWidth="2" strokeDasharray="6 6" />
                <path d="M 50 50 L 50 350" strokeWidth="2" strokeDasharray="6 6" />
                <circle cx="200" cy="200" r="8" fill="currentColor" />
                <circle cx="350" cy="280" r="8" fill="currentColor" />
                <circle cx="650" cy="100" r="8" fill="currentColor" />
              </svg>
            </div>

            {/* Dynamic Background Glow */}
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-[#DBEAFE]/40 rounded-full blur-3xl pointer-events-none" />

            {/* Central Content */}
            <div className="relative z-10 max-w-lg mx-auto flex flex-col items-center">
              
              {/* Graphic Badge */}
              <div className="w-20 h-20 rounded-3xl bg-gradient-to-tr from-[#2563EB] to-[#1D4ED8] p-1 shadow-lg shadow-blue-500/20 mb-6 transform hover:scale-105 transition-transform duration-300">
                <div className="w-full h-full bg-[#EFF6FF] rounded-[20px] flex items-center justify-center">
                  <AreaChart className="w-10 h-10 text-[#2563EB] animate-pulse" />
                </div>
              </div>

              {/* Exact Text Required */}
              <h3 className="text-2xl sm:text-3xl font-extrabold text-[#1E293B] tracking-tight mb-3">
                Graph will be displayed here
              </h3>

              <p className="text-[#64748B] text-sm leading-relaxed mb-6 max-w-md">
                Selected metric <strong className="text-[#2563EB]">{selectedKPI}</strong> for the academic year <strong className="text-[#1D4ED8]">{selectedAcademicYear}</strong> will render interactive trendlines, comparisons, and exportable charts.
              </p>

              {/* Metric Meta Pills */}
              <div className="flex flex-wrap items-center justify-center gap-3">
                <div className="flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-[#EFF6FF] border border-[#DBEAFE] text-xs font-semibold text-[#1E293B]">
                  <PieChart className="w-3.5 h-3.5 text-[#2563EB]" />
                  <span>Metric: {selectedKPI}</span>
                </div>
                <div className="flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-[#EFF6FF] border border-[#DBEAFE] text-xs font-semibold text-[#1E293B]">
                  <Calendar className="w-3.5 h-3.5 text-[#2563EB]" />
                  <span>Session: {selectedAcademicYear}</span>
                </div>
                <div className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-full bg-[#10B981]/10 border border-[#10B981]/20 text-xs font-semibold text-[#10B981]">
                  <Info className="w-3.5 h-3.5" />
                  <span>Chart Engine Standby</span>
                </div>
              </div>

            </div>
          </div>
        </section>

      </main>

      {/* Footer */}
      <footer className="bg-[#FFFFFF] border-t border-[#E2E8F0] py-6 mt-12 text-center text-xs text-[#64748B]">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-4">
          <p>© IFHE KPI - Institutional KPI Monitoring System. All rights reserved.</p>
          <p className="text-[#64748B]">KPI Module Version 1.0.0</p>
        </div>
      </footer>
    </div>
  );
}
