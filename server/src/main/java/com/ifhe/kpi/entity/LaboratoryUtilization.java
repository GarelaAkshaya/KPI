package com.ifhe.kpi.entity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

import java.time.LocalDate;

@Entity
@Table(name = "laboratory_utilization")
public class LaboratoryUtilization {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "laboratory_name", nullable = false)
    private String laboratoryName;

    @Column(name = "department", nullable = false)
    private String department;

    @Column(name = "academic_year", nullable = false)
    private String academicYear;

    @Column(name = "session_date", nullable = false)
    private LocalDate sessionDate;

    @Column(name = "time_slot")
    private String timeSlot;

    @Column(name = "capacity")
    private Integer capacity;

    @Column(name = "students_present")
    private Integer studentsPresent;

    public LaboratoryUtilization() {
    }

    public LaboratoryUtilization(String laboratoryName, String department, String academicYear,
                                 LocalDate sessionDate, String timeSlot, Integer capacity,
                                 Integer studentsPresent) {
        this.laboratoryName = laboratoryName;
        this.department = department;
        this.academicYear = academicYear;
        this.sessionDate = sessionDate;
        this.timeSlot = timeSlot;
        this.capacity = capacity;
        this.studentsPresent = studentsPresent;
    }

    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public String getLaboratoryName() {
        return laboratoryName;
    }

    public void setLaboratoryName(String laboratoryName) {
        this.laboratoryName = laboratoryName;
    }

    public String getDepartment() {
        return department;
    }

    public void setDepartment(String department) {
        this.department = department;
    }

    public String getAcademicYear() {
        return academicYear;
    }

    public void setAcademicYear(String academicYear) {
        this.academicYear = academicYear;
    }

    public LocalDate getSessionDate() {
        return sessionDate;
    }

    public void setSessionDate(LocalDate sessionDate) {
        this.sessionDate = sessionDate;
    }

    public String getTimeSlot() {
        return timeSlot;
    }

    public void setTimeSlot(String timeSlot) {
        this.timeSlot = timeSlot;
    }

    public Integer getCapacity() {
        return capacity;
    }

    public void setCapacity(Integer capacity) {
        this.capacity = capacity;
    }

    public Integer getStudentsPresent() {
        return studentsPresent;
    }

    public void setStudentsPresent(Integer studentsPresent) {
        this.studentsPresent = studentsPresent;
    }
}
