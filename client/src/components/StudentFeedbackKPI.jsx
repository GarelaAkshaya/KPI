import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  MessageSquare,
  RefreshCw,
  FileSpreadsheet,
  Star,
  CheckCircle2,
  AlertCircle,
  Lightbulb,
  BarChart3,
  TrendingUp,
  Layers,
  Sparkles,
} from 'lucide-react';
import { API_BASE_URL, apiFetch } from '../api';

const validAverage = (value) =>
  value !== null && value !== undefined && Number.isFinite(Number(value)) ? Number(value) : null;

export default function StudentFeedbackKPI({
  academicYear = '2025-2026',
  department = '',
  section = '',
  onAcademicYearChange,
}) {
  // Filter States: Department, Academic Year, Semester
  const [selectedYear, setSelectedYear] = useState(academicYear || '2025-2026');
  const [selectedDepartment, setSelectedDepartment] = useState(department || 'All');
  const [selectedSemester, setSelectedSemester] = useState('All');

  // Feedback Data State
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [updatedAt, setUpdatedAt] = useState(null);

  // Google Sheets Import States
  const [importingSheets, setImportingSheets] = useState(false);
  const [importMessage, setImportMessage] = useState('');
  const [importError, setImportError] = useState('');
  const [importResult, setImportResult] = useState(null);

  // Synchronize prop updates
  useEffect(() => {
    if (academicYear && academicYear !== selectedYear) {
      setSelectedYear(academicYear);
    }
  }, [academicYear]);

  useEffect(() => {
    if (department && department !== selectedDepartment) {
      setSelectedDepartment(department);
    }
  }, [department]);

  // Load Feedback Summary
  const load = useCallback(
    async (signal) => {
      try {
        const params = new URLSearchParams();
        if (selectedYear && selectedYear !== 'All') params.set('academic_year', selectedYear);
        if (selectedDepartment && selectedDepartment !== 'All') params.set('department', selectedDepartment);
        if (selectedSemester && selectedSemester !== 'All') params.set('semester', selectedSemester);

        const response = await apiFetch(`${API_BASE_URL}/api/feedback/summary?${params.toString()}`, { signal });
        if (!response.ok) throw new Error(`Feedback data could not be loaded (HTTP ${response.status}).`);

        const summaryData = await response.json();
        setSummary(summaryData);
        setError('');
        setUpdatedAt(new Date());
      } catch (e) {
        if (e.name !== 'AbortError') {
          setError(e.message || 'Unable to reach the feedback service.');
        }
      } finally {
        if (!signal?.aborted) setLoading(false);
      }
    },
    [selectedYear, selectedDepartment, selectedSemester]
  );

  useEffect(() => {
    const controller = new AbortController();
    setSummary(null);
    setLoading(true);
    load(controller.signal);
    const timer = window.setInterval(() => load(controller.signal), 30000);
    return () => {
      controller.abort();
      window.clearInterval(timer);
    };
  }, [load]);

  // Google Sheets Feedback Import Handler
  const handleGoogleSheetsImport = async () => {
    setImportingSheets(true);
    setImportMessage('');
    setImportError('');
    setImportResult(null);
    try {
      const response = await apiFetch(`${API_BASE_URL}/api/admin/feedback/import-google-sheet`, {
        method: 'POST',
      });
      const result = await response.json();
      if (!response.ok) {
        throw new Error(result.detail || `Import failed with HTTP ${response.status}`);
      }
      setImportResult(result);
      setImportMessage(
        result.message ||
          `Successfully processed ${result.total_rows} responses (${result.imported} newly imported, ${result.skipped} skipped duplicates).`
      );
      // Refresh dashboard after successful import
      const controller = new AbortController();
      load(controller.signal);
    } catch (err) {
      setImportError(err.message || 'Unable to import feedback from Google Sheets.');
    } finally {
      setImportingSheets(false);
    }
  };

  // Dynamic filter lists from summary
  const availableYears = useMemo(() => {
    const list = summary?.available_academic_years || ['2025-2026', '2024-2025'];
    return Array.from(new Set(list));
  }, [summary]);

  const availableDepartments = useMemo(() => {
    const list = summary?.available_departments || ['CSE', 'AI & Data Science'];
    return Array.from(new Set(list));
  }, [summary]);

  const availableSemesters = useMemo(() => {
    const list = summary?.available_semesters || ['Semester 1', 'Semester 2', 'Semester 3', 'Semester 4'];
    return Array.from(new Set(list));
  }, [summary]);

  // 1. Overall Learning Experience metrics
  const total = Number(summary?.total_responses || 0);
  const allTotal = Number(summary?.all_responses || total);
  const otherYearCount = Number(summary?.other_year_responses || 0);
  const avgSatisfaction =
    validAverage(summary?.average_overall_satisfaction) ??
    validAverage(summary?.averages?.overall_satisfaction) ??
    null;

  // 2. Rating distribution (1–5)
  const ratingDistribution = useMemo(() => {
    const dist = summary?.rating_distribution || summary?.rating_distributions?.overall_satisfaction || {};
    return {
      5: Number(dist[5] || dist['5'] || 0),
      4: Number(dist[4] || dist['4'] || 0),
      3: Number(dist[3] || dist['3'] || 0),
      2: Number(dist[2] || dist['2'] || 0),
      1: Number(dist[1] || dist['1'] || 0),
    };
  }, [summary]);

  const totalRated = useMemo(() => {
    return Object.values(ratingDistribution).reduce((a, b) => a + b, 0);
  }, [ratingDistribution]);

  // 3. Improvement areas summary
  const improvementAreas = useMemo(() => {
    return Array.isArray(summary?.improvement_areas_summary) ? summary.improvement_areas_summary : [];
  }, [summary]);

  const topImprovement = useMemo(() => {
    if (!improvementAreas.length) return null;
    const sorted = [...improvementAreas].sort((a, b) => b.count - a.count);
    return sorted[0].count > 0 ? sorted[0] : null;
  }, [improvementAreas]);

  return (
    <div className="space-y-6 rounded-3xl border border-[#E2E8F0] bg-white p-5 shadow-sm sm:p-8">
      {/* Header & Main Actions */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <div className="mb-1 flex items-center gap-2 text-xs font-semibold text-[#64748B]">
            <MessageSquare className="h-4 w-4 text-[#2563EB]" /> Institutional KPI Monitoring
          </div>
          <h3 className="text-2xl font-extrabold tracking-tight text-[#1E293B] sm:text-3xl">
            Student Academic Feedback
          </h3>
          <p className="mt-1 text-sm text-[#64748B]">
            Overall learning experience ratings and improvement areas from Google Forms.
          </p>
        </div>

        {/* Action Controls */}
        <div className="flex flex-wrap items-center gap-2.5">
          <button
            type="button"
            onClick={handleGoogleSheetsImport}
            disabled={importingSheets}
            className="inline-flex items-center gap-2 rounded-xl bg-[#2563EB] px-4 py-2.5 text-xs font-bold text-white shadow-sm hover:bg-[#1D4ED8] focus:outline-none focus:ring-2 focus:ring-[#2563EB]/40 disabled:opacity-60 transition-all"
          >
            <FileSpreadsheet className={`h-4 w-4 ${importingSheets ? 'animate-bounce' : ''}`} />
            {importingSheets ? 'Importing from Google Sheets…' : 'Import Google Forms Feedback'}
          </button>

          <button
            type="button"
            onClick={() => {
              const controller = new AbortController();
              load(controller.signal);
            }}
            disabled={loading}
            aria-label="Refresh feedback KPI"
            className="rounded-xl border border-[#E2E8F0] p-2.5 text-[#475569] hover:bg-[#F8FAFC] disabled:opacity-50 transition-colors"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Google Sheets Detailed Import Status Panel */}
      {importResult && (
        <div className="rounded-2xl border border-blue-200 bg-gradient-to-r from-blue-50/80 to-indigo-50/80 p-5 shadow-xs space-y-3.5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="h-5 w-5 text-emerald-600 shrink-0" />
              <div>
                <h4 className="text-sm font-extrabold text-slate-900">Google Sheets Import Results</h4>
                <p className="text-xs text-slate-600">{importResult.message}</p>
              </div>
            </div>
            <button
              type="button"
              onClick={() => setImportResult(null)}
              className="text-xs text-slate-500 hover:text-slate-800 font-semibold px-2 py-1 rounded-lg hover:bg-white/60 transition-colors"
            >
              Dismiss
            </button>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="rounded-xl border border-slate-200 bg-white p-3 text-center shadow-2xs">
              <p className="text-[10px] font-bold uppercase tracking-wider text-slate-500">Total Found in Sheet</p>
              <p className="mt-1 text-2xl font-black text-slate-900">{importResult.total_rows}</p>
            </div>
            <div className="rounded-xl border border-emerald-200 bg-emerald-50/50 p-3 text-center shadow-2xs">
              <p className="text-[10px] font-bold uppercase tracking-wider text-emerald-700">Newly Imported</p>
              <p className="mt-1 text-2xl font-black text-emerald-700">{importResult.imported}</p>
            </div>
            <div className="rounded-xl border border-amber-200 bg-amber-50/50 p-3 text-center shadow-2xs">
              <p className="text-[10px] font-bold uppercase tracking-wider text-amber-700">Already Imported (Skipped)</p>
              <p className="mt-1 text-2xl font-black text-amber-700">{importResult.skipped}</p>
            </div>
            <div className="rounded-xl border border-rose-200 bg-rose-50/50 p-3 text-center shadow-2xs">
              <p className="text-[10px] font-bold uppercase tracking-wider text-rose-700">Failed Responses</p>
              <p className="mt-1 text-2xl font-black text-rose-700">{importResult.failed}</p>
            </div>
          </div>

          {importResult.errors && importResult.errors.length > 0 && (
            <div className="rounded-xl border border-rose-200 bg-rose-50 p-3 text-xs text-rose-800 space-y-1">
              <p className="font-bold">Errors encountered:</p>
              <ul className="list-disc pl-5 space-y-0.5">
                {importResult.errors.map((err, i) => (
                  <li key={i}>{err}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {importError && (
        <div className="rounded-2xl border border-rose-200 bg-rose-50 p-4 text-xs font-semibold text-rose-800 flex items-center gap-2.5 shadow-sm">
          <AlertCircle className="h-4 w-4 shrink-0 text-rose-600" />
          <span>{importError}</span>
        </div>
      )}

      {error && (
        <p role="alert" className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-xs text-rose-700">
          {error}
        </p>
      )}

      {/* Cross-Year Awareness Banner */}
      {otherYearCount > 0 && selectedYear !== 'All' && (
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 rounded-2xl border border-blue-200 bg-blue-50/70 p-4 text-xs text-blue-900 shadow-2xs">
          <div className="flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-blue-600 shrink-0" />
            <span>
              Showing <strong>{total}</strong> responses for <strong>{selectedYear}</strong>. There {otherYearCount === 1 ? 'is' : 'are'} <strong>{otherYearCount}</strong> additional student {otherYearCount === 1 ? 'response' : 'responses'} recorded in other academic sessions ({availableYears.filter((y) => y !== selectedYear).join(', ')}).
            </span>
          </div>
          <button
            type="button"
            onClick={() => setSelectedYear('All')}
            className="font-bold text-blue-700 bg-white hover:bg-blue-100/60 border border-blue-300 px-3.5 py-1.5 rounded-xl self-start sm:self-auto shrink-0 transition-colors shadow-2xs"
          >
            View All Academic Years ({allTotal} total)
          </button>
        </div>
      )}

      {/* Scope Filters: Department, Academic Year, and Semester */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3.5 rounded-2xl border border-[#E2E8F0] bg-[#F8FAFC] p-4 sm:p-5">
        {/* Department Filter */}
        <div>
          <label className="block text-xs font-bold uppercase tracking-wider text-[#64748B] mb-1.5">
            Department
          </label>
          <select
            value={selectedDepartment}
            onChange={(e) => setSelectedDepartment(e.target.value)}
            className="w-full rounded-xl border border-[#CBD5E1] bg-white px-3.5 py-2.5 text-xs font-semibold text-[#1E293B] shadow-sm focus:border-[#2563EB] focus:outline-none"
          >
            <option value="All">All Departments</option>
            {availableDepartments.map((dept) => (
              <option key={dept} value={dept}>
                {dept}
              </option>
            ))}
          </select>
        </div>

        {/* Academic Year Filter */}
        <div>
          <label className="block text-xs font-bold uppercase tracking-wider text-[#64748B] mb-1.5">
            Academic Year
          </label>
          <select
            value={selectedYear}
            onChange={(e) => {
              setSelectedYear(e.target.value);
              if (onAcademicYearChange && e.target.value !== 'All') {
                onAcademicYearChange(e.target.value);
              }
            }}
            className="w-full rounded-xl border border-[#CBD5E1] bg-white px-3.5 py-2.5 text-xs font-semibold text-[#1E293B] shadow-sm focus:border-[#2563EB] focus:outline-none"
          >
            <option value="All">All Academic Years</option>
            {availableYears.map((yr) => (
              <option key={yr} value={yr}>
                {yr}
              </option>
            ))}
          </select>
        </div>

        {/* Semester Filter */}
        <div>
          <label className="block text-xs font-bold uppercase tracking-wider text-[#64748B] mb-1.5">
            Semester
          </label>
          <select
            value={selectedSemester}
            onChange={(e) => setSelectedSemester(e.target.value)}
            className="w-full rounded-xl border border-[#CBD5E1] bg-white px-3.5 py-2.5 text-xs font-semibold text-[#1E293B] shadow-sm focus:border-[#2563EB] focus:outline-none"
          >
            <option value="All">All Semesters</option>
            {availableSemesters.map((sem) => (
              <option key={sem} value={sem}>
                {sem}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Quick Summary Cards */}
      <section className="grid gap-3.5 sm:grid-cols-3 lg:grid-cols-3" aria-label="Feedback overview metrics">
        <article className="rounded-2xl border border-[#DBEAFE] bg-[#EFF6FF] p-4">
          <p className="text-xs font-bold uppercase tracking-wider text-[#2563EB]">Total Feedback Submissions</p>
          <p className="mt-2 text-3xl font-extrabold text-[#1D4ED8]">{total}</p>
          <p className="mt-1 text-xs text-[#64748B]">
            {selectedYear === 'All' ? 'All recorded submissions' : `Responses in ${selectedYear}`}
          </p>
        </article>

        <article className="rounded-2xl border border-[#E2E8F0] bg-white p-4">
          <p className="text-xs font-bold uppercase tracking-wider text-[#64748B]">Average Learning Experience</p>
          <div className="mt-2 flex items-baseline gap-1.5">
            <span className="text-3xl font-extrabold text-[#1E293B]">
              {avgSatisfaction !== null ? avgSatisfaction.toFixed(2) : '—'}
            </span>
            <span className="text-sm font-semibold text-[#64748B]">/ 5.0</span>
          </div>
          <p className="mt-1 text-xs text-[#64748B]">
            {avgSatisfaction !== null ? `${Math.round((avgSatisfaction / 5) * 100)}% satisfaction index` : 'Awaiting ratings'}
          </p>
        </article>

        <article className="rounded-2xl border border-amber-100 bg-amber-50/60 p-4">
          <p className="text-xs font-bold uppercase tracking-wider text-amber-800">Top Improvement Area</p>
          <p className="mt-2 truncate text-base font-extrabold text-amber-950" title={topImprovement ? topImprovement.area : 'None selected'}>
            {topImprovement ? topImprovement.area : 'None selected'}
          </p>
          <p className="mt-1 text-xs text-amber-800">
            {topImprovement ? `${topImprovement.count} votes (${topImprovement.percentage}%)` : 'No votes recorded'}
          </p>
        </article>
      </section>

      {/* Main Content Area */}
      {loading && !summary ? (
        <p className="py-12 text-center text-sm text-[#64748B]">Loading student feedback results…</p>
      ) : !error && total === 0 ? (
        <div className="rounded-3xl border border-dashed border-[#CBD5E1] bg-[#F8FAFC] px-6 py-14 text-center">
          <MessageSquare className="mx-auto mb-3 h-8 w-8 text-[#94A3B8]" />
          <h4 className="font-bold text-[#1E293B] text-base">No Student Feedback Records Found</h4>
          <p className="mx-auto mt-2 max-w-xl text-xs text-[#64748B]">
            There are currently no feedback responses matching the selected Department ({selectedDepartment}),
            Academic Year ({selectedYear}), or Semester ({selectedSemester}).
          </p>
          {otherYearCount > 0 && (
            <div className="mt-4">
              <button
                type="button"
                onClick={() => setSelectedYear('All')}
                className="inline-flex items-center gap-1.5 text-xs font-bold text-[#2563EB] hover:underline"
              >
                Switch to "All Academic Years" to view {allTotal} recorded responses
              </button>
            </div>
          )}
          <div className="mt-5 flex justify-center gap-3">
            <button
              type="button"
              onClick={handleGoogleSheetsImport}
              disabled={importingSheets}
              className="inline-flex items-center gap-2 rounded-xl bg-[#2563EB] px-4 py-2.5 text-xs font-bold text-white hover:bg-[#1D4ED8]"
            >
              <FileSpreadsheet className="h-4 w-4" />
              Import Google Forms Feedback Now
            </button>
          </div>
        </div>
      ) : (
        summary && (
          <div className="space-y-6">
            {/* 1 & 2: Overall Learning Experience Score + Rating Distribution (1–5) */}
            <section className="rounded-3xl border border-[#E2E8F0] bg-white p-5 sm:p-7 shadow-sm">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-6 pb-4 border-b border-[#F1F5F9]">
                <div>
                  <h4 className="text-base font-bold text-[#1E293B]">Overall Learning Experience</h4>
                  <p className="text-xs text-[#64748B] mt-0.5">
                    Rating scores from 1 (lowest) to 5 (highest) submitted by students.
                  </p>
                </div>
                <span className="text-xs font-semibold px-3 py-1 rounded-full bg-[#EFF6FF] text-[#2563EB]">
                  {totalRated} Ratings Evaluated
                </span>
              </div>

              <div className="grid gap-6 lg:grid-cols-[1fr_2fr] items-center">
                {/* 1. Large Score & Stars Display */}
                <div className="rounded-2xl border border-[#DBEAFE] bg-gradient-to-br from-[#EFF6FF] to-[#DBEAFE]/40 p-6 flex flex-col items-center justify-center text-center">
                  <span className="text-xs font-bold uppercase tracking-wider text-[#2563EB] mb-2">
                    Average Score
                  </span>
                  <div className="flex items-baseline gap-1.5">
                    <span className="text-5xl font-black text-[#1D4ED8]">
                      {avgSatisfaction !== null ? avgSatisfaction.toFixed(2) : '—'}
                    </span>
                    <span className="text-lg font-bold text-[#64748B]">/ 5</span>
                  </div>

                  {/* Star Icons */}
                  <div className="flex items-center gap-1.5 mt-3">
                    {[1, 2, 3, 4, 5].map((starNum) => {
                      const filled = avgSatisfaction !== null && avgSatisfaction >= starNum;
                      const half =
                        avgSatisfaction !== null &&
                        !filled &&
                        avgSatisfaction >= starNum - 0.5;
                      return (
                        <Star
                          key={starNum}
                          className={`h-5 w-5 ${
                            filled
                              ? 'fill-amber-400 text-amber-400'
                              : half
                              ? 'fill-amber-200 text-amber-400'
                              : 'text-slate-300'
                          }`}
                        />
                      );
                    })}
                  </div>

                  <p className="text-xs text-[#64748B] mt-3">
                    Based on {totalRated} evaluated student {totalRated === 1 ? 'submission' : 'submissions'}
                  </p>
                </div>

                {/* 2. Rating Distribution (1–5) Progress Bars */}
                <div className="space-y-3">
                  {[5, 4, 3, 2, 1].map((rating) => {
                    const count = ratingDistribution[rating] || 0;
                    const pct = totalRated > 0 ? Math.round((count / totalRated) * 100) : 0;
                    const barColor =
                      rating === 5
                        ? 'bg-emerald-500'
                        : rating === 4
                        ? 'bg-[#2563EB]'
                        : rating === 3
                        ? 'bg-amber-500'
                        : rating === 2
                        ? 'bg-orange-500'
                        : 'bg-rose-500';

                    return (
                      <div key={rating} className="grid grid-cols-[80px_1fr_90px] items-center gap-3">
                        <div className="flex items-center gap-1.5 text-xs font-bold text-[#334155]">
                          <span>{rating}</span>
                          <Star className="h-3.5 w-3.5 fill-amber-400 text-amber-400 inline" />
                          <span className="text-[#94A3B8]">({rating})</span>
                        </div>

                        <div className="h-3 w-full overflow-hidden rounded-full bg-[#F1F5F9] border border-[#E2E8F0]">
                          <div
                            className={`h-full rounded-full transition-all ${barColor}`}
                            style={{ width: `${pct}%` }}
                          />
                        </div>

                        <div className="text-right text-xs font-bold tabular-nums text-[#1E293B]">
                          <span>{count}</span>
                          <span className="text-[#64748B] font-normal ml-1">({pct}%)</span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </section>

            {/* 3. Most Frequently Selected Improvement Areas */}
            <section className="rounded-3xl border border-[#E2E8F0] bg-white p-5 sm:p-7 shadow-sm">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-6 pb-4 border-b border-[#F1F5F9]">
                <div>
                  <div className="flex items-center gap-2">
                    <Lightbulb className="h-4 w-4 text-amber-500" />
                    <h4 className="text-base font-bold text-[#1E293B]">
                      Most Frequently Selected Improvement Areas
                    </h4>
                  </div>
                  <p className="text-xs text-[#64748B] mt-0.5">
                    Ranked by the number of students who flagged each area in Google Forms.
                  </p>
                </div>
                <span className="text-xs font-semibold px-3 py-1 rounded-full bg-[#F8FAFC] text-[#475569] border border-[#E2E8F0]">
                  {improvementAreas.length} Core Dimensions
                </span>
              </div>

              {!improvementAreas.length ? (
                <p className="text-center py-6 text-xs text-[#94A3B8]">
                  No improvement areas selected for this filter scope.
                </p>
              ) : (
                <div className="space-y-4">
                  {improvementAreas.map((item, idx) => {
                    const isTop = idx === 0 && item.count > 0;
                    return (
                      <div
                        key={item.area}
                        className={`rounded-2xl border p-4 transition-all ${
                          isTop
                            ? 'border-amber-200 bg-amber-50/40 shadow-xs'
                            : 'border-[#E2E8F0] bg-[#F8FAFC]'
                        }`}
                      >
                        <div className="flex items-center justify-between gap-3 mb-2">
                          <div className="flex items-center gap-2.5">
                            <span
                              className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-lg text-xs font-extrabold ${
                                isTop
                                  ? 'bg-amber-500 text-white'
                                  : 'bg-[#E2E8F0] text-[#475569]'
                              }`}
                            >
                              #{idx + 1}
                            </span>
                            <span className="text-xs font-bold text-[#1E293B] sm:text-sm">
                              {item.area}
                            </span>
                          </div>

                          <div className="flex items-center gap-2 shrink-0">
                            <span className="rounded-lg bg-white border border-[#E2E8F0] px-2.5 py-1 text-xs font-extrabold text-[#1E293B] shadow-2xs">
                              {item.count} {item.count === 1 ? 'vote' : 'votes'}
                            </span>
                            <span className="text-xs font-bold text-[#64748B] w-12 text-right">
                              {item.percentage}%
                            </span>
                          </div>
                        </div>

                        {/* Progress Bar */}
                        <div className="h-2 w-full overflow-hidden rounded-full bg-[#E2E8F0]">
                          <div
                            className={`h-full rounded-full transition-all ${
                              isTop ? 'bg-amber-500' : 'bg-[#2563EB]'
                            }`}
                            style={{ width: `${Math.min(item.percentage, 100)}%` }}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </section>
          </div>
        )
      )}

      {/* Footer Metadata */}
      <p className="text-right text-xs text-[#94A3B8]">
        Scope: {selectedDepartment} · {selectedYear} · {selectedSemester}
        {updatedAt ? ` · Refreshed ${updatedAt.toLocaleTimeString()}` : ''}
      </p>
    </div>
  );
}
