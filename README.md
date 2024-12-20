# Nepal Compliance

This project is an app developed on top of [Frappe Framework](https://github.com/frappe/frappe) [ERPNext](https://github.com/frappe/erpnext) and [Frappe HR](https://github.com/frappe/hrms)  , free and open source projects built by Frappe Technologies.

## Key Features
This app aims to customize the HR, Payroll and Accounting modules to make your installation of ERPNext compliant with the existing laws of Nepal. We plan to slowly roll out the compliance framework. This list may or may not sync with this repository's projects.

### Basic Setup
- [x] Nepali Date support for fiscal year
- [x] Nepali Date support for input fields
- [ ] Nepali Date support for lists, views, filters, sorting & searching
- [x] Nepali Date support for reports
- [ ] Nepali Date support for print templates
### Accounting & Billing
The accounting module is expected to comply with the most recent directives of Nepal Rastra Bank (NRB) and the Inland Revenue Department (IRD).
- [x] Invoice Cancellation (No Deletion)
- [x] View or Print Report of Cancelled Invoices
- [x] Displays "Copy # of Original" on subsequent invoice prints
- [ ] Audit trail records of user activities
- [x] Auto-incremented Invoice Numbers in chronological order
- [ ] Sync with Central Billing Management System (CBMS) of the IRD
- [x] Sales and Sales Return VAT Register
- [x] Purchase and Purchase Return VAT Register
- [x] Party-wise Sales and Purchase Register
- [x] Monthly  Sales and Purchase Register
- [x] Landing Cost Reports for Purchase
- [ ] Materialized Reports
- [x] VAT Return Reports
- [x] Balance Confirmation
- [x] Sales Cancellation Register
- [ ] Audit Trial Report
- [ ] SQL Query Audit Logs

### HR & Payroll
The HR and payroll module from Frappe HR is expected to fully comply with the Labor Law 2074 BS, and the latest regulations of Nepal.
- [x] Fiscal year allocation based on Nepali Date
- [x] Mandatory fields in Employee database
- [x] Attendance, Leaves and Holidays based on Nepali Date
- [x] Automatic sick leaves and home leaves based on working days
- [x] Automatic tax slab allocation based on marital status (Filing as an Individual vs Filing as a household)
- [x] Automatic Grades and Gratitude calculation
- [x] Automatic Minimum Basic Salary configuration
- [x] CIT, Insurance & other optional contributions calculation
- [x] Compliance for Employee's Provident Fund (EPF)
- [x] Compliance for Social Security Fund (SSF)
- [ ] Compatible with Biometric attendance systems
- [ ] 

