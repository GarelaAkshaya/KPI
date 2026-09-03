import React, { useEffect, useRef, useState } from 'react';
import Navbar from '../components/Navbar';
import StudentAttendanceKPI from '../components/StudentAttendanceKPI';
import { BarChart3, Calendar, Filter, AreaChart, PieChart, Layers, ArrowUpRight, Info, Users, UserRound, Database, FileText, Settings, Bell, Home, Upload, SlidersHorizontal } from 'lucide-react';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

export default function KPIDashboardPage() {
  const [selectedKPI, setSelectedKPI] = useState('Student Attendance');
  const [selectedAcademicYear, setSelectedAcademicYear] = useState('2024-25');
  const [ratioData, setRatioData] = useState(null);
  const [ratioTrend, setRatioTrend] = useState([]);
  const [ratioDistribution, setRatioDistribution] = useState([]);
  const [ratioTrendMessage, setRatioTrendMessage] = useState('');
  const [ratioLastChecked, setRatioLastChecked] = useState(null);
  const yearSelectRef = useRef(null);
  const [ratioLoading, setRatioLoading] = useState(false);
  const [ratioError, setRatioError] = useState('');

  useEffect(() => {
    if (selectedKPI !== 'Student-Faculty Ratio') return undefined;

    const controller = new AbortController();
    setRatioLoading(true);
    setRatioError('');

    Promise.all([
      fetch(`${API_BASE_URL}/api/kpis/student-faculty-ratio`, { signal: controller.signal }),
      fetch(`${API_BASE_URL}/api/kpis/student-faculty-ratio/trend`, { signal: controller.signal }),
    ])
      .then(async ([ratioResponse, trendResponse]) => {
        if (!ratioResponse.ok || !trendResponse.ok) throw new Error('Unable to load Student-Faculty Ratio data.');
        return { ratio: await ratioResponse.json(), trend: await trendResponse.json() };
      })
      .then((response) => {
        setRatioData(response.ratio);
        setRatioTrend(Array.isArray(response.trend.data) ? response.trend.data : []);
        setRatioDistribution(Array.isArray(response.trend.distribution) ? response.trend.distribution : []);
        setRatioTrendMessage(response.trend.message || '');
        setRatioLastChecked(new Date());
      })
      .catch((error) => {
        if (error.name !== 'AbortError') setRatioError(error.message);
      })
      .finally(() => {
        if (!controller.signal.aborted) setRatioLoading(false);
      });

    return () => controller.abort();
  }, [selectedKPI]);

  const exportRatioReport = () => {
    if (!ratioData) return;
    const report = [
      ['Metric', 'Value'],
      ['Total Students', ratioData.totalStudents],
      ['Total Faculty', ratioData.totalFaculty],
      ['Student-Faculty Ratio', `${Number(ratioData.ratio).toFixed(2)} : 1`],
      ['Academic Year', selectedAcademicYear],
    ].map((row) => row.join(',')).join('\n');
    const link = document.createElement('a');
    link.href = URL.createObjectURL(new Blob([report], { type: 'text/csv' }));
    link.download = `student-faculty-ratio-${selectedAcademicYear}.csv`;
    link.click();
    URL.revokeObjectURL(link.href);
  };

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

  const isRatioPage = selectedKPI === 'Student-Faculty Ratio';
  const ratioStudents = Number(ratioData?.totalStudents || 0);
  const ratioFaculty = Number(ratioData?.totalFaculty || 0);
  const ratioTotal = ratioStudents + ratioFaculty;
  const studentShare = ratioTotal ? (ratioStudents / ratioTotal) * 100 : 0;
  const facultyShare = ratioTotal ? (ratioFaculty / ratioTotal) * 100 : 0;
  const currentRatio = Number(ratioData?.ratio || 0);
  const ratioRange = currentRatio <= 10 ? '< 10 : 1' : currentRatio <= 20 ? '10 : 1 - 20 : 1' : currentRatio <= 30 ? '20 : 1 - 30 : 1' : '> 30 : 1';

  return (
    <div className="min-h-screen bg-[#F8FAFC] text-[#1E293B] flex flex-col">
      {/* Navbar Header */}
      <Navbar />

      {/* Main Container */}
      <main className={`flex-1 w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12 ${isRatioPage ? 'max-w-[1440px] xl:pl-52' : 'max-w-7xl'}`}>
        {isRatioPage && (
          <aside className="hidden xl:flex fixed left-4 top-28 w-40 flex-col gap-2" aria-label="Dashboard navigation">
            {[
              { label: 'Home', icon: Home },
              { label: 'Dashboard', icon: BarChart3 },
              { label: 'KPI Dashboard', icon: SlidersHorizontal, active: true },
              { label: 'Data Upload', icon: Upload },
              { label: 'Data Management', icon: Database },
              { label: 'Reports', icon: FileText },
              { label: 'Alerts & Notifications', icon: Bell },
              { label: 'Settings', icon: Settings },
            ].map(({ label, icon: Icon, active }) => (
              <div key={label} className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-xs font-semibold ${active ? 'bg-[#2563EB] text-white shadow-md shadow-blue-500/20' : 'text-[#64748B]'}`}>
                <Icon className="w-4 h-4" />
                <span>{label}</span>
              </div>
            ))}
            <div className="mt-24 rounded-xl border border-[#DBEAFE] bg-[#F8FAFC] p-3 text-center">
              <FileText className="w-8 h-8 mx-auto text-[#7C9CF5] mb-2" />
              <p className="text-[10px] font-bold text-[#2563EB]">Track. Analyze. Improve.</p>
              <p className="text-[9px] text-[#64748B] mt-1">Real-time insights for better decisions.</p>
            </div>
          </aside>
        )}
        
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
                    ref={yearSelectRef}
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
          ) : selectedKPI === 'Student-Faculty Ratio' ? (
            <div className="relative overflow-hidden bg-[#FFFFFF] border border-[#E2E8F0] rounded-2xl p-5 sm:p-6 shadow-sm">
              <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-4 mb-6">
                <div>
                  <div className="flex items-center gap-2 text-xs font-semibold text-[#64748B] mb-1"><BarChart3 className="w-4 h-4 text-[#2563EB]" /> Institutional KPI</div>
                  <h3 className="text-2xl sm:text-3xl font-extrabold text-[#1E293B] tracking-tight">Student-Faculty Ratio <Info className="inline w-4 h-4 text-[#94A3B8] align-middle" /></h3>
                  <p className="text-[#64748B] text-sm mt-1">Overview of student and faculty population and ratio analysis.</p>
                </div>
                <div className="flex gap-2">
                  <button type="button" onClick={exportRatioReport} className="inline-flex items-center gap-2 px-3 py-2 rounded-lg border border-[#E2E8F0] text-xs font-semibold text-[#475569] bg-white transition-all hover:border-[#93C5FD] hover:bg-[#F8FAFC] focus:outline-none focus:ring-2 focus:ring-[#93C5FD]"> <FileText className="w-4 h-4" /> Export Report</button>
                  <button type="button" onClick={() => yearSelectRef.current?.focus()} className="inline-flex items-center gap-2 px-3 py-2 rounded-lg bg-[#2563EB] text-white text-xs font-semibold shadow-md shadow-blue-500/20 transition-all hover:bg-[#1D4ED8] focus:outline-none focus:ring-2 focus:ring-[#93C5FD]"><Filter className="w-4 h-4" /> Filter</button>
                </div>
              </div>

              {ratioLoading ? (
                <p className="text-sm text-[#64748B]">Loading ratio data...</p>
              ) : ratioError ? (
                <p className="text-sm text-red-600">{ratioError}</p>
              ) : ratioData ? (
                <div className="space-y-5">
                  <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
                    <div className="rounded-2xl border border-[#E2E8F0] bg-[#F8FAFC] p-5 shadow-sm transition-all hover:-translate-y-0.5 hover:border-[#BFDBFE] hover:shadow-md">
                      <div className="flex items-start justify-between"><div><p className="text-xs font-bold uppercase tracking-wider text-[#2563EB]">Total Students</p><p className="text-3xl font-extrabold text-[#1E293B] mt-3">{ratioData.totalStudents}</p><p className="text-xs text-[#64748B] mt-1">Total enrolled students</p></div><span className="flex h-9 w-9 items-center justify-center rounded-xl bg-[#DBEAFE] text-[#2563EB]"><Users className="w-5 h-5" /></span></div>
                    </div>
                    <div className="rounded-2xl border border-[#E2E8F0] bg-[#F8FAFC] p-5 shadow-sm transition-all hover:-translate-y-0.5 hover:border-[#BBF7D0] hover:shadow-md">
                      <div className="flex items-start justify-between"><div><p className="text-xs font-bold uppercase tracking-wider text-[#16A765]">Total Faculty</p><p className="text-3xl font-extrabold text-[#1E293B] mt-3">{ratioData.totalFaculty}</p><p className="text-xs text-[#64748B] mt-1">Total faculty members</p></div><span className="flex h-9 w-9 items-center justify-center rounded-xl bg-[#DCFCE7] text-[#16A765]"><UserRound className="w-5 h-5" /></span></div>
                    </div>
                    <div className="rounded-2xl border border-[#DBEAFE] bg-[#EFF6FF] p-5 shadow-sm transition-all hover:-translate-y-0.5 hover:shadow-md">
                      <div className="flex items-start justify-between"><div><p className="text-xs font-bold uppercase tracking-wider text-[#2563EB]">Student-Faculty Ratio</p><p className="text-3xl font-extrabold text-[#1D4ED8] mt-3">{Number(ratioData.ratio).toFixed(2)} : 1</p><p className="text-xs text-[#64748B] mt-1">Students per faculty</p></div><span className="flex h-9 w-9 items-center justify-center rounded-xl bg-white/80 text-[#2563EB]"><SlidersHorizontal className="w-5 h-5" /></span></div>
                    </div>
                    <div className="rounded-2xl border border-[#BAE6FD] bg-[#F0FDFF] p-5 shadow-sm transition-all hover:-translate-y-0.5 hover:shadow-md">
                      <div className="flex items-start justify-between"><div><p className="text-xs font-bold uppercase tracking-wider text-[#0F839B]">Ratio Benchmark</p><p className="text-3xl font-extrabold text-[#1E293B] mt-3">{ratioFaculty ? (Number(ratioData.ratio) <= 20 ? 'Good' : 'Review') : 'N/A'}</p><p className="text-xs text-[#64748B] mt-1">Current benchmark status</p></div><span className="flex h-9 w-9 items-center justify-center rounded-xl bg-white/80 text-[#0F839B]"><Database className="w-5 h-5" /></span></div>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
                  <div className="min-w-0 rounded-2xl border border-[#E2E8F0] bg-[#F8FAFC] p-4 sm:p-6">
                    <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between mb-4">
                      <div>
                        <h4 className="text-lg font-bold text-[#1E293B]">Population Comparison</h4>
                        <p className="text-sm text-[#64748B] mt-1">Current database totals used in the ratio.</p>
                      </div>
                      <div className="flex items-center gap-4 text-xs font-semibold text-[#64748B]">
                        <span className="flex items-center gap-2"><span className="w-3 h-3 rounded-sm bg-[#2563EB]" />Students</span>
                        <span className="flex items-center gap-2"><span className="w-3 h-3 rounded-sm bg-[#F59E0B]" />Faculty</span>
                      </div>
                    </div>
                    <div className="w-full">
                      <svg viewBox="0 0 500 280" className="block w-full h-[280px]" role="img" aria-label="Student and faculty population comparison">
                        <line x1="60" y1="230" x2="460" y2="230" stroke="#CBD5E1" strokeWidth="1" />
                        <line x1="60" y1="40" x2="60" y2="230" stroke="#CBD5E1" strokeWidth="1" />
                        {[0, 25, 50, 75, 100].map((tick) => (
                          <g key={tick}>
                            <line x1="60" y1={230 - (tick / 100) * 190} x2="460" y2={230 - (tick / 100) * 190} stroke="#E2E8F0" strokeDasharray="4 4" />
                            <text x="50" y={234 - (tick / 100) * 190} textAnchor="end" fontSize="10" fill="#64748B">{Math.round((tick / 100) * Math.max(ratioStudents, ratioFaculty, 1))}</text>
                          </g>
                        ))}
                        {[
                          { label: 'Students', value: ratioStudents, x: 145, color: '#2563EB' },
                          { label: 'Faculty', value: ratioFaculty, x: 315, color: '#F59E0B' },
                        ].map((item) => {
                          const maximum = Math.max(ratioStudents, ratioFaculty, 1);
                          const barHeight = (item.value / maximum) * 170;
                          const y = 230 - barHeight;
                          return (
                            <g key={item.label}>
                              <rect x={item.x} y={y} width="80" height={barHeight} rx="8" fill={item.color} opacity="0.9" />
                              <text x={item.x + 40} y={y - 10} textAnchor="middle" fontSize="12" fontWeight="700" fill="#1E293B">{item.value}</text>
                              <text x={item.x + 40} y="252" textAnchor="middle" fontSize="12" fontWeight="600" fill="#64748B">{item.label}</text>
                            </g>
                          );
                        })}
                      </svg>
                    </div>
                  </div>
                  <div className="rounded-2xl border border-[#E2E8F0] bg-white p-4 sm:p-6">
                    <h4 className="text-lg font-bold text-[#1E293B]">Student-Faculty Ratio Trend</h4>
                    <p className="text-xs text-[#64748B] mt-1">Ratio analysis over academic years.</p>
                    {ratioTrend.length >= 2 ? (
                      <svg viewBox="0 0 500 230" className="w-full h-[230px] mt-4" role="img" aria-label="Student-Faculty Ratio trend">
                        <line x1="55" y1="190" x2="470" y2="190" stroke="#CBD5E1" />
                        <line x1="55" y1="30" x2="55" y2="190" stroke="#CBD5E1" />
                        <polyline fill="none" stroke="#2563EB" strokeWidth="3" points={ratioTrend.map((point, index) => `${70 + index * (380 / (ratioTrend.length - 1))},${190 - (Number(point.ratio) / Math.max(...ratioTrend.map((item) => Number(item.ratio)), 1)) * 145}`).join(' ')} />
                        {ratioTrend.map((point, index) => <g key={point.academicYear}><circle cx={70 + index * (380 / (ratioTrend.length - 1))} cy={190 - (Number(point.ratio) / Math.max(...ratioTrend.map((item) => Number(item.ratio)), 1)) * 145} r="4" fill="#2563EB" /><text x={70 + index * (380 / (ratioTrend.length - 1))} y="210" textAnchor="middle" fontSize="9" fill="#64748B">{point.academicYear}</text></g>)}
                      </svg>
                    ) : ratioData ? (
                      <div className="mt-4"><svg viewBox="0 0 500 230" className="w-full h-[190px]" role="img" aria-label="Current Student-Faculty Ratio snapshot"><line x1="55" y1="165" x2="470" y2="165" stroke="#CBD5E1" /><line x1="55" y1="30" x2="55" y2="165" stroke="#CBD5E1" /><circle cx="260" cy="70" r="5" fill="#2563EB" /><text x="260" y="52" textAnchor="middle" fontSize="12" fontWeight="700" fill="#1E293B">{currentRatio.toFixed(2)}</text><text x="260" y="188" textAnchor="middle" fontSize="10" fill="#64748B">{selectedAcademicYear}</text></svg><p className="text-center text-[10px] text-[#64748B]">Historical trend will appear when academic-year ratio records are available.</p></div>
                    ) : <div className="flex min-h-[230px] items-center justify-center text-center text-xs text-[#64748B]">{ratioTrendMessage || 'Trend unavailable until multiple academic-year datasets exist.'}</div>}
                  </div>
                  <div className="rounded-2xl border border-[#E2E8F0] bg-white p-4 sm:p-6">
                    <h4 className="text-lg font-bold text-[#1E293B]">Ratio Distribution</h4>
                    <p className="text-xs text-[#64748B] mt-1">Current population composition.</p>
                    {ratioDistribution.length > 0 || ratioData ? <div className="flex items-center justify-center gap-4 py-6">
                      <svg viewBox="0 0 160 160" className="w-32 h-32 -rotate-90" role="img" aria-label="Student and faculty population distribution">
                        <circle cx="80" cy="80" r="50" fill="none" stroke="#DBEAFE" strokeWidth="22" />
                        <circle cx="80" cy="80" r="50" fill="none" stroke="#2563EB" strokeWidth="22" strokeDasharray="314.2 314.2" />
                        <circle cx="80" cy="80" r="30" fill="white" />
                      </svg>
                      <div className="space-y-3 text-xs font-semibold text-[#475569]"><p><span className="inline-block w-2.5 h-2.5 rounded-full bg-[#2563EB] mr-2" />Current ratio range</p><p className="text-[#64748B]">{ratioRange}</p></div>
                    </div> : <div className="flex min-h-[190px] items-center justify-center text-center text-xs text-[#64748B]">Distribution unavailable without department or academic-year ratio data.</div>}
                  </div>
                  </div>
                  <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
                    <div className="rounded-2xl border border-[#E2E8F0] bg-white p-5"><h4 className="font-bold text-[#1E293B] mb-3">Key Insights</h4><div className="space-y-3 text-xs text-[#475569]"><p className="flex gap-2"><ArrowUpRight className="w-4 h-4 text-[#16A765] shrink-0" />Current ratio: <strong>{Number(ratioData.ratio).toFixed(2)} : 1</strong></p><p className="flex gap-2"><Users className="w-4 h-4 text-[#2563EB] shrink-0" />Student strength: <strong>{ratioData.totalStudents}</strong></p><p className="flex gap-2"><UserRound className="w-4 h-4 text-[#F59E0B] shrink-0" />Faculty strength: <strong>{ratioData.totalFaculty}</strong></p><p className="flex gap-2"><Calendar className="w-4 h-4 text-[#64748B] shrink-0" />Academic year: <strong>{selectedAcademicYear}</strong></p></div></div>
                    <div className="rounded-2xl border border-[#E2E8F0] bg-white p-5"><h4 className="font-bold text-[#1E293B]">Ratio Benchmark</h4><p className="text-[10px] text-[#64748B] mt-1 mb-3">Reference ranges, not an official institutional policy.</p><div className="overflow-hidden rounded-lg border border-[#E2E8F0]"><table className="w-full text-xs text-left"><thead className="bg-[#F8FAFC] text-[#64748B]"><tr><th className="px-3 py-2 font-bold">Ratio Range</th><th className="px-3 py-2 font-bold">Performance</th></tr></thead><tbody className="text-[#475569]"><tr className="border-t border-[#E2E8F0]"><td className="px-3 py-2">Up to 20 : 1</td><td className="px-3 py-2"><span className="rounded bg-[#DCFCE7] px-2 py-1 font-semibold text-[#15803D]">Good</span></td></tr><tr className="border-t border-[#E2E8F0]"><td className="px-3 py-2">Above 20 : 1</td><td className="px-3 py-2"><span className="rounded bg-[#FEF3C7] px-2 py-1 font-semibold text-[#B45309]">Review</span></td></tr></tbody></table></div></div>
                    <div className="rounded-2xl border border-[#E2E8F0] bg-white p-5"><h4 className="font-bold text-[#1E293B] mb-3">Summary</h4><p className="text-xs leading-relaxed text-[#475569]">This ratio is calculated from current live database counts for students and faculty.</p><div className="mt-4 space-y-2 text-xs text-[#64748B]"><p>Academic Year <strong className="text-[#1E293B]">{selectedAcademicYear}</strong></p><p>Last updated <strong className="text-[#1E293B]">{ratioLastChecked ? ratioLastChecked.toLocaleString() : 'Awaiting data'}</strong></p></div></div>
                  </div>
                </div>
              ) : null}

              {ratioData?.message && (
                <p className="text-sm text-amber-700 mt-5">{ratioData.message}</p>
              )}
            </div>
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
