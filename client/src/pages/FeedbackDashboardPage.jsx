import React, { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft, RefreshCw, MessageSquare, TrendingUp } from 'lucide-react';
import Navbar from '../components/Navbar';
import { API_BASE_URL } from '../api';

const years = ['2024-2025', '2025-2026'];
const categories = [['teaching_quality', 'Teaching quality'], ['course_content', 'Course content'], ['learning_resources', 'Learning resources'], ['faculty_support', 'Faculty support'], ['overall_satisfaction', 'Overall satisfaction']];
const selectClass = 'rounded-xl border border-slate-700 bg-slate-900 px-4 py-2.5 text-sm text-slate-100 outline-none focus:border-cyan-400 focus:ring-2 focus:ring-cyan-400/20';
const safeCount = (value) => Number.isFinite(Number(value)) && Number(value) > 0 ? Number(value) : 0;

export default function FeedbackDashboardPage() {
  const [year, setYear] = useState('');
  const [department, setDepartment] = useState('');
  const [departments, setDepartments] = useState([]);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    fetch(`${API_BASE_URL}/api/departments`, { signal: controller.signal }).then((r) => r.ok ? r.json() : []).then((data) => { if (Array.isArray(data)) setDepartments(data.filter((x) => x?.name).map((x) => x.name)); }).catch(() => {});
    return () => controller.abort();
  }, []);

  const loadSummary = useCallback(async (signal) => {
    setLoading(true); setError('');
    const params = new URLSearchParams();
    if (year) params.set('academic_year', year);
    if (department) params.set('department', department);
    try {
      const response = await fetch(`${API_BASE_URL}/api/feedback/summary${params.size ? `?${params}` : ''}`, { signal });
      if (!response.ok) throw new Error(`Feedback summary could not be loaded (HTTP ${response.status}).`);
      const data = await response.json();
      if (!data || typeof data !== 'object') throw new Error('The feedback service returned an invalid summary.');
      setSummary(data);
    } catch (e) { if (e.name !== 'AbortError') { setSummary(null); setError(e.message || 'Unable to reach the feedback service.'); } }
    finally { if (!signal.aborted) setLoading(false); }
  }, [year, department]);

  useEffect(() => {
    const controller = new AbortController();
    loadSummary(controller.signal);
    return () => controller.abort();
  }, [loadSummary, refreshKey]);

  const total = safeCount(summary?.total_responses);
  return <div className="min-h-screen bg-slate-950 text-slate-100"><Navbar/><main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:py-12">
    <div className="mb-8 flex flex-col justify-between gap-5 sm:flex-row sm:items-end"><div><Link to="/feedback" className="mb-4 inline-flex items-center gap-2 text-sm font-medium text-cyan-300 hover:text-cyan-200"><ArrowLeft size={16}/> Back to feedback form</Link><span className="mb-3 flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-cyan-300"><TrendingUp size={15}/> Institutional insights</span><h1 className="text-3xl font-bold tracking-tight sm:text-4xl">Feedback Summary</h1><p className="mt-2 text-sm text-slate-400">Aggregated ratings only. Individual submissions are never displayed.</p></div><button onClick={() => setRefreshKey((v) => v + 1)} disabled={loading} className="inline-flex items-center justify-center gap-2 self-start rounded-xl border border-slate-700 bg-slate-900 px-4 py-2.5 text-sm font-semibold text-slate-200 hover:border-cyan-400/50 disabled:opacity-50"><RefreshCw size={16} className={loading ? 'animate-spin' : ''}/> Refresh</button></div>
    <section className="mb-6 grid gap-4 rounded-2xl border border-slate-800 bg-slate-900/80 p-4 sm:grid-cols-2 sm:p-5"><label className="space-y-2 text-xs font-semibold uppercase tracking-wide text-slate-400">Academic year<select aria-label="Filter by academic year" className={`${selectClass} block w-full normal-case tracking-normal`} value={year} onChange={(e) => setYear(e.target.value)}><option value="">All academic years</option>{years.map((v) => <option key={v}>{v}</option>)}</select></label><label className="space-y-2 text-xs font-semibold uppercase tracking-wide text-slate-400">Department<select aria-label="Filter by department" className={`${selectClass} block w-full normal-case tracking-normal`} value={department} onChange={(e) => setDepartment(e.target.value)}><option value="">All departments</option>{departments.map((v) => <option key={v}>{v}</option>)}</select></label></section>
    {loading ? <div role="status" className="rounded-2xl border border-slate-800 bg-slate-900 p-10 text-center text-sm text-slate-400">Loading feedback summary…</div> : error ? <div role="alert" className="rounded-2xl border border-rose-400/30 bg-rose-400/10 p-6 text-sm text-rose-200">{error}<button onClick={() => setRefreshKey((v) => v + 1)} className="ml-3 underline">Try again</button></div> : total === 0 ? <div className="rounded-2xl border border-slate-800 bg-slate-900 px-6 py-14 text-center"><MessageSquare className="mx-auto mb-3 text-slate-500" size={28}/><h2 className="font-semibold">No feedback responses yet</h2><p className="mt-2 text-sm text-slate-400">There are no responses for the selected filters.</p></div> : <>
      <section className="mb-6 rounded-2xl border border-cyan-400/20 bg-gradient-to-br from-cyan-400/10 to-slate-900 p-6"><p className="text-xs font-bold uppercase tracking-wider text-cyan-300">Total responses</p><div className="mt-2 flex items-baseline gap-3"><span className="text-4xl font-extrabold">{total}</span><span className="text-sm text-slate-400">anonymous submissions</span></div></section>
      <section className="grid gap-4 lg:grid-cols-2">{categories.map(([key, label]) => { const average = summary?.averages?.[key]; const avg = Number.isFinite(Number(average)) && average !== null && average !== '' ? Number(average) : null; const distribution = summary?.rating_distributions?.[key] || {}; return <article key={key} className="rounded-2xl border border-slate-800 bg-slate-900/80 p-5 sm:p-6"><div className="flex items-start justify-between gap-4"><h2 className="font-semibold text-slate-100">{label}</h2><div className="text-right"><span className="text-2xl font-bold text-cyan-300">{avg === null ? '—' : avg.toFixed(2)}</span><span className="ml-1 text-xs text-slate-500">/ 5</span></div></div><div className="mt-5 space-y-3">{[5,4,3,2,1].map((rating) => { const count = safeCount(distribution[rating] ?? distribution[String(rating)]); const percent = total ? Math.min((count / total) * 100, 100) : 0; return <div key={rating} className="grid grid-cols-[3.5rem_1fr_2.5rem] items-center gap-3 text-xs"><span className="text-slate-400">{rating} {rating === 1 ? 'star' : 'stars'}</span><div className="h-2 overflow-hidden rounded-full bg-slate-800" role="progressbar" aria-label={`${label}, rating ${rating}`} aria-valuemin={0} aria-valuemax={total} aria-valuenow={count}><div className="h-full rounded-full bg-cyan-400 transition-all" style={{ width: `${percent}%` }}/></div><span className="text-right tabular-nums text-slate-300">{count}</span></div>})}</div></article>; })}</section>
    </>}
  </main></div>;
}
