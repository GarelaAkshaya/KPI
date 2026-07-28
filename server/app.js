const express = require('express');
const cors = require('cors');
const multer = require('multer');
const xlsx = require('xlsx');
const sqlite3 = require('sqlite3').verbose();
const path = require('path');

const app = express();
const PORT = process.env.PORT || 5000;

app.use(cors());
app.use(express.json());

// Initialize SQLite database
const dbPath = path.join(__dirname, 'database.sqlite');
const db = new sqlite3.Database(dbPath, (err) => {
  if (err) {
    console.error('Error opening database:', err.message);
  } else {
    console.log('Connected to SQLite database.');
    // Create students table automatically if it does not exist
    db.run(
      `CREATE TABLE IF NOT EXISTS students (
        student_id TEXT PRIMARY KEY,
        student_name TEXT NOT NULL,
        total_marks INTEGER,
        percentage REAL
      )`,
      (err) => {
        if (err) {
          console.error('Error creating students table:', err.message);
        } else {
          console.log('Students table is ready.');
        }
      }
    );
  }
});

// Configure Multer for memory storage & file extension validation
const storage = multer.memoryStorage();
const upload = multer({
  storage: storage,
  fileFilter: (req, file, cb) => {
    const ext = path.extname(file.originalname).toLowerCase();
    if (ext === '.xlsx' || ext === '.xls') {
      cb(null, true);
    } else {
      cb(new Error('Invalid file format. Please upload an Excel file (.xlsx or .xls).'));
    }
  },
  limits: { fileSize: 15 * 1024 * 1024 }
});

// Helper for parsing numeric fields cleanly
const parseNum = (val) => {
  if (val === undefined || val === null || val === '') return 0;
  if (typeof val === 'number') return val;
  const cleaned = String(val).replace(/[%,\s]/g, '');
  const num = parseFloat(cleaned);
  return isNaN(num) ? 0 : num;
};

// GET /api/students - Fetch total count and all student records
app.get('/api/students', (req, res) => {
  const countSql = `SELECT COUNT(*) AS total FROM students`;
  const listSql = `SELECT student_id, student_name, total_marks, percentage FROM students ORDER BY student_id ASC`;

  db.get(countSql, [], (err, countRow) => {
    if (err) {
      return res.status(500).json({ success: false, message: 'Database error counting students: ' + err.message });
    }
    db.all(listSql, [], (err, rows) => {
      if (err) {
        return res.status(500).json({ success: false, message: 'Database error fetching students: ' + err.message });
      }
      res.json({
        success: true,
        total: countRow ? countRow.total : 0,
        students: rows || []
      });
    });
  });
});

// POST /api/students/upload - Read Excel file and insert/update every record into database
app.post('/api/students/upload', (req, res) => {
  upload.single('file')(req, res, (err) => {
    if (err) {
      return res.status(400).json({ success: false, message: err.message || 'File upload error.' });
    }
    if (!req.file) {
      return res.status(400).json({ success: false, message: 'No file uploaded. Please choose an Excel file.' });
    }

    try {
      // Read Excel workbook from buffer
      const workbook = xlsx.read(req.file.buffer, { type: 'buffer' });
      const firstSheetName = workbook.SheetNames[0];
      if (!firstSheetName) {
        return res.status(400).json({ success: false, message: 'The uploaded Excel file has no worksheets.' });
      }

      const worksheet = workbook.Sheets[firstSheetName];
      const jsonData = xlsx.utils.sheet_to_json(worksheet, { defval: '' });

      if (!jsonData || jsonData.length === 0) {
        return res.status(400).json({ success: false, message: 'The uploaded Excel file contains no data rows.' });
      }

      const recordsToInsert = [];

      for (const row of jsonData) {
        // Case-insensitive key resolution helper
        const getValue = (targetNames) => {
          for (const key of Object.keys(row)) {
            const normalizedKey = key.trim().toLowerCase();
            if (targetNames.some(tn => normalizedKey === tn.toLowerCase() || normalizedKey.includes(tn.toLowerCase()))) {
              return row[key];
            }
          }
          return undefined;
        };

        const rawId = row['Student ID'] !== undefined ? row['Student ID'] : getValue(['student id', 'studentid', 'student_id', 'id']);
        const student_id = String(rawId !== undefined && rawId !== null ? rawId : '').trim();

        const rawName = row['Student Name'] !== undefined ? row['Student Name'] : getValue(['student name', 'studentname', 'student_name', 'name']);
        const student_name = String(rawName !== undefined && rawName !== null ? rawName : '').trim();

        const rawMarks = row['Total Marks (Out of 600)'] !== undefined 
          ? row['Total Marks (Out of 600)'] 
          : getValue(['total marks', 'marks', 'total_marks']);
        const total_marks = parseNum(rawMarks);

        const rawPct = row['Percentage'] !== undefined 
          ? row['Percentage'] 
          : getValue(['percentage', 'percent', 'pct']);
        const percentage = parseNum(rawPct);

        if (student_id || student_name) {
          recordsToInsert.push({ student_id, student_name, total_marks, percentage });
        }
      }

      if (recordsToInsert.length === 0) {
        return res.status(400).json({
          success: false,
          message: 'No valid student records found. Expected columns: Student ID, Student Name, Total Marks (Out of 600), Percentage.'
        });
      }

      // Upsert records into SQLite table
      db.serialize(() => {
        const stmt = db.prepare(`
          INSERT OR REPLACE INTO students (student_id, student_name, total_marks, percentage)
          VALUES (?, ?, ?, ?)
        `);

        let hasError = false;

        for (const record of recordsToInsert) {
          stmt.run([record.student_id, record.student_name, record.total_marks, record.percentage], (runErr) => {
            if (runErr) {
              hasError = true;
              console.error('Error inserting record:', runErr.message);
            }
          });
        }

        stmt.finalize((finalizeErr) => {
          if (hasError || finalizeErr) {
            return res.status(500).json({
              success: false,
              message: 'Failed to write all records to database: ' + (finalizeErr ? finalizeErr.message : 'Database error.')
            });
          }

          res.json({
            success: true,
            message: `Successfully uploaded and stored ${recordsToInsert.length} student record(s) in the database.`,
            count: recordsToInsert.length
          });
        });
      });

    } catch (parseError) {
      return res.status(400).json({
        success: false,
        message: 'Could not read Excel file: ' + parseError.message
      });
    }
  });
});

app.listen(PORT, () => {
  console.log(`IFHE KPI Backend Server listening on port ${PORT}`);
});