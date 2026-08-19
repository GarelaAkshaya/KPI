import React, { useState, useEffect, useMemo } from 'react';
import {
  BarChart3,
  PieChart,
  Users,
  CheckCircle2,
  AlertTriangle,
  Calendar,
  BookOpen,
  ArrowUpRight,
  TrendingUp,
  Download,
  Filter,
  Check,
  X,
  Layers,
  Sparkles,
  Info,
  RefreshCw
} from 'lucide-react';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

const getAttendanceValue = (item) => item.average_attendance ?? item.attendance_percentage ?? 0;

const SUBJECT_SHORTCUTS = {
  'power skills': 'PS',
  'power skills-iii': 'PS lll',
  'power skills - iii': 'PS lll',
  'power skills-lll': 'PS lll',
  'power skills - lll': 'PS lll',
  'principle of cryptography': 'POC',
  'computer network': 'CN',
  'computer networks': 'CN',
  'programming language and compiler construction': 'PLCC',
  'machine learning': 'ML',
  'software engineering': 'SE',
  'constitution of india': 'CI',
  'special project': 'SP',
};

const getSubjectLabel = (subject) => {
  const normalizedSubject = String(subject)
    .trim()
    .toLowerCase()
    .replace(/[–—]/g, '-')
    .replace(/\s+/g, ' ')
    .replace(/\s*([-/])\s*/g, '$1');
  return SUBJECT_SHORTCUTS[normalizedSubject]
    || (normalizedSubject.startsWith('computer network') ? 'CN' : subject);
};

const isNonSubjectColumn = (subject) => /^s\.?\s*no\.?$/i.test(String(subject).trim());

export default function StudentAttendanceKPI({ academicYear = '2024-25' }) {
  const [attendanceData, setAttendanceData] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedDept, setSelectedDept] = useState('All');
  const [hoveredStudent, setHoveredStudent] = useState(null);
  const [hoveredDoughnut, setHoveredDoughnut] = useState(null);
  const [hoveredDist, setHoveredDist] = useState(null);
  const [hoveredCompare, setHoveredCompare] = useState(null);
  const [showTable, setShowTable] = useState(false);

  // Fetch live attendance data
  useEffect(() => {
    async function fetchAttendance() {
      setIsLoading(true);
      try {
        const res = await fetch(`${API_BASE_URL}/api/attendance`);
        if (res.ok) {
          const data = await res.json();
          if (Array.isArray(data)) {
            setAttendanceData(data);
          }
        }
      } catch (err) {
        console.warn('Using default attendance dataset for visual rendering.', err);
      } finally {
        setIsLoading(false);
      }
    }
    fetchAttendance();
  }, []);

  // Filter list by selected department
  const filteredData = useMemo(() => {
    return attendanceData.filter((item) => {
      if (selectedDept !== 'All' && item.department !== selectedDept) return false;
      return true;
    });
  }, [attendanceData, selectedDept]);

  const subjectAverages = useMemo(() => {
    const totals = new Map();
    filteredData.forEach((student) => {
      Object.entries(student.subject_values || {}).forEach(([subject, value]) => {
        if (isNonSubjectColumn(subject)) return;
        const numericValue = Number(value);
        if (!Number.isFinite(numericValue)) return;
        const current = totals.get(subject) || { subject, sum: 0, count: 0 };
        current.sum += numericValue;
        current.count += 1;
        totals.set(subject, current);
      });
    });
    return Array.from(totals.values()).map((item) => ({
      subject: item.subject,
      label: getSubjectLabel(item.subject),
      average: Math.round((item.sum / item.count) * 100) / 100,
      count: item.count,
    }));
  }, [filteredData]);

  const subjectDistribution = useMemo(() => {
    const subjects = new Map();
    filteredData.forEach((student) => {
      Object.entries(student.subject_values || {}).forEach(([subject, value]) => {
        if (isNonSubjectColumn(subject)) return;
        const numericValue = Number(value);
        if (!Number.isFinite(numericValue)) return;
        const current = subjects.get(subject) || { subject, eligible: 0, total: 0 };
        current.total += 1;
        if (numericValue >= 75) current.eligible += 1;
        subjects.set(subject, current);
      });
    });
    return Array.from(subjects.values()).map((item) => ({
      subject: item.subject,
      label: getSubjectLabel(item.subject),
      eligible: Math.round((item.eligible / item.total) * 100),
      belowTarget: Math.round(((item.total - item.eligible) / item.total) * 100),
      count: item.total,
    }));
  }, [filteredData]);

  // Unique departments for filter dropdown
  const departmentOptions = useMemo(() => {
    const depts = new Set(attendanceData.map((d) => d.department).filter(Boolean));
    return ['All', ...Array.from(depts)];
  }, [attendanceData]);

  // Key KPI Calculations
  const metrics = useMemo(() => {
    const totalStudents = filteredData.length;
    if (totalStudents === 0) {
      return {
        overallPercentage: 0,
        above75Count: 0,
        below75Count: 0,
        above75Percent: 0,
        below75Percent: 0,
        totalClassesConducted: 0,
        totalClassesAttended: 0,
        highestAttendance: 0,
        lowestAttendance: 0,
      };
    }

    const totalClassesConducted = filteredData.reduce((sum, item) => sum + (item.total_classes || 0), 0);
    const totalClassesAttended = filteredData.reduce((sum, item) => sum + (item.attended_classes || 0), 0);

    const sumPercentage = filteredData.reduce((sum, item) => {
      const pct = getAttendanceValue(item);
      return sum + pct;
    }, 0);

    const overallPercentage = Math.round((sumPercentage / totalStudents) * 10) / 10;

    const above75 = filteredData.filter((item) => {
      const pct = getAttendanceValue(item);
      return pct >= 75;
    });

    const below75 = filteredData.filter((item) => {
      const pct = getAttendanceValue(item);
      return pct < 75;
    });

    const percentages = filteredData.map(getAttendanceValue);

    return {
      overallPercentage,
      above75Count: above75.length,
      below75Count: below75.length,
      above75Percent: Math.round((above75.length / totalStudents) * 100),
      below75Percent: Math.round((below75.length / totalStudents) * 100),
      totalClassesConducted,
      totalClassesAttended,
      highestAttendance: Math.max(...percentages),
      lowestAttendance: Math.min(...percentages),
    };
  }, [filteredData]);

  // Distribution Brackets for Chart 4
  const distributionData = useMemo(() => {
    const brackets = [
      { range: '< 65%', label: 'Critical Shortage', min: 0, max: 64.99, color: '#EF4444', bgColor: 'bg-red-500', lightColor: '#FEE2E2', count: 0 },
      { range: '65% - 74%', label: 'At Risk', min: 65, max: 74.99, color: '#F59E0B', bgColor: 'bg-amber-500', lightColor: '#FEF3C7', count: 0 },
      { range: '75% - 84%', label: 'Satisfactory', min: 75, max: 84.99, color: '#3B82F6', bgColor: 'bg-blue-500', lightColor: '#DBEAFE', count: 0 },
      { range: '85% - 94%', label: 'Good', min: 85, max: 94.99, color: '#2563EB', bgColor: 'bg-indigo-600', lightColor: '#E0E7FF', count: 0 },
      { range: '95% - 100%', label: 'Distinction', min: 95, max: 100, color: '#10B981', bgColor: 'bg-emerald-500', lightColor: '#D1FAE5', count: 0 },
    ];

    filteredData.forEach((item) => {
      const pct = getAttendanceValue(item);
      const bracket = brackets.find((b) => pct >= b.min && pct <= b.max);
      if (bracket) bracket.count += 1;
    });

    const maxCount = Math.max(...brackets.map((b) => b.count), 1);

    return brackets.map((b) => ({
      ...b,
      percentage: filteredData.length > 0 ? Math.round((b.count / filteredData.length) * 100) : 0,
      relativeHeight: (b.count / maxCount) * 100,
    }));
  }, [filteredData]);

  // Doughnut Chart Geometry Calculations
  const doughnutAngles = useMemo(() => {
    const total = filteredData.length || 1;
    const abovePct = metrics.above75Count / total;
    const belowPct = metrics.below75Count / total;

    const radius = 68;
    const circumference = 2 * Math.PI * radius;

    const aboveStrokeDash = `${abovePct * circumference} ${circumference}`;
    const belowStrokeDash = `${belowPct * circumference} ${circumference}`;
    const belowOffset = -(abovePct * circumference);

    return {
      radius,
      circumference,
      aboveStrokeDash,
      belowStrokeDash,
      belowOffset,
    };
  }, [filteredData, metrics]);

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* ========================================================= */}
      {/* TOP SECTION: 📊 OVERALL ATTENDANCE %                     */}
      {/* ========================================================= */}
      <section className="relative overflow-hidden rounded-3xl border border-blue-200/80 bg-gradient-to-br from-white via-[#F0F7FF] to-[#E0EDFD] p-6 sm:p-8 shadow-sm">
        {/* Decorative Background Accents */}
        <div className="absolute top-0 right-0 -mt-8 -mr-8 w-64 h-64 rounded-full bg-blue-400/10 blur-3xl pointer-events-none" />
        <div className="absolute bottom-0 left-1/3 -mb-10 w-80 h-80 rounded-full bg-indigo-400/10 blur-3xl pointer-events-none" />

        <div className="relative z-10">
          {/* Header Row */}
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-blue-100/80">
            <div>
              <div className="flex items-center gap-2 mb-2">
                <span className="px-3 py-1 rounded-full bg-[#2563EB] text-white text-xs font-bold uppercase tracking-wider flex items-center gap-1.5 shadow-sm shadow-blue-500/20">
                  <BarChart3 className="w-3.5 h-3.5" />
                  Key Performance Indicator
                </span>
                <span className="text-xs font-semibold text-slate-500">• Academic Year {academicYear}</span>
              </div>
              <h2 className="text-2xl sm:text-3xl font-black text-slate-900 tracking-tight flex items-center gap-2.5">
                <span>Student Attendance KPI</span>
                <span className="text-2xl">📊</span>
              </h2>
              <p className="text-slate-600 text-xs sm:text-sm mt-1 max-w-2xl">
                Comprehensive tracking of classroom engagement, attendance thresholds, and student eligibility compliance.
              </p>
            </div>

            {/* Department Filter & Controls */}
            <div className="flex flex-wrap items-center gap-3">
              <div className="flex items-center gap-2 bg-white/90 backdrop-blur-md border border-slate-200/80 rounded-2xl px-3.5 py-2 shadow-xs">
                <Filter className="w-4 h-4 text-blue-600" />
                <span className="text-xs font-bold text-slate-700">Dept:</span>
                <select
                  value={selectedDept}
                  onChange={(e) => setSelectedDept(e.target.value)}
                  className="bg-transparent text-xs font-semibold text-slate-900 focus:outline-none cursor-pointer pr-2"
                >
                  {departmentOptions.map((dept) => (
                    <option key={dept} value={dept}>
                      {dept === 'All' ? 'All Departments' : dept}
                    </option>
                  ))}
                </select>
              </div>

              <button
                onClick={() => setShowTable(!showTable)}
                className="flex items-center gap-1.5 px-3.5 py-2 rounded-2xl text-xs font-bold transition-all duration-200 bg-white hover:bg-slate-50 border border-slate-200/80 text-slate-700 shadow-xs"
              >
                <Layers className="w-3.5 h-3.5 text-blue-600" />
                <span>{showTable ? 'Hide Records' : 'View Records Table'}</span>
              </button>
            </div>
          </div>

          {/* Top Hero Overall Metric + 4 Key KPI Cards */}
          <div className="mt-6 grid grid-cols-1 lg:grid-cols-12 gap-6 items-stretch">
            
            {/* Main Featured Overall Attendance % Card (5 cols on LG) */}
            <div className="lg:col-span-5 bg-gradient-to-br from-[#1E3A8A] to-[#2563EB] text-white rounded-3xl p-6 sm:p-7 shadow-lg shadow-blue-600/15 flex flex-col justify-between relative overflow-hidden group">
              <div className="absolute top-0 right-0 translate-x-4 -translate-y-4 w-40 h-40 bg-white/10 rounded-full blur-2xl pointer-events-none" />
              
              <div>
                <div className="flex items-center justify-between mb-4">
                  <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-white/15 backdrop-blur-md border border-white/20 text-blue-100 text-xs font-bold">
                    <Sparkles className="w-3.5 h-3.5 text-yellow-300" />
                    Top Core Metric
                  </span>

                  <span className={`px-3 py-1 rounded-full text-xs font-bold backdrop-blur-md border ${
                    metrics.overallPercentage >= 75
                      ? 'bg-emerald-500/20 border-emerald-300/40 text-emerald-200'
                      : 'bg-rose-500/20 border-rose-300/40 text-rose-200'
                  }`}>
                    {metrics.overallPercentage >= 75 ? '✓ Compliance Met' : '⚠ Below Standard'}
                  </span>
                </div>

                <p className="text-blue-200 text-xs font-bold uppercase tracking-wider">
                  Institutional Overall Attendance
                </p>

                <div className="mt-3 flex items-baseline gap-3">
                  <span className="text-5xl sm:text-6xl font-black tracking-tight text-white">
                    {metrics.overallPercentage}%
                  </span>
                  <div className="flex flex-col text-xs text-blue-200">
                    <span className="font-semibold">Target: 85.0%</span>
                    <span className="text-emerald-300 font-bold">Threshold: 75.0%</span>
                  </div>
                </div>
              </div>

              {/* Visual Progress Bar */}
              <div className="mt-6 pt-4 border-t border-white/15">
                <div className="flex justify-between text-xs text-blue-100 mb-1.5 font-medium">
                  <span>Attendance Progress vs Target</span>
                  <span>{metrics.overallPercentage}% / 100%</span>
                </div>
                <div className="w-full h-3 bg-black/25 rounded-full overflow-hidden p-0.5">
                  <div
                    className={`h-full rounded-full transition-all duration-1000 ${
                      metrics.overallPercentage >= 75
                        ? 'bg-gradient-to-r from-emerald-400 to-emerald-300'
                        : 'bg-gradient-to-r from-amber-400 to-rose-400'
                    }`}
                    style={{ width: `${Math.min(metrics.overallPercentage, 100)}%` }}
                  />
                </div>
                <div className="flex items-center justify-between text-[11px] text-blue-200 mt-2">
                  <span>0% (Minimum)</span>
                  <span className="font-bold text-amber-300">75% (Mandatory)</span>
                  <span>100% (Perfect)</span>
                </div>
              </div>
            </div>

            {/* 4 Supporting Metric Cards (7 cols on LG) */}
            <div className="lg:col-span-7 grid grid-cols-1 sm:grid-cols-2 gap-4">
              
              {/* Card 1: Students Above 75% */}
              <div className="bg-white/95 rounded-2xl p-4 sm:p-5 border border-slate-200/80 shadow-xs flex flex-col justify-between hover:shadow-md transition-shadow duration-200">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Above 75% Attendance</span>
                  <div className="w-8 h-8 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center font-bold">
                    <CheckCircle2 className="w-4 h-4" />
                  </div>
                </div>
                <div>
                  <div className="flex items-baseline gap-2">
                    <span className="text-3xl font-black text-slate-900">{metrics.above75Count}</span>
                    <span className="text-xs font-bold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full">
                      {metrics.above75Percent}% of Total
                    </span>
                  </div>
                  <p className="text-xs text-slate-500 mt-1 font-medium">
                    Students eligible for semester end examinations.
                  </p>
                </div>
              </div>

              {/* Card 2: Students Below 75% */}
              <div className="bg-white/95 rounded-2xl p-4 sm:p-5 border border-slate-200/80 shadow-xs flex flex-col justify-between hover:shadow-md transition-shadow duration-200">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Below 75% Attendance</span>
                  <div className="w-8 h-8 rounded-xl bg-rose-50 text-rose-600 flex items-center justify-center font-bold">
                    <AlertTriangle className="w-4 h-4" />
                  </div>
                </div>
                <div>
                  <div className="flex items-baseline gap-2">
                    <span className="text-3xl font-black text-slate-900">{metrics.below75Count}</span>
                    <span className="text-xs font-bold text-rose-600 bg-rose-50 px-2 py-0.5 rounded-full">
                      {metrics.below75Percent}% of Total
                    </span>
                  </div>
                  <p className="text-xs text-slate-500 mt-1 font-medium">
                    Students with attendance shortage (intervention needed).
                  </p>
                </div>
              </div>

              {/* Card 3: Total Classes Attended */}
              <div className="bg-white/95 rounded-2xl p-4 sm:p-5 border border-slate-200/80 shadow-xs flex flex-col justify-between hover:shadow-md transition-shadow duration-200">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Classes Attended</span>
                  <div className="w-8 h-8 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center font-bold">
                    <BookOpen className="w-4 h-4" />
                  </div>
                </div>
                <div>
                  <div className="flex items-baseline gap-2">
                    <span className="text-3xl font-black text-slate-900">{metrics.totalClassesAttended.toLocaleString()}</span>
                    <span className="text-xs font-medium text-slate-500">/ {metrics.totalClassesConducted.toLocaleString()} total</span>
                  </div>
                  <p className="text-xs text-slate-500 mt-1 font-medium">
                    Aggregated student-sessions attended.
                  </p>
                </div>
              </div>

              {/* Card 4: Total Tracked Students */}
              <div className="bg-white/95 rounded-2xl p-4 sm:p-5 border border-slate-200/80 shadow-xs flex flex-col justify-between hover:shadow-md transition-shadow duration-200">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Students Monitored</span>
                  <div className="w-8 h-8 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center font-bold">
                    <Users className="w-4 h-4" />
                  </div>
                </div>
                <div>
                  <div className="flex items-baseline gap-2">
                    <span className="text-3xl font-black text-slate-900">{filteredData.length}</span>
                    <span className="text-xs font-bold text-blue-600 bg-blue-50 px-2 py-0.5 rounded-full">
                      {selectedDept === 'All' ? 'Institutional' : selectedDept}
                    </span>
                  </div>
                  <p className="text-xs text-slate-500 mt-1 font-medium">
                    Peak: <strong className="text-emerald-600">{metrics.highestAttendance}%</strong> • Low: <strong className="text-rose-600">{metrics.lowestAttendance}%</strong>
                  </p>
                </div>
              </div>

            </div>
          </div>
        </div>
      </section>

      {/* ========================================================= */}
      {/* DATA TABLE DRAWER (TOGGLEABLE)                            */}
      {/* ========================================================= */}
      {showTable && (
        <section className="bg-white rounded-3xl border border-slate-200 p-6 shadow-sm animate-fadeIn">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="font-bold text-slate-900 text-lg">Student Attendance Master List</h3>
              <p className="text-xs text-slate-500">Active records loaded from database and Excel sync.</p>
            </div>
            <button
              onClick={() => setShowTable(false)}
              className="text-xs font-semibold text-slate-500 hover:text-slate-800"
            >
              Close Table ✕
            </button>
          </div>
          <div className="overflow-x-auto max-h-72">
            <table className="min-w-full text-xs text-left">
              <thead className="bg-slate-50 sticky top-0 text-slate-700 font-bold border-b border-slate-200">
                <tr>
                  <th className="p-3">Enrollment Number</th>
                  <th className="p-3">Student Name</th>
                  <th className="p-3">Department</th>
                  <th className="p-3">Total Classes</th>
                  <th className="p-3">Attended</th>
                  <th className="p-3">Attendance %</th>
                  <th className="p-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filteredData.map((item, idx) => {
                  const pct = getAttendanceValue(item);
                  const isEligible = pct >= 75;
                  return (
                    <tr key={item.student_id || idx} className="hover:bg-slate-50">
                      <td className="p-3 font-bold text-slate-900">{item.enrollment_number || item.student_id}</td>
                      <td className="p-3 text-slate-800">{item.student_name}</td>
                      <td className="p-3 text-slate-600">{item.department}</td>
                      <td className="p-3 text-slate-700">{item.total_classes}</td>
                      <td className="p-3 font-semibold text-slate-900">{item.attended_classes}</td>
                      <td className="p-3 font-black text-slate-900">{pct}%</td>
                      <td className="p-3">
                        <span className={`px-2.5 py-0.5 rounded-full font-bold text-[10px] ${
                          isEligible ? 'bg-emerald-100 text-emerald-700' : 'bg-rose-100 text-rose-700'
                        }`}>
                          {isEligible ? 'Eligible (≥75%)' : 'Shortage (<75%)'}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {/* ========================================================= */}
      {/* BELOW: 4 INTERACTIVE CHARTS                               */}
      {/* ========================================================= */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">

        {/* --------------------------------------------------------- */}
        {/* CHART 1: Average Attendance % by Subject — Bar Chart       */}
        {/* --------------------------------------------------------- */}
        <div className="bg-white rounded-3xl border border-slate-200 p-6 sm:p-7 shadow-xs flex flex-col justify-between hover:shadow-md transition-shadow">
          <div>
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center font-bold">
                  <BarChart3 className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="font-extrabold text-slate-900 text-base">Average Attendance % by Subject</h3>
                  <p className="text-xs text-slate-500">Subject-wise average with 75% baseline</p>
                </div>
              </div>
              <span className="text-[11px] font-bold text-blue-600 bg-blue-50 px-2.5 py-1 rounded-full border border-blue-100">
                Bar Chart
              </span>
            </div>

            {/* Legend / Status indicators */}
            <div className="flex items-center gap-4 text-xs font-semibold text-slate-600 my-3">
              <div className="flex items-center gap-1.5">
                <span className="w-3 h-3 rounded-md bg-blue-600 inline-block" />
                  <span>On target (≥75%)</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-3 h-3 rounded-md bg-rose-500 inline-block" />
                  <span>Below target (&lt;75%)</span>
              </div>
              <div className="flex items-center gap-1.5 text-amber-600">
                <span className="w-3.5 border-t-2 border-dashed border-amber-500 inline-block" />
                <span>75% Benchmark</span>
              </div>
            </div>

            {/* Bar Chart SVG */}
            <div className="mt-4 relative overflow-x-auto">
              <div className="min-w-[480px]">
                <svg viewBox="0 0 540 240" className="w-full h-64">
                  {/* Background Grid Lines */}
                  {[0, 25, 50, 75, 100].map((tick) => {
                    const y = 200 - (tick / 100) * 160;
                    return (
                      <g key={tick}>
                        <line
                          x1="35"
                          y1={y}
                          x2="520"
                          y2={y}
                          stroke={tick === 75 ? '#F59E0B' : '#F1F5F9'}
                          strokeWidth={tick === 75 ? '1.5' : '1'}
                          strokeDasharray={tick === 75 ? '4 4' : undefined}
                        />
                        <text x="5" y={y + 3} fontSize="10" fill={tick === 75 ? '#D97706' : '#94A3B8'} fontWeight={tick === 75 ? 'bold' : 'normal'}>
                          {tick}%
                        </text>
                      </g>
                    );
                  })}

                  {/* 75% Reference Label */}
                  <text x="450" y="75" fontSize="9" fill="#D97706" fontWeight="bold" textAnchor="end">
                    Required 75% Threshold
                  </text>

                  {/* Subject Bars */}
                  {subjectAverages.map((item, idx) => {
                    const pct = item.average;
                    const isEligible = pct >= 75;
                    const barCount = subjectAverages.length || 1;
                    const availableWidth = 470;
                    const slotWidth = availableWidth / barCount;
                    const barWidth = Math.min(Math.max(slotWidth * 0.65, 16), 34);
                    const x = 45 + idx * slotWidth + (slotWidth - barWidth) / 2;
                    const barHeight = (pct / 100) * 160;
                    const y = 200 - barHeight;

                    const isHovered = hoveredStudent?.subject === item.subject;

                    return (
                      <g
                        key={item.subject}
                        className="cursor-pointer transition-all duration-200"
                        onMouseEnter={() => setHoveredStudent(item)}
                        onMouseLeave={() => setHoveredStudent(null)}
                      >
                        {/* Hover Highlight Column Background */}
                        {isHovered && (
                          <rect
                            x={x - 4}
                            y={35}
                            width={barWidth + 8}
                            height={170}
                            rx="8"
                            fill="#EFF6FF"
                            opacity="0.8"
                          />
                        )}

                        {/* Bar Shape */}
                        <rect
                          x={x}
                          y={y}
                          width={barWidth}
                          height={barHeight}
                          rx="6"
                          fill={isEligible ? '#2563EB' : '#EF4444'}
                          opacity={isHovered ? 1 : 0.88}
                          className="transition-all duration-300"
                        />

                        {/* Percentage Label on Top of Bar */}
                        <text
                          x={x + barWidth / 2}
                          y={y - 5}
                          textAnchor="middle"
                          fontSize="9"
                          fontWeight="bold"
                          fill={isEligible ? '#1E3A8A' : '#991B1B'}
                        >
                          {Math.round(pct)}%
                        </text>

                        {/* Student Name / ID X-axis label */}
                        <text
                          x={x + barWidth / 2}
                          y={215}
                          textAnchor="middle"
                          fontSize="8.5"
                          fill="#475569"
                          fontWeight={isHovered ? 'bold' : 'normal'}
                        >
                          {item.label}
                        </text>
                      </g>
                    );
                  })}
                </svg>
              </div>
            </div>
          </div>

          {/* Interactive Tooltip Card for Chart 1 */}
          <div className="mt-2 min-h-[44px] bg-slate-50 border border-slate-100 rounded-2xl p-2.5 flex items-center justify-between text-xs">
            {hoveredStudent ? (
              <div className="flex items-center justify-between w-full">
                <div className="flex items-center gap-2">
                  <span className="font-bold text-slate-900">{hoveredStudent.label}</span>
                  <span className="text-slate-500">• {hoveredStudent.count} student records</span>
                </div>
                <div className="flex items-center gap-2 font-bold">
                  <span className={`px-2 py-0.5 rounded-full ${
                    hoveredStudent.average >= 75 ? 'bg-emerald-100 text-emerald-700' : 'bg-rose-100 text-rose-700'
                  }`}>
                    {hoveredStudent.average}%
                  </span>
                </div>
              </div>
            ) : (
              <span className="text-slate-400 italic">Hover over any subject bar to view its average.</span>
            )}
          </div>
        </div>

        {/* --------------------------------------------------------- */}
        {/* CHART 2: Above 75% vs Below 75% — Doughnut Chart          */}
        {/* --------------------------------------------------------- */}
        <div className="bg-white rounded-3xl border border-slate-200 p-6 sm:p-7 shadow-xs flex flex-col justify-between hover:shadow-md transition-shadow">
          <div>
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center font-bold">
                  <PieChart className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="font-extrabold text-slate-900 text-base">Above 75% vs Below 75%</h3>
                  <p className="text-xs text-slate-500">Eligibility ratio and shortage breakdown</p>
                </div>
              </div>
              <span className="text-[11px] font-bold text-indigo-600 bg-indigo-50 px-2.5 py-1 rounded-full border border-indigo-100">
                Doughnut Chart
              </span>
            </div>

            {/* Doughnut Graphic & Breakdown Row */}
            <div className="mt-4 flex flex-col sm:flex-row items-center justify-around gap-6">
              
              {/* SVG Doughnut */}
              <div className="relative w-48 h-48 flex items-center justify-center shrink-0">
                <svg viewBox="0 0 160 160" className="w-full h-full transform -rotate-90">
                  {/* Background Circle Track */}
                  <circle
                    cx="80"
                    cy="80"
                    r={doughnutAngles.radius}
                    fill="transparent"
                    stroke="#F1F5F9"
                    strokeWidth="20"
                  />

                  {/* Below 75% Arc (Red/Rose) */}
                  <circle
                    cx="80"
                    cy="80"
                    r={doughnutAngles.radius}
                    fill="transparent"
                    stroke="#EF4444"
                    strokeWidth={hoveredDoughnut === 'below' ? '24' : '20'}
                    strokeDasharray={doughnutAngles.belowStrokeDash}
                    strokeDashoffset={doughnutAngles.belowOffset}
                    className="cursor-pointer transition-all duration-300"
                    onMouseEnter={() => setHoveredDoughnut('below')}
                    onMouseLeave={() => setHoveredDoughnut(null)}
                  />

                  {/* Above 75% Arc (Emerald / Blue) */}
                  <circle
                    cx="80"
                    cy="80"
                    r={doughnutAngles.radius}
                    fill="transparent"
                    stroke="#10B981"
                    strokeWidth={hoveredDoughnut === 'above' ? '24' : '20'}
                    strokeDasharray={doughnutAngles.aboveStrokeDash}
                    strokeDashoffset="0"
                    className="cursor-pointer transition-all duration-300"
                    onMouseEnter={() => setHoveredDoughnut('above')}
                    onMouseLeave={() => setHoveredDoughnut(null)}
                  />
                </svg>

                {/* Center Text inside Doughnut */}
                <div className="absolute inset-0 flex flex-col items-center justify-center text-center pointer-events-none">
                  <span className="text-3xl font-black text-slate-900 leading-none">
                    {metrics.above75Percent}%
                  </span>
                  <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500 mt-1">
                    Eligible
                  </span>
                </div>
              </div>

              {/* Side Breakdown Legend */}
              <div className="space-y-3.5 w-full sm:w-auto">
                
                {/* Segment 1: Above 75% */}
                <div 
                  className={`p-3.5 rounded-2xl border transition-all cursor-pointer ${
                    hoveredDoughnut === 'above' ? 'bg-emerald-50 border-emerald-300 scale-102 shadow-xs' : 'bg-slate-50/70 border-slate-200/80 hover:bg-slate-50'
                  }`}
                  onMouseEnter={() => setHoveredDoughnut('above')}
                  onMouseLeave={() => setHoveredDoughnut(null)}
                >
                  <div className="flex items-center justify-between gap-4 mb-1">
                    <div className="flex items-center gap-2">
                      <div className="w-3.5 h-3.5 rounded-md bg-emerald-500" />
                      <span className="text-xs font-extrabold text-slate-900">Above 75% (Eligible)</span>
                    </div>
                    <span className="text-xs font-black text-emerald-600">{metrics.above75Percent}%</span>
                  </div>
                  <div className="flex items-center justify-between text-xs text-slate-500">
                    <span>{metrics.above75Count} Students</span>
                    <span className="text-[10px] font-bold text-emerald-700 bg-emerald-100/80 px-2 py-0.5 rounded-full">Good Standing</span>
                  </div>
                </div>

                {/* Segment 2: Below 75% */}
                <div 
                  className={`p-3.5 rounded-2xl border transition-all cursor-pointer ${
                    hoveredDoughnut === 'below' ? 'bg-rose-50 border-rose-300 scale-102 shadow-xs' : 'bg-slate-50/70 border-slate-200/80 hover:bg-slate-50'
                  }`}
                  onMouseEnter={() => setHoveredDoughnut('below')}
                  onMouseLeave={() => setHoveredDoughnut(null)}
                >
                  <div className="flex items-center justify-between gap-4 mb-1">
                    <div className="flex items-center gap-2">
                      <div className="w-3.5 h-3.5 rounded-md bg-rose-500" />
                      <span className="text-xs font-extrabold text-slate-900">Below 75% (Shortage)</span>
                    </div>
                    <span className="text-xs font-black text-rose-600">{metrics.below75Percent}%</span>
                  </div>
                  <div className="flex items-center justify-between text-xs text-slate-500">
                    <span>{metrics.below75Count} Students</span>
                    <span className="text-[10px] font-bold text-rose-700 bg-rose-100/80 px-2 py-0.5 rounded-full">Action Required</span>
                  </div>
                </div>

              </div>

            </div>
          </div>

          <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500 font-medium">
            <span>Minimum qualifying criterion: <strong>75%</strong></span>
            <span>Total Sample: <strong>{filteredData.length} Students</strong></span>
          </div>
        </div>

        {/* --------------------------------------------------------- */}
        {/* CHART 3: Subject-wise Attendance Distribution — Bar Chart */}
        {/* --------------------------------------------------------- */}
        <div className="bg-white rounded-3xl border border-slate-200 p-6 sm:p-7 shadow-xs flex flex-col justify-between hover:shadow-md transition-shadow">
          <div>
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center font-bold">
                  <TrendingUp className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="font-extrabold text-slate-900 text-base">Subject-wise Attendance Distribution</h3>
                  <p className="text-xs text-slate-500">Student distribution by subject against the 75% threshold</p>
                </div>
              </div>
              <span className="text-[11px] font-bold text-emerald-600 bg-emerald-50 px-2.5 py-1 rounded-full border border-emerald-100">
                Grouped Bar Chart
              </span>
            </div>

            {/* Legend */}
            <div className="flex items-center gap-4 text-xs font-semibold text-slate-600 my-3">
              <div className="flex items-center gap-1.5">
                <span className="w-3 h-3 rounded-md bg-emerald-500 inline-block" />
                <span>At or above 75%</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-3 h-3 rounded-md bg-rose-500 inline-block" />
                <span>Below 75%</span>
              </div>
            </div>

            {/* Grouped Bar Chart SVG */}
            <div className="mt-4 relative overflow-x-auto">
              <div className="min-w-[480px]">
                <svg viewBox="0 0 540 240" className="w-full h-64">
                  {/* Grid Lines */}
                  {[0, 25, 50, 75, 100].map((val) => {
                    const y = 200 - (val / 100) * 160;
                    return (
                      <g key={val}>
                        <line x1="35" y1={y} x2="520" y2={y} stroke="#F1F5F9" strokeWidth="1" />
                        <text x="10" y={y + 3} fontSize="10" fill="#94A3B8">
                          {val}
                        </text>
                      </g>
                    );
                  })}

                  {/* Subject Distribution Pairs */}
                  {subjectDistribution.map((item, idx) => {
                    const barCount = subjectDistribution.length || 1;
                    const availableWidth = 470;
                    const slotWidth = availableWidth / barCount;
                    const singleBarWidth = Math.min(Math.max(slotWidth * 0.36, 8), 16);
                    
                    const groupX = 45 + idx * slotWidth + (slotWidth - singleBarWidth * 2 - 4) / 2;

                    const eligibleHeight = (item.eligible / 100) * 160;
                    const belowTargetHeight = (item.belowTarget / 100) * 160;

                    const eligibleY = 200 - eligibleHeight;
                    const belowTargetY = 200 - belowTargetHeight;

                    const isHovered = hoveredCompare?.subject === item.subject;

                    return (
                      <g
                        key={item.subject}
                        className="cursor-pointer"
                        onMouseEnter={() => setHoveredCompare(item)}
                        onMouseLeave={() => setHoveredCompare(null)}
                      >
                        {/* Hover Column Indicator */}
                        {isHovered && (
                          <rect
                            x={groupX - 3}
                            y={35}
                            width={singleBarWidth * 2 + 10}
                            height={170}
                            rx="6"
                            fill="#F0FDF4"
                            opacity="0.9"
                          />
                        )}

                        {/* At or above 75% Bar */}
                        <rect
                          x={groupX}
                          y={eligibleY}
                          width={singleBarWidth}
                          height={eligibleHeight}
                          rx="4"
                          fill="#10B981"
                        />

                        {/* Below 75% Bar */}
                        <rect
                          x={groupX + singleBarWidth + 3}
                          y={belowTargetY}
                          width={singleBarWidth}
                          height={belowTargetHeight}
                          rx="4"
                          fill="#EF4444"
                        />

                        {/* X-axis Label */}
                        <text
                          x={groupX + singleBarWidth + 1}
                          y={215}
                          textAnchor="middle"
                          fontSize="8.5"
                          fill="#475569"
                          fontWeight={isHovered ? 'bold' : 'normal'}
                        >
                          {item.label}
                        </text>
                      </g>
                    );
                  })}
                </svg>
              </div>
            </div>
          </div>

          {/* Interactive Tooltip Card for Chart 3 */}
          <div className="mt-2 min-h-[44px] bg-slate-50 border border-slate-100 rounded-2xl p-2.5 flex items-center justify-between text-xs">
            {hoveredCompare ? (
              <div className="flex items-center justify-between w-full">
                <span className="font-bold text-slate-900">
                  {hoveredCompare.label}
                </span>
                <div className="flex items-center gap-3 font-semibold">
                  <span className="text-emerald-700">At/above 75%: <strong>{hoveredCompare.eligible}%</strong></span>
                  <span className="text-rose-600">Below 75%: <strong>{hoveredCompare.belowTarget}%</strong></span>
                  <span className="text-slate-500">Records: <strong className="text-slate-800">{hoveredCompare.count}</strong></span>
                </div>
              </div>
            ) : (
              <span className="text-slate-400 italic">Hover over any subject group to view its attendance distribution.</span>
            )}
          </div>
        </div>

        {/* --------------------------------------------------------- */}
        {/* CHART 4: Attendance Distribution — Bar Chart              */}
        {/* --------------------------------------------------------- */}
        <div className="bg-white rounded-3xl border border-slate-200 p-6 sm:p-7 shadow-xs flex flex-col justify-between hover:shadow-md transition-shadow">
          <div>
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center font-bold">
                  <Layers className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="font-extrabold text-slate-900 text-base">Attendance Distribution</h3>
                  <p className="text-xs text-slate-500">Student population segmented by attendance bands</p>
                </div>
              </div>
              <span className="text-[11px] font-bold text-amber-600 bg-amber-50 px-2.5 py-1 rounded-full border border-amber-100">
                Distribution Chart
              </span>
            </div>

            {/* Distribution Histogram SVG */}
            <div className="mt-4 relative overflow-x-auto">
              <div className="min-w-[460px]">
                <svg viewBox="0 0 500 230" className="w-full h-64">
                  {/* Grid Lines */}
                  {[0, 2, 4, 6, 8].map((val) => {
                    const y = 180 - (val / 8) * 140;
                    return (
                      <g key={val}>
                        <line x1="35" y1={y} x2="480" y2={y} stroke="#F1F5F9" strokeWidth="1" />
                        <text x="15" y={y + 3} fontSize="10" fill="#94A3B8">
                          {val}
                        </text>
                      </g>
                    );
                  })}

                  {/* Distribution Bins */}
                  {distributionData.map((bin, idx) => {
                    const x = 50 + idx * 86;
                    const barWidth = 60;
                    const maxScale = Math.max(...distributionData.map((d) => d.count), 6);
                    const barHeight = Math.max((bin.count / maxScale) * 140, 6);
                    const y = 180 - barHeight;

                    const isHovered = hoveredDist?.range === bin.range;

                    return (
                      <g
                        key={bin.range}
                        className="cursor-pointer"
                        onMouseEnter={() => setHoveredDist(bin)}
                        onMouseLeave={() => setHoveredDist(null)}
                      >
                        {/* Bar */}
                        <rect
                          x={x}
                          y={y}
                          width={barWidth}
                          height={barHeight}
                          rx="8"
                          fill={bin.color}
                          opacity={isHovered ? 1 : 0.88}
                          className="transition-all duration-300"
                        />

                        {/* Count Badge on Top */}
                        <text
                          x={x + barWidth / 2}
                          y={y - 8}
                          textAnchor="middle"
                          fontSize="11"
                          fontWeight="bold"
                          fill={bin.color}
                        >
                          {bin.count} {bin.count === 1 ? 'student' : 'students'}
                        </text>

                        {/* Range Label */}
                        <text
                          x={x + barWidth / 2}
                          y={196}
                          textAnchor="middle"
                          fontSize="9.5"
                          fontWeight="bold"
                          fill="#1E293B"
                        >
                          {bin.range}
                        </text>

                        {/* Bracket Label */}
                        <text
                          x={x + barWidth / 2}
                          y={210}
                          textAnchor="middle"
                          fontSize="8.5"
                          fill="#64748B"
                        >
                          {bin.label}
                        </text>
                      </g>
                    );
                  })}
                </svg>
              </div>
            </div>
          </div>

          {/* Interactive Info Footer for Chart 4 */}
          <div className="mt-2 min-h-[44px] bg-slate-50 border border-slate-100 rounded-2xl p-2.5 flex items-center justify-between text-xs">
            {hoveredDist ? (
              <div className="flex items-center justify-between w-full">
                <span className="font-bold text-slate-900">
                  Bracket {hoveredDist.range} ({hoveredDist.label}):
                </span>
                <span className="font-bold text-blue-600">
                  {hoveredDist.count} Students ({hoveredDist.percentage}% of cohort)
                </span>
              </div>
            ) : (
              <div className="flex items-center justify-between w-full text-slate-500 font-medium">
                <span>Healthy Distribution Target: <strong>&gt;80% in &ge;75% brackets</strong></span>
                <span className="font-bold text-emerald-600">{metrics.above75Percent}% Compliant</span>
              </div>
            )}
          </div>
        </div>

      </div>
    </div>
  );
}
