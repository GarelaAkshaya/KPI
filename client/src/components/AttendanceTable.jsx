import React from 'react';

export default function AttendanceTable({ attendance }) {
  return (
    <div className="mt-4 w-full">
      <div className="rounded-2xl border border-[#E2E8F0] bg-[#FFFFFF] overflow-hidden shadow-sm">
        <div className="max-h-80 overflow-y-auto w-full">
          <table className="min-w-full table-auto text-sm">
            <thead className="sticky top-0 bg-[#EFF6FF]">
              <tr className="text-left border-b border-[#E2E8F0]">
                <th className="px-4 py-3 text-[#1E293B] font-semibold">S.No</th>
                <th className="px-4 py-3 text-[#1E293B] font-semibold">Student ID</th>
                <th className="px-4 py-3 text-[#1E293B] font-semibold">Student Name</th>
                <th className="px-4 py-3 text-[#1E293B] font-semibold">Department</th>
                <th className="px-4 py-3 text-[#1E293B] font-semibold">Academic Year</th>
                <th className="px-4 py-3 text-[#1E293B] font-semibold">Classes</th>
                <th className="px-4 py-3 text-[#1E293B] font-semibold">Attendance</th>
              </tr>
            </thead>

            <tbody className="divide-y divide-[#E2E8F0]">
              {attendance.map((a, idx) => {
                const pct = a.attendance_percentage ?? (a.total_classes > 0 ? Math.round((a.attended_classes / a.total_classes) * 100) : 0);
                const isGood = pct >= 75;

                return (
                  <tr
                    key={a.id ?? idx}
                    className={"transition-colors hover:bg-[#DBEAFE]/40 " + (idx % 2 === 0 ? 'bg-[#FFFFFF]' : 'bg-[#F8FAFC]')}
                  >
                    <td className="px-4 py-3 text-[#1E293B]">{idx + 1}</td>
                    <td className="px-4 py-3 font-medium text-[#1E293B]">{a.student_id}</td>
                    <td className="px-4 py-3 text-[#1E293B]">{a.student_name}</td>
                    <td className="px-4 py-3 text-[#64748B]">{a.department || 'N/A'}</td>
                    <td className="px-4 py-3 text-[#64748B]">{a.academic_year || '2024-25'}</td>
                    <td className="px-4 py-3 text-[#1E293B]">
                      {a.attended_classes} / {a.total_classes}
                    </td>
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
