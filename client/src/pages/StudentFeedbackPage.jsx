import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, CheckCircle2, MessageSquare, ShieldCheck } from 'lucide-react';
import Navbar from '../components/Navbar';
import { API_BASE_URL } from '../api';

const years = ['2024-2025', '2025-2026'];
const ratings = [
  ['teaching_quality', 'Teaching quality'],
  ['course_content', 'Course content'],
  ['learning_resources', 'Learning resources'],
  ['faculty_support', 'Faculty support'],
  ['overall_satisfaction', 'Overall satisfaction'],
];
const meanings = ['Poor', 'Fair', 'Good', 'Very good', 'Excellent'];
const blankForm = () => ({ academic_year: '', department: '', teaching_quality: 0, course_content: 0, learning_resources: 0, faculty_support: 0, overall_satisfaction: 0, comment: '' });
const inputClass = 'w-full rounded-xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20';

export default function StudentFeedbackPage() {
  const [form, setForm] = useState(blankForm);
  const [departments, setDepartments] = useState([]);
  const [loadingDepartments, setLoadingDepartments] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    const controller = new AbortController();
    fetch(`${API_BASE_URL}/api/departments`, { signal: controller.signal })
      .then(async (response) => {
        if (!response.ok) throw new Error('Could not load department options. Please refresh and try again.');
        const data = await response.json();
        setDepartments(Array.isArray(data) ? data.filter((item) => item?.name).map((item) => item.name) : []);
      })
      .catch((e) => { if (e.name !== 'AbortError') setError(e.message); })
      .finally(() => { if (!controller.signal.aborted) setLoadingDepartments(false); });
    return () => controller.abort();
  }, []);

  const update = (key, value) => setForm((current) => ({ ...current, [key]: value }));
  const submit = async (event) => {
    event.preventDefault();
    setError(''); setSuccess('');
    if (!form.academic_year || !form.department || ratings.some(([key]) => !Number.isInteger(form[key]) || form[key] < 1 || form[key] > 5)) {
      setError('Choose an academic year and department, then rate each category from 1 to 5.'); return;
    }
    setSubmitting(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/feedback`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ ...form, comment: form.comment.trim() || null }) });
      if (!response.ok) {
        let detail = 'Feedback could not be submitted. Please try again.';
        try { const body = await response.json(); detail = typeof body.detail === 'string' ? body.detail : detail; } catch { /* retain fallback */ }
        throw new Error(detail);
      }
      setForm(blankForm());
      setSuccess('Thank you. Your anonymous feedback has been submitted.');
    } catch (e) { setError(e.message || 'Unable to reach the feedback service. Check your connection and try again.'); }
    finally { setSubmitting(false); }
  };

  return <div className="min-h-screen bg-slate-950 text-slate-100"><Navbar /><main className="mx-auto max-w-5xl px-4 py-8 sm:px-6 lg:py-12">
    <div className="mb-8 flex flex-col justify-between gap-5 sm:flex-row sm:items-end"><div><span className="mb-3 inline-flex items-center gap-2 rounded-full border border-cyan-400/20 bg-cyan-400/10 px-3 py-1 text-xs font-semibold uppercase tracking-wider text-cyan-300"><MessageSquare size={14}/> Student voice</span><h1 className="text-3xl font-bold tracking-tight sm:text-4xl">Student Feedback</h1><p className="mt-2 max-w-2xl text-sm leading-6 text-slate-400">Help us improve teaching and the learning experience. Your feedback is anonymous.</p></div><Link to="/feedback/dashboard" className="inline-flex items-center gap-2 self-start rounded-xl border border-slate-700 bg-slate-900 px-4 py-2.5 text-sm font-semibold text-slate-200 hover:border-cyan-400/50">View feedback insights <ArrowRight size={16}/></Link></div>
    <div className="mb-6 flex gap-3 rounded-2xl border border-emerald-400/20 bg-emerald-400/[0.07] p-4 text-sm text-emerald-100"><ShieldCheck className="mt-0.5 shrink-0 text-emerald-300" size={20}/><p><strong>Anonymous by design.</strong> This form does not ask for or collect student names or IDs. Only the ratings, selected academic details, and optional comment are submitted.</p></div>
    <form onSubmit={submit} className="space-y-6 rounded-3xl border border-slate-800 bg-slate-900/80 p-5 shadow-2xl shadow-black/20 sm:p-8">
      <div className="grid gap-5 sm:grid-cols-2"><label className="space-y-2 text-sm font-semibold text-slate-200">Academic year<select required className={inputClass} value={form.academic_year} onChange={(e) => update('academic_year', e.target.value)}><option value="">Select academic year</option>{years.map((year) => <option key={year}>{year}</option>)}</select></label><label className="space-y-2 text-sm font-semibold text-slate-200">Department<select required className={inputClass} value={form.department} onChange={(e) => update('department', e.target.value)} disabled={loadingDepartments || !departments.length}><option value="">{loadingDepartments ? 'Loading departments…' : departments.length ? 'Select department' : 'Departments unavailable'}</option>{departments.map((department) => <option key={department}>{department}</option>)}</select></label></div>
      <fieldset><legend className="mb-4 text-sm font-semibold text-slate-200">Rate your experience <span className="font-normal text-slate-400">(1 = Poor, 5 = Excellent)</span></legend><div className="space-y-3">{ratings.map(([key, label]) => <div key={key} className="grid gap-3 rounded-2xl border border-slate-800 bg-slate-950/60 p-4 sm:grid-cols-[1fr_auto] sm:items-center"><div><p className="text-sm font-semibold text-slate-100">{label}<span className="text-rose-300"> *</span></p><p className="mt-1 text-xs text-slate-500">{form[key] ? meanings[form[key] - 1] : 'Select a rating'}</p></div><div role="radiogroup" aria-label={label} className="flex gap-2">{meanings.map((meaning, i) => <button key={meaning} type="button" role="radio" aria-checked={form[key] === i + 1} aria-label={`${i + 1}: ${meaning}`} onClick={() => update(key, i + 1)} className={`h-10 w-10 rounded-xl border text-sm font-bold transition focus:outline-none focus:ring-2 focus:ring-cyan-400 ${form[key] === i + 1 ? 'border-cyan-300 bg-cyan-400 text-slate-950' : 'border-slate-700 bg-slate-900 text-slate-300 hover:border-cyan-400/60'}`}>{i + 1}</button>)}</div></div>)}</div></fieldset>
      <label className="block space-y-2 text-sm font-semibold text-slate-200">Comments <span className="font-normal text-slate-400">(optional)</span><textarea className={`${inputClass} min-h-32 resize-y`} maxLength={5000} value={form.comment} onChange={(e) => update('comment', e.target.value)} placeholder="Share any suggestions that could improve your learning experience…"/><span className="block text-right text-xs font-normal text-slate-500">{form.comment.length}/5000</span></label>
      {error && <p role="alert" className="rounded-xl border border-rose-400/30 bg-rose-400/10 px-4 py-3 text-sm text-rose-200">{error}</p>}{success && <p role="status" className="flex items-center gap-2 rounded-xl border border-emerald-400/30 bg-emerald-400/10 px-4 py-3 text-sm text-emerald-200"><CheckCircle2 size={18}/>{success}</p>}
      <div className="flex flex-col justify-between gap-4 border-t border-slate-800 pt-5 sm:flex-row sm:items-center"><p className="text-xs text-slate-500">All five ratings are required. Your input helps guide academic improvements.</p><button disabled={submitting || loadingDepartments || !departments.length} type="submit" className="rounded-xl bg-cyan-400 px-6 py-3 text-sm font-bold text-slate-950 transition hover:bg-cyan-300 disabled:cursor-not-allowed disabled:opacity-50">{submitting ? 'Submitting feedback…' : 'Submit Feedback'}</button></div>
    </form>
  </main></div>;
}
