app_name = "nepal_compliance"
app_title = "Nepal Compliance"
app_publisher = "Yarsa Labs Pvt. Ltd."
app_description = "ERPNext app to comply with Nepali laws and regulations"
app_email = "support@yarsalabs.com"
app_license = "GNU General Public License (v3)"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "nepal_compliance",
# 		"logo": "/assets/nepal_compliance/logo.png",
# 		"title": "Nepal Compliance",
# 		"route": "/nepal_compliance",
# 		"has_permission": "nepal_compliance.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
app_include_css = [
    "/assets/nepal_compliance/css/nepali_calendar.css",
    "/assets/nepal_compliance/css/date.css"]

app_include_js = [
    "https://unpkg.com/react@18.3.1/umd/react.production.min.js",
    "https://unpkg.com/react-dom@18.3.1/umd/react-dom.production.min.js",
    "/assets/nepal_compliance/js/nepali_date_lib.js",
    "/assets/nepal_compliance/js/nepali_calendar_lib.js",
    "/assets/nepal_compliance/js/nepali_date_override.js",
    "/assets/nepal_compliance/js/formatter.js",
    "/assets/nepal_compliance/js/report_filter.js",
    "/assets/nepal_compliance/js/icon_patch.js",
    "/assets/nepal_compliance/js/employee_benefit_claim.js"]

boot_session = "nepal_compliance.boot.get_boot_info"

# include js, css files in header of web template
# web_include_css = "/assets/nepal_compliance/css/nepal_compliance.css"
# web_include_js = "/assets/nepal_compliance/js/nepal_compliance.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "nepal_compliance/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {
    "Company": "public/js/validate.js",
    "User": "public/js/nepali_date.js",
    "Salary Slip" : "public/js/salary_slip.js",
    "Expense Claim": "public/js/bs_date.js",
    "Leave Application": "public/js/bs_date.js",
    "Holiday List": ["public/js/bs_date.js","public/js/holiday_list.js"],
    "Holiday": "public/js/holiday_list.js",
    "Leave Allocation": "public/js/bs_date.js",
    "Attendance": "public/js/bs_date.js",
    "Fiscal Year": "public/js/bs_date.js",
    "Stock Entry": "public/js/hrms_bs_date.js",
    "Material Request": "public/js/hrms_bs_date.js",
    "Purchase Invoice": ["public/js/bs_date.js", "public/js/utils.js", "public/js/validate.js", "public/js/email.js"],
    "Purchase Order": "public/js/bs_date.js","Purchase Receipt": "public/js/bs_date.js",
    "Sales Order": "public/js/bs_date.js","Delivery Note": "public/js/bs_date.js",
    "Sales Invoice": ["public/js/bs_date.js", "public/js/utils.js", "public/js/validate.js", "public/js/email.js"],
    "CBMS Settings": "nepal_compliance/doctype/cbms_settings/cbms_settings.js",
    "Payment Entry": "public/js/bs_date.js",
    "Journal Entry": ["public/js/bs_date.js", "public/js/utils.js"],
    "Supplier": "public/js/validate.js",
    "Customer": "public/js/validate.js",
    "Request for Quotation": "public/js/bs_date.js","Supplier Quotation": "public/js/bs_date.js", "Quotation": "public/js/bs_date.js",
    "Blanket Order": "public/js/bs_date.js",
    "Landed Cost Voucher": "public/js/bs_date.js",
    "Asset": "public/js/bs_date.js", "Asset Repair": "public/js/bs_date.js", "Asset Movement": "public/js/bs_date.js", "Asset Value Adjustment": "public/js/bs_date.js", "Asset Capitalization": "public/js/bs_date.js",
    "POS Opening Entry": "public/js/bs_date.js", "POS Closing Entry": "public/js/bs_date.js",
    "Loyalty Program": "public/js/bs_date.js", "Promotional Scheme": "public/js/bs_date.js", "Pricing Rule": "public/js/bs_date.js", "Coupon Code": "public/js/bs_date.js",
    "Serial No": "public/js/bs_date.js", "Batch": "public/js/bs_date.js",
    "Installation Note": "public/js/bs_date.js", "Stock Reconciliation": "public/js/bs_date.js", "Quality Inspection": "public/js/bs_date.js", "Quick Stock Balance": "public/js/bs_date.js",
    "Payroll Entry": "public/js/payroll_bs_date.js", "Income Tax Slab": "public/js/payroll_bs_date.js", "Payroll Period": "public/js/payroll_bs_date.js", "Salary Structure Assignment": ["public/js/payroll_bs_date.js"], "Salary Withholding": "public/js/payroll_bs_date.js", "Additional Salary": "public/js/payroll_bs_date.js", "Employee Incentive": "public/js/payroll_bs_date.js", "Retention Bonus": "public/js/payroll_bs_date.js",
    "Employee Tax Exemption Proof Submission": "public/js/payroll_bs_date.js", "Employee Benefit Application": "public/js/payroll_bs_date.js", "Employee Benefit Claim": "public/js/hrms_bs_date.js",
    "Attendance Request": "public/js/hrms_bs_date.js", "Compensatory Leave Request": "public/js/hrms_bs_date.js", "Employee Advance": "public/js/hrms_bs_date.js", "Shift Assignment": "public/js/hrms_bs_date.js", "Shift Request": "public/js/hrms_bs_date.js", "Job Offer": "public/js/hrms_bs_date.js", "Employee Referral": "public/js/hrms_bs_date.js", "Shift Assignment Tool": "public/js/hrms_bs_date.js",
    "Upload Attendance": "public/js/hrms_bs_date.js", "Leave Period": "public/js/hrms_bs_date.js", "Leave Policy Assignment": "public/js/hrms_bs_date.js", "Leave Control Panel": "public/js/hrms_bs_date.js", "Leave Encashment": "public/js/hrms_bs_date.js",
    "Bulk Salary Structure Assignment": "public/js/bs_date.js", "Employee Attendance Tool": 'public/js/bs_date.js',
    "Period Closing Voucher": "public/js/bs_date.js", "Invoice Discounting": "public/js/bs_date.js", "Dunning": "public/js/bs_date.js", "Process Deferred Accounting": "public/js/bs_date.js", "POS Invoice": "public/js/bs_date.js"
}

doctype_list_js = {
    "Salary Component": "public/js/custom_button.js",
    "Leave Allocation": "public/js/utils.js",
    "Sales Invoice" : "public/js/bulk_update_nepali_date.js"
}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "nepal_compliance/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "nepal_compliance.utils.jinja_methods",
# 	"filters": "nepal_compliance.utils.jinja_filters"
# }

# Installation
# ------------
after_install = "nepal_compliance.install.install"
after_sync = ["nepal_compliance.custom_code.payroll.salary_structure.create_salary_structures",
              "nepal_compliance.custom_code.leave_type.leave_type.setup_default_leave_types"]

# Uninstallation
# ------------

before_uninstall = "nepal_compliance.uninstall.cleanup_salary_structures"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "nepal_compliance.utils.before_app_install"
# after_app_install = "nepal_compliance.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "nepal_compliance.utils.before_app_uninstall"
# after_app_uninstall = "nepal_compliance.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "nepal_compliance.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes
override_doctype_class = {
    "Sales Invoice": "nepal_compliance.overrides.custom_sales_invoice.CustomSalesInvoice",
    "Salary Structure": "nepal_compliance.overrides.salary_structure.CustomSalaryStructure",
    "Employee Benefit Claim": "nepal_compliance.overrides.employee_benefit_claim.CustomEmployeeBenefitClaim",
    "Salary Slip": "nepal_compliance.overrides.salary_slip.CustomSalarySlip",
    "Payroll Entry": "nepal_compliance.overrides.salary_slip.CustomPayrollEntry",
    "Leave Policy Assignment": "nepal_compliance.custom_code.leave_allocation.monthly_leave_bs.LeavePolicyAssignment"
}

# Document Events
# ---------------
# Hook on document methods and events
doc_events = {
    "*": {
        "validate": "nepal_compliance.backdated_doctype_restriction.validate_backdate_and_sequence"
    },
    "Purchase Invoice" : {
        "on_trash": "nepal_compliance.utils.prevent_invoice_deletion",
        "before_insert": "nepal_compliance.utils.set_vat_numbers",
        "on_submit": "nepal_compliance.qr_code.create_qr_code",
        "before_submit": "nepal_compliance.utils.bill_no_required"
    },
    "Sales Invoice" : {
        "autoname": "nepal_compliance.utils.custom_autoname",
        "before_insert": ["nepal_compliance.utils.set_vat_numbers", "nepal_compliance.utils.load_nepali_date"],
        "on_submit": "nepal_compliance.cbms_api.post_sales_invoice_or_return_to_cbms",
        "validate": "nepal_compliance.qr_code.create_qr_code"
    },
    "Salary Slip": {
        "after_insert": "nepal_compliance.patches.payroll_entry.execute",
    }
}
# Scheduled Tasks
# ---------------
scheduler_events = {
    "daily": [
        "nepal_compliance.custom_code.leave_allocation.scheduled_tasks.run_daily_bs_tasks"
    ]
}

# Testing
# -------

# before_tests = "nepal_compliance.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "nepal_compliance.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "nepal_compliance.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["nepal_compliance.utils.before_request"]
# after_request = ["nepal_compliance.utils.after_request"]

# Job Events
# ----------
# before_job = ["nepal_compliance.utils.before_job"]
# after_job = ["nepal_compliance.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"nepal_compliance.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

purchase_sales = ["Purchase Invoice", "Sales Invoice"]

doctype_lists = ["Asset","Asset Capitalization","Asset Repair","Dunning","Invoice Discounting","Journal Entry",
                 "Landed Cost Voucher","Payment Entry","Period Closing Voucher","Process Deferred Accounting","Purchase Invoice",
                 "Purchase Receipt","POS Invoice","Sales Invoice","Stock Entry","Stock Reconciliation"]