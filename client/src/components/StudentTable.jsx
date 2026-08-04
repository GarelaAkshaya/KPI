import React from 'react';

export default function StudentTable({ students }) {
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
                <th className="px-4 py-3 text-[#1E293B] font-semibold">Total Marks</th>
                <th className="px-4 py-3 text-[#1E293B] font-semibold">Percentage</th>
              </tr>
            </thead>

            <tbody className="divide-y divide-[#E2E8F0]">
              {students.map((s, idx) => (
                <tr
                  key={s.id ?? idx}
                  className={"transition-colors hover:bg-[#DBEAFE]/40 " + (idx % 2 === 0 ? 'bg-[#FFFFFF]' : 'bg-[#F8FAFC]')}
                >
                  <td className="px-4 py-3 text-[#1E293B]">{idx + 1}</td>
                  <td className="px-4 py-3 text-[#1E293B]">{s.studentId}</td>
                  <td className="px-4 py-3 text-[#1E293B]">{s.studentName}</td>
                  <td className="px-4 py-3 text-[#1E293B]">{s.totalMarks}</td>
                  <td className="px-4 py-3 text-[#1E293B]">{s.percentage}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
