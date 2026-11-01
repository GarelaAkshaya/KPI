import React, { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Download, Eye, MessageSquare, RefreshCw } from 'lucide-react';
import { API_BASE_URL, apiFetch } from '../api';

const criteria = [
  ['teaching_quality', 'Teaching Quality'],
  ['course_content', 'Course Content'],
  ['learning_resources', 'Learning Resources'],
  ['faculty_support', 'Faculty Support'],
  ['overall_satisfaction', 'Overall Satisfaction'],
];
const validAverage = (value) => value !== null && value !== undefined && Number.isFinite(Number(value)) ? Number(value) : null;

export default function StudentFeedbackKPI({ academicYear, department, section }) {
  const [summary, setSummary] = useState(null);
  const [facultySummary, setFacultySummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [issuingCodes, setIssuingCodes] = useState(false);
  const [codeExportMessage, setCodeExportMessage] = useState('');
  const [codeExportError, setCodeExportError] = useState('');
  const [showTokenForm, setShowTokenForm] = useState(false);
  const [facultyOptions, setFacultyOptions] = useState([]);
  const [facultyLoading, setFacultyLoading] = useState(false);
  const [facultyLoadError, setFacultyLoadError] = useState('');
  const [selectedFacultyId, setSelectedFacultyId] = useState('');
  const [tokenCount, setTokenCount] = useState(50);
  const [updatedAt, setUpdatedAt] = useState(null);
  const load = useCallback(async (signal) => {
    try {
      const params = new URLSearchParams({ academic_year: academicYear, ...(department ? { department } : {}), ...(section ? { section } : {}) });
      const facultyParams = new URLSearchParams({ academic_year: academicYear, ...(department ? { department } : {}) });
      const [response, facultyResponse] = await Promise.all([
        apiFetch(`${API_BASE_URL}/api/feedback/summary?${params}`, { signal }),
        apiFetch(`${API_BASE_URL}/api/feedback/faculty?${facultyParams}`, { signal }),
      ]);
      if (!response.ok) throw new Error(`Feedback data could not be loaded (HTTP ${response.status}).`);
      if (!facultyResponse.ok) throw new Error(`Faculty feedback could not be loaded (HTTP ${facultyResponse.status}).`);
      const [summaryData, facultyData] = await Promise.all([response.json(), facultyResponse.json()]);
      setSummary(summaryData);
      setFacultySummary(facultyData);
      setError('');
      setUpdatedAt(new Date());
    } catch (e) { if (e.name !== 'AbortError') { setError(e.message || 'Unable to reach the feedback service.'); setFacultySummary(null); } }
    finally { if (!signal.aborted) setLoading(false); }
  }, [academicYear, department, section]);
  useEffect(() => {
    const controller = new AbortController();
    setSummary(null);
    setLoading(true);
    load(controller.signal);
    const timer = window.setInterval(() => load(controller.signal), 30000);
    return () => { controller.abort(); window.clearInterval(timer); };
  }, [load]);

  const total = Number(summary?.total_responses || 0);
  const allResponses = Number(summary?.all_responses ?? summary?.total_responses ?? 0);
  const unattributedResponses = Number(summary?.unattributed_responses || 0);
  const otherYearResponses = Number(summary?.other_year_responses || 0);
  const timeline = Array.isArray(summary?.timeline) ? summary.timeline : [];
  const feedbackViewQuery = new URLSearchParams({
    academic_year: academicYear,
    ...(department ? { department } : {}),
  }).toString();
  const loadFacultyOptions = async () => {
    setFacultyLoading(true);
    setFacultyLoadError('');
    try {
      const response = await apiFetch(`${API_BASE_URL}/api/faculty`);
      if (!response.ok) throw new Error(`Faculty list could not be loaded (HTTP ${response.status}).`);
      const result = await response.json();
      if (!Array.isArray(result)) throw new Error('The faculty service returned invalid data.');
      setFacultyOptions(result);
    } catch (cause) {
      setFacultyLoadError(cause.message || 'Unable to load faculty records.');
    } finally {
      setFacultyLoading(false);
    }
  };
  const openTokenForm = () => {
    if (showTokenForm) {
      setShowTokenForm(false);
      return;
    }
    setShowTokenForm(true);
    if (!facultyOptions.length && !facultyLoading) loadFacultyOptions();
  };
  const downloadFeedbackTokens = async (event) => {
    event.preventDefault();
    if (!selectedFacultyId || !Number.isInteger(Number(tokenCount)) || Number(tokenCount) < 1 || Number(tokenCount) > 10000) {
      setCodeExportError('Select a faculty member and enter between 1 and 10,000 codes.');
      return;
    }
    setIssuingCodes(true);
    setCodeExportMessage('');
    setCodeExportError('');
    try {
      const response = await apiFetch(`${API_BASE_URL}/api/feedback/tokens/issue`, {
        method: 'POST',
        body: JSON.stringify({
          academic_year: academicYear,
          faculty_id: selectedFacultyId,
          count: Number(tokenCount),
        }),
      });
      if (!response.ok) {
        let detail = `Feedback codes could not be issued (HTTP ${response.status}).`;
        try {
          const body = await response.json();
          if (typeof body.detail === 'string') detail = body.detail;
        } catch {
          // Keep the HTTP error if the response is not JSON.
        }
        throw new Error(detail);
      }
      const blob = await response.blob();
      const csvText = await blob.text();
      const availableCodes = Math.max(csvText.trimEnd().split(/\r?\n/).length - 1, 0);
      const objectUrl = URL.createObjectURL(blob);
      const anchor = document.createElement('a');
      anchor.href = objectUrl;
      anchor.download = `ifhe-feedback-codes-${selectedFacultyId}-${academicYear}.csv`;
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      window.setTimeout(() => URL.revokeObjectURL(objectUrl), 1000);
      setCodeExportMessage(`Downloaded ${availableCodes} unique codes for ${academicYear}. Distribute them privately and securely remove this CSV.`);
    } catch (cause) {
      setCodeExportError(cause.message || 'Unable to issue feedback codes.');
    } finally {
      setIssuingCodes(false);
    }
  };
  const priorAverage = timeline.length >= 2 ? validAverage(timeline[timeline.length - 2].overall_satisfaction) : null;
  const currentAverage = timeline.length >= 2 ? validAverage(timeline[timeline.length - 1].overall_satisfaction) : null;
  const change = priorAverage === null || currentAverage === null ? null : currentAverage - priorAverage;
  const maxValue = 5;

  return <div className="space-y-5 rounded-3xl border border-[#E2E8F0] bg-white p-5 shadow-sm sm:p-8">
    <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between"><div><div className="mb-1 flex items-center gap-2 text-xs font-semibold text-[#64748B]"><MessageSquare className="h-4 w-4 text-[#2563EB]"/> Institutional KPI</div><h3 className="text-2xl font-extrabold tracking-tight text-[#1E293B] sm:text-3xl">Student Feedback Improvement</h3><p className="mt-1 text-sm text-[#64748B]">Rating averages and changes calculated from submitted student feedback.</p></div><div className="flex flex-wrap items-center gap-3"><button type="button" onClick={openTokenForm} className="inline-flex items-center gap-2 rounded-lg border border-[#CBD5E1] bg-white px-3 py-2 text-xs font-semibold text-[#334155] hover:border-[#93C5FD]"><Download className="h-4 w-4"/>{showTokenForm ? 'Close code generation' : 'Generate feedback codes'}</button><Link to={`/feedback/view?${feedbackViewQuery}`} className="inline-flex items-center gap-2 rounded-lg bg-[#2563EB] px-4 py-2.5 text-sm font-semibold text-white hover:bg-[#1D4ED8]"><Eye className="h-4 w-4"/> View Feedback</Link><button type="button" onClick={() => { const controller = new AbortController(); load(controller.signal); }} disabled={loading} aria-label="Refresh feedback KPI" className="rounded-lg border border-[#E2E8F0] p-2 text-[#475569] hover:bg-[#F8FAFC] disabled:opacity-50"><RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`}/></button></div></div>
    {showTokenForm && <form onSubmit={downloadFeedbackTokens} className="grid gap-4 rounded-2xl border border-[#E2E8F0] bg-[#F8FAFC] p-4 sm:grid-cols-[2fr_1fr_auto] sm:items-end">
      <label className="space-y-2 text-xs font-bold uppercase tracking-wide text-[#64748B]">Faculty
        <select required disabled={facultyLoading || Boolean(facultyLoadError)} value={selectedFacultyId} onChange={(event) => setSelectedFacultyId(event.target.value)} className="block w-full rounded-xl border border-[#CBD5E1] bg-white px-4 py-3 text-sm font-normal normal-case tracking-normal text-[#1E293B]">
          <option value="">{facultyLoading ? 'Loading faculty…' : 'Select faculty member'}</option>
          {facultyOptions.map((member) => <option key={member.faculty_id} value={member.faculty_id}>{member.name} · {member.department}</option>)}
        </select>
      </label>
      <label className="space-y-2 text-xs font-bold uppercase tracking-wide text-[#64748B]">Number of codes
        <input type="number" min="1" max="10000" required value={tokenCount} onChange={(event) => setTokenCount(event.target.value)} className="block w-full rounded-xl border border-[#CBD5E1] bg-white px-4 py-3 text-sm font-normal normal-case tracking-normal text-[#1E293B]" />
      </label>
      <button type="submit" disabled={issuingCodes || facultyLoading || Boolean(facultyLoadError)} className="rounded-xl bg-[#2563EB] px-5 py-3 text-sm font-bold text-white hover:bg-[#1D4ED8] disabled:opacity-50">{issuingCodes ? 'Generating…' : `Generate for ${academicYear}`}</button>
      {facultyLoadError && <p role="alert" className="text-sm text-rose-700 sm:col-span-3">{facultyLoadError}<button type="button" onClick={loadFacultyOptions} className="ml-2 underline">Try again</button></p>}
    </form>}
    {codeExportError && <p role="alert" className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">{codeExportError}</p>}
    {codeExportMessage && <p role="status" className="rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-800">{codeExportMessage}</p>}
    {error && <p role="alert" className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">{error}</p>}
    {summary && <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4" aria-label="Feedback response counts">
      <article className="rounded-2xl border border-[#E2E8F0] bg-[#F8FAFC] p-4"><p className="text-xs font-bold uppercase tracking-wider text-[#64748B]">All saved feedback</p><p className="mt-2 text-2xl font-extrabold text-[#1E293B]">{allResponses}</p><p className="mt-1 text-xs text-[#64748B]">Responses in the database</p></article>
      <article className="rounded-2xl border border-[#DBEAFE] bg-[#EFF6FF] p-4"><p className="text-xs font-bold uppercase tracking-wider text-[#2563EB]">Attributed to {academicYear}</p><p className="mt-2 text-2xl font-extrabold text-[#1D4ED8]">{total}</p><p className="mt-1 text-xs text-[#64748B]">Used for the selected KPI</p></article>
      <article className="rounded-2xl border border-amber-200 bg-amber-50 p-4"><p className="text-xs font-bold uppercase tracking-wider text-amber-800">Year not recorded</p><p className="mt-2 text-2xl font-extrabold text-amber-900">{unattributedResponses}</p><p className="mt-1 text-xs text-amber-800">Not included in year results</p></article>
      <article className="rounded-2xl border border-[#E2E8F0] bg-white p-4"><p className="text-xs font-bold uppercase tracking-wider text-[#64748B]">Attributed to another year</p><p className="mt-2 text-2xl font-extrabold text-[#1E293B]">{otherYearResponses}</p><p className="mt-1 text-xs text-[#64748B]">Excluded from this selection</p></article>
    </section>}
    {facultySummary && <>
      <section className="grid gap-3 sm:grid-cols-2 2xl:grid-cols-5" aria-label="Faculty rating summary">
        <article className="rounded-2xl border border-[#DBEAFE] bg-[#EFF6FF] p-4"><p className="text-xs font-bold uppercase tracking-wider text-[#2563EB]">Faculty feedback submissions</p><p className="mt-2 text-2xl font-extrabold text-[#1D4ED8]">{facultySummary.total_responses}</p><p className="mt-1 text-xs text-[#64748B]">For {academicYear}</p></article>
        <article className="rounded-2xl border border-[#E2E8F0] bg-[#F8FAFC] p-4"><p className="text-xs font-bold uppercase tracking-wider text-[#64748B]">Faculty with feedback</p><p className="mt-2 text-2xl font-extrabold text-[#1E293B]">{facultySummary.total_faculty}</p><p className="mt-1 text-xs text-[#64748B]">With attributed submissions</p></article>
        <article className="rounded-2xl border border-[#E2E8F0] bg-[#F8FAFC] p-4"><p className="text-xs font-bold uppercase tracking-wider text-[#64748B]">Departments receiving feedback</p><p className="mt-2 text-2xl font-extrabold text-[#1E293B]">{facultySummary.total_departments}</p><p className="mt-1 text-xs text-[#64748B]">With attributed submissions</p></article>
        <article className="rounded-2xl border border-[#E2E8F0] bg-white p-4"><p className="text-xs font-bold uppercase tracking-wider text-[#64748B]">Average faculty rating</p><p className="mt-2 text-2xl font-extrabold text-[#1E293B]">{facultySummary.overall_average_rating == null ? '—' : `${Number(facultySummary.overall_average_rating).toFixed(2)}/10`}</p><p className="mt-1 text-xs text-[#64748B]">Calculated from valid ratings</p></article>
        <article className="rounded-2xl border border-[#E2E8F0] bg-white p-4"><p className="text-xs font-bold uppercase tracking-wider text-[#64748B]">Highest-rated faculty</p>{facultySummary.highest_rated_faculty ? <><p className="mt-2 truncate text-lg font-extrabold text-[#1E293B]" title={facultySummary.highest_rated_faculty.name}>{facultySummary.highest_rated_faculty.name}</p><p className="text-sm font-bold text-[#2563EB]">{Number(facultySummary.highest_rated_faculty.average_rating).toFixed(2)}/10</p></> : <p className="mt-2 text-sm text-[#64748B]">No feedback available</p>}</article>
      </section>
      <section className="grid gap-4 lg:grid-cols-2" aria-label="Faculty rating charts">
        {[['Faculty Rating Comparison', facultySummary.faculty.map((item) => ({ key: item.faculty_id, name: item.name, average_rating: item.average_rating }))], ['Department-wise Average Rating', facultySummary.departments.map((item) => ({ key: item.department, name: item.department, average_rating: item.average_rating }))]].map(([title, items]) => {
          return <article key={title} className="rounded-2xl border border-[#E2E8F0] p-5">
            <h4 className="font-bold text-[#1E293B]">{title}</h4>
            {!items.length ? <p className="mt-4 text-sm text-[#64748B]">No feedback available.</p> : <div className="mt-4 max-h-64 space-y-3 overflow-y-auto">
              {items.map((item) => <div key={item.key} className="grid grid-cols-[minmax(90px,1fr)_2fr_auto] items-center gap-2 text-xs">
                <span className="truncate text-[#475569]" title={item.name}>{item.name}</span>
                {item.average_rating == null
                  ? <span className="text-[#94A3B8]">No feedback available</span>
                  : <><div className="h-2.5 overflow-hidden rounded-full bg-[#E2E8F0]" role="progressbar" aria-label={`${item.name} average rating`} aria-valuemin={0} aria-valuemax={10} aria-valuenow={item.average_rating}><div className="h-full rounded-full bg-[#2563EB]" style={{ width: `${Math.min(Number(item.average_rating) * 10, 100)}%` }}/></div><span className="w-14 text-right font-bold text-[#1E293B]">{Number(item.average_rating).toFixed(2)}/10</span></>}
              </div>)}
            </div>}
          </article>;
        })}
        <article className="rounded-2xl border border-[#E2E8F0] p-5 lg:col-span-2"><h4 className="font-bold text-[#1E293B]">Feedback Distribution</h4><p className="mt-1 text-xs text-[#64748B]">Number of valid faculty ratings on the 0–10 scale.</p><div role="img" aria-label="Faculty rating distribution out of 10" className="mt-4 flex h-36 items-end gap-2 border-b border-l border-[#CBD5E1] px-2 sm:gap-4">{Array.from({ length: 11 }, (_, rating) => rating).map((rating) => { const count = Number(facultySummary.rating_distribution?.[rating] || 0); const maxCount = Math.max(1, ...Object.values(facultySummary.rating_distribution || {}).map(Number)); return <div key={rating} className="flex h-full min-w-0 flex-1 flex-col items-center justify-end gap-1"><span className="text-[10px] text-[#475569]">{count || ''}</span><div className="w-full max-w-8 rounded-t bg-[#2563EB]" style={{ height: `${count ? Math.max(count / maxCount * 75, 4) : 0}%` }}/><span className="text-[10px] text-[#64748B]">{rating}</span></div>; })}</div></article>
      </section>
    </>}
    {loading && !summary ? <p className="py-12 text-center text-sm text-[#64748B]">Loading feedback results…</p> : !error && total === 0 ? <div className="rounded-2xl border border-dashed border-[#CBD5E1] bg-[#F8FAFC] px-6 py-14 text-center"><MessageSquare className="mx-auto mb-3 h-7 w-7 text-[#94A3B8]"/><h4 className="font-semibold text-[#1E293B]">No feedback attributed to {academicYear}</h4><p className="mx-auto mt-2 max-w-2xl text-sm text-[#64748B]">Feedback without an academic year is shown separately and is not included in this result.</p><Link to={`/feedback/view?${feedbackViewQuery}`} className="mt-5 inline-flex items-center gap-2 rounded-lg bg-[#2563EB] px-4 py-2.5 text-sm font-semibold text-white hover:bg-[#1D4ED8]"><Eye className="h-4 w-4"/> View Feedback</Link></div> : summary && <>
      <div className="grid gap-4 sm:grid-cols-2"><article className="rounded-2xl border border-[#DBEAFE] bg-[#EFF6FF] p-5"><p className="text-xs font-bold uppercase tracking-wider text-[#2563EB]">Overall student satisfaction</p><p className="mt-2 text-3xl font-extrabold text-[#1D4ED8]">{validAverage(summary.averages?.overall_satisfaction)?.toFixed(2) ?? '—'} <span className="text-base font-semibold">/ 5</span></p><p className="mt-1 text-xs text-[#64748B]">Across {total} {total === 1 ? 'response' : 'responses'}</p></article><article className="rounded-2xl border border-[#E2E8F0] bg-[#F8FAFC] p-5"><p className="text-xs font-bold uppercase tracking-wider text-[#64748B]">Change between recorded periods</p><p className={`mt-2 text-3xl font-extrabold ${change === null ? 'text-[#64748B]' : change > 0 ? 'text-emerald-600' : change < 0 ? 'text-rose-600' : 'text-[#1E293B]'}`}>{change === null ? 'Not available' : `${change > 0 ? '+' : ''}${change.toFixed(2)} points`}</p><p className="mt-1 text-xs text-[#64748B]">{timeline.length < 2 ? 'Requires feedback recorded on at least two different dates.' : `${timeline[timeline.length - 2].date} compared with ${timeline[timeline.length - 1].date}`}</p></article></div>
      <section className="rounded-2xl border border-[#E2E8F0] p-5"><div className="mb-5"><h4 className="font-bold text-[#1E293B]">Average rating by criterion</h4><p className="mt-1 text-xs text-[#64748B]">Mean rating on a five point scale.</p></div><div className="space-y-4">{criteria.map(([key, label]) => { const avg = validAverage(summary.averages?.[key]); return <div key={key} className="grid grid-cols-[minmax(120px,1fr)_2fr_auto] items-center gap-3"><span className="text-xs font-medium text-[#475569] sm:text-sm">{label}</span><div className="h-3 overflow-hidden rounded-full bg-[#E2E8F0]" role="progressbar" aria-label={`${label} average`} aria-valuemin={0} aria-valuemax={maxValue} aria-valuenow={avg ?? 0}><div className="h-full rounded-full bg-[#2563EB] transition-all" style={{ width: `${avg === null ? 0 : avg / maxValue * 100}%` }}/></div><span className="w-10 text-right text-sm font-bold tabular-nums text-[#1E293B]">{avg === null ? '—' : avg.toFixed(2)}</span></div>; })}</div><p className="mt-5 text-xs text-[#64748B]">{total} {total === 1 ? 'response' : 'responses'} included</p></section>
      <section className="rounded-2xl border border-[#E2E8F0] p-5"><div className="mb-4"><h4 className="font-bold text-[#1E293B]">Ratings by criterion</h4><p className="mt-1 text-xs text-[#64748B]">Average ratings from {total} response{total === 1 ? '' : 's'} attributed to {academicYear}.</p></div><div className="overflow-x-auto"><svg viewBox="0 0 700 260" className="h-64 min-w-[620px] w-full" role="img" aria-label={`Average feedback ratings by criterion for ${academicYear}`}>
        {[1, 2, 3, 4, 5].map((tick) => { const y = 210 - tick * 34; return <g key={tick}><line x1="54" y1={y} x2="680" y2={y} stroke="#E2E8F0" strokeDasharray="4 4"/><text x="34" y={y + 4} textAnchor="middle" fontSize="11" fill="#64748B">{tick}</text></g>; })}
        {criteria.map(([key, label], index) => { const avg = validAverage(summary.averages?.[key]); const x = 80 + index * 120; const height = avg === null ? 0 : avg * 34; const y = 210 - height; return <g key={key}><rect x={x} y={y} width="64" height={height} rx="8" fill="#2563EB" opacity="0.9"/><text x={x + 32} y={avg === null ? 198 : y - 8} textAnchor="middle" fontSize="12" fontWeight="700" fill="#1E293B">{avg === null ? '—' : avg.toFixed(2)}</text><text x={x + 32} y="232" textAnchor="middle" fontSize="10" fill="#64748B">{['Teaching', 'Course', 'Resources', 'Support', 'Satisfaction'][index]}</text></g>; })}
      </svg></div></section>
      {timeline.length >= 2 && <section className="rounded-2xl border border-[#E2E8F0] p-5"><h4 className="font-bold text-[#1E293B]">Overall satisfaction over time</h4><p className="mt-1 text-xs text-[#64748B]">Daily averages from recorded submissions.</p><div className="mt-4 overflow-x-auto"><svg viewBox={`0 0 ${Math.max(520, timeline.length * 90)} 220`} className="h-56 min-w-[520px] w-full" role="img" aria-label="Overall satisfaction daily rating chart"><line x1="48" y1="180" x2={Math.max(500, timeline.length * 90 - 20)} y2="180" stroke="#CBD5E1"/>{[1,2,3,4,5].map((tick) => <g key={tick}><line x1="48" y1={180 - tick * 30} x2={Math.max(500, timeline.length * 90 - 20)} y2={180 - tick * 30} stroke="#E2E8F0" strokeDasharray="4 4"/><text x="24" y={184 - tick * 30} fontSize="11" fill="#64748B">{tick}</text></g>)}<polyline fill="none" stroke="#2563EB" strokeWidth="3" strokeLinejoin="round" strokeLinecap="round" points={timeline.map((row, i) => `${64 + i * (Math.max(450, timeline.length * 90 - 80) / Math.max(1, timeline.length - 1))},${180 - Number(row.overall_satisfaction) * 30}`).join(' ')}/>{timeline.map((row, i) => { const x = 64 + i * (Math.max(450, timeline.length * 90 - 80) / Math.max(1, timeline.length - 1)); const y = 180 - Number(row.overall_satisfaction) * 30; return <g key={row.date}><circle cx={x} cy={y} r="5" fill="#2563EB"/><text x={x} y="204" textAnchor="middle" fontSize="10" fill="#64748B">{row.date.slice(5)}</text></g>; })}</svg></div></section>}
      <p className="text-right text-xs text-[#94A3B8]">Academic year: {academicYear} · {updatedAt ? `Updated ${updatedAt.toLocaleTimeString()}` : ''} · refreshes every 30 seconds</p>
    </>}
  </div>;
}
