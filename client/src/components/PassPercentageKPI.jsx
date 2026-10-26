import React, { useState, useEffect, useMemo } from 'react';
import {
  GraduationCap,
  CheckCircle2,
  AlertCircle,
  TrendingUp,
  BarChart3,
  Calendar,
  Layers,
  Sparkles,
  Info,
  BookOpen,
  Users,
  Award,
  AlertTriangle
} from 'lucide-react';

import { API_BASE_URL, apiFetch } from '../api';

const SUBJECT_DETAILS = {
  DM: { code: 'DM', name: 'Discrete Mathematics', credits: 4, icon: '📐' },
  DSC: { code: 'DSC', name: 'Dynamics of Social Change', credits: 3, icon: '🌍' },
  COA: { code: 'COA', name: 'Computer Organization & Architecture', credits: 4, icon: '💻' },
  Python: { code: 'Python', name: 'Industry Coding Practice', credits: 3, icon: '🐍' },
  ML: { code: 'ML', name: 'Machine Learning', credits: 4, icon: '🤖' },
};

export default function PassPercentageKPI({ academicYear = '2024-2025', department, section, onAcademicYearChange }) {
  const [internalYear, setInternalYear] = useState(academicYear);

  useEffect(() => {
    setInternalYear(academicYear);
  }, [academicYear]);

  const activeYear = internalYear || academicYear;
  const [data, setData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [hoveredSubject, setHoveredSubject] = useState(null);
  const [showSubjectTable, setShowSubjectTable] = useState(false);

  useEffect(() => {
    async function fetchPassPercentage() {
      setIsLoading(true);
      setError('');
      try {
        const queryParam = `?${new URLSearchParams({ academic_year: activeYear, ...(department ? { department } : {}), ...(section ? { section } : {}) })}`;
        const res = await apiFetch(`${API_BASE_URL}/api/kpis/pass-percentage${queryParam}`);
        if (!res.ok) {
          throw new Error('Unable to retrieve pass percentage KPI data.');
        }
        const json = await res.json();
        setData(json);
      } catch (err) {
        setError(err.message || 'Error fetching pass percentage KPI.');
      } finally {
        setIsLoading(false);
      }
    }
    fetchPassPercentage();
  }, [activeYear, department, section]);

  const totalEvaluated = data?.total_students_evaluated || 0;
  const overallPassed = data?.overall?.passed || 0;
  const overallFailed = data?.overall?.failed || 0;
  const overallPassPct = data?.overall?.pass_percentage || 0;
  const overallFailPct = data?.overall?.fail_percentage || 0;
  const subjectsList = data?.subjects || [];

  // Grouped Bar Chart Maximum for Scaling
  const maxBarCount = useMemo(() => {
    if (!subjectsList.length) return 10;
    const maxVal = Math.max(
      ...subjectsList.map((s) => Math.max(s.passed, s.failed)),
      1
    );
    return Math.ceil(maxVal * 1.15) || 10;
  }, [subjectsList]);

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* ========================================================= */}
      {/* HEADER SECTION                                            */}
      {/* ========================================================= */}
      <section className="relative overflow-hidden rounded-3xl border border-indigo-200/80 bg-gradient-to-br from-white via-[#F5F7FF] to-[#EBEFFF] p-6 sm:p-8 shadow-sm">
        <div className="absolute top-0 right-0 -mt-8 -mr-8 w-64 h-64 rounded-full bg-indigo-500/10 blur-3xl pointer-events-none" />
        <div className="absolute bottom-0 left-1/3 -mb-10 w-80 h-80 rounded-full bg-blue-500/10 blur-3xl pointer-events-none" />

        <div className="relative z-10">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-indigo-100/80">
            <div>
              <div className="flex items-center gap-2 mb-2">
                <span className="px-3 py-1 rounded-full bg-[#4F46E5] text-white text-xs font-bold uppercase tracking-wider flex items-center gap-1.5 shadow-sm shadow-indigo-500/20">
                  <GraduationCap className="w-3.5 h-3.5" />
                  Academic Excellence KPI
                </span>
                <span className="text-xs font-semibold text-slate-500">• Academic Year {activeYear}</span>
              </div>
              <h2 className="text-2xl sm:text-3xl font-black text-slate-900 tracking-tight flex items-center gap-2.5">
                <span>Pass Percentage KPI</span>
                <span className="text-2xl">🎓</span>
              </h2>
              <p className="text-slate-600 text-xs sm:text-sm mt-1 max-w-2xl">
                Comprehensive semester outcome tracking for Artificial Intelligence and Data Science (AIDS), evaluating subject-level pass thresholds (≥ 40 marks) and overall student success across all 5 mandatory subjects.
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-3">
              <div className="flex items-center gap-2 bg-white/90 backdrop-blur-md border border-slate-200/80 rounded-2xl px-3.5 py-2 shadow-xs text-xs font-bold text-slate-700">
                <Calendar className="w-4 h-4 text-[#4F46E5]" />
                <span>Year:</span>
                <select
                  value={activeYear}
                  onChange={(e) => {
                    const newYear = e.target.value;
                    setInternalYear(newYear);
                    if (onAcademicYearChange) onAcademicYearChange(newYear);
                  }}
                  className="bg-transparent font-bold text-slate-900 focus:outline-none cursor-pointer pr-1"
                >
                  <option value="2024-2025">2024-2025</option>
                  <option value="2025-2026">2025-2026</option>
                </select>
              </div>

              <div className="flex items-center gap-2 bg-white/90 backdrop-blur-md border border-slate-200/80 rounded-2xl px-3.5 py-2 shadow-xs text-xs font-bold text-slate-700">
                <BookOpen className="w-4 h-4 text-[#4F46E5]" />
                <span>Dept: AIDS</span>
              </div>

              <button
                onClick={() => setShowSubjectTable(!showSubjectTable)}
                className="flex items-center gap-1.5 px-3.5 py-2 rounded-2xl text-xs font-bold transition-all duration-200 bg-white hover:bg-slate-50 border border-slate-200/80 text-slate-700 shadow-xs cursor-pointer"
              >
                <Layers className="w-3.5 h-3.5 text-[#4F46E5]" />
                <span>{showSubjectTable ? 'Hide Table' : 'Subject Table'}</span>
              </button>
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="mt-4 rounded-2xl border border-rose-200 bg-rose-50 p-4 text-xs text-rose-700 flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0 text-rose-500" />
              <span>{error}</span>
            </div>
          )}

          {/* Empty State Banner when no evaluated student records */}
          {totalEvaluated === 0 && !isLoading && !error && (
            <div className="mt-6 rounded-2xl border border-indigo-200 bg-white p-6 sm:p-8 text-center shadow-xs">
              <div className="mx-auto w-12 h-12 rounded-2xl bg-indigo-50 text-[#4F46E5] flex items-center justify-center mb-3">
                <GraduationCap className="w-6 h-6" />
              </div>
              <h3 className="text-base font-bold text-slate-800">No Evaluated Student Marks for Academic Year {activeYear}</h3>
              <p className="text-xs text-slate-500 mt-1 max-w-md mx-auto">
                There are currently no student records in the database with complete marks for all 5 subjects (DM, DSC, COA, Python, ML). Upload a student marks spreadsheet for {activeYear} to view live KPI analytics.
              </p>
            </div>
          )}

          {/* ========================================================= */}
          {/* 5 KPI SUMMARY CARDS                                       */}
          {/* ========================================================= */}
          <div className="mt-6 grid grid-cols-1 lg:grid-cols-12 gap-6 items-stretch">
            
            {/* CARD 1: Featured Overall Pass % (5 cols on LG) */}
            <div className="lg:col-span-5 bg-gradient-to-br from-[#312E81] via-[#3730A3] to-[#4F46E5] text-white rounded-3xl p-6 sm:p-7 shadow-lg shadow-indigo-600/15 flex flex-col justify-between relative overflow-hidden group">
              <div className="absolute top-0 right-0 translate-x-4 -translate-y-4 w-40 h-40 bg-white/10 rounded-full blur-2xl pointer-events-none" />

              <div>
                <div className="flex items-center justify-between mb-4">
                  <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-white/15 backdrop-blur-md border border-white/20 text-indigo-100 text-xs font-bold">
                    <Sparkles className="w-3.5 h-3.5 text-yellow-300" />
                    Top Core Metric
                  </span>

                  <span className={`px-3 py-1 rounded-full text-xs font-bold backdrop-blur-md border ${
                    overallPassPct >= 60
                      ? 'bg-emerald-500/20 border-emerald-300/40 text-emerald-200'
                      : 'bg-rose-500/20 border-rose-300/40 text-rose-200'
                  }`}>
                    {overallPassPct >= 60 ? '✓ Institutional Benchmark Met' : '⚠ Action Required'}
                  </span>
                </div>

                <p className="text-indigo-200 text-xs font-bold uppercase tracking-wider">
                  Overall Student Pass Rate
                </p>

                <div className="mt-3 flex items-baseline gap-3">
                  <span className="text-5xl sm:text-6xl font-black tracking-tight text-white">
                    {overallPassPct}%
                  </span>
                  <div className="flex flex-col text-xs text-indigo-200">
                    <span className="font-semibold">Target: 75.0%</span>
                    <span className="text-emerald-300 font-bold">Min Pass: ≥ 40 Marks</span>
                  </div>
                </div>

                <p className="text-[11px] text-indigo-200 mt-2">
                  Criteria: Student passes all 5 core subjects (DM, DSC, COA, Python, ML).
                </p>
              </div>

              {/* Visual Progress Bar */}
              <div className="mt-6 pt-4 border-t border-white/15">
                <div className="flex justify-between text-xs text-indigo-100 mb-1.5 font-medium">
                  <span>Pass Rate vs Evaluated Cohort</span>
                  <span>{overallPassed} / {totalEvaluated} Passed</span>
                </div>
                <div className="w-full h-3 bg-black/25 rounded-full overflow-hidden p-0.5">
                  <div
                    className={`h-full rounded-full transition-all duration-1000 ${
                      overallPassPct >= 60
                        ? 'bg-gradient-to-r from-emerald-400 to-emerald-300'
                        : 'bg-gradient-to-r from-amber-400 to-rose-400'
                    }`}
                    style={{ width: `${Math.min(overallPassPct, 100)}%` }}
                  />
                </div>
                <div className="flex items-center justify-between text-[11px] text-indigo-200 mt-2">
                  <span>0% (All Failed)</span>
                  <span className="font-bold text-emerald-300">Target ≥ 75%</span>
                  <span>100% (100% Cleared)</span>
                </div>
              </div>
            </div>

            {/* 4 Supporting Metric Cards (7 cols on LG) */}
            <div className="lg:col-span-7 grid grid-cols-1 sm:grid-cols-2 gap-4">
              
              {/* CARD 2: Overall Fail Percentage */}
              <div className="bg-white/95 rounded-2xl p-4 sm:p-5 border border-slate-200/80 shadow-xs flex flex-col justify-between hover:shadow-md transition-shadow duration-200">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Overall Fail Rate</span>
                  <div className="w-8 h-8 rounded-xl bg-rose-50 text-rose-600 flex items-center justify-center font-bold">
                    <AlertTriangle className="w-4 h-4" />
                  </div>
                </div>
                <div>
                  <div className="flex items-baseline gap-2">
                    <span className="text-3xl font-black text-rose-600">{overallFailPct}%</span>
                    <span className="text-xs font-bold text-rose-700 bg-rose-50 px-2 py-0.5 rounded-full">
                      {overallFailed} of {totalEvaluated}
                    </span>
                  </div>
                  <p className="text-xs text-slate-500 mt-1 font-medium">
                    Students scoring &lt; 40 in at least one subject.
                  </p>
                </div>
              </div>

              {/* CARD 3: Students Passed Overall */}
              <div className="bg-white/95 rounded-2xl p-4 sm:p-5 border border-slate-200/80 shadow-xs flex flex-col justify-between hover:shadow-md transition-shadow duration-200">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Passed All 5 Subjects</span>
                  <div className="w-8 h-8 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center font-bold">
                    <CheckCircle2 className="w-4 h-4" />
                  </div>
                </div>
                <div>
                  <div className="flex items-baseline gap-2">
                    <span className="text-3xl font-black text-slate-900">{overallPassed}</span>
                    <span className="text-xs font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full">
                      Fully Cleared
                    </span>
                  </div>
                  <p className="text-xs text-slate-500 mt-1 font-medium">
                    Students with zero backlogs across all 5 subjects.
                  </p>
                </div>
              </div>

              {/* CARD 4: Students Failed Overall */}
              <div className="bg-white/95 rounded-2xl p-4 sm:p-5 border border-slate-200/80 shadow-xs flex flex-col justify-between hover:shadow-md transition-shadow duration-200">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Failed ≥ 1 Subject</span>
                  <div className="w-8 h-8 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center font-bold">
                    <AlertCircle className="w-4 h-4" />
                  </div>
                </div>
                <div>
                  <div className="flex items-baseline gap-2">
                    <span className="text-3xl font-black text-slate-900">{overallFailed}</span>
                    <span className="text-xs font-bold text-amber-700 bg-amber-50 px-2 py-0.5 rounded-full">
                      Arrears / Remedial
                    </span>
                  </div>
                  <p className="text-xs text-slate-500 mt-1 font-medium">
                    Require supplemental examinations or faculty coaching.
                  </p>
                </div>
              </div>

              {/* CARD 5: Total Students Evaluated */}
              <div className="bg-white/95 rounded-2xl p-4 sm:p-5 border border-slate-200/80 shadow-xs flex flex-col justify-between hover:shadow-md transition-shadow duration-200">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Total Evaluated Cohort</span>
                  <div className="w-8 h-8 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center font-bold">
                    <Users className="w-4 h-4" />
                  </div>
                </div>
                <div>
                  <div className="flex items-baseline gap-2">
                    <span className="text-3xl font-black text-slate-900">{totalEvaluated}</span>
                    <span className="text-xs font-bold text-blue-700 bg-blue-50 px-2 py-0.5 rounded-full">
                      Denominator
                    </span>
                  </div>
                  <p className="text-xs text-slate-500 mt-1 font-medium">
                    Total students with valid 5-subject marks records.
                  </p>
                </div>
              </div>

            </div>
          </div>
        </div>
      </section>

      {/* ========================================================= */}
      {/* CHARTS SECTION: CHART A & CHART B                         */}
      {/* ========================================================= */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        
        {/* ========================================================= */}
        {/* CHART A: SUBJECT-WISE PASS AND FAIL (7 cols on LG)        */}
        {/* Grouped Bar Chart: DM, DSC, COA, Python, ML               */}
        {/* ========================================================= */}
        <section className="lg:col-span-7 bg-white rounded-3xl border border-slate-200 p-6 sm:p-7 shadow-xs">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-5 border-b border-slate-100">
            <div>
              <div className="flex items-center gap-2">
                <div className="p-1.5 rounded-lg bg-emerald-50 text-emerald-600">
                  <BarChart3 className="w-4 h-4" />
                </div>
                <h3 className="text-lg font-extrabold text-slate-900">
                  Chart A — Subject-wise Pass and Fail
                </h3>
              </div>
              <p className="text-xs text-slate-500 mt-1">
                Grouped comparison showing exact counts and pass rates for each individual course.
              </p>
            </div>

            {/* Legend */}
            <div className="flex items-center gap-4 text-xs font-bold">
              <div className="flex items-center gap-1.5">
                <span className="w-3 h-3 rounded-md bg-[#10B981]" />
                <span className="text-slate-700">Passed</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-3 h-3 rounded-md bg-[#EF4444]" />
                <span className="text-slate-700">Failed</span>
              </div>
            </div>
          </div>

          {/* SVG Grouped Bar Chart */}
          <div className="mt-6">
            {subjectsList.length === 0 ? (
              <div className="h-64 flex items-center justify-center text-xs text-slate-400">
                Awaiting student marks upload to display subject-wise chart.
              </div>
            ) : (
              <div className="w-full overflow-x-auto">
                <svg
                  viewBox="0 0 650 300"
                  className="w-full min-w-[540px] h-[300px]"
                  role="img"
                  aria-label="Subject-wise pass and fail grouped bar chart"
                >
                  {/* Grid Lines */}
                  {[0, 0.25, 0.5, 0.75, 1.0].map((ratio) => {
                    const y = 240 - ratio * 190;
                    const val = Math.round(ratio * maxBarCount);
                    return (
                      <g key={ratio}>
                        <line x1="50" y1={y} x2="620" y2={y} stroke="#F1F5F9" strokeDasharray="3 3" />
                        <text x="35" y={y + 4} textAnchor="end" fontSize="10" fill="#94A3B8" fontWeight="600">
                          {val}
                        </text>
                      </g>
                    );
                  })}

                  {/* Baseline Axis */}
                  <line x1="50" y1="240" x2="620" y2="240" stroke="#CBD5E1" strokeWidth="1.5" />

                  {/* 5 Subjects Grouped Bars */}
                  {subjectsList.map((subj, idx) => {
                    const groupWidth = 110;
                    const groupX = 65 + idx * groupWidth;
                    const barWidth = 32;

                    const passHeight = maxBarCount > 0 ? (subj.passed / maxBarCount) * 190 : 0;
                    const passY = 240 - passHeight;

                    const failHeight = maxBarCount > 0 ? (subj.failed / maxBarCount) * 190 : 0;
                    const failY = 240 - failHeight;

                    const isHovered = hoveredSubject === subj.subject;

                    return (
                      <g
                        key={subj.subject}
                        onMouseEnter={() => setHoveredSubject(subj.subject)}
                        onMouseLeave={() => setHoveredSubject(null)}
                        className="cursor-pointer transition-opacity duration-150"
                        opacity={hoveredSubject && !isHovered ? 0.45 : 1}
                      >
                        {/* Hover Background Highlight */}
                        {isHovered && (
                          <rect
                            x={groupX - 10}
                            y="25"
                            width={barWidth * 2 + 30}
                            height="225"
                            rx="12"
                            fill="#F8FAFC"
                          />
                        )}

                        {/* Bar 1: Passed (Green) */}
                        <rect
                          x={groupX}
                          y={passY}
                          width={barWidth}
                          height={Math.max(passHeight, 2)}
                          rx="6"
                          fill="#10B981"
                          className="transition-all duration-300"
                        />
                        {/* Passed Count Label */}
                        <text
                          x={groupX + barWidth / 2}
                          y={passY - 6}
                          textAnchor="middle"
                          fontSize="11"
                          fontWeight="700"
                          fill="#047857"
                        >
                          {subj.passed}
                        </text>

                        {/* Bar 2: Failed (Red) */}
                        <rect
                          x={groupX + barWidth + 8}
                          y={failY}
                          width={barWidth}
                          height={Math.max(failHeight, 2)}
                          rx="6"
                          fill="#EF4444"
                          className="transition-all duration-300"
                        />
                        {/* Failed Count Label */}
                        <text
                          x={groupX + barWidth + 8 + barWidth / 2}
                          y={failY - 6}
                          textAnchor="middle"
                          fontSize="11"
                          fontWeight="700"
                          fill="#B91C1C"
                        >
                          {subj.failed}
                        </text>

                        {/* Subject Code Label */}
                        <text
                          x={groupX + barWidth + 4}
                          y="262"
                          textAnchor="middle"
                          fontSize="12"
                          fontWeight="800"
                          fill="#1E293B"
                        >
                          {subj.subject}
                        </text>

                        {/* Pass % Badge below label */}
                        <text
                          x={groupX + barWidth + 4}
                          y="278"
                          textAnchor="middle"
                          fontSize="10"
                          fontWeight="700"
                          fill="#10B981"
                        >
                          {subj.pass_percentage}% Pass
                        </text>
                      </g>
                    );
                  })}
                </svg>
              </div>
            )}
          </div>

          {/* Active Hover Detail Tooltip Banner */}
          {hoveredSubject && (
            <div className="mt-4 p-3.5 rounded-2xl bg-slate-50 border border-slate-200 flex items-center justify-between text-xs animate-fadeIn">
              <div className="flex items-center gap-2">
                <span className="text-lg">{SUBJECT_DETAILS[hoveredSubject]?.icon || '📚'}</span>
                <div>
                  <p className="font-bold text-slate-900">
                    {hoveredSubject} — {SUBJECT_DETAILS[hoveredSubject]?.name || hoveredSubject}
                  </p>
                  <p className="text-[11px] text-slate-500">Pass Criteria: Marks ≥ 40 / 100</p>
                </div>
              </div>
              <div className="flex items-center gap-4 text-xs font-bold">
                <span className="text-emerald-700">
                  Passed: {subjectsList.find((s) => s.subject === hoveredSubject)?.passed} ({subjectsList.find((s) => s.subject === hoveredSubject)?.pass_percentage}%)
                </span>
                <span className="text-rose-700">
                  Failed: {subjectsList.find((s) => s.subject === hoveredSubject)?.failed} ({subjectsList.find((s) => s.subject === hoveredSubject)?.fail_percentage}%)
                </span>
              </div>
            </div>
          )}
        </section>

        {/* ========================================================= */}
        {/* CHART B: OVERALL STUDENT PASS/FAIL (5 cols on LG)         */}
        {/* Overall Pass = All 5 Passed; Fail = >= 1 Failed           */}
        {/* ========================================================= */}
        <section className="lg:col-span-5 bg-white rounded-3xl border border-slate-200 p-6 sm:p-7 shadow-xs flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 pb-5 border-b border-slate-100">
              <div className="p-1.5 rounded-lg bg-indigo-50 text-indigo-600">
                <Award className="w-4 h-4" />
              </div>
              <div>
                <h3 className="text-lg font-extrabold text-slate-900">
                  Chart B — Overall Student Pass / Fail
                </h3>
                <p className="text-xs text-slate-500 mt-1">
                  Distribution of students passing all 5 subjects vs students failing one or more subjects.
                </p>
              </div>
            </div>

            {/* Circular Donut Diagram */}
            <div className="py-6 flex flex-col items-center justify-center">
              <div className="relative w-52 h-52 flex items-center justify-center">
                <svg className="w-full h-full -rotate-90" viewBox="0 0 160 160">
                  {/* Background Track */}
                  <circle
                    cx="80"
                    cy="80"
                    r="60"
                    fill="none"
                    stroke="#F1F5F9"
                    strokeWidth="20"
                  />
                  {/* Passed Arc (Green) */}
                  <circle
                    cx="80"
                    cy="80"
                    r="60"
                    fill="none"
                    stroke="#10B981"
                    strokeWidth="20"
                    strokeDasharray={`${(overallPassPct / 100) * 377} 377`}
                    strokeLinecap="round"
                    className="transition-all duration-1000 ease-out"
                  />
                  {/* Failed Arc (Red) */}
                  <circle
                    cx="80"
                    cy="80"
                    r="60"
                    fill="none"
                    stroke="#EF4444"
                    strokeWidth="20"
                    strokeDasharray={`${(overallFailPct / 100) * 377} 377`}
                    strokeDashoffset={`${-(overallPassPct / 100) * 377}`}
                    strokeLinecap="round"
                    className="transition-all duration-1000 ease-out"
                  />
                </svg>

                {/* Center Stats Overlay */}
                <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
                  <span className="text-3xl font-black text-slate-900">{overallPassPct}%</span>
                  <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">Overall Pass</span>
                  <span className="text-[10px] text-slate-400 font-semibold">{overallPassed} / {totalEvaluated} Cohort</span>
                </div>
              </div>

              {/* Counts and Percentages Breakdown Badges */}
              <div className="w-full grid grid-cols-2 gap-3 mt-6">
                <div className="rounded-2xl p-3.5 bg-emerald-50/70 border border-emerald-200/80 text-center">
                  <div className="flex items-center justify-center gap-1.5 text-xs font-bold text-emerald-800 mb-1">
                    <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
                    Passed Overall
                  </div>
                  <p className="text-2xl font-black text-emerald-900">{overallPassed}</p>
                  <p className="text-[11px] font-bold text-emerald-700 mt-0.5">{overallPassPct}% of Students</p>
                  <p className="text-[10px] text-emerald-600 mt-1">Cleared All 5 Subjects</p>
                </div>

                <div className="rounded-2xl p-3.5 bg-rose-50/70 border border-rose-200/80 text-center">
                  <div className="flex items-center justify-center gap-1.5 text-xs font-bold text-rose-800 mb-1">
                    <span className="w-2.5 h-2.5 rounded-full bg-rose-500" />
                    Failed Overall
                  </div>
                  <p className="text-2xl font-black text-rose-900">{overallFailed}</p>
                  <p className="text-[11px] font-bold text-rose-700 mt-0.5">{overallFailPct}% of Students</p>
                  <p className="text-[10px] text-rose-600 mt-1">Failed ≥ 1 Subject</p>
                </div>
              </div>
            </div>
          </div>

          {/* Footer Note */}
          <div className="pt-4 border-t border-slate-100 text-[11px] text-slate-500 flex items-center gap-1.5">
            <Info className="w-4 h-4 text-indigo-500 shrink-0" />
            <span>Strict standard: Failure in any single subject counts as an overall failure for this KPI.</span>
          </div>
        </section>
      </div>

      {/* ========================================================= */}
      {/* SUBJECT BREAKDOWN TABLE (Collapsible or visible)         */}
      {/* ========================================================= */}
      {showSubjectTable && (
        <section className="bg-white rounded-3xl border border-slate-200 p-6 sm:p-7 shadow-xs animate-fadeIn">
          <div className="flex items-center justify-between pb-4 border-b border-slate-100">
            <div>
              <h3 className="text-base font-extrabold text-slate-900">
                Subject-Level Performance Breakdown
              </h3>
              <p className="text-xs text-slate-500 mt-0.5">
                Detailed passing and failing student headcounts for Department of Artificial Intelligence & Data Science.
              </p>
            </div>
            <span className="px-3 py-1 rounded-full bg-indigo-50 text-[#4F46E5] text-xs font-bold">
              Pass Mark: ≥ 40 / 100
            </span>
          </div>

          <div className="mt-4 overflow-x-auto">
            <table className="w-full text-xs text-left">
              <thead>
                <tr className="bg-slate-50 text-slate-600 font-bold border-b border-slate-200">
                  <th className="px-4 py-3 rounded-l-xl">Subject Code</th>
                  <th className="px-4 py-3">Subject Name</th>
                  <th className="px-4 py-3 text-center">Evaluated</th>
                  <th className="px-4 py-3 text-center text-emerald-700">Passed (≥ 40)</th>
                  <th className="px-4 py-3 text-center text-emerald-700">Pass %</th>
                  <th className="px-4 py-3 text-center text-rose-700">Failed (&lt; 40)</th>
                  <th className="px-4 py-3 text-center text-rose-700">Fail %</th>
                  <th className="px-4 py-3 rounded-r-xl">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-700 font-medium">
                {subjectsList.map((s) => (
                  <tr key={s.subject} className="hover:bg-slate-50/80 transition-colors">
                    <td className="px-4 py-3 font-bold text-slate-900">
                      <span className="px-2.5 py-1 rounded-lg bg-indigo-50 text-[#4F46E5]">
                        {s.subject}
                      </span>
                    </td>
                    <td className="px-4 py-3 font-semibold text-slate-800">
                      {s.subject_name}
                    </td>
                    <td className="px-4 py-3 text-center font-bold text-slate-900">{s.total}</td>
                    <td className="px-4 py-3 text-center font-bold text-emerald-600">{s.passed}</td>
                    <td className="px-4 py-3 text-center font-bold text-emerald-700 bg-emerald-50/40">
                      {s.pass_percentage}%
                    </td>
                    <td className="px-4 py-3 text-center font-bold text-rose-600">{s.failed}</td>
                    <td className="px-4 py-3 text-center font-bold text-rose-700 bg-rose-50/40">
                      {s.fail_percentage}%
                    </td>
                    <td className="px-4 py-3">
                      <span className={`px-2.5 py-1 rounded-full text-[10px] font-bold ${
                        s.pass_percentage >= 75
                          ? 'bg-emerald-100 text-emerald-800'
                          : s.pass_percentage >= 50
                          ? 'bg-amber-100 text-amber-800'
                          : 'bg-rose-100 text-rose-800'
                      }`}>
                        {s.pass_percentage >= 75 ? 'Optimal' : s.pass_percentage >= 50 ? 'Moderate' : 'Critical'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}
    </div>
  );
}
