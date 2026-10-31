import React, { useState } from 'react';
import { BookOpen, ChevronDown, ChevronUp, Layers, CheckCircle2 } from 'lucide-react';

export default function StudentTable({ students }) {
  const [expandedRow, setExpandedRow] = useState(null);

  const toggleRow = (idx) => {
    setExpandedRow(expandedRow === idx ? null : idx);
  };

  const getSubjectMarks = (s) => {
    if (s.subject_marks && Object.keys(s.subject_marks).length > 0) {
      return s.subject_marks;
    }
    if (s.subject_marks_json) {
      try {
        const parsed = JSON.parse(s.subject_marks_json);
        if (parsed && typeof parsed === 'object') return parsed;
      } catch {
        // ignore
      }
    }
    // Fallback to legacy fields
    const legacy = {};
    if (s.dm !== null && s.dm !== undefined) legacy['DM'] = s.dm;
    if (s.dsc !== null && s.dsc !== undefined) legacy['DSC'] = s.dsc;
    if (s.coa !== null && s.coa !== undefined) legacy['COA'] = s.coa;
    if (s.python_marks !== null && s.python_marks !== undefined) legacy['Python'] = s.python_marks;
    if (s.ml !== null && s.ml !== undefined) legacy['ML'] = s.ml;
    return legacy;
  };

  const getComponentMarks = (s) => {
    if (s.component_marks && Object.keys(s.component_marks).length > 0) {
      return s.component_marks;
    }
    if (s.component_marks_json) {
      try {
        const parsed = JSON.parse(s.component_marks_json);
        if (parsed && typeof parsed === 'object') return parsed;
      } catch {
        // ignore
      }
    }
    return {};
  };

  return (
    <div className="mt-4 w-full">
      <div className="rounded-2xl border border-[#E2E8F0] bg-[#FFFFFF] overflow-hidden shadow-sm">
        <div className="max-h-[500px] overflow-y-auto w-full">
          <table className="min-w-full table-auto text-sm">
            <thead className="sticky top-0 bg-[#EFF6FF] z-10">
              <tr className="text-left border-b border-[#E2E8F0]">
                <th className="px-4 py-3 text-[#1E293B] font-semibold">S.No</th>
                <th className="px-4 py-3 text-[#1E293B] font-semibold">Enrollment Number</th>
                <th className="px-4 py-3 text-[#1E293B] font-semibold">Student Name</th>
                <th className="px-4 py-3 text-[#1E293B] font-semibold">Department</th>
                <th className="px-4 py-3 text-[#1E293B] font-semibold">Section</th>
                <th className="px-4 py-3 text-[#1E293B] font-semibold">Semester</th>
                <th className="px-4 py-3 text-[#1E293B] font-semibold">Academic Year</th>
                <th className="px-4 py-3 text-[#1E293B] font-semibold">Total Marks</th>
                <th className="px-4 py-3 text-[#1E293B] font-semibold">Percentage</th>
                <th className="px-4 py-3 text-[#1E293B] font-semibold text-center">Subjects</th>
              </tr>
            </thead>

            <tbody className="divide-y divide-[#E2E8F0]">
              {students.map((s, idx) => {
                const subjectMarks = getSubjectMarks(s);
                const componentMarks = getComponentMarks(s);
                const subjectKeys = Object.keys(subjectMarks);
                const isExpanded = expandedRow === idx;

                return (
                  <React.Fragment key={s.id ?? idx}>
                    <tr
                      className={
                        'transition-colors hover:bg-[#DBEAFE]/30 ' +
                        (idx % 2 === 0 ? 'bg-[#FFFFFF]' : 'bg-[#F8FAFC]') +
                        (isExpanded ? ' bg-[#EFF6FF]/40' : '')
                      }
                    >
                      <td className="px-4 py-3 text-[#1E293B] font-medium">{idx + 1}</td>
                      <td className="px-4 py-3 font-semibold text-[#1E293B]">
                        {s.enrollment_number || s.enrollmentNumber || s.studentId}
                      </td>
                      <td className="px-4 py-3 text-[#1E293B]">{s.studentName}</td>
                      <td className="px-4 py-3 text-xs text-[#64748B]">{s.department || 'AIDS'}</td>
                      <td className="px-4 py-3 text-xs text-[#64748B] font-semibold">{s.section || '—'}</td>
                      <td className="px-4 py-3">
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-50 text-indigo-700 border border-indigo-200">
                          {s.semester || 'Semester 1'}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-[#EFF6FF] text-[#2563EB] border border-[#BFDBFE]">
                          {s.academic_year || s.academicYear || '2024-2025'}
                        </span>
                      </td>
                      <td className="px-4 py-3 font-semibold text-[#1E293B]">{s.totalMarks ?? '—'}</td>
                      <td className="px-4 py-3 font-semibold text-[#1E293B]">
                        {s.percentage !== undefined && s.percentage !== null ? `${s.percentage}%` : '—'}
                      </td>
                      <td className="px-4 py-3 text-center">
                        {subjectKeys.length > 0 ? (
                          <button
                            type="button"
                            onClick={() => toggleRow(idx)}
                            className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-xl text-xs font-semibold bg-white border border-[#E2E8F0] text-[#2563EB] hover:bg-[#EFF6FF] transition shadow-2xs cursor-pointer"
                          >
                            <BookOpen className="w-3.5 h-3.5" />
                            <span>{subjectKeys.length} Subjects</span>
                            {isExpanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                          </button>
                        ) : (
                          <span className="text-xs text-[#94A3B8]">—</span>
                        )}
                      </td>
                    </tr>

                    {/* Expandable Subject Breakdown Row */}
                    {isExpanded && subjectKeys.length > 0 && (
                      <tr className="bg-[#F8FAFC]">
                        <td colSpan={10} className="px-6 py-4 border-t border-b border-indigo-100">
                          <div className="bg-white rounded-xl border border-indigo-100 p-4 shadow-xs">
                            <div className="flex items-center justify-between mb-3">
                              <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2">
                                <Layers className="w-4 h-4 text-indigo-600" />
                                <span>Subject Marks Breakdown • {s.semester || 'Semester 1'}</span>
                              </h4>
                              <span className="text-xs text-slate-500 font-medium">
                                Student: <strong>{s.studentName}</strong> ({s.enrollment_number || s.studentId})
                              </span>
                            </div>

                            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
                              {subjectKeys.map((subj) => {
                                const totalMark = subjectMarks[subj];
                                const comp = componentMarks[subj] || {};
                                const passed = totalMark >= 40;

                                return (
                                  <div
                                    key={subj}
                                    className={`rounded-xl p-3 border ${
                                      passed ? 'bg-emerald-50/40 border-emerald-200' : 'bg-rose-50/40 border-rose-200'
                                    }`}
                                  >
                                    <div className="flex items-center justify-between gap-1 mb-1.5">
                                      <p className="text-xs font-bold text-slate-800 truncate" title={subj}>
                                        {subj}
                                      </p>
                                      <span
                                        className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
                                          passed ? 'bg-emerald-100 text-emerald-800' : 'bg-rose-100 text-rose-800'
                                        }`}
                                      >
                                        {passed ? 'PASS' : 'FAIL'}
                                      </span>
                                    </div>

                                    <div className="flex items-baseline justify-between">
                                      <span className="text-xl font-extrabold text-slate-900">{totalMark}</span>
                                      <span className="text-[11px] text-slate-500 font-medium">/ 100</span>
                                    </div>

                                    {comp.test1 !== undefined && (
                                      <div className="mt-2 pt-2 border-t border-slate-100 grid grid-cols-3 gap-1 text-[10px] text-slate-600">
                                        <div>T1: <strong className="text-slate-800">{comp.test1}</strong></div>
                                        <div>L1: <strong className="text-slate-800">{comp.lab1}</strong></div>
                                        <div>T2: <strong className="text-slate-800">{comp.test2}</strong></div>
                                        <div>L2: <strong className="text-slate-800">{comp.lab2}</strong></div>
                                        <div className="col-span-2">Comp: <strong className="text-slate-800">{comp.compre}</strong></div>
                                      </div>
                                    )}
                                  </div>
                                );
                              })}
                            </div>
                          </div>
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
