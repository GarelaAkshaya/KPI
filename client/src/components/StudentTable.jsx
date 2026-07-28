import React from 'react';

export default function StudentTable({ students }) {
  return (
    <div className="mt-4 w-full">
      <div className="rounded-2xl border border-slate-800 bg-slate-900/80 overflow-hidden">
        <div className="max-h-80 overflow-y-auto w-full">
          <table className="min-w-full table-auto text-sm">
            <thead className="sticky top-0 bg-slate-900/90">
              <tr className="text-left">
                <th className="px-4 py-3 text-slate-300 font-semibold">S.No</th>
                <th className="px-4 py-3 text-slate-300 font-semibold">Student ID</th>
                <th className="px-4 py-3 text-slate-300 font-semibold">Student Name</th>
                <th className="px-4 py-3 text-slate-300 font-semibold">Total Marks</th>
                <th className="px-4 py-3 text-slate-300 font-semibold">Percentage</th>
              </tr>
            </thead>

            <tbody className="divide-y divide-slate-800">
              {students.map((s, idx) => (
                <tr
                  key={s.id ?? idx}
                  className={"transition-colors hover:bg-slate-800 " + (idx % 2 === 0 ? 'bg-slate-950/60' : 'bg-slate-900/60')}
                >
                  <td className="px-4 py-3 text-slate-200">{idx + 1}</td>
                  <td className="px-4 py-3 text-slate-200">{s.studentId}</td>
                  <td className="px-4 py-3 text-slate-200">{s.studentName}</td>
                  <td className="px-4 py-3 text-slate-200">{s.totalMarks}</td>
                  <td className="px-4 py-3 text-slate-200">{s.percentage}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
