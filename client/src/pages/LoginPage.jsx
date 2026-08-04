import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { GraduationCap, User, Lock, ArrowRight, ShieldCheck, Activity } from 'lucide-react';

export default function LoginPage() {
  const navigate = useNavigate();
  const [username, setUsername] = useState('admin');
  const [password, setPassword] = useState('••••••••');

  const handleSubmit = (e) => {
    e.preventDefault();
    // Dummy login navigation as specified
    navigate('/home');
  };

  return (
    <div className="relative min-h-screen w-full bg-[#F8FAFC] flex items-center justify-center p-4 sm:p-6 overflow-hidden">
      {/* Background Decorative Gradient Blobs */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] rounded-full bg-gradient-to-tr from-[#2563EB]/15 via-[#DBEAFE]/30 to-[#EFF6FF]/40 blur-3xl pointer-events-none animate-pulse-glow" />
      <div className="absolute bottom-10 right-10 w-[350px] h-[350px] rounded-full bg-[#2563EB]/10 blur-3xl pointer-events-none" />
      <div className="absolute top-10 left-10 w-[300px] h-[300px] rounded-full bg-[#DBEAFE]/30 blur-3xl pointer-events-none" />

      {/* Main Centered Login Card */}
      <div className="relative w-full max-w-md">
        {/* Outer Glow Border Effect */}
        <div className="absolute -inset-0.5 bg-gradient-to-r from-[#2563EB] via-[#3B82F6] to-[#1D4ED8] rounded-3xl blur opacity-20 group-hover:opacity-100 transition duration-1000 group-hover:duration-200" />

        <div className="relative bg-[#FFFFFF] backdrop-blur-xl border border-[#E2E8F0] rounded-3xl p-8 sm:p-10 shadow-xl shadow-blue-900/5">
          
          {/* Logo Badge Header */}
          <div className="flex flex-col items-center text-center mb-8">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-[#2563EB] to-[#1D4ED8] p-1 shadow-lg shadow-blue-500/20 mb-4 transform hover:scale-105 transition-transform duration-300">
              <div className="w-full h-full bg-[#EFF6FF] rounded-[12px] flex items-center justify-center">
                <GraduationCap className="w-9 h-9 text-[#2563EB]" />
              </div>
            </div>

            <h1 className="text-3xl font-extrabold tracking-tight text-[#1E293B]">
              IFHE KPI
            </h1>
            <p className="mt-2 text-sm font-medium text-[#64748B]">
              Institutional KPI Monitoring System
            </p>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Username Field */}
            <div className="space-y-2">
              <label className="block text-xs font-bold uppercase tracking-wider text-[#1E293B]">
                Username
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-[#64748B]">
                  <User className="w-5 h-5" />
                </div>
                <input
                  type="text"
                  required
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="Enter administrator username"
                  className="w-full pl-11 pr-4 py-3.5 bg-[#F8FAFC] border border-[#E2E8F0] rounded-2xl text-[#1E293B] placeholder-[#64748B] focus:outline-none focus:ring-2 focus:ring-[#2563EB]/40 focus:border-[#2563EB] focus:bg-[#FFFFFF] transition-all duration-200 text-sm font-medium"
                />
              </div>
            </div>

            {/* Password Field */}
            <div className="space-y-2">
              <label className="block text-xs font-bold uppercase tracking-wider text-[#1E293B]">
                Password
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-[#64748B]">
                  <Lock className="w-5 h-5" />
                </div>
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter password"
                  className="w-full pl-11 pr-4 py-3.5 bg-[#F8FAFC] border border-[#E2E8F0] rounded-2xl text-[#1E293B] placeholder-[#64748B] focus:outline-none focus:ring-2 focus:ring-[#2563EB]/40 focus:border-[#2563EB] focus:bg-[#FFFFFF] transition-all duration-200 text-sm font-medium"
                />
              </div>
            </div>

            {/* Security Note */}
            <div className="flex items-center justify-between text-xs text-[#64748B] px-1">
              <div className="flex items-center gap-1.5">
                <ShieldCheck className="w-4 h-4 text-[#10B981]" />
                <span>Authorized Personnel Portal</span>
              </div>
              <div className="flex items-center gap-1 text-[#2563EB]">
                <Activity className="w-3.5 h-3.5" />
                <span>v2.4 Active</span>
              </div>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              className="w-full group relative flex items-center justify-center gap-2 py-4 px-6 rounded-2xl text-white font-bold text-base bg-[#2563EB] hover:bg-[#3B82F6] shadow-lg shadow-blue-500/20 active:bg-[#1D4ED8] transition-all duration-300 active:scale-[0.99]"
            >
              <span>Login to Portal</span>
              <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform duration-200" />
            </button>
          </form>

          {/* Footer branding */}
          <div className="mt-8 pt-6 border-t border-[#E2E8F0] text-center">
            <p className="text-xs text-[#64748B]">
              ICFAI Foundation for Higher Education (IFHE)
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
