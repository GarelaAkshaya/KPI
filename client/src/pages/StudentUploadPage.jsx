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
  Check,
  Eye,
  X,
  FileCheck,
  AlertTriangle,
  BookOpen
} from 'lucide-react';
import StudentTable from '../components/StudentTable';
import AttendanceTable from '../components/AttendanceTable';
import { API_BASE_URL, apiFetch } from '../api';

const DEFAULT_SEMESTER_CONFIG = {
  'Semester 1': ['Computer Programming', 'Basic Electronics', 'English', 'Digital Fabrication', 'Chemistry'],
  'Semester 2': ['Data Structures', 'Engineering Graphics', 'EVS', 'Physics', 'Higher Calculus'],
  'Semester 3': ['AI', 'IoT', 'OOPs', 'DBMS', 'EEM'],
  'Semester 4': [] // dynamic / configurable for future subjects
};

export default function StudentUploadPage() {
  const navigate = useNavigate();

  // Active Tab: 'marks' | 'attendance'
  const [activeTab, setActiveTab] = useState('marks');

  // Student Marks Upload State
  const [selectedMarksFile, setSelectedMarksFile] = useState(null);
  const [marksAcademicYear, setMarksAcademicYear] = useState('');
  const [marksDepartment, setMarksDepartment] = useState('');
  const [marksSection, setMarksSection] = useState('');
  const [marksSemester, setMarksSemester] = useState('Semester 1');
  const [marksFilterYear, setMarksFilterYear] = useState('All');
  const [marksFilterSemester, setMarksFilterSemester] = useState('All');
  const [marksFilterDepartment, setMarksFilterDepartment] = useState('All');
  const [marksFilterSection, setMarksFilterSection] = useState('All');
  const [isUploadingMarks, setIsUploadingMarks] = useState(false);
  const [isPreviewingMarks, setIsPreviewingMarks] = useState(false);
  const [marksMessage, setMarksMessage] = useState('');
  const [marksStatus, setMarksStatus] = useState('idle');
  const [students, setStudents] = useState([]);
  const [totalStudents, setTotalStudents] = useState(null);
  const [showMarksTable, setShowMarksTable] = useState(false);
  const [loadingStudents, setLoadingStudents] = useState(false);
  const [fetchMarksError, setFetchMarksError] = useState('');

  // Preview Modal State
  const [previewModalOpen, setPreviewModalOpen] = useState(false);
  const [previewData, setPreviewData] = useState(null);
  const [previewActiveTab, setPreviewActiveTab] = useState(0);

  // Submit Student Marks
  const handleMarksSubmit = async (event) => {
    if (event?.preventDefault) event.preventDefault();

    if (!selectedMarksFile) {
      setMarksStatus('error');
      setMarksMessage('Please choose an Excel file for student marks before uploading.');
      return;
    }

    if (!marksAcademicYear) {
      setMarksStatus('error');
      setMarksMessage('Academic Year is required. Please explicitly select an Academic Year before uploading.');
      return;
    }

    if (!marksDepartment) {
      setMarksStatus('error');
      setMarksMessage('Department is required. Please select the department for this upload.');
      return;
    }

    if (!marksSection) {
      setMarksStatus('error');
      setMarksMessage('Section is required. Please enter the student section for this upload.');
      return;
    }

    if (!marksSemester) {
      setMarksStatus('error');
      setMarksMessage('Semester is required. Please select Semester 1, 2, 3 or 4.');
      return;
    }

    setIsUploadingMarks(true);
    setMarksStatus('idle');
    setMarksMessage('');

    const formData = new FormData();
    formData.append('file', selectedMarksFile);
    formData.append('academic_year', marksAcademicYear);
    formData.append('department', marksDepartment);
    formData.append('section', marksSection);
    formData.append('semester', marksSemester);

    try {
      const response = await apiFetch(`${API_BASE_URL}/api/upload-students`, {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.message || (data.errors ? data.errors.join('; ') : 'Upload failed.'));
      }

      setMarksStatus('success');
      setMarksMessage(data.message || `Uploaded ${data.count} student marks records successfully.`);
      setPreviewModalOpen(false);
      setPreviewData(null);
      await fetchStudents();
      setSelectedMarksFile(null);
      setMarksAcademicYear('');
      setMarksDepartment('');
      setMarksSection('');
      const fileInput = document.getElementById('marks-file-input');
      if (fileInput) fileInput.value = '';
    } catch (error) {
      setMarksStatus('error');
      setMarksMessage(error.message || 'Unexpected error while uploading marks.');
    } finally {
      setIsUploadingMarks(false);
    }
  };

  // Preview & Validate Marks Workbook
  const handlePreviewMarks = async () => {
    if (!selectedMarksFile) {
      setMarksStatus('error');
      setMarksMessage('Please choose an Excel workbook to preview.');
      return;
    }

    if (!marksAcademicYear) {
      setMarksStatus('error');
      setMarksMessage('Academic Year is required before previewing.');
      return;
    }

    if (!marksDepartment) {
      setMarksStatus('error');
      setMarksMessage('Department is required before previewing.');
      return;
    }

    if (!marksSection) {
      setMarksStatus('error');
      setMarksMessage('Section is required before previewing.');
      return;
    }

    if (!marksSemester) {
      setMarksStatus('error');
      setMarksMessage('Semester is required. Please select Semester 1, 2, 3 or 4.');
      return;
    }

    setIsPreviewingMarks(true);
    setMarksStatus('idle');
    setMarksMessage('');

    const formData = new FormData();
    formData.append('file', selectedMarksFile);
    formData.append('academic_year', marksAcademicYear);
    formData.append('department', marksDepartment);
    formData.append('section', marksSection);
    formData.append('semester', marksSemester);

    try {
      const response = await apiFetch(`${API_BASE_URL}/api/preview-student-marks`, {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || data.message || 'Validation failed.');
      }

      setPreviewData(data);
      setPreviewActiveTab(0);
      setPreviewModalOpen(true);
    } catch (error) {
      setMarksStatus('error');
      setMarksMessage(error.message || 'Workbook validation preview failed.');
    } finally {
      setIsPreviewingMarks(false);
    }
  };

  // Student Attendance Upload State
  const [selectedAttendanceFile, setSelectedAttendanceFile] = useState(null);
  const [attendanceAcademicYear, setAttendanceAcademicYear] = useState('');
  const [attendanceDepartment, setAttendanceDepartment] = useState('');
  const [attendanceSection, setAttendanceSection] = useState('');
  const [attendanceFilterYear, setAttendanceFilterYear] = useState('All');
  const [attendanceFilterDepartment, setAttendanceFilterDepartment] = useState('All');
  const [attendanceFilterSection, setAttendanceFilterSection] = useState('All');
  const [isUploadingAttendance, setIsUploadingAttendance] = useState(false);
  const [attendanceMessage, setAttendanceMessage] = useState('');
  const [attendanceStatus, setAttendanceStatus] = useState('idle');
  const [attendanceList, setAttendanceList] = useState([]);
  const [totalAttendance, setTotalAttendance] = useState(null);
  const [showAttendanceTable, setShowAttendanceTable] = useState(false);
  const [loadingAttendance, setLoadingAttendance] = useState(false);
  const [fetchAttendanceError, setFetchAttendanceError] = useState('');
  const [attendanceSubjects, setAttendanceSubjects] = useState([]);
  const [attendanceUploadSummary, setAttendanceUploadSummary] = useState(null);

  // Submit Student Attendance
  const handleAttendanceSubmit = async (event) => {
    event.preventDefault();

    if (!selectedAttendanceFile) {
      setAttendanceStatus('error');
      setAttendanceMessage('Please choose an Excel file for student attendance before uploading.');
      return;
    }

    if (!attendanceAcademicYear) {
      setAttendanceStatus('error');
      setAttendanceMessage('Academic Year is required. Please explicitly select an Academic Year before uploading.');
      return;
    }

    if (!attendanceDepartment) {
      setAttendanceStatus('error');
      setAttendanceMessage('Department is required. Please select the department for this upload.');
      return;
    }

    if (!attendanceSection) {
      setAttendanceStatus('error');
      setAttendanceMessage('Section is required. Please enter the student section for this upload.');
      return;
    }

    setIsUploadingAttendance(true);
    setAttendanceStatus('idle');
    setAttendanceMessage('');

    const formData = new FormData();
    formData.append('file', selectedAttendanceFile);
    formData.append('academic_year', attendanceAcademicYear);
    formData.append('department', attendanceDepartment);
    formData.append('section', attendanceSection);

    try {
      const response = await apiFetch(`${API_BASE_URL}/api/upload-attendance`, {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.message || 'Upload failed.');
      }

      setAttendanceStatus('success');
      setAttendanceMessage(data.message || 'Student attendance uploaded successfully.');
      setAttendanceUploadSummary({
        students: data.students ?? data.count,
        subjects: data.subjects ?? data.subject_names?.length ?? 0,
      });
      setAttendanceSubjects(data.subject_names || []);
      await fetchAttendance();
      setSelectedAttendanceFile(null);
      setAttendanceAcademicYear('');
      setAttendanceDepartment('');
      setAttendanceSection('');
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
      const res = await apiFetch(`${API_BASE_URL}/api/students`);
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
      const res = await apiFetch(`${API_BASE_URL}/api/attendance`);
      if (!res.ok) throw new Error('Failed to fetch attendance records.');
      const data = await res.json();
      if (!Array.isArray(data)) throw new Error('Invalid response from server.');
      setAttendanceList(data);
      setTotalAttendance(data.length);
      setAttendanceSubjects(Array.from(new Set(data.flatMap((record) => record.subjects || []))));
    } catch (err) {
      setFetchAttendanceError(err.message || 'Error fetching attendance');
    } finally {
      setLoadingAttendance(false);
    }
  }

  function processStudentRecords(records) {
    const map = new Map();
    for (const r of records) {
      const sid = String(r.studentId ?? '').trim();
      const year = r.academic_year || r.academicYear || '2024-2025';
      const sem = r.semester || 'Semester 1';
      if (!sid) continue;
      const key = `${sid}_${year}_${sem}`;
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

  // Filtered views for tables
  const departmentOptions = ['Computer Science and Engineering', 'AI & Data Science'];

  const filteredStudents = React.useMemo(() => {
    return students.filter((s) => {
      const yearMatches = marksFilterYear === 'All' || (s.academic_year || s.academicYear) === marksFilterYear;
      const departmentMatches = marksFilterDepartment === 'All' || (s.department || '').trim() === marksFilterDepartment;
      const sectionMatches = marksFilterSection === 'All' || (s.section || '').trim().toUpperCase() === marksFilterSection.toUpperCase();
      const semesterMatches = marksFilterSemester === 'All' || (s.semester || 'Semester 1') === marksFilterSemester;
      return yearMatches && departmentMatches && sectionMatches && semesterMatches;
    });
  }, [students, marksFilterYear, marksFilterDepartment, marksFilterSection, marksFilterSemester]);

  const filteredAttendance = React.useMemo(() => {
    return attendanceList.filter((a) => {
      const yearMatches = attendanceFilterYear === 'All' || (a.academic_year || a.academicYear) === attendanceFilterYear;
      const departmentMatches = attendanceFilterDepartment === 'All' || (a.department || '').trim() === attendanceFilterDepartment;
      const sectionMatches = attendanceFilterSection === 'All' || (a.section || '').trim().toUpperCase() === attendanceFilterSection.toUpperCase();
      return yearMatches && departmentMatches && sectionMatches;
    });
  }, [attendanceList, attendanceFilterYear, attendanceFilterDepartment, attendanceFilterSection]);

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
          <section className="space-y-6">
            <div className="rounded-3xl border border-[#E2E8F0] bg-[#FFFFFF] p-6 sm:p-8 shadow-sm">
              <div className="flex items-center gap-3 mb-6">
                <div className="rounded-2xl bg-[#EFF6FF] p-3 text-[#2563EB]">
                  <FileSpreadsheet className="w-6 h-6" />
                </div>
                <div>
                  <h1 className="text-2xl font-extrabold text-[#1E293B]">Upload Semester Marks Workbook</h1>
                  <p className="text-sm text-[#64748B]">
                    Upload one Excel workbook (.xlsx) per semester containing separate worksheets for each subject.
                  </p>
                </div>
              </div>

              <form onSubmit={handleMarksSubmit} className="space-y-6">
                {/* Department, Year, Section, Semester Controls Grid */}
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                  {/* Department Selection */}
                  <div className="space-y-2">
                    <label htmlFor="marks-department" className="block text-xs font-bold uppercase tracking-wider text-[#1E293B] flex items-center gap-1.5">
                      Department <span className="text-rose-500">*</span>
                    </label>
                    <select
                      id="marks-department"
                      required
                      value={marksDepartment}
                      onChange={(event) => setMarksDepartment(event.target.value)}
                      className="w-full appearance-none bg-[#F8FAFC] border border-[#E2E8F0] rounded-2xl px-4 py-3 text-[#1E293B] text-sm font-semibold focus:outline-none focus:ring-2 focus:ring-[#2563EB]/40 focus:border-[#2563EB] focus:bg-[#FFFFFF] transition cursor-pointer"
                    >
                      <option value="">Select Department</option>
                      {departmentOptions.map((dept) => (
                        <option key={dept} value={dept}>{dept}</option>
                      ))}
                    </select>
                  </div>

                  {/* Academic Year Selection */}
                  <div className="space-y-2">
                    <label htmlFor="marks-academic-year" className="block text-xs font-bold uppercase tracking-wider text-[#1E293B] flex items-center gap-1.5">
                      Academic Year <span className="text-rose-500">*</span>
                    </label>
                    <div className="relative">
                      <select
                        id="marks-academic-year"
                        required
                        value={marksAcademicYear}
                        onChange={(event) => setMarksAcademicYear(event.target.value)}
                        className="w-full appearance-none bg-[#F8FAFC] border border-[#E2E8F0] rounded-2xl px-4 py-3 pr-10 text-[#1E293B] text-sm font-semibold focus:outline-none focus:ring-2 focus:ring-[#2563EB]/40 focus:border-[#2563EB] focus:bg-[#FFFFFF] transition cursor-pointer"
                      >
                        <option value="" disabled>Select Year</option>
                        <option value="2024-2025">2024-2025</option>
                        <option value="2025-2026">2025-2026</option>
                      </select>
                      <div className="absolute inset-y-0 right-0 flex items-center px-4 pointer-events-none text-[#64748B]">
                        <svg className="w-4 h-4 fill-current" viewBox="0 0 20 20">
                          <path d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" />
                        </svg>
                      </div>
                    </div>
                  </div>

                  {/* Section Selection */}
                  <div className="space-y-2">
                    <label htmlFor="marks-section" className="block text-xs font-bold uppercase tracking-wider text-[#1E293B] flex items-center gap-1.5">
                      Section <span className="text-rose-500">*</span>
                    </label>
                    <input
                      id="marks-section"
                      type="text"
                      required
                      value={marksSection}
                      onChange={(event) => setMarksSection(event.target.value)}
                      placeholder="e.g. A, B"
                      className="w-full bg-[#F8FAFC] border border-[#E2E8F0] rounded-2xl px-4 py-3 text-[#1E293B] text-sm font-semibold focus:outline-none focus:ring-2 focus:ring-[#2563EB]/40 focus:border-[#2563EB] focus:bg-[#FFFFFF] transition"
                    />
                  </div>

                  {/* Semester Selection */}
                  <div className="space-y-2">
                    <label htmlFor="marks-semester" className="block text-xs font-bold uppercase tracking-wider text-[#1E293B] flex items-center gap-1.5">
                      Semester <span className="text-rose-500">*</span>
                    </label>
                    <div className="relative">
                      <select
                        id="marks-semester"
                        required
                        value={marksSemester}
                        onChange={(event) => setMarksSemester(event.target.value)}
                        className="w-full appearance-none bg-[#F8FAFC] border border-[#E2E8F0] rounded-2xl px-4 py-3 pr-10 text-[#1E293B] text-sm font-semibold focus:outline-none focus:ring-2 focus:ring-[#2563EB]/40 focus:border-[#2563EB] focus:bg-[#FFFFFF] transition cursor-pointer"
                      >
                        <option value="Semester 1">Semester 1</option>
                        <option value="Semester 2">Semester 2</option>
                        <option value="Semester 3">Semester 3</option>
                        <option value="Semester 4">Semester 4</option>
                      </select>
                      <div className="absolute inset-y-0 right-0 flex items-center px-4 pointer-events-none text-[#64748B]">
                        <svg className="w-4 h-4 fill-current" viewBox="0 0 20 20">
                          <path d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" />
                        </svg>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Semester Subject Guidance Card */}
                <div className="rounded-2xl border border-[#DBEAFE] bg-[#F0F7FF] p-4 text-xs space-y-3">
                  <div className="flex items-center justify-between flex-wrap gap-2">
                    <div className="flex items-center gap-2 font-bold text-[#1E293B]">
                      <BookOpen className="w-4 h-4 text-[#2563EB]" />
                      <span>{marksSemester} Subjects (Worksheet Names):</span>
                    </div>
                    <span className="text-[#64748B]">Format: S#, Enrolno, Name, Test 1 (15), Lab-1 (15), Test 2 (15), Lab-2 (15), Compre (40), Total (100)</span>
                  </div>

                  <div className="flex flex-wrap gap-2">
                    {(DEFAULT_SEMESTER_CONFIG[marksSemester] || []).length > 0 ? (
                      (DEFAULT_SEMESTER_CONFIG[marksSemester] || []).map((sub) => (
                        <span
                          key={sub}
                          className="inline-flex items-center gap-1.5 px-3 py-1 rounded-xl bg-white border border-[#BFDBFE] text-[#1E40AF] font-semibold text-xs shadow-xs"
                        >
                          <CheckCircle2 className="w-3.5 h-3.5 text-[#2563EB]" />
                          {sub}
                        </span>
                      ))
                    ) : (
                      <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-xl bg-white border border-amber-300 text-amber-800 font-semibold text-xs">
                        <Info className="w-3.5 h-3.5 text-amber-600" />
                        Semester 4 subjects are configurable: all worksheet tabs will be dynamically identified as subjects.
                      </span>
                    )}
                  </div>

                  <p className="text-[#64748B] text-[11px] leading-relaxed">
                    <strong className="text-[#1E293B]">Automatic Calculation:</strong> Total (100) is calculated automatically from individual components (Test 1 + Lab-1 + Test 2 + Lab-2 + Compre).
                  </p>
                </div>

                {/* File Upload Dropzone */}
                <label className="flex cursor-pointer flex-col items-center justify-center rounded-2xl border border-dashed border-[#E2E8F0] bg-[#F8FAFC] px-6 py-10 text-center transition hover:border-[#2563EB] hover:bg-[#EFF6FF]">
                  <UploadCloud className="mb-4 h-10 w-10 text-[#2563EB]" />
                  <span className="text-lg font-semibold text-[#1E293B]">Choose Semester Excel Workbook</span>
                  <span className="mt-2 text-sm text-[#64748B]">Supported formats: .xlsx, .xls (one sheet per subject)</span>
                  <input
                    id="marks-file-input"
                    type="file"
                    accept=".xlsx,.xls"
                    className="sr-only"
                    onChange={(event) => setSelectedMarksFile(event.target.files?.[0] || null)}
                  />
                </label>

                {selectedMarksFile && (
                  <div className="rounded-2xl border border-[#10B981]/30 bg-[#10B981]/10 px-4 py-3 text-sm text-[#10B981] flex items-center justify-between">
                    <span className="flex items-center gap-2">
                      <FileCheck className="w-5 h-5 text-[#10B981]" />
                      Selected file: <strong className="font-semibold">{selectedMarksFile.name}</strong> ({(selectedMarksFile.size / 1024).toFixed(1)} KB)
                    </span>
                    <button
                      type="button"
                      onClick={() => {
                        setSelectedMarksFile(null);
                        const fileInput = document.getElementById('marks-file-input');
                        if (fileInput) fileInput.value = '';
                      }}
                      className="text-xs text-rose-500 hover:underline cursor-pointer"
                    >
                      Remove
                    </button>
                  </div>
                )}

                {/* Action Buttons */}
                <div className="flex flex-wrap items-center gap-3">
                  <button
                    type="button"
                    onClick={handlePreviewMarks}
                    disabled={isPreviewingMarks || !selectedMarksFile}
                    className="inline-flex items-center gap-2 rounded-2xl bg-white border border-[#2563EB] text-[#2563EB] px-5 py-2.5 text-sm font-semibold transition hover:bg-[#EFF6FF] disabled:cursor-not-allowed disabled:opacity-50 shadow-xs cursor-pointer"
                  >
                    <Eye className="w-4 h-4" />
                    {isPreviewingMarks ? 'Validating Workbook...' : 'Preview & Validate Workbook'}
                  </button>

                  <button
                    type="submit"
                    disabled={isUploadingMarks || !selectedMarksFile}
                    className="inline-flex items-center gap-2 rounded-2xl bg-[#2563EB] px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-[#1D4ED8] disabled:cursor-not-allowed disabled:opacity-60 shadow-xs cursor-pointer"
                  >
                    <UploadCloud className="w-4 h-4" />
                    {isUploadingMarks ? 'Uploading & Replacing...' : 'Upload & Save Marks'}
                  </button>

                  <span className="text-xs text-[#64748B]">
                    Safe replacement: Updates only matching records for the selected semester, section, and workbook subjects.
                  </span>
                </div>
              </form>

              {marksMessage && (
                <div className={`mt-6 flex items-start gap-3 rounded-2xl border px-4 py-3 text-sm ${marksStatus === 'success' ? 'border-[#10B981]/30 bg-[#10B981]/10 text-[#10B981]' : 'border-rose-300 bg-rose-50 text-rose-600'}`}>
                  {marksStatus === 'success' ? <CheckCircle2 className="mt-0.5 h-5 w-5" /> : <AlertCircle className="mt-0.5 h-5 w-5" />}
                  <span>{marksMessage}</span>
                </div>
              )}
            </div>

            {/* Preview Modal */}
            {previewModalOpen && previewData && (
              <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 sm:p-6 overflow-y-auto">
                <div className="bg-white rounded-3xl max-w-4xl w-full max-h-[90vh] flex flex-col shadow-2xl border border-[#E2E8F0] overflow-hidden">
                  {/* Modal Header */}
                  <div className="p-6 border-b border-[#E2E8F0] flex items-start justify-between bg-slate-50">
                    <div>
                      <div className="flex items-center gap-2 flex-wrap">
                        <h2 className="text-xl font-bold text-[#1E293B]">Workbook Validation & Preview</h2>
                        <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold ${
                          previewData.valid 
                            ? 'bg-emerald-100 text-emerald-800 border border-emerald-300' 
                            : 'bg-rose-100 text-rose-800 border border-rose-300'
                        }`}>
                          {previewData.valid ? 'Validation Passed' : 'Validation Errors'}
                        </span>
                      </div>
                      <div className="flex items-center gap-2 mt-2 text-xs text-[#64748B] flex-wrap">
                        <span className="font-semibold text-[#1E293B]">{previewData.department}</span>
                        <span>•</span>
                        <span>Section {previewData.section}</span>
                        <span>•</span>
                        <span className="font-semibold text-[#2563EB]">{previewData.semester}</span>
                        <span>•</span>
                        <span>{previewData.academic_year}</span>
                        <span>•</span>
                        <span className="font-mono text-slate-500">{previewData.filename}</span>
                      </div>
                    </div>
                    <button
                      onClick={() => setPreviewModalOpen(false)}
                      className="p-2 text-slate-400 hover:text-slate-700 rounded-xl hover:bg-slate-200 transition cursor-pointer"
                    >
                      <X className="w-5 h-5" />
                    </button>
                  </div>

                  {/* Modal Content */}
                  <div className="p-6 overflow-y-auto space-y-5 flex-1">
                    {/* Validation Errors */}
                    {previewData.errors && previewData.errors.length > 0 && (
                      <div className="rounded-2xl border border-rose-200 bg-rose-50 p-4 text-xs text-rose-800 space-y-1">
                        <div className="font-bold flex items-center gap-1.5 text-rose-900">
                          <AlertTriangle className="w-4 h-4 text-rose-600" />
                          Validation Issues Found ({previewData.errors.length}):
                        </div>
                        <ul className="list-disc list-inside space-y-0.5 pl-1">
                          {previewData.errors.map((err, i) => (
                            <li key={i}>{err}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Warnings */}
                    {previewData.warnings && previewData.warnings.length > 0 && (
                      <div className="rounded-2xl border border-amber-200 bg-amber-50 p-4 text-xs text-amber-800 space-y-1">
                        <div className="font-bold flex items-center gap-1.5 text-amber-900">
                          <Info className="w-4 h-4 text-amber-600" />
                          Validation Warnings:
                        </div>
                        <ul className="list-disc list-inside space-y-0.5 pl-1">
                          {previewData.warnings.map((w, i) => (
                            <li key={i}>{w}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Metrics Row */}
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                      <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                        <div className="text-slate-500 font-medium">Worksheets</div>
                        <div className="text-lg font-bold text-slate-900 mt-0.5">{previewData.total_sheets} Sheets</div>
                      </div>
                      <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                        <div className="text-slate-500 font-medium">Students Detected</div>
                        <div className="text-lg font-bold text-slate-900 mt-0.5">{previewData.total_students} Students</div>
                      </div>
                      <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                        <div className="text-slate-500 font-medium">Semester Target</div>
                        <div className="text-lg font-bold text-indigo-600 mt-0.5">{previewData.semester}</div>
                      </div>
                      <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                        <div className="text-slate-500 font-medium">Status</div>
                        <div className={`text-lg font-bold mt-0.5 ${previewData.valid ? 'text-emerald-600' : 'text-rose-600'}`}>
                          {previewData.valid ? 'Ready to Save' : 'Invalid'}
                        </div>
                      </div>
                    </div>

                    {/* Sheet Selection Tabs */}
                    {previewData.sheets && previewData.sheets.length > 0 && (
                      <div className="space-y-3">
                        <div className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                          Subject Worksheets (Click to inspect rows):
                        </div>
                        <div className="flex gap-2 overflow-x-auto pb-1">
                          {previewData.sheets.map((sheet, idx) => (
                            <button
                              key={sheet.sheet_name || idx}
                              type="button"
                              onClick={() => setPreviewActiveTab(idx)}
                              className={`px-3.5 py-2 rounded-xl text-xs font-semibold whitespace-nowrap transition flex items-center gap-1.5 border cursor-pointer ${
                                previewActiveTab === idx
                                  ? 'bg-[#2563EB] text-white border-[#2563EB] shadow-xs'
                                  : 'bg-white text-slate-700 border-slate-200 hover:bg-slate-50'
                              }`}
                            >
                              <span>{sheet.subject_name || sheet.sheet_name}</span>
                              <span className={`text-[10px] px-1.5 py-0.5 rounded-full ${
                                previewActiveTab === idx ? 'bg-white/20 text-white' : 'bg-slate-100 text-slate-600'
                              }`}>
                                {sheet.valid_rows ?? sheet.total_rows}
                              </span>
                            </button>
                          ))}
                        </div>

                        {/* Selected Sheet Rows Table */}
                        {previewData.sheets[previewActiveTab] && (
                          <div className="border border-slate-200 rounded-2xl overflow-hidden bg-white shadow-xs">
                            <div className="p-3 bg-slate-50 border-b border-slate-200 flex items-center justify-between flex-wrap gap-2 text-xs">
                              <span className="font-bold text-slate-800">
                                Sheet: {previewData.sheets[previewActiveTab].sheet_name} ({previewData.sheets[previewActiveTab].valid_rows} students)
                              </span>
                              <span className="text-slate-500 text-[11px]">
                                Auto-calculated: Total (100) = Test 1 (15) + Lab-1 (15) + Test 2 (15) + Lab-2 (15) + Compre (40)
                              </span>
                            </div>
                            <div className="max-h-64 overflow-y-auto">
                              <table className="min-w-full text-xs">
                                <thead className="sticky top-0 bg-slate-100 text-slate-700 font-semibold border-b border-slate-200">
                                  <tr>
                                    <th className="px-3 py-2 text-left">#</th>
                                    <th className="px-3 py-2 text-left">Enrollment No</th>
                                    <th className="px-3 py-2 text-left">Student Name</th>
                                    <th className="px-3 py-2 text-center">Test 1 (15)</th>
                                    <th className="px-3 py-2 text-center">Lab-1 (15)</th>
                                    <th className="px-3 py-2 text-center">Test 2 (15)</th>
                                    <th className="px-3 py-2 text-center">Lab-2 (15)</th>
                                    <th className="px-3 py-2 text-center">Compre (40)</th>
                                    <th className="px-3 py-2 text-center bg-blue-50 text-blue-900 font-bold">Total (100)</th>
                                  </tr>
                                </thead>
                                <tbody className="divide-y divide-slate-100">
                                  {(previewData.sheets[previewActiveTab].sample_rows || []).map((row, rIdx) => (
                                    <tr key={rIdx} className="hover:bg-slate-50 transition">
                                      <td className="px-3 py-1.5 text-slate-500">{rIdx + 1}</td>
                                      <td className="px-3 py-1.5 font-semibold text-slate-800">{row.enrollment_number}</td>
                                      <td className="px-3 py-1.5 text-slate-700">{row.student_name}</td>
                                      <td className="px-3 py-1.5 text-center">{row.test1 ?? '—'}</td>
                                      <td className="px-3 py-1.5 text-center">{row.lab1 ?? '—'}</td>
                                      <td className="px-3 py-1.5 text-center">{row.test2 ?? '—'}</td>
                                      <td className="px-3 py-1.5 text-center">{row.lab2 ?? '—'}</td>
                                      <td className="px-3 py-1.5 text-center">{row.compre ?? '—'}</td>
                                      <td className="px-3 py-1.5 text-center bg-blue-50/50 font-bold text-blue-700">
                                        {row.total !== null && row.total !== undefined ? Number(row.total).toFixed(1) : '—'}
                                      </td>
                                    </tr>
                                  ))}
                                </tbody>
                              </table>
                            </div>
                          </div>
                        )}
                      </div>
                    )}

                    {/* Replacement Safety Notice */}
                    <div className="p-3 bg-amber-50/80 border border-amber-200 rounded-xl text-xs text-amber-800 flex items-start gap-2">
                      <Info className="w-4 h-4 text-amber-600 mt-0.5 shrink-0" />
                      <span>
                        <strong>Safe Re-upload Protection:</strong> Saving will only replace existing records for{' '}
                        <strong>{previewData.department}</strong>, Section <strong>{previewData.section}</strong>,{' '}
                        <strong>{previewData.semester}</strong> ({previewData.academic_year}) for the{' '}
                        <strong>{previewData.total_sheets} subjects</strong> in this workbook. Attendance, faculty, lab utilization, and other semesters are strictly untouched.
                      </span>
                    </div>
                  </div>

                  {/* Modal Footer */}
                  <div className="p-4 bg-slate-50 border-t border-[#E2E8F0] flex items-center justify-between">
                    <button
                      type="button"
                      onClick={() => setPreviewModalOpen(false)}
                      className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-700 hover:bg-slate-200 transition cursor-pointer"
                    >
                      Close Preview
                    </button>

                    <button
                      type="button"
                      onClick={() => handleMarksSubmit()}
                      disabled={!previewData.valid || isUploadingMarks}
                      className="inline-flex items-center gap-1.5 px-5 py-2.5 rounded-xl bg-[#2563EB] text-white text-xs font-semibold hover:bg-[#1D4ED8] transition disabled:opacity-50 disabled:cursor-not-allowed shadow-xs cursor-pointer"
                    >
                      <Check className="w-4 h-4" />
                      {isUploadingMarks ? 'Saving Records...' : 'Confirm & Save to Database'}
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* Student Marks Table Section */}
            <div className="rounded-3xl border border-[#E2E8F0] bg-[#FFFFFF] p-6 sm:p-8 shadow-sm space-y-6">
              <div className="flex flex-wrap items-center justify-between gap-4">
                <div className="flex flex-wrap items-center gap-3">
                  <div className="rounded-xl bg-[#EFF6FF] border border-[#DBEAFE] px-4 py-2 text-sm text-[#1E293B]">
                    <span className="text-[#64748B]">Showing Students: </span>
                    <span className="font-semibold text-[#2563EB]">{filteredStudents.length}</span>
                    <span className="text-xs text-[#64748B] ml-2">({marksFilterYear === 'All' ? 'All Years' : marksFilterYear} • {marksFilterSemester === 'All' ? 'All Semesters' : marksFilterSemester})</span>
                  </div>

                  <div className="flex items-center gap-2 bg-[#F8FAFC] border border-[#E2E8F0] rounded-xl px-3 py-1.5 text-xs">
                    <span className="text-[#64748B] font-semibold">Semester:</span>
                    <select
                      value={marksFilterSemester}
                      onChange={(e) => setMarksFilterSemester(e.target.value)}
                      className="bg-transparent font-bold text-[#1E293B] focus:outline-none cursor-pointer"
                    >
                      <option value="All">All Semesters</option>
                      <option value="Semester 1">Semester 1</option>
                      <option value="Semester 2">Semester 2</option>
                      <option value="Semester 3">Semester 3</option>
                      <option value="Semester 4">Semester 4</option>
                    </select>
                  </div>

                  <div className="flex items-center gap-2 bg-[#F8FAFC] border border-[#E2E8F0] rounded-xl px-3 py-1.5 text-xs">
                    <span className="text-[#64748B] font-semibold">Filter Year:</span>
                    <select
                      value={marksFilterYear}
                      onChange={(e) => setMarksFilterYear(e.target.value)}
                      className="bg-transparent font-bold text-[#1E293B] focus:outline-none cursor-pointer"
                    >
                      <option value="All">All Years</option>
                      <option value="2024-2025">2024-2025</option>
                      <option value="2025-2026">2025-2026</option>
                    </select>
                  </div>

                  <div className="flex items-center gap-2 bg-[#F8FAFC] border border-[#E2E8F0] rounded-xl px-3 py-1.5 text-xs">
                    <span className="text-[#64748B] font-semibold">Department:</span>
                    <select
                      value={marksFilterDepartment}
                      onChange={(e) => setMarksFilterDepartment(e.target.value)}
                      className="bg-transparent font-bold text-[#1E293B] focus:outline-none cursor-pointer"
                    >
                      <option value="All">All</option>
                      {departmentOptions.map((dept) => (
                        <option key={dept} value={dept}>{dept}</option>
                      ))}
                    </select>
                  </div>

                  <div className="flex items-center gap-2 bg-[#F8FAFC] border border-[#E2E8F0] rounded-xl px-3 py-1.5 text-xs">
                    <span className="text-[#64748B] font-semibold">Section:</span>
                    <select
                      value={marksFilterSection}
                      onChange={(e) => setMarksFilterSection(e.target.value)}
                      className="bg-transparent font-bold text-[#1E293B] focus:outline-none cursor-pointer"
                    >
                      <option value="All">All</option>
                      {Array.from(new Set(students.map((s) => String(s.section || '').trim()).filter(Boolean))).sort().map((section) => (
                        <option key={section} value={section}>{section}</option>
                      ))}
                    </select>
                  </div>
                </div>
              </div>

              <div>
                {loadingStudents ? (
                  <div className="flex items-center gap-2 text-sm text-[#64748B] py-6">
                    <div className="h-4 w-4 rounded-full border-2 border-t-transparent border-[#2563EB] animate-spin" />
                    Loading students...
                  </div>
                ) : (
                  <>
                    {filteredStudents.length === 0 ? (
                      <div className="rounded-2xl border border-[#E2E8F0] bg-[#F8FAFC] px-4 py-8 text-center text-sm text-[#64748B]">
                        No student records found for the selected filters.
                      </div>
                    ) : (
                      <StudentTable students={filteredStudents} />
                    )}
                  </>
                )}
              </div>
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
                  <h3 className="font-bold text-[#1E293B] text-base mb-1">Attendance Sheet Format</h3>
                  <p className="text-sm text-[#64748B] mb-3">
                    Use the first column for each student name or identifier. Every remaining header is detected as a subject automatically.
                  </p>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                    <div className="rounded-xl bg-white border border-[#DBEAFE] p-3">
                      <div className="flex items-center gap-1.5 text-[#10B981] font-bold mb-1">
                        <Check className="w-4 h-4" /> Student Identifier
                      </div>
                      <ul className="space-y-1 text-[#334155]">
                        <li>• Include an Enrollment Number column matching uploaded student details</li>
                        <li>• Student names are filled from the matching student record</li>
                      </ul>
                    </div>

                    <div className="rounded-xl bg-white border border-[#DBEAFE] p-3">
                      <div className="flex items-center gap-1.5 text-[#2563EB] font-bold mb-1">
                        <Layers className="w-4 h-4" /> Dynamic Subject Columns
                      </div>
                      <ul className="space-y-1 text-[#334155]">
                        <li>• Subject headers and values are read from the uploaded file</li>
                        <li>• Values are treated as attendance percentages from 0 to 100</li>
                        <li>• Overall attendance is the average of valid subject values</li>
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
                {/* Academic Year Selection */}
                <div className="space-y-2">
                  <label htmlFor="attendance-academic-year" className="block text-xs font-bold uppercase tracking-wider text-[#1E293B] flex items-center gap-1.5">
                    Academic Year <span className="text-rose-500">*</span>
                  </label>
                  <div className="relative">
                    <select
                      id="attendance-academic-year"
                      required
                      value={attendanceAcademicYear}
                      onChange={(event) => setAttendanceAcademicYear(event.target.value)}
                      className="w-full appearance-none bg-[#F8FAFC] border border-[#E2E8F0] rounded-2xl px-4 py-3 pr-10 text-[#1E293B] text-sm font-semibold focus:outline-none focus:ring-2 focus:ring-[#16A34A]/40 focus:border-[#16A34A] focus:bg-[#FFFFFF] transition cursor-pointer"
                    >
                      <option value="" disabled>Select Academic Year</option>
                      <option value="2024-2025">2024-2025</option>
                      <option value="2025-2026">2025-2026</option>
                    </select>
                    <div className="absolute inset-y-0 right-0 flex items-center px-4 pointer-events-none text-[#64748B]">
                      <svg className="w-4 h-4 fill-current" viewBox="0 0 20 20">
                        <path d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" />
                      </svg>
                    </div>
                  </div>
                </div>

                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <label htmlFor="attendance-department" className="block text-xs font-bold uppercase tracking-wider text-[#1E293B] flex items-center gap-1.5">
                      Department <span className="text-rose-500">*</span>
                    </label>
                    <select
                      id="attendance-department"
                      required
                      value={attendanceDepartment}
                      onChange={(event) => setAttendanceDepartment(event.target.value)}
                      className="w-full appearance-none bg-[#F8FAFC] border border-[#E2E8F0] rounded-2xl px-4 py-3 text-[#1E293B] text-sm font-semibold focus:outline-none focus:ring-2 focus:ring-[#16A34A]/40 focus:border-[#16A34A] focus:bg-[#FFFFFF] transition cursor-pointer"
                    >
                      <option value="">Select Department</option>
                      {departmentOptions.map((dept) => (
                        <option key={dept} value={dept}>{dept}</option>
                      ))}
                    </select>
                  </div>

                  <div className="space-y-2">
                    <label htmlFor="attendance-section" className="block text-xs font-bold uppercase tracking-wider text-[#1E293B] flex items-center gap-1.5">
                      Section <span className="text-rose-500">*</span>
                    </label>
                    <input
                      id="attendance-section"
                      type="text"
                      required
                      value={attendanceSection}
                      onChange={(event) => setAttendanceSection(event.target.value)}
                      placeholder="e.g. A, B, C1"
                      className="w-full bg-[#F8FAFC] border border-[#E2E8F0] rounded-2xl px-4 py-3 text-[#1E293B] text-sm font-semibold focus:outline-none focus:ring-2 focus:ring-[#16A34A]/40 focus:border-[#16A34A] focus:bg-[#FFFFFF] transition"
                    />
                  </div>
                </div>

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

              {/* Attendance count, filter and view button */}
              <div className="mt-6 pt-6 border-t border-[#E2E8F0]">
                <div className="flex flex-wrap items-center justify-between gap-4">
                  <div className="flex flex-wrap items-center gap-3">
                    <div className="rounded-lg bg-[#F0FDF4] border border-[#DCFCE7] px-4 py-2.5 text-sm text-[#1E293B]">
                      <span className="text-[#64748B]">Showing Records: </span>
                      <span className="font-semibold text-[#16A34A]">{filteredAttendance.length}</span>
                      <span className="text-xs text-[#64748B] ml-2">({attendanceFilterYear === 'All' ? 'All Years' : attendanceFilterYear})</span>
                    </div>

                    <div className="flex items-center gap-2 bg-[#F8FAFC] border border-[#E2E8F0] rounded-xl px-3 py-1.5 text-xs">
                      <span className="text-[#64748B] font-semibold">Filter Year:</span>
                      <select
                        value={attendanceFilterYear}
                        onChange={(e) => setAttendanceFilterYear(e.target.value)}
                        className="bg-transparent font-bold text-[#1E293B] focus:outline-none cursor-pointer"
                      >
                        <option value="All">All Years</option>
                        <option value="2024-2025">2024-2025</option>
                        <option value="2025-2026">2025-2026</option>
                      </select>
                    </div>

                    <div className="flex items-center gap-2 bg-[#F8FAFC] border border-[#E2E8F0] rounded-xl px-3 py-1.5 text-xs">
                      <span className="text-[#64748B] font-semibold">Department:</span>
                      <select
                        value={attendanceFilterDepartment}
                        onChange={(e) => setAttendanceFilterDepartment(e.target.value)}
                        className="bg-transparent font-bold text-[#1E293B] focus:outline-none cursor-pointer"
                      >
                        <option value="All">All</option>
                        {departmentOptions.map((dept) => (
                          <option key={dept} value={dept}>{dept}</option>
                        ))}
                      </select>
                    </div>

                    <div className="flex items-center gap-2 bg-[#F8FAFC] border border-[#E2E8F0] rounded-xl px-3 py-1.5 text-xs">
                      <span className="text-[#64748B] font-semibold">Section:</span>
                      <select
                        value={attendanceFilterSection}
                        onChange={(e) => setAttendanceFilterSection(e.target.value)}
                        className="bg-transparent font-bold text-[#1E293B] focus:outline-none cursor-pointer"
                      >
                        <option value="All">All</option>
                        {Array.from(new Set(attendanceList.map((a) => String(a.section || '').trim()).filter(Boolean))).sort().map((section) => (
                          <option key={section} value={section}>{section}</option>
                        ))}
                      </select>
                    </div>
                  </div>

                  <div>
                    <button
                      onClick={toggleAttendanceTable}
                      className="rounded-2xl bg-[#16A34A] px-4 py-2 text-sm font-semibold text-white transition hover:bg-[#15803D]"
                    >
                      {loadingAttendance ? 'Loading...' : (showAttendanceTable ? 'Hide Records' : 'View Records')}
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
                        {filteredAttendance.length === 0 ? (
                          <div className="rounded-2xl border border-[#E2E8F0] bg-[#F8FAFC] px-4 py-6 text-sm text-[#64748B]">
                            No attendance records found for {attendanceFilterYear === 'All' ? 'any academic year' : attendanceFilterYear}.
                          </div>
                        ) : (
                          <AttendanceTable attendance={filteredAttendance} />
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
