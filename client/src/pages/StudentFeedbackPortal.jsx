import React, { useEffect, useMemo, useState } from 'react';
import { CheckCircle2, GraduationCap, LoaderCircle, LockKeyhole, MessageSquare, ShieldCheck, Star } from 'lucide-react';
import { API_BASE_URL, apiPublicFetch } from '../api';

const ratingQuestions = [
  ['teaching_quality', 'Teaching Quality'],
  ['subject_knowledge', 'Subject Knowledge'],
  ['communication_skills', 'Communication Skills'],
  ['student_interaction', 'Student Interaction'],
  ['overall_rating', 'Overall Satisfaction'],
];

const initialRatings = Object.fromEntries(ratingQuestions.map(([key]) => [key, null]));
const inputClass = 'block w-full rounded-xl border border-[#CBD5E1] bg-white px-4 py-3 text-sm text-[#1E293B] outline-none transition focus:border-[#2563EB] focus:ring-2 focus:ring-[#2563EB]/20 disabled:bg-[#F1F5F9]';

async function responseError(response, fallback) {
  try {
    const body = await response.json();
    if (typeof body.detail === 'string') return body.detail;
    if (Array.isArray(body.detail)) return body.detail.map((item) => item.msg).filter(Boolean).join(' ');
  } catch {
    // Use the provided message for non-JSON responses.
  }
  if (response.status === 409) return 'This feedback code has already been used.';
  if (response.status === 400) return 'The feedback code is invalid for this faculty member or academic year.';
  if (response.status === 429) return 'Too many attempts. Please wait a moment before trying again.';
  return fallback;
}

function RatingControl({ label, value, onChange, disabled }) {
  return <fieldset className="min-w-0">
    <legend className="mb-3 text-sm font-semibold text-[#334155]">{label}<span className="ml-1 text-rose-600" aria-hidden="true">*</span></legend>
    <div role="radiogroup" aria-label={label} className="grid grid-cols-6 gap-2 sm:grid-cols-11">
      {Array.from({ length: 11 }, (_, rating) => (
        <button
          key={rating}
          type="button"
          role="radio"
          aria-checked={value === rating}
          aria-label={`${label}: ${rating} out of 10`}
          disabled={disabled}
          onClick={() => onChange(rating)}
          className={`h-10 rounded-lg border text-sm font-bold transition focus:outline-none focus:ring-2 focus:ring-[#2563EB]/40 disabled:cursor-not-allowed disabled:opacity-60 ${
            value === rating
              ? 'border-[#2563EB] bg-[#2563EB] text-white shadow-sm'
              : 'border-[#CBD5E1] bg-white text-[#475569] hover:border-[#93C5FD] hover:bg-[#EFF6FF]'
          }`}
        >
          {rating}
        </button>
      ))}
    </div>
    <div className="mt-1 flex justify-between text-[11px] text-[#64748B]"><span>Lowest</span><span>Highest</span></div>
  </fieldset>;
}

export default function StudentFeedbackPortal() {
  const [academicYear, setAcademicYear] = useState('');
  const [departments, setDepartments] = useState([]);
  const [faculty, setFaculty] = useState([]);
  const [departmentId, setDepartmentId] = useState('');
  const [facultyId, setFacultyId] = useState('');
  const [subject, setSubject] = useState('');
  const [feedbackCode, setFeedbackCode] = useState('');
  const [ratings, setRatings] = useState(initialRatings);
  const [comments, setComments] = useState('');
  const [verified, setVerified] = useState(false);
  const [loadingInitial, setLoadingInitial] = useState(true);
  const [loadingFaculty, setLoadingFaculty] = useState(false);
  const [validating, setValidating] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState('');
  const [pageError, setPageError] = useState('');

  useEffect(() => {
    const controller = new AbortController();
    async function loadOptions() {
      setLoadingInitial(true);
      setPageError('');
      try {
        const [yearResponse, departmentsResponse] = await Promise.all([
          apiPublicFetch(`${API_BASE_URL}/api/public/feedback/academic-year`, { signal: controller.signal }),
          apiPublicFetch(`${API_BASE_URL}/api/public/feedback/departments`, { signal: controller.signal }),
        ]);
        if (!yearResponse.ok) throw new Error(await responseError(yearResponse, 'The active academic year could not be loaded.'));
        if (!departmentsResponse.ok) throw new Error(await responseError(departmentsResponse, 'Departments could not be loaded.'));
        const [yearData, departmentData] = await Promise.all([yearResponse.json(), departmentsResponse.json()]);
        if (typeof yearData.academic_year !== 'string' || !Array.isArray(departmentData)) {
          throw new Error('The feedback service returned incomplete form data.');
        }
        setAcademicYear(yearData.academic_year);
        setDepartments(departmentData);
      } catch (cause) {
        if (cause.name !== 'AbortError') setPageError(cause.message || 'Unable to load the feedback form.');
      } finally {
        if (!controller.signal.aborted) setLoadingInitial(false);
      }
    }
    loadOptions();
    return () => controller.abort();
  }, []);

  useEffect(() => {
    if (!departmentId) {
      setFaculty([]);
      setFacultyId('');
      return undefined;
    }
    const controller = new AbortController();
    async function loadFaculty() {
      setLoadingFaculty(true);
      setPageError('');
      setFaculty([]);
      setFacultyId('');
      try {
        const response = await apiPublicFetch(
          `${API_BASE_URL}/api/public/feedback/faculty/?department_id=${encodeURIComponent(departmentId)}`,
          { signal: controller.signal },
        );
        if (!response.ok) throw new Error(await responseError(response, 'Faculty could not be loaded.'));
        const result = await response.json();
        if (!Array.isArray(result)) throw new Error('The faculty service returned invalid data.');
        setFaculty(result);
      } catch (cause) {
        if (cause.name !== 'AbortError') setPageError(cause.message || 'Unable to load faculty.');
      } finally {
        if (!controller.signal.aborted) setLoadingFaculty(false);
      }
    }
    loadFaculty();
    return () => controller.abort();
  }, [departmentId]);

  const selectedFaculty = useMemo(
    () => faculty.find((member) => member.faculty_id === facultyId) || null,
    [faculty, facultyId],
  );
  const canValidate = Boolean(
    academicYear && departmentId && facultyId && feedbackCode.trim() && !validating && !loadingInitial,
  );
  const allRatingsSelected = ratingQuestions.every(([key]) => Number.isInteger(ratings[key]) && ratings[key] >= 0 && ratings[key] <= 10);

  const invalidateCode = () => {
    setVerified(false);
    setError('');
  };

  const validateCode = async (event) => {
    event.preventDefault();
    setError('');
    setVerified(false);
    if (!departmentId || !facultyId || !academicYear || !feedbackCode.trim()) {
      setError('Select your department and faculty, and enter your private feedback code.');
      return;
    }
    setValidating(true);
    try {
      const response = await apiPublicFetch(`${API_BASE_URL}/api/public/feedback/validate-token`, {
        method: 'POST',
        body: JSON.stringify({
          feedback_code: feedbackCode.trim(),
          faculty_id: facultyId,
          department_id: Number(departmentId),
          academic_year: academicYear,
        }),
      });
      if (!response.ok) throw new Error(await responseError(response, 'The feedback code could not be validated.'));
      const result = await response.json();
      if (result.valid !== true || result.faculty_id !== facultyId || result.academic_year !== academicYear) {
        throw new Error('This feedback code is not valid for the selected faculty and academic year.');
      }
      setVerified(true);
      setRatings(initialRatings);
    } catch (cause) {
      setError(cause.message || 'Unable to validate this feedback code.');
    } finally {
      setValidating(false);
    }
  };

  const submitFeedback = async (event) => {
    event.preventDefault();
    setError('');
    if (!verified) {
      setError('Validate your feedback code before submitting.');
      return;
    }
    if (!subject.trim()) {
      setError('Enter the subject for your feedback.');
      return;
    }
    if (!allRatingsSelected) {
      setError('Please answer each rating question from 0 to 10.');
      return;
    }
    setSubmitting(true);
    try {
      const response = await apiPublicFetch(`${API_BASE_URL}/api/public/feedback/submit`, {
        method: 'POST',
        body: JSON.stringify({
          feedback_code: feedbackCode.trim(),
          faculty_id: facultyId,
          department_id: Number(departmentId),
          academic_year: academicYear,
          subject: subject.trim(),
          ...ratings,
          comments: comments.trim() || null,
        }),
      });
      if (!response.ok) {
        if (response.status === 400 || response.status === 409) setVerified(false);
        throw new Error(await responseError(response, 'Your feedback could not be submitted.'));
      }
      setVerified(false);
      setSubmitted(true);
    } catch (cause) {
      setError(cause.message || 'Unable to submit your feedback. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  return <div className="min-h-screen bg-[#F8FAFC] text-[#1E293B]">
    <header className="border-b border-[#E2E8F0] bg-white">
      <div className="mx-auto flex max-w-5xl items-center gap-3 px-4 py-4 sm:px-6">
        <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-[#DBEAFE] text-[#2563EB]"><GraduationCap size={24} /></div>
        <div><p className="font-extrabold tracking-wide text-[#1E293B]">IFHE</p><p className="text-xs text-[#64748B]">Student Feedback Portal</p></div>
      </div>
    </header>

    <main className="mx-auto w-full max-w-3xl px-4 py-8 sm:px-6 sm:py-12">
      <div className="mb-7">
        <span className="mb-3 inline-flex items-center gap-2 rounded-full border border-[#2563EB]/20 bg-[#DBEAFE] px-3 py-1 text-xs font-semibold uppercase tracking-wider text-[#2563EB]"><MessageSquare size={14} /> Your voice matters</span>
        <h1 className="text-3xl font-extrabold tracking-tight sm:text-4xl">Faculty Feedback</h1>
        <p className="mt-2 text-sm leading-6 text-[#64748B]">Share your experience to help us improve teaching and learning at IFHE.</p>
      </div>

      <div className="mb-6 flex items-start gap-3 rounded-2xl border border-[#BFDBFE] bg-[#EFF6FF] p-4 text-sm leading-6 text-[#1E3A8A]">
        <ShieldCheck className="mt-0.5 h-5 w-5 shrink-0 text-[#2563EB]" />
        <p>Your feedback is anonymous. Your identity is not stored with your feedback. Each feedback code can be used only once for the selected faculty and academic year.</p>
      </div>

      {pageError && <p role="alert" className="mb-5 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">{pageError}</p>}

      {submitted ? <section role="status" className="rounded-3xl border border-emerald-200 bg-white p-8 text-center shadow-sm sm:p-12">
        <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-emerald-100 text-emerald-700"><CheckCircle2 size={34} /></div>
        <h2 className="mt-5 text-2xl font-extrabold text-[#1E293B]">Feedback submitted</h2>
        <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-[#64748B]">Thank you for sharing your feedback. Your response has been recorded anonymously and this code can no longer be used.</p>
      </section> : <form onSubmit={submitFeedback} className="space-y-6 rounded-3xl border border-[#E2E8F0] bg-white p-5 shadow-sm sm:p-8">
        {loadingInitial ? <div role="status" className="flex items-center gap-2 py-4 text-sm text-[#64748B]"><LoaderCircle className="h-4 w-4 animate-spin" /> Loading feedback form…</div> : <>
          <div className="grid gap-5 sm:grid-cols-2">
            <label className="space-y-2 text-sm font-semibold text-[#334155]">Academic Year
              <input aria-label="Active academic year" readOnly value={academicYear} className={inputClass} />
            </label>
            <label className="space-y-2 text-sm font-semibold text-[#334155]">Department<span className="text-rose-600" aria-hidden="true"> *</span>
              <select required disabled={submitted || submitting || !departments.length} value={departmentId} onChange={(event) => { setDepartmentId(event.target.value); setFacultyId(''); invalidateCode(); }} className={inputClass}>
                <option value="">Select department</option>
                {departments.map((department) => <option key={department.id} value={department.id}>{department.name}</option>)}
              </select>
            </label>
            <label className="space-y-2 text-sm font-semibold text-[#334155] sm:col-span-2">Faculty Name<span className="text-rose-600" aria-hidden="true"> *</span>
              <select required disabled={!departmentId || loadingFaculty || !faculty.length || submitting || submitted} value={facultyId} onChange={(event) => { setFacultyId(event.target.value); invalidateCode(); }} className={inputClass}>
                <option value="">{loadingFaculty ? 'Loading faculty…' : departmentId ? 'Select faculty member' : 'Select a department first'}</option>
                {faculty.map((member) => <option key={member.faculty_id} value={member.faculty_id}>{member.name}{member.designation ? ` · ${member.designation}` : ''}</option>)}
              </select>
            </label>
            <label className="space-y-2 text-sm font-semibold text-[#334155] sm:col-span-2">Subject<span className="text-rose-600" aria-hidden="true"> *</span>
              <input required maxLength={256} value={subject} onChange={(event) => setSubject(event.target.value)} placeholder="Enter the course or subject" disabled={submitted || submitting} className={inputClass} />
            </label>
          </div>

          <section className="rounded-2xl border border-[#E2E8F0] bg-[#F8FAFC] p-4 sm:p-5">
            <h2 className="text-base font-bold text-[#1E293B]">Verify your feedback code</h2>
            <p className="mt-1 text-sm leading-5 text-[#64748B]">Codes are valid for one faculty member and academic year.</p>
            <div className="mt-4 flex flex-col gap-3 sm:flex-row">
              <label className="min-w-0 flex-1 space-y-2 text-sm font-semibold text-[#334155]">Private Feedback Code
                <input required autoComplete="off" autoCapitalize="none" spellCheck="false" maxLength={128} value={feedbackCode} onChange={(event) => { setFeedbackCode(event.target.value); invalidateCode(); }} placeholder="Enter your privately distributed code" disabled={submitted || submitting} className={inputClass} />
              </label>
              <button type="button" onClick={validateCode} disabled={!canValidate || submitted || submitting} className="self-end rounded-xl border border-[#2563EB] px-5 py-3 text-sm font-bold text-[#2563EB] transition hover:bg-[#EFF6FF] disabled:cursor-not-allowed disabled:opacity-50">
                {validating ? <span className="inline-flex items-center gap-2"><LoaderCircle size={16} className="animate-spin" /> Checking…</span> : 'Validate code'}
              </button>
            </div>
            {verified && selectedFaculty && <p role="status" className="mt-3 flex items-center gap-2 text-sm font-medium text-emerald-700"><CheckCircle2 size={17} /> Code validated for {selectedFaculty.name} · {academicYear}.</p>}
          </section>

          <section className="space-y-6">
            <div>
              <h2 className="text-base font-bold text-[#1E293B]">Rate your experience</h2>
              <p className="mt-1 text-sm text-[#64748B]">Select a score from 0 (lowest) to 10 (highest) for each question.</p>
            </div>
            {ratingQuestions.map(([key, label]) => (
              <RatingControl
                key={key}
                label={label}
                value={ratings[key]}
                disabled={!verified || submitted || submitting}
                onChange={(rating) => setRatings((current) => ({ ...current, [key]: rating }))}
              />
            ))}
          </section>

          <label className="block space-y-2 text-sm font-semibold text-[#334155]">Additional Comments <span className="font-normal text-[#64748B]">(Optional)</span>
            <textarea maxLength={4000} rows={4} value={comments} onChange={(event) => setComments(event.target.value)} placeholder="Please do not include your name or other identifying information." disabled={!verified || submitted || submitting} className={`${inputClass} resize-y`} />
            <span className="block text-xs font-normal text-[#64748B]">Please do not include your name or other identifying information.</span>
          </label>

          {error && <p role="alert" className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">{error}</p>}

          <div className="border-t border-[#E2E8F0] pt-5">
            <button type="submit" disabled={!verified || !allRatingsSelected || submitting || submitted} className="inline-flex w-full items-center justify-center gap-2 rounded-xl bg-[#2563EB] px-6 py-3.5 text-sm font-bold text-white shadow-sm transition hover:bg-[#1D4ED8] focus:outline-none focus:ring-2 focus:ring-[#2563EB]/40 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 sm:w-auto">
              {submitting ? <><LoaderCircle size={17} className="animate-spin" /> Submitting feedback…</> : <><Star size={17} /> Submit Feedback</>}
            </button>
            {!verified && <p className="mt-3 inline-flex items-center gap-1.5 text-xs text-[#64748B]"><LockKeyhole size={13} /> Validate your code to enable the rating form.</p>}
          </div>
        </>}
      </form>}

      <p className="mt-5 text-center text-xs text-[#94A3B8]">IFHE · Student Feedback Portal</p>
    </main>
  </div>;
}
