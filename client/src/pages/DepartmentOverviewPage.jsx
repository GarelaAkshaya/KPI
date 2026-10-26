import React, { useEffect, useState } from 'react';
import Navbar from '../components/Navbar';
import { Building2, Loader2, AlertCircle, Users, UserCheck } from 'lucide-react';
import { API_BASE_URL, apiFetch } from '../api';

export default function DepartmentOverviewPage() {
  const [departments, setDepartments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    async function fetchDepartmentOverview() {
      try {
        setLoading(true);
        setError('');

        const response = await apiFetch(`${API_BASE_URL}/api/departments/overview`);
        if (!response.ok) {
          throw new Error(`Failed to load department overview: ${response.statusText}`);
        }

        const data = await response.json();
        setDepartments(Array.isArray(data) ? data : []);
      } catch (err) {
        setError(err.message || 'Unable to load department overview data.');
      } finally {
        setLoading(false);
      }
    }

    fetchDepartmentOverview();
  }, []);

  return (
    <div className="min-h-screen bg-[#F8FAFC] text-[#1E293B] flex flex-col">
      <Navbar />

      <main className="max-w-6xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12">
        <header className="mb-8">
          <div className="inline-flex items-center gap-2 rounded-full border border-[#DBEAFE] bg-[#EFF6FF] px-3 py-1.5 text-xs font-semibold uppercase tracking-[0.12em] text-[#2563EB]">
            <Building2 className="w-3.5 h-3.5" />
            Department Module
          </div>
          <h1 className="mt-4 text-3xl sm:text-4xl font-extrabold tracking-tight text-[#1E293B]">
            Department Overview
          </h1>
          <p className="mt-2 max-w-2xl text-sm sm:text-base text-[#64748B]">
            Live department composition across the active institutional database.
          </p>
        </header>

        {loading && (
          <div className="flex flex-col items-center justify-center rounded-2xl border border-[#E2E8F0] bg-white py-16 shadow-sm">
            <Loader2 className="h-10 w-10 animate-spin text-[#2563EB]" />
            <p className="mt-4 text-sm font-medium text-[#475569]">Loading department data...</p>
          </div>
        )}

        {!loading && error && (
          <div className="rounded-2xl border border-[#FECACA] bg-[#FEF2F2] p-6 text-center shadow-sm">
            <div className="flex items-center justify-center gap-2 text-[#B91C1C] font-semibold">
              <AlertCircle className="h-5 w-5" />
              Unable to Load Department Overview
            </div>
            <p className="mt-2 text-sm text-[#7F1D1D]">{error}</p>
          </div>
        )}

        {!loading && !error && departments.length === 0 && (
          <div className="rounded-2xl border border-[#E2E8F0] bg-white p-10 text-center shadow-sm">
            <Building2 className="mx-auto h-12 w-12 text-[#94A3B8]" />
            <p className="mt-3 text-lg font-semibold text-[#334155]">No department records found</p>
            <p className="mt-1 text-sm text-[#64748B]">Department data will appear here when records are available.</p>
          </div>
        )}

        {!loading && !error && departments.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {departments.map((department) => (
              <div
                key={department.name}
                className="rounded-3xl border border-[#E2E8F0] bg-white p-6 shadow-sm hover:shadow-md transition-shadow duration-200"
              >
                <div className="flex items-center justify-between gap-4">
                  <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-[#EFF6FF] text-[#2563EB]">
                    <Building2 className="h-6 w-6" />
                  </div>
                  <span className="rounded-full border border-[#DBEAFE] bg-[#EFF6FF] px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.12em] text-[#2563EB]">
                    Department
                  </span>
                </div>

                <h2 className="mt-5 text-2xl font-extrabold tracking-tight text-[#1E293B]">
                  {department.name}
                </h2>

                <div className="mt-6 grid grid-cols-2 gap-4">
                  <div className="rounded-2xl bg-[#F8FAFC] border border-[#E2E8F0] p-4">
                    <div className="flex items-center gap-2 text-[#64748B] text-xs font-semibold uppercase tracking-[0.08em]">
                      <Users className="h-4 w-4 text-[#2563EB]" />
                      Students
                    </div>
                    <p className="mt-3 text-3xl font-extrabold text-[#0F172A]">
                      {department.studentCount ?? 0}
                    </p>
                  </div>

                  <div className="rounded-2xl bg-[#F8FAFC] border border-[#E2E8F0] p-4">
                    <div className="flex items-center gap-2 text-[#64748B] text-xs font-semibold uppercase tracking-[0.08em]">
                      <UserCheck className="h-4 w-4 text-[#10B981]" />
                      Faculty
                    </div>
                    <p className="mt-3 text-3xl font-extrabold text-[#0F172A]">
                      {department.facultyCount ?? 0}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
