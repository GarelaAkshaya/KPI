import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Navbar from '../components/Navbar';
import { 
  ArrowLeft, 
  FileSpreadsheet, 
  UploadCloud, 
  CheckCircle2, 
  AlertCircle, 
  CalendarCheck, 
  GraduationCap, 
  Info,
  Layers,
  Check
} from 'lucide-react';
import StudentTable from '../components/StudentTable';
import AttendanceTable from '../components/AttendanceTable';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

export default function StudentUploadPage() {
  const navigate = useNavigate();

  // Active Tab: 'marks' | 'attendance'
  const [activeTab, setActiveTab] = useState('marks');

  // Student Marks Upload State
  const [selectedMarksFile, setSelectedMarksFile] = useState(null);
  const [isUploadingMarks, setIsUploadingMarks] = useState(false);
  const [marksMessage, setMarksMessage] = useState('');
  const [marksStatus, setMarksStatus] = useState('idle');
  const [students, setStudents] = useState([]);
  const [totalStudents, setTotalStudents] = useState(null);
  const [showMarksTable, setShowMarksTable] = useState(false);
  const [loadingStudents, setLoadingStudents] = useState(false);
  const [fetchMarksError, setFetchMarksError] = useState('');

  // Student Attendance Upload State
  const [selectedAttendanceFile, setSelectedAttendanceFile] = useState(null);
  const [isUploadingAttendance, setIsUploadingAttendance] = useState(false);
  const [attendanceMessage, setAttendanceMessage] = useState('');
  const [attendanceStatus, setAttendanceStatus] = useState('idle');
  const [attendanceList, setAttendanceList] = useState([]);
  const [totalAttendance, setTotalAttendance] = useState(null);
  const [showAttendanceTable, setShowAttendanceTable] = useState(false);
  const [loadingAttendance, setLoadingAttendance] = useState(false);
  const [fetchAttendanceError, setFetchAttendanceError] = useState('');

  // Submit Student Marks
  const handleMarksSubmit = async (event) => {
    event.preventDefault();

    if (!selectedMarksFile) {
      setMarksStatus('error');
      setMarksMessage('Please choose an Excel file for student marks before uploading.');
      return;
    }

    setIsUploadingMarks(true);
    setMarksStatus('idle');
    setMarksMessage('');

    const formData = new FormData();
    formData.append('file', selectedMarksFile);

    try {
      const response = await fetch(`${API_BASE_URL}/api/upload-students`, {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.message || 'Upload failed.');
      }

      setMarksStatus('success');
      setMarksMessage(data.message || `Uploaded ${data.count} student marks records successfully.`);
      await fetchStudents();
      setSelectedMarksFile(null);
      event.target.reset();
    } catch (error) {
      setMarksStatus('error');
      setMarksMessage(error.message || 'Unexpected error while uploading marks.');
    } finally {
      setIsUploadingMarks(false);
    }
  };

  // Submit Student Attendance
  const handleAttendanceSubmit = async (event) => {
    event.preventDefault();

    if (!selectedAttendanceFile) {
      setAttendanceStatus('error');
      setAttendanceMessage('Please choose an Excel file for student attendance before uploading.');
      return;
    }

    setIsUploadingAttendance(true);
    setAttendanceStatus('idle');
    setAttendanceMessage('');

    const formData = new FormData();
    formData.append('file', selectedAttendanceFile);

    try {
      const response = await fetch(`${API_BASE_URL}/api/upload-attendance`, {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.message || 'Upload failed.');
      }

      setAttendanceStatus('success');
      setAttendanceMessage(data.message || `Uploaded ${data.count} student attendance records successfully.`);
      await fetchAttendance();
      setSelectedAttendanceFile(null);
      event.target.reset();
    } catch (error) {
      setAttendanceStatus('error');
      setAttendanceMessage(error.message || 'Unexpected error while uploading attendance.');
    } finally {
      setIsUploadingAttendance(false);
    }
  };

  // Fetch Students Data
  async function fetchStudents() {
    setFetchMarksError('');
    setLoadingStudents(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/students`);
      if (!res.ok) throw new Error('Failed to fetch student records.');
      const data = await res.json();
      if (!Array.isArray(data)) throw new Error('Invalid response from server.');
      const processed = processStudentRecords(data);
      setStudents(processed);
      setTotalStudents(processed.length);
    } catch (err) {
      setFetchMarksError(err.message || 'Error fetching students');
    } finally {
      setLoadingStudents(false);
    }
  }

  // Fetch Attendance Data
  async function fetchAttendance() {
    setFetchAttendanceError('');
    setLoadingAttendance(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/attendance`);
      if (!res.ok) throw new Error('Failed to fetch attendance records.');
      const data = await res.json();
      if (!Array.isArray(data)) throw new Error('Invalid response from server.');
      setAttendanceList(data);
      setTotalAttendance(data.length);
    } catch (err) {
      setFetchAttendanceError(err.message || 'Error fetching attendance');
    } finally {
      setLoadingAttendance(false);
    }
  }

  function processStudentRecords(records) {
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

  const toggleMarksTable = async () => {
    const willShow = !showMarksTable;
    setShowMarksTable(willShow);
    if (willShow && students.length === 0) {
      await fetchStudents();
    }
  };

  const toggleAttendanceTable = async () => {
    const willShow = !showAttendanceTable;
    setShowAttendanceTable(willShow);
    if (willShow && attendanceList.length === 0) {
      await fetchAttendance();
    }
  };

  useEffect(() => {
    fetchStudents();
    fetchAttendance();
  }, []);

  return (
    <div className="min-h-screen bg-[#F8FAFC] text-[#1E293B] flex flex-col">
      <Navbar />

      <main className="flex-1 max-w-5xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12">
        <div className="mb-6 flex items-center justify-between">
          <button
            onClick={() => navigate('/home')}
            className="inline-flex items-center gap-2 text-sm font-semibold text-[#64748B] hover:text-[#1E293B] transition"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Home
          </button>
        </div>

        {/* Tab Selection */}
        <div className="flex items-center gap-3 mb-6 p-1.5 bg-[#E2E8F0]/60 rounded-2xl w-fit">
          <button
            onClick={() => setActiveTab('marks')}
            className={`flex items-center gap-2 px-5 py-2.5 rounded-xl font-semibold text-sm transition ${
              activeTab === 'marks'
                ? 'bg-white text-[#2563EB] shadow-sm'
                : 'text-[#64748B] hover:text-[#1E293B]'
            }`}
          >
            <GraduationCap className="w-4 h-4" />
            Student Marks Upload
          </button>

          <button
            onClick={() => setActiveTab('attendance')}
            className={`flex items-center gap-2 px-5 py-2.5 rounded-xl font-semibold text-sm transition ${
              activeTab === 'attendance'
                ? 'bg-white text-[#2563EB] shadow-sm'
                : 'text-[#64748B] hover:text-[#1E293B]'
            }`}
          >
            <CalendarCheck className="w-4 h-4" />
            Student Attendance Upload
          </button>
        </div>

        {/* ================= TAB 1: MARKS UPLOAD ================= */}
        {activeTab === 'marks' && (
          <section className="rounded-3xl border border-[#E2E8F0] bg-[#FFFFFF] p-6 sm:p-8 shadow-sm">
            <div className="flex items-center gap-3 mb-6">
              <div className="rounded-2xl bg-[#EFF6FF] p-3 text-[#2563EB]">
                <FileSpreadsheet className="w-6 h-6" />
              </div>
              <div>
                <h1 className="text-2xl font-extrabold text-[#1E293B]">Upload Student Marks Data</h1>
                <p className="text-sm text-[#64748B]">Select an Excel sheet with Student ID, Student Name, Total Marks, and Percentage columns.</p>
              </div>
            </div>

            <form onSubmit={handleMarksSubmit} className="space-y-5">
              <label className="flex cursor-pointer flex-col items-center justify-center rounded-2xl border border-dashed border-[#E2E8F0] bg-[#F8FAFC] px-6 py-10 text-center transition hover:border-[#2563EB] hover:bg-[#EFF6FF]">
                <UploadCloud className="mb-4 h-10 w-10 text-[#2563EB]" />
                <span className="text-lg font-semibold text-[#1E293B]">Choose Marks Excel File</span>
                <span className="mt-2 text-sm text-[#64748B]">Supported formats: .xlsx, .xls, .csv</span>
                <input
                  type="file"
                  accept=".xlsx,.xls,.csv"
                  className="sr-only"
                  onChange={(event) => setSelectedMarksFile(event.target.files?.[0] || null)}
                />
              </label>

              {selectedMarksFile && (
                <div className="rounded-2xl border border-[#10B981]/30 bg-[#10B981]/10 px-4 py-3 text-sm text-[#10B981]">
                  Selected file: <span className="font-semibold">{selectedMarksFile.name}</span>
                </div>
              )}

              <div className="flex flex-wrap items-center gap-3">
                <button
                  type="submit"
                  disabled={isUploadingMarks}
                  className="rounded-2xl bg-[#2563EB] px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-[#3B82F6] disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {isUploadingMarks ? 'Uploading...' : 'Upload & Save Marks'}
                </button>
                <span className="text-sm text-[#64748B]">Student marks will be stored safely in the database.</span>
              </div>
            </form>

            {marksMessage && (
              <div className={`mt-6 flex items-start gap-3 rounded-2xl border px-4 py-3 text-sm ${marksStatus === 'success' ? 'border-[#10B981]/30 bg-[#10B981]/10 text-[#10B981]' : 'border-rose-300 bg-rose-50 text-rose-600'}`}>
                {marksStatus === 'success' ? <CheckCircle2 className="mt-0.5 h-5 w-5" /> : <AlertCircle className="mt-0.5 h-5 w-5" />}
                <span>{marksMessage}</span>
              </div>
            )}

            {/* Student Marks count and view button */}
            <div className="mt-6 pt-6 border-t border-[#E2E8F0]">
              <div className="flex items-center justify-between gap-4">
                <div className="rounded-lg bg-[#EFF6FF] border border-[#DBEAFE] px-4 py-3 text-sm text-[#1E293B]">
                  <span className="text-[#64748B]">Total Uploaded Students: </span>
                  <span className="font-semibold">{totalStudents !== null ? totalStudents : (loadingStudents ? 'Loading...' : '0')}</span>
                </div>

                <div>
                  <button
                    onClick={toggleMarksTable}
                    className="rounded-2xl bg-[#2563EB] px-4 py-2 text-sm font-semibold text-white transition hover:bg-[#3B82F6]"
                  >
                    {loadingStudents ? 'Loading...' : (showMarksTable ? 'Hide Students' : 'View Students')}
                  </button>
                </div>
              </div>

              {fetchMarksError && (
                <div className="mt-3 rounded-2xl border border-rose-300 bg-rose-50 px-4 py-3 text-sm text-rose-600">
                  {fetchMarksError}
                </div>
              )}

              {showMarksTable && (
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
        )}

        {/* ================= TAB 2: ATTENDANCE UPLOAD ================= */}
        {activeTab === 'attendance' && (
          <section className="space-y-6">
            {/* Attribute Guidance Box */}
            <div className="rounded-3xl border border-[#DBEAFE] bg-[#EFF6FF]/60 p-6 shadow-sm">
              <div className="flex items-start gap-3">
                <div className="rounded-xl bg-[#DBEAFE] p-2 text-[#2563EB] mt-0.5">
                  <Info className="w-5 h-5" />
                </div>
                <div className="flex-1">
                  <h3 className="font-bold text-[#1E293B] text-base mb-1">Expected Excel Attributes for Student Attendance</h3>
                  <p className="text-sm text-[#64748B] mb-3">
                    Your Excel sheet (.xlsx, .xls, or .csv) should have header column names matching the attributes below:
                  </p>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                    <div className="rounded-xl bg-white border border-[#DBEAFE] p-3">
                      <div className="flex items-center gap-1.5 text-[#10B981] font-bold mb-1">
                        <Check className="w-4 h-4" /> Required Columns
                      </div>
                      <ul className="space-y-1 text-[#334155]">
                        <li>• <span className="font-semibold text-[#1E293B]">Student ID</span> (e.g. Roll No / StudentID / ID)</li>
                        <li>• <span className="font-semibold text-[#1E293B]">Student Name</span> (e.g. StudentName / Name)</li>
                      </ul>
                    </div>

                    <div className="rounded-xl bg-white border border-[#DBEAFE] p-3">
                      <div className="flex items-center gap-1.5 text-[#2563EB] font-bold mb-1">
                        <Layers className="w-4 h-4" /> Optional / Calculated Columns
                      </div>
                      <ul className="space-y-1 text-[#334155]">
                        <li>• <span className="font-semibold text-[#1E293B]">Total Classes</span> (defaults to 100 if not specified)</li>
                        <li>• <span className="font-semibold text-[#1E293B]">Attended Classes</span> (classes present)</li>
                        <li>• <span className="font-semibold text-[#1E293B]">Attendance %</span> (auto-calculated if classes given)</li>
                        <li>• <span className="font-semibold text-[#1E293B]">Department</span> & <span className="font-semibold text-[#1E293B]">Academic Year</span></li>
                      </ul>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Attendance Upload Card */}
            <div className="rounded-3xl border border-[#E2E8F0] bg-[#FFFFFF] p-6 sm:p-8 shadow-sm">
              <div className="flex items-center gap-3 mb-6">
                <div className="rounded-2xl bg-[#F0FDF4] p-3 text-[#16A34A]">
                  <CalendarCheck className="w-6 h-6" />
                </div>
                <div>
                  <h1 className="text-2xl font-extrabold text-[#1E293B]">Upload Student Attendance Sheet</h1>
                  <p className="text-sm text-[#64748B]">Choose an Excel file containing student attendance records to store in the database.</p>
                </div>
              </div>

              <form onSubmit={handleAttendanceSubmit} className="space-y-5">
                <label className="flex cursor-pointer flex-col items-center justify-center rounded-2xl border border-dashed border-[#E2E8F0] bg-[#F8FAFC] px-6 py-10 text-center transition hover:border-[#16A34A] hover:bg-[#F0FDF4]">
                  <UploadCloud className="mb-4 h-10 w-10 text-[#16A34A]" />
                  <span className="text-lg font-semibold text-[#1E293B]">Choose Attendance Excel File</span>
                  <span className="mt-2 text-sm text-[#64748B]">Supported formats: .xlsx, .xls, .csv</span>
                  <input
                    type="file"
                    accept=".xlsx,.xls,.csv"
                    className="sr-only"
                    onChange={(event) => setSelectedAttendanceFile(event.target.files?.[0] || null)}
                  />
                </label>

                {selectedAttendanceFile && (
                  <div className="rounded-2xl border border-[#10B981]/30 bg-[#10B981]/10 px-4 py-3 text-sm text-[#10B981]">
                    Selected attendance file: <span className="font-semibold">{selectedAttendanceFile.name}</span>
                  </div>
                )}

                <div className="flex flex-wrap items-center gap-3">
                  <button
                    type="submit"
                    disabled={isUploadingAttendance}
                    className="rounded-2xl bg-[#16A34A] px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-[#15803D] disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    {isUploadingAttendance ? 'Uploading...' : 'Upload & Save Attendance'}
                  </button>
                  <span className="text-sm text-[#64748B]">Attendance records will be saved into the database table.</span>
                </div>
              </form>

              {attendanceMessage && (
                <div className={`mt-6 flex items-start gap-3 rounded-2xl border px-4 py-3 text-sm ${attendanceStatus === 'success' ? 'border-[#10B981]/30 bg-[#10B981]/10 text-[#10B981]' : 'border-rose-300 bg-rose-50 text-rose-600'}`}>
                  {attendanceStatus === 'success' ? <CheckCircle2 className="mt-0.5 h-5 w-5" /> : <AlertCircle className="mt-0.5 h-5 w-5" />}
                  <span>{attendanceMessage}</span>
                </div>
              )}

              {/* Attendance count and view button */}
              <div className="mt-6 pt-6 border-t border-[#E2E8F0]">
                <div className="flex items-center justify-between gap-4">
                  <div className="rounded-lg bg-[#F0FDF4] border border-[#DCFCE7] px-4 py-3 text-sm text-[#1E293B]">
                    <span className="text-[#64748B]">Total Attendance Records: </span>
                    <span className="font-semibold text-[#16A34A]">{totalAttendance !== null ? totalAttendance : (loadingAttendance ? 'Loading...' : '0')}</span>
                  </div>

                  <div>
                    <button
                      onClick={toggleAttendanceTable}
                      className="rounded-2xl bg-[#16A34A] px-4 py-2 text-sm font-semibold text-white transition hover:bg-[#15803D]"
                    >
                      {loadingAttendance ? 'Loading...' : (showAttendanceTable ? 'Hide Attendance Records' : 'View Attendance Records')}
                    </button>
                  </div>
                </div>

                {fetchAttendanceError && (
                  <div className="mt-3 rounded-2xl border border-rose-300 bg-rose-50 px-4 py-3 text-sm text-rose-600">
                    {fetchAttendanceError}
                  </div>
                )}

                {showAttendanceTable && (
                  <div className="mt-4">
                    {loadingAttendance ? (
                      <div className="flex items-center gap-2 text-sm text-[#64748B]">
                        <div className="h-4 w-4 rounded-full border-2 border-t-transparent border-[#16A34A] animate-spin" />
                        Loading attendance records...
                      </div>
                    ) : (
                      <>
                        {attendanceList.length === 0 ? (
                          <div className="rounded-2xl border border-[#E2E8F0] bg-[#F8FAFC] px-4 py-6 text-sm text-[#64748B]">No attendance records found.</div>
                        ) : (
                          <AttendanceTable attendance={attendanceList} />
                        )}
                      </>
                    )}
                  </div>
                )}
              </div>
            </div>
          </section>
        )}
      </main>
    </div>
  );
}
