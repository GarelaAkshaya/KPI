import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, CheckCircle2, MessageSquare } from 'lucide-react';
import Navbar from '../components/Navbar';
import { API_BASE_URL, apiFetch } from '../api';

const ratings = [
  ['teaching_quality', 'Teaching Quality'],
  ['course_content', 'Course Content'],
  ['learning_resources', 'Learning Resources'],
  ['faculty_support', 'Faculty Support'],
  ['overall_satisfaction', 'Overall Satisfaction'],
];
const meanings = ['Poor', 'Fair', 'Good', 'Very good', 'Excellent'];
const blankForm = () => Object.fromEntries(ratings.map(([key]) => [key, 0]));

export default function StudentFeedbackPage() {
  const [form, setForm] = useState(blankForm);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const submit = async (event) => {
    event.preventDefault();
    setError(''); setSuccess('');
    if (ratings.some(([key]) => !Number.isInteger(form[key]) || form[key] < 1 || form[key] > 5)) {
      setError('Please rate each criterion from 1 to 5.'); return;
    }
    setSubmitting(true);
    try {
      const response = await apiFetch(`${API_BASE_URL}/api/feedback`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(form),
      });
      if (!response.ok) {
        let detail = 'Feedback could not be submitted. Please try again.';
        try { const body = await response.json(); if (typeof body.detail === 'string') detail = body.detail; } catch { /* use fallback */ }
        throw new Error(detail);
      }
      setForm(blankForm());
      setSuccess('Thank you. Your feedback has been submitted.');
    } catch (e) { setError(e.message || 'Unable to reach the feedback service. Please try again.'); }
    finally { setSubmitting(false); }
  };

  return <div className="min-h-screen bg-[#F8FAFC] text-[#1E293B] flex flex-col"><Navbar/><main className="mx-auto w-full max-w-5xl flex-1 px-4 py-8 sm:px-6 lg:py-12">
    <div className="mb-8 flex flex-col justify-between gap-5 sm:flex-row sm:items-end"><div><span className="mb-3 inline-flex items-center gap-2 rounded-full border border-[#2563EB]/20 bg-[#DBEAFE] px-3 py-1 text-xs font-semibold uppercase tracking-wider text-[#2563EB]"><MessageSquare size={14}/> Student voice</span><h1 className="text-3xl font-extrabold tracking-tight sm:text-4xl">Student Feedback</h1><p className="mt-2 max-w-2xl text-sm leading-6 text-[#64748B]">Rate five parts of your learning experience to help us improve.</p></div><Link to="/dashboard" state={{ selectedKPI: 'Student Feedback Improvement' }} className="inline-flex items-center gap-2 self-start rounded-xl border border-[#E2E8F0] bg-white px-4 py-2.5 text-sm font-semibold text-[#2563EB] hover:border-[#93C5FD]">View KPI insights <ArrowRight size={16}/></Link></div>
    <form onSubmit={submit} className="space-y-6 rounded-3xl border border-[#E2E8F0] bg-white p-5 shadow-sm sm:p-8">
      <fieldset><legend className="mb-4 text-sm font-semibold text-[#1E293B]">Rate your experience <span className="font-normal text-[#64748B]">(1 = Poor, 5 = Excellent)</span></legend><div className="space-y-3">{ratings.map(([key, label]) => <div key={key} className="grid gap-3 rounded-2xl border border-[#E2E8F0] bg-[#F8FAFC] p-4 sm:grid-cols-[1fr_auto] sm:items-center"><div><p className="text-sm font-semibold text-[#1E293B]">{label}<span className="text-rose-600"> *</span></p><p className="mt-1 text-xs text-[#64748B]">{form[key] ? meanings[form[key] - 1] : 'Select a rating'}</p></div><div role="radiogroup" aria-label={label} className="flex gap-2">{meanings.map((meaning, i) => <button key={meaning} type="button" role="radio" aria-checked={form[key] === i + 1} aria-label={`${i + 1}: ${meaning}`} onClick={() => setForm((current) => ({ ...current, [key]: i + 1 }))} className={`h-10 w-10 rounded-xl border text-sm font-bold transition focus:outline-none focus:ring-2 focus:ring-[#2563EB]/40 ${form[key] === i + 1 ? 'border-[#2563EB] bg-[#2563EB] text-white' : 'border-[#CBD5E1] bg-white text-[#475569] hover:border-[#2563EB]'}`}>{i + 1}</button>)}</div></div>)}</div></fieldset>
      {error && <p role="alert" className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">{error}</p>}{success && <p role="status" className="flex items-center gap-2 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700"><CheckCircle2 size={18}/>{success}</p>}
      <div className="flex flex-col justify-between gap-4 border-t border-[#E2E8F0] pt-5 sm:flex-row sm:items-center"><p className="text-xs text-[#64748B]">All five ratings are required. Responses are submitted without identifying details.</p><button disabled={submitting} type="submit" className="rounded-xl bg-[#2563EB] px-6 py-3 text-sm font-bold text-white transition hover:bg-[#1D4ED8] disabled:cursor-not-allowed disabled:opacity-50">{submitting ? 'Submitting feedback…' : 'Submit Feedback'}</button></div>
    </form>
  </main></div>;
}
