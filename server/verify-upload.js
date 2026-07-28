const fs = require('fs');
const path = require('path');
const http = require('node:http');
const XLSX = require('xlsx');

const boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW';
const ws = XLSX.utils.aoa_to_sheet([
  ['Student ID', 'Student Name', 'Total Marks (Out of 600)', 'Percentage'],
  ['1001', 'Asha Kumar', 540, 90],
]);
const wb = XLSX.utils.book_new();
XLSX.utils.book_append_sheet(wb, ws, 'Students');
const filePath = path.join(__dirname, 'sample-students.xlsx');
XLSX.writeFile(wb, filePath);
const fileBuffer = fs.readFileSync(filePath);

const payload = Buffer.concat([
  Buffer.from(`--${boundary}\r\nContent-Disposition: form-data; name="file"; filename="sample-students.xlsx"\r\nContent-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet\r\n\r\n`),
  fileBuffer,
  Buffer.from(`\r\n--${boundary}--\r\n`),
]);

const req = http.request(
  {
    host: 'localhost',
    port: 5000,
    path: '/api/upload-students',
    method: 'POST',
    headers: {
      'Content-Type': `multipart/form-data; boundary=${boundary}`,
      'Content-Length': payload.length,
    },
  },
  (res) => {
    let body = '';
    res.on('data', (chunk) => {
      body += chunk;
    });
    res.on('end', () => {
      console.log('status', res.statusCode);
      console.log(body);
    });
  }
);

req.on('error', (error) => {
  console.error(error);
  process.exit(1);
});

req.write(payload);
req.end();
