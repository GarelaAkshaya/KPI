import React, { useState } from 'react';
import Navbar from '../components/Navbar';
import StudentAttendanceKPI from '../components/StudentAttendanceKPI';
import { BarChart3, Calendar, Filter, AreaChart, PieChart, Layers, ArrowUpRight, Info } from 'lucide-react';

export default function KPIDashboardPage() {
  const [selectedKPI, setSelectedKPI] = useState('Student Attendance');
  const [selectedAcademicYear, setSelectedAcademicYear] = useState('2024-25');

  const kpiOptions = [
    'Student Attendance',
    'Student-Faculty Ratio',
    'Pass Percentage',
    'Laboratory Utilization',
  ];

  const yearOptions = [
    '2022-23',
    '2023-24',
    '2024-25',
    '2025-26',
  ];

  const laboratoryUtilizationData = [
    { laboratoryName: 'LART', department: 'Computer Science & Engineering', sessionDate: '2024-09-01', capacity: 45, studentsPresent: 41 },
    { laboratoryName: 'LLOCK', department: 'Electronics & Communication Engineering', sessionDate: '2024-09-02', capacity: 40, studentsPresent: 38 },
    { laboratoryName: 'LIVIA', department: 'Computer Science & Engineering', sessionDate: '2024-09-03', capacity: 50, studentsPresent: 47 },
    { laboratoryName: 'VLSI', department: 'Electronics & Communication Engineering', sessionDate: '2024-09-04', capacity: 35, studentsPresent: 32 },
    { laboratoryName: 'R-111', department: 'Electrical & Electronics Engineering', sessionDate: '2024-09-05', capacity: 42, studentsPresent: 39 },
    { laboratoryName: 'DF LAB', department: 'Computer Science & Engineering', sessionDate: '2024-09-06', capacity: 38, studentsPresent: 35 },
    { laboratoryName: 'PHY LAB', department: 'Physics', sessionDate: '2024-09-07', capacity: 40, studentsPresent: 36 },
    { laboratoryName: 'CHEM LAB', department: 'Chemistry', sessionDate: '2024-09-08', capacity: 35, studentsPresent: 31 },
    { laboratoryName: 'BE LAB', department: 'Mechanical Engineering', sessionDate: '2024-09-09', capacity: 30, studentsPresent: 27 },
  ];

  const utilizationPercentage = (capacity, studentsPresent) => {
    if (!capacity || !studentsPresent) return 0;
    return Math.round((studentsPresent / capacity) * 100);
  };

  const laboratoryUtilizationRows = laboratoryUtilizationData.map((row) => ({
    ...row,
    utilization: utilizationPercentage(row.capacity, row.studentsPresent),
  }));

  const laboratoryUtilizationSummary = {
    totalLaboratories: new Set(laboratoryUtilizationRows.map((row) => row.laboratoryName)).size,
    sessionsConducted: laboratoryUtilizationRows.length,
    averageUtilization: Math.round(laboratoryUtilizationRows.reduce((sum, row) => sum + row.utilization, 0) / laboratoryUtilizationRows.length),
    highestUtilizedLaboratory: laboratoryUtilizationRows.reduce((max, row) => (row.utilization > max.utilization ? row : max), laboratoryUtilizationRows[0]),
  };

  const summaryCards = [
    { label: 'Total Laboratories', value: laboratoryUtilizationSummary.totalLaboratories, caption: 'Active labs tracked' },
    { label: 'Sessions Conducted', value: laboratoryUtilizationSummary.sessionsConducted, caption: 'Recordings in current view' },
    { label: 'Average Utilization', value: `${laboratoryUtilizationSummary.averageUtilization}%`, caption: 'Mean occupancy rate' },
    { label: 'Highest Utilized Laboratory', value: laboratoryUtilizationSummary.highestUtilizedLaboratory?.laboratoryName || 'N/A', caption: `${laboratoryUtilizationSummary.highestUtilizedLaboratory?.utilization || 0}% peak usage` },
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

        {/* Main KPI Content Section */}
        <section>
          {selectedKPI === 'Student Attendance' ? (
            <StudentAttendanceKPI academicYear={selectedAcademicYear} />
          ) : selectedKPI === 'Laboratory Utilization' ? (
            <div className="relative overflow-hidden bg-[#FFFFFF] border border-[#E2E8F0] rounded-3xl p-6 sm:p-8 shadow-sm">
              <div className="space-y-6">
                <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <h3 className="text-2xl sm:text-3xl font-extrabold text-[#1E293B] tracking-tight mb-2">
                      Laboratory Utilization
                    </h3>
                    <p className="text-[#64748B] text-sm leading-relaxed max-w-2xl">
                      Selected metric <strong className="text-[#2563EB]">{selectedKPI}</strong> for the academic year <strong className="text-[#1D4ED8]">{selectedAcademicYear}</strong> is shown with summary insights and session-level details.
                    </p>
                  </div>
                  <div className="inline-flex items-center gap-2 px-3.5 py-2 rounded-full bg-[#EFF6FF] border border-[#DBEAFE] text-xs font-semibold text-[#2563EB]">
                    <AreaChart className="w-4 h-4" />
                    <span>Live Sample View</span>
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
                  {summaryCards.map((card) => (
                    <div key={card.label} className="rounded-2xl border border-[#E2E8F0] bg-[#F8FAFC] p-4 shadow-sm">
                      <div className="flex items-center justify-between mb-3">
                        <span className="text-xs font-bold uppercase tracking-wider text-[#64748B]">{card.label}</span>
                        <ArrowUpRight className="w-4 h-4 text-[#2563EB]" />
                      </div>
                      <p className="text-2xl font-extrabold text-[#1E293B]">{card.value}</p>
                      <p className="text-xs text-[#64748B] mt-1">{card.caption}</p>
                    </div>
                  ))}
                </div>

                <div className="rounded-3xl border border-[#E2E8F0] bg-[#FFFFFF] p-4 sm:p-6">
                  <div className="mb-4">
                    <h4 className="text-lg font-bold text-[#1E293B]">Utilization by Laboratory</h4>
                    <p className="text-sm text-[#64748B] mt-1">Responsive comparison of laboratory occupancy levels.</p>
                  </div>
                  <div className="w-full overflow-x-auto">
                    <svg viewBox="0 0 640 260" className="min-w-[560px] w-full h-[260px]">
                      <line x1="40" y1="220" x2="600" y2="220" stroke="#E2E8F0" strokeWidth="1" />
                      <line x1="40" y1="40" x2="40" y2="220" stroke="#E2E8F0" strokeWidth="1" />
                      {[0, 25, 50, 75, 100].map((tick) => (
                        <g key={tick}>
                          <line x1="40" y1={220 - (tick / 100) * 180} x2="600" y2={220 - (tick / 100) * 180} stroke="#F1F5F9" strokeDasharray="4 4" />
                          <text x="12" y={224 - (tick / 100) * 180} fontSize="10" fill="#64748B">{tick}</text>
                        </g>
                      ))}
                      {laboratoryUtilizationRows.map((row, index) => {
                        const x = 70 + index * 120;
                        const barHeight = (row.utilization / 100) * 160;
                        const y = 220 - barHeight;
                        return (
                          <g key={row.laboratoryName}>
                            <rect x={x} y={y} width="70" height={barHeight} rx="10" fill="#2563EB" opacity="0.9" />
                            <text x={x + 35} y="238" textAnchor="middle" fontSize="10" fill="#64748B">{row.laboratoryName.split(' ')[0]}</text>
                            <text x={x + 35} y={y - 8} textAnchor="middle" fontSize="10" fill="#1E293B">{row.utilization}%</text>
                          </g>
                        );
                      })}
                    </svg>
                  </div>
                </div>

                <div className="rounded-3xl border border-[#E2E8F0] bg-[#F8FAFC] overflow-hidden">
                  <div className="overflow-x-auto">
                    <table className="min-w-full text-sm">
                      <thead className="bg-[#EFF6FF]">
                        <tr className="text-left border-b border-[#E2E8F0]">
                          <th className="px-4 py-3 text-[#1E293B] font-semibold">Laboratory Name</th>
                          <th className="px-4 py-3 text-[#1E293B] font-semibold">Department</th>
                          <th className="px-4 py-3 text-[#1E293B] font-semibold">Session Date</th>
                          <th className="px-4 py-3 text-[#1E293B] font-semibold">Capacity</th>
                          <th className="px-4 py-3 text-[#1E293B] font-semibold">Students Present</th>
                          <th className="px-4 py-3 text-[#1E293B] font-semibold">Utilization Percentage</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[#E2E8F0]">
                        {laboratoryUtilizationRows.map((row, index) => (
                          <tr key={row.laboratoryName} className={index % 2 === 0 ? 'bg-[#FFFFFF]' : 'bg-[#F8FAFC]'}>
                            <td className="px-4 py-3 text-[#1E293B]">{row.laboratoryName}</td>
                            <td className="px-4 py-3 text-[#1E293B]">{row.department}</td>
                            <td className="px-4 py-3 text-[#1E293B]">{row.sessionDate}</td>
                            <td className="px-4 py-3 text-[#1E293B]">{row.capacity}</td>
                            <td className="px-4 py-3 text-[#1E293B]">{row.studentsPresent}</td>
                            <td className="px-4 py-3 text-[#1E293B]">{row.utilization}%</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="relative overflow-hidden bg-[#FFFFFF] border border-[#E2E8F0] rounded-3xl p-6 sm:p-8 shadow-sm">
              <div className="relative min-h-[420px] flex flex-col items-center justify-center text-center">
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

                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-[#DBEAFE]/40 rounded-full blur-3xl pointer-events-none" />

                <div className="relative z-10 max-w-lg mx-auto flex flex-col items-center">
                  <div className="w-20 h-20 rounded-3xl bg-gradient-to-tr from-[#2563EB] to-[#1D4ED8] p-1 shadow-lg shadow-blue-500/20 mb-6 transform hover:scale-105 transition-transform duration-300">
                    <div className="w-full h-full bg-[#EFF6FF] rounded-[20px] flex items-center justify-center">
                      <AreaChart className="w-10 h-10 text-[#2563EB] animate-pulse" />
                    </div>
                  </div>

                  <h3 className="text-2xl sm:text-3xl font-extrabold text-[#1E293B] tracking-tight mb-3">
                    Graph will be displayed here
                  </h3>

                  <p className="text-[#64748B] text-sm leading-relaxed mb-6 max-w-md">
                    Selected metric <strong className="text-[#2563EB]">{selectedKPI}</strong> for the academic year <strong className="text-[#1D4ED8]">{selectedAcademicYear}</strong> will render interactive trendlines, comparisons, and exportable charts.
                  </p>

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
            </div>
          )}
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
