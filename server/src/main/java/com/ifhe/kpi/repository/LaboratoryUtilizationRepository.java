package com.ifhe.kpi.repository;

import com.ifhe.kpi.entity.LaboratoryUtilization;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface LaboratoryUtilizationRepository extends JpaRepository<LaboratoryUtilization, Long> {
}
