import React from 'react';

export default function AttendanceTable({ attendance }) {
  const subjects = Array.from(new Set(attendance.flatMap((record) => record.subjects || [])));

  return (
    <div className="mt-4 w-full">
      <div className="rounded-2xl border border-[#E2E8F0] bg-[#FFFFFF] overflow-hidden shadow-sm">
        <div className="max-h-80 overflow-y-auto w-full">
          <table className="min-w-full table-auto text-sm">
            <thead className="sticky top-0 bg-[#EFF6FF]">
              <tr className="text-left border-b border-[#E2E8F0]">
                <th className="px-4 py-3 text-[#1E293B] font-semibold">S.No</th>
                <th className="px-4 py-3 text-[#1E293B] font-semibold">Enrollment Number</th>
                <th className="px-4 py-3 text-[#1E293B] font-semibold">Student Name</th>
                {subjects.map((subject) => (
                  <th key={subject} className="px-4 py-3 text-[#1E293B] font-semibold">{subject}</th>
                ))}
                <th className="px-4 py-3 text-[#1E293B] font-semibold">Average Attendance</th>
              </tr>
            </thead>

            <tbody className="divide-y divide-[#E2E8F0]">
              {attendance.map((a, idx) => {
                const pct = a.average_attendance ?? a.attendance_percentage ?? 0;
                const isGood = pct >= 75;

                return (
                  <tr
                    key={a.id ?? idx}
                    className={"transition-colors hover:bg-[#DBEAFE]/40 " + (idx % 2 === 0 ? 'bg-[#FFFFFF]' : 'bg-[#F8FAFC]')}
                  >
                    <td className="px-4 py-3 text-[#1E293B]">{idx + 1}</td>
                    <td className="px-4 py-3 font-medium text-[#1E293B]">{a.enrollment_number || a.student_id}</td>
                    <td className="px-4 py-3 text-[#1E293B]">{a.student_name}</td>
                    {subjects.map((subject) => (
                      <td key={subject} className="px-4 py-3 text-[#1E293B]">
                        {a.subject_values?.[subject] ?? '—'}
                      </td>
                    ))}
                    <td className="px-4 py-3">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                        isGood ? 'bg-[#10B981]/10 text-[#10B981]' : 'bg-rose-100 text-rose-700'
                      }`}>
                        {pct}%
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
