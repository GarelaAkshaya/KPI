const test = require('node:test');
const assert = require('node:assert/strict');
const { normalizeStudentRows } = require('../studentUpload');

test('normalizes uploaded workbook rows into database-friendly records', () => {
  const rows = [
    {
      'Student ID': '1001',
      'Student Name': 'Asha Kumar',
      'Total Marks (Out of 600)': 540,
      Percentage: '90',
    },
    {
      'student id': '1002',
      'student name': 'Bharat Rao',
      'total marks (out of 600)': 300,
    },
  ];

  const normalized = normalizeStudentRows(rows);

  assert.equal(normalized[0].studentId, '1001');
  assert.equal(normalized[0].studentName, 'Asha Kumar');
  assert.equal(normalized[0].totalMarks, 540);
  assert.equal(normalized[0].percentage, 90);

  assert.equal(normalized[1].studentId, '1002');
  assert.equal(normalized[1].studentName, 'Bharat Rao');
  assert.equal(normalized[1].totalMarks, 300);
  assert.equal(normalized[1].percentage, 50);
});

test('parses percentages written as percentage strings or decimals', () => {
  const rows = [
    {
      'Student ID': '1003',
      'Student Name': 'Chetan Singh',
      'Total Marks (Out of 600)': 480,
      'Percentage (%)': '80%',
    },
    {
      'student id': '1004',
      'student name': 'Disha Patil',
      'total marks (out of 600)': 330,
      'percentage': '0.55',
    },
  ];

  const normalized = normalizeStudentRows(rows);

  assert.equal(normalized[0].percentage, 80);
  assert.equal(normalized[1].percentage, 55);
});
