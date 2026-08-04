import React from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { ShieldCheck, BarChart3, Home, LogOut, GraduationCap } from 'lucide-react';

export default function Navbar() {
  const location = useLocation();
  const navigate = useNavigate();

  const handleLogout = () => {
    navigate('/');
  };

  return (
    <header className="sticky top-0 z-40 bg-[#FFFFFF]/90 backdrop-blur-md border-b border-[#E2E8F0] shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-20">
          {/* Brand Logo & Title */}
          <Link to="/home" className="flex items-center gap-3.5 group">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-tr from-[#2563EB] to-[#1D4ED8] p-0.5 shadow-md shadow-blue-500/20 group-hover:scale-105 transition-transform duration-300">
              <div className="w-full h-full bg-[#EFF6FF] rounded-[10px] flex items-center justify-center">
                <GraduationCap className="w-6 h-6 text-[#2563EB] group-hover:text-[#1D4ED8] transition-colors" />
              </div>
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-extrabold text-xl tracking-wider text-[#1E293B]">
                  IFHE KPI
                </span>
                <span className="text-[10px] uppercase font-bold tracking-widest px-2 py-0.5 rounded-full bg-[#DBEAFE] text-[#2563EB] border border-[#2563EB]/20">
                  Portal
                </span>
              </div>
              <p className="text-xs text-[#64748B] font-medium hidden sm:block">
                Institutional KPI Monitoring System
              </p>
            </div>
          </Link>

          {/* Navigation Links & Admin Controls */}
          <div className="flex items-center gap-3 sm:gap-6">
            <nav className="flex items-center bg-[#F8FAFC] p-1.5 rounded-xl border border-[#E2E8F0]">
              <Link
                to="/home"
                className={`flex items-center gap-2 px-3.5 py-2 rounded-lg text-sm font-semibold transition-all duration-200 ${
                  location.pathname === '/home'
                    ? 'bg-[#2563EB] text-white shadow-md shadow-blue-500/20'
                    : 'text-[#64748B] hover:text-[#1E293B] hover:bg-[#EFF6FF]'
                }`}
              >
                <Home className="w-4 h-4" />
                <span>Home</span>
              </Link>

              <Link
                to="/dashboard"
                className={`flex items-center gap-2 px-3.5 py-2 rounded-lg text-sm font-semibold transition-all duration-200 ${
                  location.pathname === '/dashboard'
                    ? 'bg-[#2563EB] text-white shadow-md shadow-blue-500/20'
                    : 'text-[#64748B] hover:text-[#1E293B] hover:bg-[#EFF6FF]'
                }`}
              >
                <BarChart3 className="w-4 h-4" />
                <span>KPI Dashboard</span>
              </Link>
            </nav>

            {/* Admin Badge & Logout */}
            <div className="flex items-center gap-3 pl-3 border-l border-[#E2E8F0]">
              <div className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[#EFF6FF] border border-[#DBEAFE]">
                <ShieldCheck className="w-4 h-4 text-[#10B981]" />
                <span className="text-xs font-semibold text-[#1E293B]">Administrator</span>
              </div>

              <button
                onClick={handleLogout}
                title="Logout"
                className="flex items-center gap-1.5 px-3 py-2 rounded-xl text-[#64748B] hover:text-red-600 hover:bg-red-50 border border-transparent hover:border-red-200 transition-all duration-200 text-sm font-medium"
              >
                <LogOut className="w-4 h-4" />
                <span className="hidden sm:inline">Logout</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
