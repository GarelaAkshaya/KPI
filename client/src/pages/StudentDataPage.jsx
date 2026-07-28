import React, { useState, useEffect, useRef } from 'react';
import Navbar from '../components/Navbar';
import { 
  FileSpreadsheet, 
  Upload, 
  Users, 
  CheckCircle2, 
  AlertCircle, 
  RefreshCw, 
  Search, 
  X, 
  FileText,
  GraduationCap
} from 'lucide-react';

export default function StudentDataPage() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [loadingData, setLoadingData] = useState(true);
  const [alert, setAlert] = useState({ type: '', message: '' });
  
  const [totalStudents, setTotalStudents] = useState(0);
  const [students, setStudents] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  
  const fileInputRef = useRef(null);

  // Fetch students data from API
  const fetchStudentData = async () => {
    setLoadingData(true);
    try {
      const response = await fetch('/api/students');
      const data = await response.json();
      if (data.success) {
        setTotalStudents(data.total || 0);
        setStudents(data.students || []);
      } else {
        setAlert({ type: 'error', message: data.message || 'Failed to fetch student records.' });
      }
    } catch (err) {
      console.error('Error fetching student data:', err);
      // Backend may be offline or starting
      setAlert({ type: 'error', message: 'Could not connect to server. Please check backend API status.' });
    } finally {
      setLoadingData(false);
    }
  };

  useEffect(() => {
    fetchStudentData();
  }, []);

  // Handle file selection
  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const fileExt = file.name.split('.').pop().toLowerCase();
    if (fileExt !== 'xlsx' && fileExt !== 'xls') {
      setAlert({ 
        type: 'error', 
        message: 'Invalid file format. Please select an Excel file (.xlsx or .xls).' 
      });
      setSelectedFile(null);
      if (fileInputRef.current) fileInputRef.current.value = '';
      return;
    }

    setAlert({ type: '', message: '' });
    setSelectedFile(file);
  };

  const handleChooseFileClick = () => {
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  const handleClearFile = () => {
    setSelectedFile(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  // Handle file upload submit
  const handleUploadSubmit = async (e) => {
    e.preventDefault();
    if (!selectedFile) {
      setAlert({ type: 'error', message: 'Please choose an Excel file (.xlsx / .xls) before uploading.' });
      return;
    }

    setUploading(true);
    setAlert({ type: '', message: '' });

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const response = await fetch('/api/students/upload', {
        method: 'POST',
        body: formData,
      });

      const result = await response.json();

      if (response.ok && result.success) {
        setAlert({ type: 'success', message: result.message || 'Students uploaded successfully!' });
        handleClearFile();
        // Automatically refresh data table and total count
        await fetchStudentData();
      } else {
        setAlert({ type: 'error', message: result.message || 'Upload failed. Please check file format.' });
      }
    } catch (err) {
      console.error('Upload error:', err);
      setAlert({ type: 'error', message: 'An unexpected error occurred during upload. Server connection failed.' });
    } finally {
      setUploading(false);
    }
  };

  // Filter students based on search query
  const filteredStudents = students.filter(student => {
    const query = searchQuery.toLowerCase().trim();
    if (!query) return true;
    return (
      String(student.student_id).toLowerCase().includes(query) ||
      String(student.student_name).toLowerCase().includes(query)
    );
  });

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      {/* Navbar */}
      <Navbar />

      {/* Main Content Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12">

        {/* Page Header Banner */}
        <section className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-slate-900 via-indigo-950/70 to-slate-900 border border-slate-800 p-8 sm:p-10 mb-8 shadow-2xl">
          <div className="absolute top-0 right-0 -mt-10 -mr-10 w-96 h-96 bg-indigo-600/10 rounded-full blur-3xl pointer-events-none" />
          <div className="absolute bottom-0 left-1/3 -mb-10 w-72 h-72 bg-purple-600/10 rounded-full blur-3xl pointer-events-none" />

          <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
            <div>
              <div className="flex items-center gap-2 mb-3">
                <span className="px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-xs font-bold uppercase tracking-widest flex items-center gap-1.5">
                  <FileSpreadsheet className="w-3.5 h-3.5" />
                  Database Module
                </span>
                <span className="text-xs text-slate-400">• Excel Synchronization</span>
              </div>
              <h1 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
                Student Data Management
              </h1>
              <p className="text-slate-400 text-sm max-w-2xl mt-2 leading-relaxed">
                Upload student academic records from Excel spreadsheets (.xlsx, .xls) to update the institutional database. View real-time record metrics and table listings below.
              </p>
            </div>

            {/* Quick Stats Pill */}
            <div className="flex items-center gap-4 bg-slate-950/80 border border-slate-800 p-4 rounded-2xl self-start md:self-auto shadow-inner">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-tr from-indigo-600 to-purple-600 flex items-center justify-center text-white shadow-md shadow-indigo-500/20">
                <Users className="w-6 h-6" />
              </div>
              <div>
                <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Total Database Students</p>
                <p className="text-2xl font-black text-white">
                  {loadingData ? '...' : totalStudents.toLocaleString()}
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* Feedback Alert Banners */}
        {alert.message && (
          <div className={`mb-6 p-4 rounded-2xl border flex items-start justify-between gap-4 transition-all duration-300 shadow-lg ${
            alert.type === 'success' 
              ? 'bg-emerald-950/40 border-emerald-500/30 text-emerald-300' 
              : 'bg-rose-950/40 border-rose-500/30 text-rose-300'
          }`}>
            <div className="flex items-start gap-3">
              {alert.type === 'success' ? (
                <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
              ) : (
                <AlertCircle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
              )}
              <div>
                <h4 className="text-sm font-bold">
                  {alert.type === 'success' ? 'Upload Successful' : 'Error'}
                </h4>
                <p className="text-xs text-slate-300 mt-0.5 leading-relaxed">
                  {alert.message}
                </p>
              </div>
            </div>
            <button 
              onClick={() => setAlert({ type: '', message: '' })}
              className="text-slate-400 hover:text-white p-1 rounded-lg transition-colors"
              title="Close alert"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        )}

        {/* Excel Upload Section */}
        <section className="bg-slate-900/70 border border-slate-800 rounded-3xl p-6 sm:p-8 mb-10 shadow-xl backdrop-blur-sm">
          <div className="flex items-center gap-3 mb-6 pb-4 border-b border-slate-800">
            <div className="w-10 h-10 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400">
              <Upload className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-white">Upload Student Excel Sheet</h2>
              <p className="text-xs text-slate-400">Select and submit an Excel file containing Student ID, Student Name, Total Marks (Out of 600), and Percentage columns.</p>
            </div>
          </div>

          {/* Form with File Picker & Upload Buttons */}
          <form onSubmit={handleUploadSubmit} className="space-y-6">
            <input 
              type="file" 
              ref={fileInputRef} 
              onChange={handleFileChange}
              accept=".xlsx, .xls" 
              className="hidden" 
              id="student-excel-input"
            />

            <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-4">
              {/* Choose Excel File Button */}
              <button
                type="button"
                onClick={handleChooseFileClick}
                className="flex items-center justify-center gap-2.5 px-5 py-3.5 rounded-xl bg-slate-800 hover:bg-slate-750 text-slate-200 hover:text-white font-semibold text-sm border border-slate-700 hover:border-slate-600 transition-all shadow-sm active:scale-[0.98]"
              >
                <FileSpreadsheet className="w-4 h-4 text-indigo-400" />
                <span>Choose Excel File</span>
              </button>

              {/* Upload Students Button */}
              <button
                type="submit"
                disabled={uploading || !selectedFile}
                className={`flex items-center justify-center gap-2 px-6 py-3.5 rounded-xl font-bold text-sm text-white transition-all shadow-md ${
                  uploading || !selectedFile
                    ? 'bg-indigo-600/40 text-slate-400 cursor-not-allowed border border-indigo-500/20'
                    : 'bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 hover:from-indigo-500 hover:to-pink-500 shadow-indigo-500/25 active:scale-[0.98]'
                }`}
              >
                {uploading ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin text-white" />
                    <span>Processing Upload...</span>
                  </>
                ) : (
                  <>
                    <Upload className="w-4 h-4" />
                    <span>Upload Students</span>
                  </>
                )}
              </button>
            </div>

            {/* Selected File Status Indicator */}
            {selectedFile ? (
              <div className="flex items-center justify-between p-3.5 rounded-xl bg-indigo-500/10 border border-indigo-500/30 text-indigo-200 text-xs">
                <div className="flex items-center gap-2.5 truncate">
                  <FileText className="w-4 h-4 text-indigo-400 shrink-0" />
                  <span className="font-medium truncate">{selectedFile.name}</span>
                  <span className="text-slate-400 shrink-0">
                    ({(selectedFile.size / 1024).toFixed(1)} KB)
                  </span>
                </div>
                <button
                  type="button"
                  onClick={handleClearFile}
                  className="text-slate-400 hover:text-rose-400 p-1 transition-colors"
                  title="Remove selected file"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <p className="text-xs text-slate-400 italic">
                No file chosen. Click "Choose Excel File" to select a .xlsx or .xls file.
              </p>
            )}
          </form>
        </section>

        {/* Student Records Table Section */}
        <section className="bg-slate-900/70 border border-slate-800 rounded-3xl p-6 sm:p-8 shadow-xl backdrop-blur-sm">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6 pb-4 border-b border-slate-800">
            <div>
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                <span>Student Database Records</span>
                <span className="px-2.5 py-0.5 rounded-full bg-slate-800 border border-slate-700 text-xs font-semibold text-indigo-300">
                  {students.length} Total
                </span>
              </h2>
              <p className="text-xs text-slate-400 mt-1">Live database records stored in SQLite.</p>
            </div>

            <div className="flex items-center gap-3">
              {/* Search input */}
              <div className="relative">
                <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  placeholder="Search ID or Name..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-9 pr-4 py-2 rounded-xl bg-slate-950 border border-slate-800 text-slate-200 text-xs focus:outline-none focus:border-indigo-500 transition-colors w-48 sm:w-64"
                />
                {searchQuery && (
                  <button 
                    onClick={() => setSearchQuery('')} 
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-200"
                  >
                    <X className="w-3.5 h-3.5" />
                  </button>
                )}
              </div>

              {/* Refresh button */}
              <button
                onClick={fetchStudentData}
                disabled={loadingData}
                className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 hover:text-white transition-colors"
                title="Refresh Table"
              >
                <RefreshCw className={`w-4 h-4 ${loadingData ? 'animate-spin' : ''}`} />
              </button>
            </div>
          </div>

          {/* Table View */}
          <div className="overflow-x-auto rounded-2xl border border-slate-800">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="bg-slate-950/80 border-b border-slate-800 text-slate-400 font-bold uppercase tracking-wider">
                  <th className="py-4 px-6">Student ID</th>
                  <th className="py-4 px-6">Student Name</th>
                  <th className="py-4 px-6 text-right">Total Marks</th>
                  <th className="py-4 px-6 text-right">Percentage</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-medium">
                {loadingData ? (
                  <tr>
                    <td colSpan="4" className="py-12 text-center text-slate-400">
                      <div className="flex flex-col items-center justify-center gap-2">
                        <RefreshCw className="w-6 h-6 animate-spin text-indigo-400" />
                        <span>Loading database records...</span>
                      </div>
                    </td>
                  </tr>
                ) : filteredStudents.length === 0 ? (
                  <tr>
                    <td colSpan="4" className="py-12 text-center text-slate-400">
                      <div className="flex flex-col items-center justify-center gap-2">
                        <GraduationCap className="w-8 h-8 text-slate-600" />
                        <span className="text-sm font-semibold text-slate-300">
                          {searchQuery ? 'No student records matched your search filter.' : 'No student records found in database.'}
                        </span>
                        <p className="text-xs text-slate-400">
                          {searchQuery ? 'Try searching with a different ID or name.' : 'Upload an Excel file above to add students to the database.'}
                        </p>
                      </div>
                    </td>
                  </tr>
                ) : (
                  filteredStudents.map((student, idx) => (
                    <tr 
                      key={student.student_id || idx} 
                      className="hover:bg-indigo-500/5 transition-colors text-slate-200"
                    >
                      <td className="py-4 px-6 font-semibold text-indigo-300 font-mono">
                        {student.student_id}
                      </td>
                      <td className="py-4 px-6 font-semibold text-white">
                        {student.student_name}
                      </td>
                      <td className="py-4 px-6 text-right text-slate-300 font-mono">
                        {student.total_marks !== undefined && student.total_marks !== null ? student.total_marks : '-'}
                      </td>
                      <td className="py-4 px-6 text-right">
                        <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-bold font-mono ${
                          student.percentage >= 75
                            ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                            : student.percentage >= 60
                            ? 'bg-blue-500/10 text-blue-400 border border-blue-500/20'
                            : student.percentage >= 40
                            ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                            : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                        }`}>
                          {typeof student.percentage === 'number' ? `${student.percentage.toFixed(2)}%` : `${student.percentage}%`}
                        </span>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </section>

      </main>

      {/* Footer */}
      <footer className="bg-slate-900/50 border-t border-slate-800/80 py-6 mt-12 text-center text-xs text-slate-400">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-4">
          <p>© IFHE KPI - Institutional KPI Monitoring System. All rights reserved.</p>
          <div className="flex items-center gap-4 text-slate-400">
            <span>Database Status: <strong className="text-emerald-400 font-semibold">Active (SQLite)</strong></span>
            <span>|</span>
            <span>Module: <strong className="text-slate-300 font-semibold">Student Data Management</strong></span>
          </div>
        </div>
      </footer>
    </div>
  );
}
