const path = require('path');
const { DatabaseSync } = require('node:sqlite');

const dbPath = path.join(__dirname, 'student-data.db');
const db = new DatabaseSync(dbPath);

function initDb() {
  db.exec(`
    CREATE TABLE IF NOT EXISTS student_uploads (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      studentId TEXT NOT NULL,
      studentName TEXT NOT NULL,
      totalMarks INTEGER NOT NULL,
      percentage REAL NOT NULL,
      createdAt TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
  `);

  db.exec(`
    CREATE TABLE IF NOT EXISTS laboratory_utilization (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      laboratory_name TEXT NOT NULL,
      department TEXT NOT NULL,
      academic_year TEXT NOT NULL,
      session_date TEXT NOT NULL,
      time_slot TEXT,
      capacity INTEGER,
      students_present INTEGER
    );
  `);
}

function parsePercentageValue(value) {
  if (value === undefined || value === null) return null;

  const text = String(value).trim();
  if (text === '') return null;

  const hasPercentSymbol = text.includes('%');
  const numericText = text.replace(/[%\s]/g, '');
  const parsed = Number(numericText);

  if (!Number.isFinite(parsed)) return null;

  if (hasPercentSymbol) {
    return parsed;
  }

  if (parsed <= 1) {
    return parsed * 100;
  }

  return parsed;
}

function normalizeStudentRows(rows) {
  return rows.map((row) => {
    const studentId = row['Student ID'] ?? row['student id'] ?? '';
    const studentName = row['Student Name'] ?? row['student name'] ?? '';
    const totalMarksValue = row['Total Marks (Out of 600)'] ?? row['total marks (out of 600)'] ?? 0;
    const percentageValue = row['Percentage'] ?? row['percentage'] ?? row['Percentage (%)'] ?? row['percentage (%)'] ?? row['Percentage %'] ?? row['percentage %'];

    const totalMarks = Number(totalMarksValue) || 0;

    let percentage = parsePercentageValue(percentageValue);
    if (percentage === null) {
      percentage = (totalMarks / 600) * 100;
    }

    if (!Number.isFinite(percentage)) percentage = 0;

    // Normalize to two decimals
    percentage = Math.round(percentage * 100) / 100;

    return {
      studentId: String(studentId).trim(),
      studentName: String(studentName).trim(),
      totalMarks: Math.round(totalMarks),
      percentage,
    };
  });
}

function saveStudentRecords(records) {
  db.exec('BEGIN');
  try {
    // Use positional parameters to avoid named-placeholder binding issues
    const insert = db.prepare(
      'INSERT INTO student_uploads (studentId, studentName, totalMarks, percentage) VALUES (?, ?, ?, ?)'
    );

    for (const rawItem of records) {
      const studentId = rawItem.studentId ? String(rawItem.studentId).trim() : '';
      const studentName = rawItem.studentName ? String(rawItem.studentName).trim() : '';
      const totalMarks = Number.isFinite(Number(rawItem.totalMarks)) ? Math.round(Number(rawItem.totalMarks)) : 0;
      const percentage = Number.isFinite(Number(rawItem.percentage)) ? Number(rawItem.percentage) : 0;

      // Log each row being inserted for debugging (kept minimal)
      // console.log('Inserting student:', { studentId, studentName, totalMarks, percentage });

      insert.run(studentId, studentName, totalMarks, percentage);
    }

    db.exec('COMMIT');
    return records.length;
  } catch (error) {
    db.exec('ROLLBACK');
    throw error;
  }
}

function getStudentRecords() {
  return db.prepare('SELECT * FROM student_uploads ORDER BY id DESC').all();
}

function clearStudentRecords() {
  db.prepare('DELETE FROM student_uploads').run();
}

initDb();

module.exports = {
  initDb,
  normalizeStudentRows,
  saveStudentRecords,
  getStudentRecords,
  clearStudentRecords,
};
