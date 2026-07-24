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
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      {/* Navbar Header */}
      <Navbar />

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12">
        
        {/* Page Title & Context Header */}
        <section className="mb-8">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-slate-800">
            <div>
              <div className="flex items-center gap-2 mb-2">
                <span className="px-3 py-1 rounded-full bg-gradient-to-r from-indigo-500/20 to-purple-500/20 text-indigo-300 border border-indigo-500/30 text-xs font-bold uppercase tracking-wider flex items-center gap-1.5">
                  <BarChart3 className="w-3.5 h-3.5 text-indigo-400" />
                  Analytics Center
                </span>
                <span className="text-xs text-slate-400">• Institutional KPI Monitoring</span>
              </div>
              <h1 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
                IFHE KPI
              </h1>
              <p className="text-slate-400 text-sm mt-1">
                Institutional Performance & Quality Benchmark Dashboard
              </p>
            </div>

            {/* Selected Active Filters Badge */}
            <div className="flex items-center gap-3 bg-slate-900/90 border border-slate-800 rounded-2xl p-3.5 shadow-lg">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-600 to-purple-600 flex items-center justify-center text-white font-bold">
                <Filter className="w-5 h-5" />
              </div>
              <div className="text-xs">
                <p className="text-slate-400 font-medium">Current View Filter</p>
                <p className="font-bold text-slate-200">
                  {selectedKPI} <span className="text-indigo-400">({selectedAcademicYear})</span>
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* Dropdowns Control Panel */}
        <section className="mb-8">
          <div className="bg-slate-900/90 border border-slate-800 rounded-3xl p-6 sm:p-8 shadow-xl shadow-slate-950/50">
            <h2 className="text-base font-bold text-slate-200 mb-4 flex items-center gap-2">
              <Layers className="w-4 h-4 text-indigo-400" />
              <span>Select Indicator & Academic Session</span>
            </h2>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              
              {/* Dropdown 1: KPI */}
              <div className="space-y-2">
                <label htmlFor="kpi-select" className="block text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-2">
                  <BarChart3 className="w-4 h-4 text-indigo-400" />
                  KPI
                </label>
                <div className="relative">
                  <select
                    id="kpi-select"
                    value={selectedKPI}
                    onChange={(e) => setSelectedKPI(e.target.value)}
                    className="w-full appearance-none bg-slate-950/80 border border-slate-800 rounded-2xl px-4 py-3.5 pr-10 text-slate-100 text-sm font-semibold focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500 transition-all cursor-pointer shadow-inner"
                  >
                    {kpiOptions.map((option) => (
                      <option key={option} value={option} className="bg-slate-900 text-slate-100 py-2">
                        {option}
                      </option>
                    ))}
                  </select>
                  <div className="absolute inset-y-0 right-0 flex items-center px-4 pointer-events-none text-slate-400">
                    <svg className="w-4 h-4 fill-current" viewBox="0 0 20 20">
                      <path d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" />
                    </svg>
                  </div>
                </div>
              </div>

              {/* Dropdown 2: Academic Year */}
              <div className="space-y-2">
                <label htmlFor="year-select" className="block text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-2">
                  <Calendar className="w-4 h-4 text-purple-400" />
                  Academic Year
                </label>
                <div className="relative">
                  <select
                    id="year-select"
                    value={selectedAcademicYear}
                    onChange={(e) => setSelectedAcademicYear(e.target.value)}
                    className="w-full appearance-none bg-slate-950/80 border border-slate-800 rounded-2xl px-4 py-3.5 pr-10 text-slate-100 text-sm font-semibold focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-purple-500 transition-all cursor-pointer shadow-inner"
                  >
                    {yearOptions.map((year) => (
                      <option key={year} value={year} className="bg-slate-900 text-slate-100 py-2">
                        {year}
                      </option>
                    ))}
                  </select>
                  <div className="absolute inset-y-0 right-0 flex items-center px-4 pointer-events-none text-slate-400">
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
          <div className="relative overflow-hidden bg-slate-900/90 border border-slate-800 rounded-3xl p-8 sm:p-12 shadow-2xl min-h-[420px] flex flex-col items-center justify-center text-center">
            
            {/* Background Decorative Chart Mesh / Wireframe */}
            <div className="absolute inset-0 opacity-10 pointer-events-none flex items-center justify-center">
              <svg className="w-full h-full text-indigo-500" viewBox="0 0 800 400" fill="none" stroke="currentColor">
                <path d="M 50 350 Q 200 200 350 280 T 650 100 T 750 150" strokeWidth="4" fill="none" />
                <path d="M 50 350 L 750 350" strokeWidth="2" strokeDasharray="6 6" />
                <path d="M 50 50 L 50 350" strokeWidth="2" strokeDasharray="6 6" />
                <circle cx="200" cy="200" r="8" fill="currentColor" />
                <circle cx="350" cy="280" r="8" fill="currentColor" />
                <circle cx="650" cy="100" r="8" fill="currentColor" />
              </svg>
            </div>

            {/* Dynamic Background Glow */}
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-indigo-600/10 rounded-full blur-3xl pointer-events-none" />

            {/* Central Content */}
            <div className="relative z-10 max-w-lg mx-auto flex flex-col items-center">
              
              {/* Graphic Badge */}
              <div className="w-20 h-20 rounded-3xl bg-gradient-to-tr from-indigo-600 via-purple-600 to-pink-500 p-1 shadow-2xl shadow-indigo-500/30 mb-6 transform hover:scale-105 transition-transform duration-300">
                <div className="w-full h-full bg-slate-950 rounded-[20px] flex items-center justify-center">
                  <AreaChart className="w-10 h-10 text-indigo-400 animate-pulse" />
                </div>
              </div>

              {/* Exact Text Required */}
              <h3 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight mb-3">
                Graph will be displayed here
              </h3>

              <p className="text-slate-400 text-sm leading-relaxed mb-6 max-w-md">
                Selected metric <strong className="text-indigo-300">{selectedKPI}</strong> for the academic year <strong className="text-purple-300">{selectedAcademicYear}</strong> will render interactive trendlines, comparisons, and exportable charts.
              </p>

              {/* Metric Meta Pills */}
              <div className="flex flex-wrap items-center justify-center gap-3">
                <div className="flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-slate-950/80 border border-slate-800 text-xs font-semibold text-slate-300">
                  <PieChart className="w-3.5 h-3.5 text-indigo-400" />
                  <span>Metric: {selectedKPI}</span>
                </div>
                <div className="flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-slate-950/80 border border-slate-800 text-xs font-semibold text-slate-300">
                  <Calendar className="w-3.5 h-3.5 text-purple-400" />
                  <span>Session: {selectedAcademicYear}</span>
                </div>
                <div className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-xs font-semibold text-emerald-400">
                  <Info className="w-3.5 h-3.5" />
                  <span>Chart Engine Standby</span>
                </div>
              </div>

            </div>
          </div>
        </section>

      </main>

      {/* Footer */}
      <footer className="bg-slate-900/50 border-t border-slate-800/80 py-6 mt-12 text-center text-xs text-slate-400">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-4">
          <p>© IFHE KPI - Institutional KPI Monitoring System. All rights reserved.</p>
          <p className="text-slate-400">KPI Module Version 1.0.0</p>
        </div>
      </footer>
    </div>
  );
}
