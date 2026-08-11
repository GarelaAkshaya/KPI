import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Navbar from '../components/Navbar';
import { ArrowLeft, FileSpreadsheet, UploadCloud, CheckCircle2, AlertCircle } from 'lucide-react';
import StudentTable from '../components/StudentTable';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

export default function StudentUploadPage() {
  const navigate = useNavigate();
  const [selectedFile, setSelectedFile] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [message, setMessage] = useState('');
  const [status, setStatus] = useState('idle');
  const [students, setStudents] = useState([]);
  const [totalStudents, setTotalStudents] = useState(null);
  const [showTable, setShowTable] = useState(false);
  const [loadingStudents, setLoadingStudents] = useState(false);
  const [fetchError, setFetchError] = useState('');

  const handleSubmit = async (event) => {
    event.preventDefault();

    if (!selectedFile) {
      setStatus('error');
      setMessage('Please choose an Excel file before uploading.');
      return;
    }

    setIsUploading(true);
    setStatus('idle');
    setMessage('');

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const response = await fetch(`${API_BASE_URL}/api/upload-students`, {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.message || 'Upload failed.');
      }

      setStatus('success');
      setMessage(data.message || `Uploaded ${data.count} student records successfully.`);
      // Always refresh the full student list after upload so old data remains visible
      await fetchStudents();
      setSelectedFile(null);
      event.target.reset();
    } catch (error) {
      setStatus('error');
      setMessage(error.message || 'Unexpected error while uploading.');
    } finally {
      setIsUploading(false);
    }
  };

  async function fetchStudents() {
    setFetchError('');
    setLoadingStudents(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/students`);
      if (!res.ok) throw new Error('Failed to fetch student records.');
      const data = await res.json();
      if (!Array.isArray(data)) throw new Error('Invalid response from server.');
      const processed = processRecords(data);
      setStudents(processed);
      setTotalStudents(processed.length);
    } catch (err) {
      setFetchError(err.message || 'Error fetching students');
    } finally {
      setLoadingStudents(false);
    }
  }

  // Deduplicate by studentId (keep latest createdAt) and sort by studentId (numeric when possible)
  function processRecords(records) {
    const map = new Map();
    for (const r of records) {
      const key = String(r.studentId ?? '').trim();
      if (!key) continue;
      if (!map.has(key)) {
        map.set(key, r);
      } else {
        const existing = map.get(key);
        try {
          const a = new Date(existing.createdAt);
          const b = new Date(r.createdAt);
          if (b > a) map.set(key, r);
        } catch (e) {
          // fallback: keep current
          map.set(key, r);
        }
      }
    }

    const deduped = Array.from(map.values());

    deduped.sort((a, b) => {
      const ai = a.studentId ?? '';
      const bi = b.studentId ?? '';
      const an = Number(ai);
      const bn = Number(bi);
      if (!Number.isNaN(an) && !Number.isNaN(bn)) return an - bn;
      return String(ai).localeCompare(String(bi), undefined, { numeric: true, sensitivity: 'base' });
    });

    return deduped;
  }

  const toggleShow = async () => {
    const willShow = !showTable;
    setShowTable(willShow);
    if (willShow && students.length === 0) {
      await fetchStudents();
    }
  };

  useEffect(() => {
    // fetch existing records when page loads so user can view already uploaded data
    fetchStudents();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="min-h-screen bg-[#F8FAFC] text-[#1E293B] flex flex-col">
      <Navbar />

      <main className="flex-1 max-w-5xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12">
        <div className="mb-6">
          <button
            onClick={() => navigate('/home')}
            className="inline-flex items-center gap-2 text-sm font-semibold text-[#64748B] hover:text-[#1E293B] transition"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Home
          </button>
        </div>

        <section className="rounded-3xl border border-[#E2E8F0] bg-[#FFFFFF] p-6 sm:p-8 shadow-sm">
          <div className="flex items-center gap-3 mb-6">
            <div className="rounded-2xl bg-[#EFF6FF] p-3 text-[#2563EB]">
              <FileSpreadsheet className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-2xl font-extrabold text-[#1E293B]">Upload Student Data</h1>
              <p className="text-sm text-[#64748B]">Select an Excel sheet with Student ID, Student Name, Total Marks, and Percentage columns.</p>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            <label className="flex cursor-pointer flex-col items-center justify-center rounded-2xl border border-dashed border-[#E2E8F0] bg-[#F8FAFC] px-6 py-12 text-center transition hover:border-[#2563EB] hover:bg-[#EFF6FF]">
              <UploadCloud className="mb-4 h-10 w-10 text-[#2563EB]" />
              <span className="text-lg font-semibold text-[#1E293B]">Choose Excel File</span>
              <span className="mt-2 text-sm text-[#64748B]">Supported formats: .xlsx, .xls, .csv</span>
              <input
                type="file"
                accept=".xlsx,.xls,.csv"
                className="sr-only"
                onChange={(event) => setSelectedFile(event.target.files?.[0] || null)}
              />
            </label>

            {selectedFile && (
              <div className="rounded-2xl border border-[#10B981]/30 bg-[#10B981]/10 px-4 py-3 text-sm text-[#10B981]">
                Selected file: <span className="font-semibold">{selectedFile.name}</span>
              </div>
            )}

            <div className="flex flex-wrap items-center gap-3">
              <button
                type="submit"
                disabled={isUploading}
                className="rounded-2xl bg-[#2563EB] px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-[#3B82F6] disabled:cursor-not-allowed disabled:opacity-60"
              >
                {isUploading ? 'Uploading...' : 'Upload & Save'}
              </button>
              <span className="text-sm text-[#64748B]">Records will be stored in the server database with the required attributes.</span>
            </div>
          </form>

          {message && (
            <div className={`mt-6 flex items-start gap-3 rounded-2xl border px-4 py-3 text-sm ${status === 'success' ? 'border-[#10B981]/30 bg-[#10B981]/10 text-[#10B981]' : 'border-rose-300 bg-rose-50 text-rose-600'}`}>
              {status === 'success' ? <CheckCircle2 className="mt-0.5 h-5 w-5" /> : <AlertCircle className="mt-0.5 h-5 w-5" />}
              <span>{message}</span>
            </div>
          )}

          {/* Student count and view button (always available) */}
          <div className="mt-4">
            <div className="flex items-center justify-between gap-4">
              <div className="rounded-lg bg-[#EFF6FF] border border-[#DBEAFE] px-4 py-3 text-sm text-[#1E293B]">
                <span className="text-[#64748B]">Total Students: </span>
                <span className="font-semibold">{totalStudents !== null ? totalStudents : (loadingStudents ? 'Loading...' : '0')}</span>
              </div>

              <div>
                <button
                  onClick={toggleShow}
                  className="rounded-2xl bg-[#2563EB] px-4 py-2 text-sm font-semibold text-white transition hover:bg-[#3B82F6]"
                >
                  {loadingStudents ? 'Loading...' : (showTable ? 'Hide Students' : 'View Students')}
                </button>
              </div>
            </div>

            {fetchError && (
              <div className="mt-3 rounded-2xl border border-rose-300 bg-rose-50 px-4 py-3 text-sm text-rose-600">
                {fetchError}
              </div>
            )}

            {showTable && (
              <div className="mt-4">
                {loadingStudents ? (
                  <div className="flex items-center gap-2 text-sm text-[#64748B]">
                    <div className="h-4 w-4 rounded-full border-2 border-t-transparent border-[#2563EB] animate-spin" />
                    Loading students...
                  </div>
                ) : (
                  <>
                    {students.length === 0 ? (
                      <div className="rounded-2xl border border-[#E2E8F0] bg-[#F8FAFC] px-4 py-6 text-sm text-[#64748B]">No student records found.</div>
                    ) : (
                      <StudentTable students={students} />
                    )}
                  </>
                )}
              </div>
            )}
          </div>
        </section>
      </main>
    </div>
  );
}
