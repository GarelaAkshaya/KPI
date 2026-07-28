const express = require('express');
const multer = require('multer');
const XLSX = require('xlsx');
const { normalizeStudentRows, saveStudentRecords, getStudentRecords } = require('./studentUpload');

const app = express();
const upload = multer({ storage: multer.memoryStorage() });

app.use(express.json());
app.use((req, res, next) => {
  res.header('Access-Control-Allow-Origin', '*');
  res.header('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  res.header('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,OPTIONS');
  // Respond to preflight requests
  if (req.method === 'OPTIONS') {
    return res.sendStatus(204);
  }
  next();
});

app.get('/', (req, res) => res.send('IFHE KPI API'));

app.post('/api/upload-students', upload.single('file'), (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({ message: 'Please upload a file.' });
    }

    const workbook = XLSX.read(req.file.buffer, { type: 'buffer' });
    if (!workbook || !workbook.SheetNames || workbook.SheetNames.length === 0) {
      return res.status(400).json({ message: 'Uploaded file has no sheets.' });
    }

    const sheetName = workbook.SheetNames[0];
    const rows = XLSX.utils.sheet_to_json(workbook.Sheets[sheetName]);

    if (!Array.isArray(rows) || rows.length === 0) {
      return res.status(400).json({ message: 'Excel sheet is empty or could not be parsed.' });
    }

    const normalizedRecords = normalizeStudentRows(rows);

    // Validate normalized records contain required fields
    const invalid = normalizedRecords.find((r) => !r.studentId || !r.studentName);
    if (invalid) {
      return res.status(400).json({ message: 'One or more rows are missing Student ID or Student Name.' });
    }

    const count = saveStudentRecords(normalizedRecords);

    return res.status(200).json({ message: 'Student records uploaded successfully.', count });
  } catch (error) {
    console.error('Upload error:', error);
    return res.status(500).json({ message: 'Failed to process the uploaded Excel file.', error: String(error.message || error) });
  }
});

app.get('/api/students', (req, res) => {
  try {
    return res.status(200).json(getStudentRecords());
  } catch (error) {
    console.error(error);
    return res.status(500).json({ message: 'Failed to retrieve student records.' });
  }
});

app.listen(5000, () => console.log('API on 5000'));
