import React, { useEffect, useMemo, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { ArrowLeft, Eye, MessageSquare, RefreshCw, Search, Star } from 'lucide-react';
import Navbar from '../components/Navbar';
import { API_BASE_URL, apiFetch } from '../api';

const years = ['2024-2025', '2025-2026'];
const selectClass = 'block w-full rounded-xl border border-[#CBD5E1] bg-white px-4 py-3 text-sm text-[#1E293B] outline-none focus:border-[#2563EB] focus:ring-2 focus:ring-[#2563EB]/20';
const formatDate = (value) => {
  if (!value) return null;
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
};

function RatingBars({ items, label, nameKey }) {
  return <section className="rounded-2xl border border-[#E2E8F0] bg-white p-5 sm:p-6">
    <h2 className="font-bold text-[#1E293B]">{label}</h2>
    {!items.length ? <p className="mt-4 text-sm text-[#64748B]">No feedback available for this chart.</p> : <div role="img" aria-label={label} className="mt-5 max-h-80 space-y-4 overflow-y-auto">
      {items.map((item) => <div key={item.faculty_id || item[nameKey]} className="grid grid-cols-[minmax(90px,1fr)_2fr_auto] items-center gap-3 text-xs sm:grid-cols-[minmax(140px,1fr)_3fr_auto]">
        <span className="truncate font-medium text-[#475569]" title={item[nameKey]}>{item[nameKey]}</span>
        {item.average_rating === null || item.average_rating === undefined
          ? <span className="text-[#94A3B8]">No feedback available</span>
          : <><div className="h-3 overflow-hidden rounded-full bg-[#E2E8F0]" role="progressbar" aria-label={`${item[nameKey]} average rating`} aria-valuemin={0} aria-valuemax={10} aria-valuenow={item.average_rating}>
            <div className="h-full rounded-full bg-[#2563EB] transition-all" style={{ width: `${Math.min(Number(item.average_rating) * 10, 100)}%` }} />
          </div>
          <span className="w-14 text-right font-bold tabular-nums text-[#1E293B]">{Number(item.average_rating).toFixed(2)}/10</span></>}
      </div>)}
    </div>}
  </section>;
}

function FeedbackList({ feedback }) {
  if (!feedback.length) return <p className="mt-4 rounded-xl bg-[#F8FAFC] p-4 text-sm text-[#64748B]">No feedback available.</p>;
  return <ul className="mt-4 space-y-3">
    {feedback.map((item, index) => <li key={`${item.created_at || 'undated'}-${index}`} className="rounded-xl border border-[#E2E8F0] bg-[#F8FAFC] p-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <span className="inline-flex items-center gap-1.5 rounded-full bg-[#DBEAFE] px-2.5 py-1 text-xs font-bold text-[#1D4ED8]"><Star size={13} />{item.faculty_rating === null || item.faculty_rating === undefined ? 'Rating unavailable' : `${item.faculty_rating}/10`}</span>
        {formatDate(item.created_at) && <time className="text-xs text-[#64748B]" dateTime={item.created_at}>{formatDate(item.created_at)}</time>}
      </div>
      <p className="mt-3 whitespace-pre-wrap break-words text-sm leading-6 text-[#334155]">{item.comment?.trim() || 'No written comment provided.'}</p>
      {(item.subject || item.teaching_quality != null || item.subject_knowledge != null || item.communication_skills != null || item.student_interaction != null) && <div className="mt-4 border-t border-[#E2E8F0] pt-3">
        {item.subject && <p className="mb-3 text-xs text-[#64748B]"><span className="font-semibold text-[#475569]">Subject:</span> {item.subject}</p>}
        <dl className="grid gap-2 sm:grid-cols-2">
          {[
            ['Teaching Quality', item.teaching_quality],
            ['Subject Knowledge', item.subject_knowledge],
            ['Communication Skills', item.communication_skills],
            ['Student Interaction', item.student_interaction],
          ].map(([label, rating]) => rating !== null && rating !== undefined && <div key={label} className="flex items-center justify-between gap-2 rounded-lg bg-white px-3 py-2 text-xs">
            <dt className="text-[#64748B]">{label}</dt>
            <dd className="font-bold tabular-nums text-[#1E293B]">{rating}/{item.criteria_rating_scale || 10}</dd>
          </div>)}
        </dl>
      </div>}
    </li>)}
  </ul>;
}

export default function FacultyFeedbackPage() {
  const location = useLocation();
  const initialParams = useMemo(() => new URLSearchParams(location.search), [location.search]);
  const [year, setYear] = useState(years.includes(initialParams.get('academic_year')) ? initialParams.get('academic_year') : '');
  const [department, setDepartment] = useState(initialParams.get('department') || '');
  const [search, setSearch] = useState('');
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [refreshKey, setRefreshKey] = useState(0);
  const [expandedFaculty, setExpandedFaculty] = useState('');

  useEffect(() => {
    const controller = new AbortController();
    const params = new URLSearchParams();
    if (year) params.set('academic_year', year);
    if (department) params.set('department', department);
    const loadFeedback = async () => {
      setLoading(true);
      setError('');
      try {
        const response = await apiFetch(`${API_BASE_URL}/api/feedback/faculty${params.size ? `?${params}` : ''}`, { signal: controller.signal });
        if (!response.ok) {
          let message = `Faculty feedback could not be loaded (HTTP ${response.status}).`;
          try {
            const body = await response.json();
            if (typeof body.detail === 'string') message = body.detail;
          } catch {
            // Keep the HTTP error when the response is not JSON.
          }
          throw new Error(message);
        }
        const result = await response.json();
        if (!result || !Array.isArray(result.faculty)) throw new Error('The feedback service returned invalid faculty data.');
        setData(result);
      } catch (cause) {
        if (cause.name !== 'AbortError') {
          setData(null);
          setError(cause.message || 'Unable to reach the feedback service.');
        }
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    };
    loadFeedback();
    const timer = window.setInterval(loadFeedback, 30000);
    return () => {
      controller.abort();
      window.clearInterval(timer);
    };
  }, [year, department, refreshKey]);

  const visibleFaculty = useMemo(() => {
    const normalizedSearch = search.trim().toLocaleLowerCase();
    if (!normalizedSearch) return data?.faculty || [];
    return (data?.faculty || []).filter((item) => `${item.name} ${item.department} ${item.designation || ''}`.toLocaleLowerCase().includes(normalizedSearch));
  }, [data, search]);
  const groupedFaculty = useMemo(() => visibleFaculty.reduce((groups, member) => {
    groups[member.department] = [...(groups[member.department] || []), member];
    return groups;
  }, {}), [visibleFaculty]);
  const totalResponses = Number(data?.total_responses || 0);
  const overallAverage = data?.overall_average_rating;

  return <div className="min-h-screen bg-[#F8FAFC] text-[#1E293B]">
    <Navbar />
    <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:py-12">
      <div className="mb-8 flex flex-col justify-between gap-5 sm:flex-row sm:items-end">
        <div>
          <Link to="/dashboard" state={{ selectedKPI: 'Student Feedback Improvement' }} className="mb-4 inline-flex items-center gap-2 text-sm font-medium text-[#2563EB] hover:text-[#1D4ED8]"><ArrowLeft size={16} /> Back to KPI dashboard</Link>
          <span className="mb-3 flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-[#2563EB]"><Eye size={15} /> Administrator view · Read only</span>
          <h1 className="text-3xl font-extrabold tracking-tight sm:text-4xl">Faculty Feedback</h1>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-[#64748B]">Anonymous student ratings and comments, grouped by department and faculty. Student identities are not collected or displayed.</p>
        </div>
        <button type="button" onClick={() => setRefreshKey((value) => value + 1)} disabled={loading} className="inline-flex items-center justify-center gap-2 self-start rounded-xl border border-[#E2E8F0] bg-white px-4 py-2.5 text-sm font-semibold text-[#334155] hover:border-[#93C5FD] disabled:opacity-50"><RefreshCw size={16} className={loading ? 'animate-spin' : ''} /> Refresh</button>
      </div>

      <section className="mb-6 grid gap-4 rounded-2xl border border-[#E2E8F0] bg-white p-4 sm:grid-cols-2 sm:p-5">
        <label className="space-y-2 text-xs font-bold uppercase tracking-wide text-[#64748B]">Academic year
          <select aria-label="Filter by academic year" className={`${selectClass} normal-case tracking-normal`} value={year} onChange={(event) => setYear(event.target.value)}><option value="">All academic years</option>{years.map((value) => <option key={value} value={value}>{value}</option>)}</select>
        </label>
        <label className="space-y-2 text-xs font-bold uppercase tracking-wide text-[#64748B]">Department
          <select aria-label="Filter by department" className={`${selectClass} normal-case tracking-normal`} value={department} onChange={(event) => setDepartment(event.target.value)}><option value="">All departments</option>{(data?.available_departments || []).map((value) => <option key={value} value={value}>{value}</option>)}</select>
        </label>
      </section>

      {loading && !data ? <div role="status" className="rounded-2xl border border-[#E2E8F0] bg-white p-10 text-center text-sm text-[#64748B]">Loading faculty feedback…</div>
        : error ? <div role="alert" className="rounded-2xl border border-rose-200 bg-rose-50 p-6 text-sm text-rose-700">{error}<button type="button" onClick={() => setRefreshKey((value) => value + 1)} className="ml-3 font-semibold underline">Try again</button></div>
          : data && <>
            <section aria-label="Faculty feedback summary" className="mb-6 grid gap-4 sm:grid-cols-2 2xl:grid-cols-5">
              <article className="rounded-2xl border border-[#DBEAFE] bg-[#EFF6FF] p-5"><p className="text-xs font-bold uppercase tracking-wider text-[#2563EB]">Feedback submissions</p><p className="mt-2 text-3xl font-extrabold text-[#1D4ED8]">{totalResponses}</p><p className="mt-1 text-xs text-[#64748B]">{year || 'All years'} · yearless entries excluded from a selected year</p></article>
              <article className="rounded-2xl border border-[#E2E8F0] bg-white p-5"><p className="text-xs font-bold uppercase tracking-wider text-[#64748B]">Faculty with feedback</p><p className="mt-2 text-3xl font-extrabold text-[#1E293B]">{data.total_faculty}</p><p className="mt-1 text-xs text-[#64748B]">Faculty members with attributed submissions</p></article>
              <article className="rounded-2xl border border-[#E2E8F0] bg-white p-5"><p className="text-xs font-bold uppercase tracking-wider text-[#64748B]">Departments receiving feedback</p><p className="mt-2 text-3xl font-extrabold text-[#1E293B]">{data.total_departments}</p><p className="mt-1 text-xs text-[#64748B]">Departments with attributed submissions</p></article>
              <article className="rounded-2xl border border-[#E2E8F0] bg-white p-5"><p className="text-xs font-bold uppercase tracking-wider text-[#64748B]">Overall average rating</p><p className="mt-2 text-3xl font-extrabold text-[#1E293B]">{overallAverage === null || overallAverage === undefined ? '—' : `${Number(overallAverage).toFixed(2)}/10`}</p><p className="mt-1 text-xs text-[#64748B]">Across {data.rating_distribution ? Object.values(data.rating_distribution).reduce((sum, count) => sum + Number(count), 0) : 0} valid faculty ratings</p></article>
              <article className="rounded-2xl border border-[#E2E8F0] bg-white p-5"><p className="text-xs font-bold uppercase tracking-wider text-[#64748B]">Highest-rated faculty</p>{data.highest_rated_faculty ? <><p className="mt-2 truncate text-xl font-extrabold text-[#1E293B]" title={data.highest_rated_faculty.name}>{data.highest_rated_faculty.name}</p><p className="mt-1 text-sm font-bold text-[#2563EB]">{Number(data.highest_rated_faculty.average_rating).toFixed(2)}/10</p></> : <p className="mt-2 text-sm text-[#64748B]">No feedback available</p>}</article>
            </section>

            {Number(data.unassigned_year_responses) > 0 && <section className="mb-6 rounded-2xl border border-amber-200 bg-amber-50 p-5">
              <h2 className="font-bold text-amber-950">Feedback without an academic year ({data.unassigned_year_responses})</h2>
              <p className="mt-1 text-sm text-amber-900">These legacy submissions are shown separately and are not included in academic-year ratings.</p>
              <ul className="mt-4 space-y-3">{data.unassigned_year_feedback.map((item, index) => <li key={`${item.created_at || 'undated'}-${index}`} className="rounded-xl border border-amber-200 bg-white/70 p-4">
                <p className="whitespace-pre-wrap break-words text-sm leading-6 text-[#334155]">{item.comment?.trim() || 'No written comment provided.'}</p>
                <p className="mt-2 text-xs text-[#64748B]">{item.department || 'Department not assigned'}{formatDate(item.created_at) ? ` · ${formatDate(item.created_at)}` : ''}</p>
              </li>)}</ul>
            </section>}

            {Number(data.unassigned_faculty_responses) > 0 && <section className="mb-6 rounded-2xl border border-amber-200 bg-amber-50 p-5">
              <h2 className="font-bold text-amber-950">Feedback without a faculty association ({data.unassigned_faculty_responses})</h2>
              <p className="mt-1 text-sm text-amber-900">These records cannot be attributed to an individual faculty member and are excluded from faculty ratings.</p>
              <FeedbackList feedback={data.unassigned_faculty_feedback} />
            </section>}

            <div className="mb-6 grid gap-4 lg:grid-cols-2">
              <RatingBars items={data.faculty} label="Faculty Rating Comparison" nameKey="name" />
              <RatingBars items={data.departments.map((item) => ({ ...item, name: item.department }))} label="Department-wise Average Rating" nameKey="name" />
              <section className="rounded-2xl border border-[#E2E8F0] bg-white p-5 sm:p-6 lg:col-span-2">
                <h2 className="font-bold text-[#1E293B]">Feedback Distribution</h2>
                <p className="mt-1 text-xs text-[#64748B]">Number of valid faculty ratings at each point on the 10-point scale.</p>
                <div role="img" aria-label="Feedback distribution by faculty rating out of 10" className="mt-5 flex h-48 items-end gap-2 border-b border-l border-[#CBD5E1] px-2 sm:gap-4">
                  {Array.from({ length: 11 }, (_, index) => index).map((rating) => {
                    const count = Number(data.rating_distribution?.[rating] || 0);
                    const maxCount = Math.max(1, ...Object.values(data.rating_distribution || {}).map(Number));
                    return <div key={rating} className="flex h-full min-w-0 flex-1 flex-col items-center justify-end gap-2">
                      <span className="text-[10px] font-semibold tabular-nums text-[#475569]">{count || ''}</span>
                      <div className="w-full max-w-10 rounded-t-md bg-[#2563EB]" style={{ height: `${count ? Math.max(count / maxCount * 75, 4) : 0}%` }} title={`${count} response${count === 1 ? '' : 's'} rated ${rating}`} />
                      <span className="mb-[-1.25rem] text-[10px] text-[#64748B]">{rating}</span>
                    </div>;
                  })}
                </div>
              </section>
            </div>

            <section className="rounded-2xl border border-[#E2E8F0] bg-white p-5 sm:p-6">
              <div className="mb-5 flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
                <div><h2 className="text-xl font-bold text-[#1E293B]">Faculty feedback by department</h2><p className="mt-1 text-sm text-[#64748B]">Select a faculty member to read their complete available feedback.</p></div>
                <label className="relative block w-full sm:max-w-sm"><span className="sr-only">Search faculty</span><Search size={17} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#64748B]" /><input type="search" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search faculty or department" className={`${selectClass} pl-10`} /></label>
              </div>
              {!visibleFaculty.length ? <div className="rounded-xl bg-[#F8FAFC] px-5 py-10 text-center"><MessageSquare className="mx-auto mb-2 text-[#94A3B8]" size={24} /><p className="text-sm font-semibold text-[#334155]">{search ? 'No faculty match your search.' : 'No faculty records are available.'}</p></div>
                : Object.entries(groupedFaculty).sort(([a], [b]) => a.localeCompare(b)).map(([facultyDepartment, members]) => <section key={facultyDepartment} className="mb-6 last:mb-0">
                  <h3 className="mb-3 border-b border-[#E2E8F0] pb-2 text-sm font-bold uppercase tracking-wide text-[#475569]">{facultyDepartment}</h3>
                  <div className="grid gap-3 lg:grid-cols-2">
                    {members.map((member) => {
                      const expanded = expandedFaculty === member.faculty_id;
                      return <article key={member.faculty_id} className="rounded-2xl border border-[#E2E8F0] bg-white p-4 sm:p-5">
                        <button type="button" aria-expanded={expanded} onClick={() => setExpandedFaculty(expanded ? '' : member.faculty_id)} className="flex w-full items-start justify-between gap-4 text-left">
                          <span><span className="block font-bold text-[#1E293B]">{member.name}</span><span className="mt-1 block text-xs text-[#64748B]">{member.designation || 'Designation not listed'} · {member.department}</span><span className="mt-2 block text-xs font-medium text-[#2563EB]">{expanded ? 'Hide feedback details' : 'View complete feedback'}</span></span>
                          <span className="shrink-0 rounded-xl bg-[#EFF6FF] px-3 py-2 text-right"><span className="block text-lg font-extrabold text-[#1D4ED8]">{member.average_rating === null ? '—' : `${Number(member.average_rating).toFixed(2)}/10`}</span><span className="block text-[10px] text-[#64748B]">{member.response_count} {member.response_count === 1 ? 'response' : 'responses'}</span></span>
                        </button>
                        {member.response_count > 0 && <p className="mt-3 text-xs text-[#64748B]">{member.rating_count} valid ratings used in the average</p>}
                        {expanded && <div className="mt-4 border-t border-[#E2E8F0] pt-1"><FeedbackList feedback={member.feedback} /></div>}
                        {member.response_count === 0 && !expanded && <p className="mt-3 text-sm text-[#64748B]">No feedback available.</p>}
                      </article>;
                    })}
                  </div>
                </section>)}
            </section>

            <p className="mt-4 text-right text-xs text-[#94A3B8]">All ratings and comments are read-only. No student identity is exposed.</p>
          </>}
    </main>
  </div>;
}
