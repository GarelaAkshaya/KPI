import React, { useState, useEffect } from 'react';
import Navbar from '../components/Navbar';
import { ChevronRight, Users } from 'lucide-react';

export default function FacultyDataPage() {
  const [facultyData, setFacultyData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedFaculty, setSelectedFaculty] = useState(null);
  const [showModal, setShowModal] = useState(false);

  useEffect(() => {
    async function fetchFacultyData() {
      try {
        setLoading(true);
        setError(null);
        const response = await fetch('http://localhost:5000/api/faculty');
        
        if (!response.ok) {
          throw new Error(`Failed to fetch faculty data: ${response.statusText}`);
        }
        
        const data = await response.json();
        setFacultyData(data);
      } catch (err) {
        setError(err.message || 'Failed to load faculty data');
        console.error('Faculty data fetch error:', err);
      } finally {
        setLoading(false);
      }
    }

    fetchFacultyData();
  }, []);

  const handleViewMore = (faculty) => {
    setSelectedFaculty(faculty);
    setShowModal(true);
  };

  const handleCloseModal = () => {
    setShowModal(false);
    setSelectedFaculty(null);
  };

  const getPlaceholderImage = (name) => {
    const initials = name
      .split(' ')
      .map((n) => n[0])
      .join('')
      .toUpperCase()
      .slice(0, 2);
    
    const colors = [
      '#2563EB', '#9333EA', '#DC2626', '#059669', '#F59E0B', '#06B6D4',
      '#7C3AED', '#DB2777', '#0891B2', '#7C2D12'
    ];
    const colorIndex = name.charCodeAt(0) % colors.length;
    const bgColor = colors[colorIndex];
    
    return {
      initials,
      bgColor,
      isPlaceholder: true,
    };
  };

  return (
    <div className="min-h-screen bg-white text-[#1E293B] flex flex-col">
      <Navbar />

      <main className="flex-1 w-full">
        {/* Department Header Section */}
        <section className="bg-white border-b border-[#E2E8F0]">
          <div className="max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12">
            {/* Breadcrumb */}
            <p className="text-[#64748B] text-sm mb-4">
              ICFAI Tech School, Hyderabad / Computer Science & Engineering
            </p>

            {/* Main Header with Image and Content */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-stretch">
              {/* Left: Department Image - Narrow and Tall */}
              <div className="lg:col-span-4 rounded-2xl overflow-hidden shadow-xl">
                <img
                  src="https://www.ifheindia.org/IcfaiTechassets/img/inner-banners/faculty-computer-science-engineering.jpg"
                  alt="Computer Science & Engineering Department"
                  className="w-full h-96 lg:h-full object-cover hover:scale-105 transition-transform duration-300"
                />
              </div>

              {/* Right: Department Info - Takes more space */}
              <div className="lg:col-span-8 flex flex-col justify-center">
                <h1 className="text-5xl lg:text-6xl font-extrabold text-[#1E293B] mb-8 tracking-tight leading-tight">
                  Computer Science & Engineering
                </h1>

                <div className="space-y-4 text-[#475569] text-base lg:text-lg leading-relaxed">
                  <p className="flex gap-4">
                    <span className="text-[#2563EB] font-bold text-xl flex-shrink-0">•</span>
                    <span>The B.Tech Programme is approved by AICTE. We are living in the midst of an extraordinary transformation of the way we live, powered by computers.</span>
                  </p>
                  <p className="flex gap-4">
                    <span className="text-[#2563EB] font-bold text-xl flex-shrink-0">•</span>
                    <span>This transformation has impacted every aspect of society – from communication, manufacturing, transportation, medical care, governance, education, entertainment, and social interactions.</span>
                  </p>
                  <p className="flex gap-4">
                    <span className="text-[#2563EB] font-bold text-xl flex-shrink-0">•</span>
                    <span>Our curriculum prepares the student by providing a rigorous foundation in the discipline, exposure to emerging areas that are gaining wide application and relevance such as Artificial Intelligence, Data Analytics and Information Security through elective offerings, mastery of the concepts through projects and assignments, experience in real-world applications and practices through industry internships, and exposure to ongoing research problems and the methodology of research and innovation.</span>
                  </p>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Faculty Directory Section */}
        <div className="max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12">
          {/* Page Header */}
          <div className="mb-8">
            <div className="flex items-center gap-3 mb-2">
              <Users className="w-8 h-8 text-[#2563EB]" />
              <h2 className="text-3xl sm:text-4xl font-extrabold text-[#1E293B] tracking-tight">
                Faculty Directory
              </h2>
            </div>
            <p className="text-[#64748B] text-base leading-relaxed max-w-2xl">
              Browse and explore comprehensive faculty profiles and qualifications across the institution.
            </p>
          </div>

        {/* Loading State */}
        {loading && (
          <div className="flex flex-col items-center justify-center py-16 gap-3">
            <div className="w-12 h-12 border-4 border-[#E2E8F0] border-t-[#2563EB] rounded-full animate-spin" />
            <p className="text-[#64748B] font-medium">Loading faculty records...</p>
          </div>
        )}

        {/* Error State */}
        {error && !loading && (
          <div className="rounded-2xl bg-[#FEE2E2] border border-[#FECACA] p-6 text-center">
            <p className="text-[#DC2626] font-semibold mb-2">Unable to Load Faculty Data</p>
            <p className="text-[#991B1B] text-sm">{error}</p>
            <button
              onClick={() => window.location.reload()}
              className="mt-4 px-4 py-2 bg-[#DC2626] text-white rounded-lg hover:bg-[#B91C1C] transition-colors"
            >
              Try Again
            </button>
          </div>
        )}

        {/* Empty State */}
        {!loading && !error && facultyData.length === 0 && (
          <div className="rounded-2xl bg-white border border-[#E2E8F0] p-12 text-center">
            <Users className="w-12 h-12 text-[#CBD5E1] mx-auto mb-3" />
            <p className="text-[#64748B] font-semibold">No faculty records found</p>
            <p className="text-sm text-[#94A3B8] mt-1">
              Faculty data will appear here once records are added to the system.
            </p>
          </div>
        )}

        {/* Faculty Cards Grid */}
        {!loading && !error && facultyData.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {facultyData.map((faculty) => {
              const placeholder = getPlaceholderImage(faculty.name);
              return (
                <div
                  key={faculty.id}
                  className="bg-white rounded-xl border border-[#E2E8F0] overflow-hidden shadow-sm hover:shadow-md transition-shadow duration-300"
                >
                  {/* Top Border (Yellow/Orange) */}
                  <div className="h-1 bg-gradient-to-r from-[#F59E0B] to-[#F97316]" />

                  {/* Faculty Photo Section */}
                  <div className="p-6 pb-4">
                    {faculty.image_path ? (
                      <img
                        src={faculty.image_path}
                        alt={faculty.name}
                        className="w-full h-40 object-cover rounded-lg mb-4"
                      />
                    ) : (
                      <div
                        className="w-full h-40 rounded-lg mb-4 flex items-center justify-center text-white font-bold text-3xl"
                        style={{ backgroundColor: placeholder.bgColor }}
                      >
                        {placeholder.initials}
                      </div>
                    )}
                  </div>

                  {/* Faculty Info */}
                  <div className="px-6 pb-6">
                    <h3 className="text-lg font-bold text-[#1E293B] mb-2 line-clamp-2">
                      {faculty.name}
                    </h3>

                    <p className="text-sm text-[#64748B] font-medium mb-1 line-clamp-2">
                      {faculty.designation}
                    </p>

                    <p className="text-sm text-[#94A3B8] mb-4">
                      {faculty.qualification}
                    </p>

                    <button
                      onClick={() => handleViewMore(faculty)}
                      className="w-full inline-flex items-center justify-center gap-2 px-4 py-2.5 bg-[#DC2626] text-white font-semibold text-sm rounded-lg hover:bg-[#B91C1C] transition-colors duration-200"
                    >
                      View More
                      <ChevronRight className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
        </div>
      </main>

      {/* Faculty Detail Modal */}
      {showModal && selectedFaculty && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full p-6 max-h-[90vh] overflow-y-auto">
            {/* Close Button */}
            <button
              onClick={handleCloseModal}
              className="float-right text-[#64748B] hover:text-[#1E293B] text-2xl leading-none"
            >
              ×
            </button>

            {/* Faculty Photo */}
            {selectedFaculty.image_path ? (
              <img
                src={selectedFaculty.image_path}
                alt={selectedFaculty.name}
                className="w-full h-48 object-cover rounded-lg mb-4"
              />
            ) : (
              <div
                className="w-full h-48 rounded-lg mb-4 flex items-center justify-center text-white font-bold text-4xl"
                style={{ backgroundColor: getPlaceholderImage(selectedFaculty.name).bgColor }}
              >
                {getPlaceholderImage(selectedFaculty.name).initials}
              </div>
            )}

            {/* Faculty Details */}
            <div className="space-y-4">
              <div>
                <h2 className="text-2xl font-bold text-[#1E293B] mb-1">
                  {selectedFaculty.name}
                </h2>
                <p className="text-[#F59E0B] font-semibold text-sm">
                  Faculty Member
                </p>
              </div>

              <div className="border-t border-[#E2E8F0] pt-4 space-y-3">
                <div>
                  <p className="text-xs uppercase tracking-wider text-[#94A3B8] font-semibold mb-1">
                    Designation
                  </p>
                  <p className="text-[#1E293B] font-medium">
                    {selectedFaculty.designation || 'N/A'}
                  </p>
                </div>

                <div>
                  <p className="text-xs uppercase tracking-wider text-[#94A3B8] font-semibold mb-1">
                    Qualification
                  </p>
                  <p className="text-[#1E293B] font-medium">
                    {selectedFaculty.qualification || 'N/A'}
                  </p>
                </div>

                <div>
                  <p className="text-xs uppercase tracking-wider text-[#94A3B8] font-semibold mb-1">
                    Department
                  </p>
                  <p className="text-[#1E293B] font-medium">
                    {selectedFaculty.department || 'N/A'}
                  </p>
                </div>

                {selectedFaculty.email && (
                  <div>
                    <p className="text-xs uppercase tracking-wider text-[#94A3B8] font-semibold mb-1">
                      Email
                    </p>
                    <p className="text-[#1E293B] font-medium break-all">
                      {selectedFaculty.email}
                    </p>
                  </div>
                )}
              </div>
            </div>

            <button
              onClick={handleCloseModal}
              className="w-full mt-6 px-4 py-2.5 bg-[#E2E8F0] text-[#1E293B] font-semibold rounded-lg hover:bg-[#CBD5E1] transition-colors"
            >
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
