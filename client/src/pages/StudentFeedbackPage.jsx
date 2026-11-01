import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft, CheckCircle2, GraduationCap, MessageSquare, ShieldCheck } from 'lucide-react';
import { API_BASE_URL, apiFetch } from '../api';

const ratings = [
  ['teaching_quality', 'Teaching Quality'],
  ['subject_knowledge', 'Subject Knowledge'],
  ['communication_skills', 'Communication Skills'],
  ['student_interaction', 'Student Interaction'],
];
const meanings = ['Poor', 'Fair', 'Good', 'Very good', 'Excellent'];
const initialRatings = () => Object.fromEntries(ratings.map(([key]) => [key, 0]));
const inputClass = 'block w-full rounded-xl border border-[#CBD5E1] bg-white px-4 py-3 text-sm text-[#1E293B] outline-none focus:border-[#2563EB] focus:ring-2 focus:ring-[#2563EB]/20';

export default function StudentFeedbackPage() {
  const [token, setToken] = useState('');
  const [verified, setVerified] = useState(null);
  const [form, setForm] = useState(initialRatings);
  const [overallRating, setOverallRating] = useState(0);
  const [subject, setSubject] = useState('');
  const [comments, setComments] = useState('');
  const [validating, setValidating] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const validateToken = async (event) => {
    event.preventDefault();
    setError('');
    setSuccess('');
    setVerified(null);
    if (!token.trim()) {
      setError('Enter the feedback code distributed to you.');
      return;
    }
    setValidating(true);
    try {
      const response = await apiFetch(`${API_BASE_URL}/api/feedback/validate-code`, {
        method: 'POST',
        body: JSON.stringify({ token: token.trim() }),
      });
      const body = await response.json();
      if (!response.ok) throw new Error(body.detail || `The code could not be verified (HTTP ${response.status}).`);
      setVerified(body);
      setForm(initialRatings());
      setOverallRating(0);
      setSubject('');
      setComments('');
    } catch (cause) {
      setError(cause.message || 'Unable to verify the feedback code.');
    } finally {
      setValidating(false);
    }
  };

  const submit = async (event) => {
    event.preventDefault();
    setError('');
    setSuccess('');
    if (!verified) {
      setError('Verify your feedback code before submitting.');
      return;
    }
    if (!subject.trim()) {
      setError('Enter the subject for this feedback.');
      return;
    }
    if (ratings.some(([key]) => !Number.isInteger(form[key]) || form[key] < 1 || form[key] > 5)) {
      setError('Please rate each criterion from 1 to 5.');
      return;
    }
    if (!Number.isInteger(overallRating) || overallRating < 1 || overallRating > 10) {
      setError('Please select an overall rating from 1 to 10.');
      return;
    }

    setSubmitting(true);
    try {
      const response = await apiFetch(`${API_BASE_URL}/api/feedback`, {
        method: 'POST',
        body: JSON.stringify({
          token: token.trim(),
          subject: subject.trim(),
          ...form,
          overall_rating: overallRating,
          comments,
        }),
      });
      const body = await response.json();
      if (!response.ok) throw new Error(body.detail || `Feedback could not be submitted (HTTP ${response.status}).`);
      setToken('');
      setVerified(null);
      setForm(initialRatings());
      setOverallRating(0);
      setSubject('');
      setComments('');
      setSuccess('Thank you. Your anonymous feedback has been submitted.');
    } catch (cause) {
      setError(cause.message || 'Unable to reach the feedback service. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  return <div className="min-h-screen bg-[#F8FAFC] text-[#1E293B]">
    <header className="border-b border-[#E2E8F0] bg-white">
      <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-4 sm:px-6">
        <div className="flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-[#DBEAFE] text-[#2563EB]"><GraduationCap size={24} /></div>
          <div><p className="font-extrabold tracking-wide text-[#1E293B]">IFHE</p><p className="text-xs text-[#64748B]">Student Feedback Portal</p></div>
        </div>
        <Link to="/" className="inline-flex items-center gap-2 text-sm font-semibold text-[#2563EB] hover:text-[#1D4ED8]"><ArrowLeft size={16} /> Admin portal</Link>
      </div>
    </header>

    <main className="mx-auto w-full max-w-4xl px-4 py-8 sm:px-6 lg:py-12">
      <div className="mb-8">
        <span className="mb-3 inline-flex items-center gap-2 rounded-full border border-[#2563EB]/20 bg-[#DBEAFE] px-3 py-1 text-xs font-semibold uppercase tracking-wider text-[#2563EB]"><MessageSquare size={14} /> Your voice matters</span>
        <h1 className="text-3xl font-extrabold tracking-tight sm:text-4xl">Faculty Feedback</h1>
        <p className="mt-2 max-w-2xl text-sm leading-6 text-[#64748B]">Use the private, single-use code provided to you to share anonymous feedback.</p>
      </div>

      <section className="mb-6 rounded-2xl border border-[#E2E8F0] bg-white p-5 shadow-sm sm:p-6">
        <form onSubmit={validateToken} className="flex flex-col gap-3 sm:flex-row sm:items-end">
          <label className="flex-1 space-y-2 text-sm font-semibold text-[#334155]">
            Private feedback code
            <input autoComplete="off" autoCapitalize="none" spellCheck="false" maxLength={128} value={token} onChange={(event) => { setToken(event.target.value); setVerified(null); setSuccess(''); }} placeholder="Enter your single-use code" className={inputClass} />
          </label>
          <button type="submit" disabled={validating || !token.trim()} className="rounded-xl border border-[#2563EB] px-5 py-3 text-sm font-bold text-[#2563EB] hover:bg-[#EFF6FF] disabled:cursor-not-allowed disabled:opacity-50">{validating ? 'Checking code…' : 'Verify code'}</button>
        </form>
        {verified && <div role="status" className="mt-4 flex items-start gap-3 rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-900">
          <CheckCircle2 size={19} className="mt-0.5 shrink-0 text-emerald-700" />
          <p>Code verified for <strong>{verified.faculty_name}</strong>{verified.designation ? `, ${verified.designation}` : ''} · {verified.department} · {verified.academic_year}.</p>
        </div>}
      </section>
      {error && <p role="alert" className="mb-6 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">{error}</p>}
      {success && <p role="status" className="mb-6 flex items-center gap-2 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700"><CheckCircle2 size={18} />{success}</p>}

      {verified && <form onSubmit={submit} className="space-y-6 rounded-3xl border border-[#E2E8F0] bg-white p-5 shadow-sm sm:p-8">
        <label className="block space-y-2 text-sm font-semibold text-[#334155]">
          Subject
          <input required maxLength={256} value={subject} onChange={(event) => setSubject(event.target.value)} placeholder="Enter the course or subject" className={inputClass} />
        </label>

        <fieldset>
          <legend className="mb-4 text-sm font-semibold text-[#1E293B]">Overall rating <span className="font-normal text-[#64748B]">(1 = lowest, 10 = highest)</span></legend>
          <div role="radiogroup" aria-label="Overall rating" className="grid grid-cols-5 gap-2 sm:grid-cols-10">
            {Array.from({ length: 10 }, (_, index) => index + 1).map((rating) => (
              <button key={rating} type="button" role="radio" aria-checked={overallRating === rating} aria-label={`Overall rating ${rating} out of 10`} onClick={() => setOverallRating(rating)} className={`h-11 rounded-xl border text-sm font-bold transition focus:outline-none focus:ring-2 focus:ring-[#2563EB]/40 ${overallRating === rating ? 'border-[#2563EB] bg-[#2563EB] text-white' : 'border-[#CBD5E1] bg-white text-[#475569] hover:border-[#2563EB]'}`}>{rating}</button>
            ))}
          </div>
        </fieldset>

        <fieldset>
          <legend className="mb-4 text-sm font-semibold text-[#1E293B]">Rate your learning experience <span className="font-normal text-[#64748B]">(1 = Poor, 5 = Excellent)</span></legend>
          <div className="space-y-3">
            {ratings.map(([key, label]) => (
              <div key={key} className="grid gap-3 rounded-2xl border border-[#E2E8F0] bg-[#F8FAFC] p-4 sm:grid-cols-[1fr_auto] sm:items-center">
                <div><p className="text-sm font-semibold text-[#1E293B]">{label}<span className="text-rose-600"> *</span></p><p className="mt-1 text-xs text-[#64748B]">{form[key] ? meanings[form[key] - 1] : 'Select a rating'}</p></div>
                <div role="radiogroup" aria-label={label} className="flex gap-2">
                  {meanings.map((meaning, index) => <button key={meaning} type="button" role="radio" aria-checked={form[key] === index + 1} aria-label={`${index + 1}: ${meaning}`} onClick={() => setForm((current) => ({ ...current, [key]: index + 1 }))} className={`h-10 w-10 rounded-xl border text-sm font-bold transition focus:outline-none focus:ring-2 focus:ring-[#2563EB]/40 ${form[key] === index + 1 ? 'border-[#2563EB] bg-[#2563EB] text-white' : 'border-[#CBD5E1] bg-white text-[#475569] hover:border-[#2563EB]'}`}>{index + 1}</button>)}
                </div>
              </div>
            ))}
          </div>
        </fieldset>

        <label className="block space-y-2 text-sm font-semibold text-[#334155]">
          Comments <span className="font-normal text-[#64748B]">(optional)</span>
          <textarea maxLength={4000} rows={5} value={comments} onChange={(event) => setComments(event.target.value)} placeholder="Share constructive feedback about your experience." className={`${inputClass} resize-y`} />
        </label>

        <div className="flex items-start gap-2 rounded-xl bg-[#F8FAFC] p-4 text-xs leading-5 text-[#64748B]"><ShieldCheck size={17} className="mt-0.5 shrink-0 text-[#2563EB]" /><p>Your code is used only to verify this submission and is not saved with your feedback. Do not include student-identifying information in comments. Each code works once.</p></div>
        <div className="flex justify-end border-t border-[#E2E8F0] pt-5">
          <button disabled={submitting} type="submit" className="rounded-xl bg-[#2563EB] px-6 py-3 text-sm font-bold text-white transition hover:bg-[#1D4ED8] disabled:cursor-not-allowed disabled:opacity-50">{submitting ? 'Submitting feedback…' : 'Submit Feedback'}</button>
        </div>
      </form>}

      {!verified && <p className="mt-6 text-center text-xs text-[#64748B]">Feedback is anonymous. A verified code is required before the form is displayed.</p>}
    </main>
  </div>;
}
