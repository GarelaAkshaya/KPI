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
    <div className="relative min-h-screen w-full bg-slate-950 flex items-center justify-center p-4 sm:p-6 overflow-hidden">
      {/* Background Decorative Gradient Blobs */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] rounded-full bg-gradient-to-tr from-indigo-600/30 via-purple-600/20 to-pink-500/30 blur-3xl pointer-events-none animate-pulse-glow" />
      <div className="absolute bottom-10 right-10 w-[350px] h-[350px] rounded-full bg-blue-600/20 blur-3xl pointer-events-none" />
      <div className="absolute top-10 left-10 w-[300px] h-[300px] rounded-full bg-purple-600/20 blur-3xl pointer-events-none" />

      {/* Main Centered Login Card */}
      <div className="relative w-full max-w-md">
        {/* Outer Glow Border Effect */}
        <div className="absolute -inset-0.5 bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 rounded-3xl blur opacity-30 group-hover:opacity-100 transition duration-1000 group-hover:duration-200" />

        <div className="relative bg-slate-900/90 backdrop-blur-xl border border-slate-800 rounded-3xl p-8 sm:p-10 shadow-2xl shadow-slate-950">
          
          {/* Logo Badge Header */}
          <div className="flex flex-col items-center text-center mb-8">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-indigo-600 via-purple-600 to-pink-500 p-1 shadow-xl shadow-indigo-500/25 mb-4 transform hover:scale-105 transition-transform duration-300">
              <div className="w-full h-full bg-slate-950 rounded-[12px] flex items-center justify-center">
                <GraduationCap className="w-9 h-9 text-indigo-400" />
              </div>
            </div>

            <h1 className="text-3xl font-extrabold tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-white via-slate-100 to-indigo-200">
              IFHE KPI
            </h1>
            <p className="mt-2 text-sm font-medium text-slate-400">
              Institutional KPI Monitoring System
            </p>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Username Field */}
            <div className="space-y-2">
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-300">
                Username
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                  <User className="w-5 h-5" />
                </div>
                <input
                  type="text"
                  required
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="Enter administrator username"
                  className="w-full pl-11 pr-4 py-3.5 bg-slate-950/70 border border-slate-800 rounded-2xl text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500 transition-all duration-200 text-sm font-medium"
                />
              </div>
            </div>

            {/* Password Field */}
            <div className="space-y-2">
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-300">
                Password
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                  <Lock className="w-5 h-5" />
                </div>
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter password"
                  className="w-full pl-11 pr-4 py-3.5 bg-slate-950/70 border border-slate-800 rounded-2xl text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500 transition-all duration-200 text-sm font-medium"
                />
              </div>
            </div>

            {/* Security Note */}
            <div className="flex items-center justify-between text-xs text-slate-400 px-1">
              <div className="flex items-center gap-1.5">
                <ShieldCheck className="w-4 h-4 text-emerald-400" />
                <span>Authorized Personnel Portal</span>
              </div>
              <div className="flex items-center gap-1 text-indigo-400">
                <Activity className="w-3.5 h-3.5" />
                <span>v2.4 Active</span>
              </div>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              className="w-full group relative flex items-center justify-center gap-2 py-4 px-6 rounded-2xl text-white font-bold text-base bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 hover:from-indigo-500 hover:via-purple-500 hover:to-pink-500 shadow-xl shadow-indigo-500/30 hover:shadow-indigo-500/50 transition-all duration-300 active:scale-[0.99]"
            >
              <span>Login to Portal</span>
              <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform duration-200" />
            </button>
          </form>

          {/* Footer branding */}
          <div className="mt-8 pt-6 border-t border-slate-800/80 text-center">
            <p className="text-xs text-slate-400">
              ICFAI Foundation for Higher Education (IFHE)
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
